import os
from io import StringIO
from unittest.mock import patch

import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from cuentas.models import Restaurante

from .cliente import ErrorGuardian, Sesion, clave_de_restaurante

URL = "https://guardian.prueba/api/v1"
VARIABLES = {
    "GUARDIAN_URL": URL,
    "GUARDIAN_POLICY_ID": "policy-1",
    "GUARDIAN_PROPONENTE_EMAIL": "proponente@prueba.uy",
    "GUARDIAN_PROPONENTE_PASSWORD": "clave-proponente",
    "GUARDIAN_R001_EMAIL": "r001@prueba.uy",
    "GUARDIAN_R001_PASSWORD": "clave-r001",
}
USUARIOS = {
    "proponente@prueba.uy": ("clave-proponente", "Eggologic_Proponente", "Project_Proponent"),
    "r001@prueba.uy": ("clave-r001", "Eggologic_r001", "Project_Participating_Entity"),
}


class Respuesta:
    def __init__(self, datos, status_code=200):
        self.datos = datos
        self.status_code = status_code
        self.ok = status_code < 400

    def json(self):
        return self.datos


class GuardianFalso:
    """Contesta como MGS a los pedidos de la app, sin salir a la red."""

    def __init__(self, red="testnet", nombre_alta="R-001", estado_alta="APPROVED", proyectos=()):
        self.red = red
        self.nombre_alta = nombre_alta
        self.estado_alta = estado_alta
        self.proyectos = list(proyectos)
        self.pedidos = []

    def did(self, usuario):
        return f"did:hedera:{self.red}:{usuario}_0.0.1"

    def __call__(self, sesion_http, metodo, url, json=None, timeout=None):
        ruta = url.removeprefix(URL + "/")
        self.pedidos.append((metodo, ruta, json))
        usuario = sesion_http.headers.get("Authorization", "").removeprefix("Bearer acceso-")

        if ruta == "accounts/loginByEmail":
            password, nombre, _ = USUARIOS.get(json["email"], (None, None, None))
            if password != json["password"]:
                return Respuesta({"message": "Unauthorized", "statusCode": 401}, 401)
            return Respuesta({"success": True, "login": {
                "username": nombre, "did": self.did(nombre), "role": "USER", "refreshToken": f"renovar-{nombre}",
            }})
        if ruta == "accounts/access-token":
            return Respuesta({"accessToken": "acceso-" + json["refreshToken"].removeprefix("renovar-")})
        if ruta == "policies/policy-1":
            rol = {nombre: rol for _, nombre, rol in USUARIOS.values()}[usuario]
            return Respuesta({"name": "Food Loss & Waste (International) - 1.0", "status": "PUBLISH", "userRole": rol})
        if ruta == "policies/policy-1/tag/ppe_grid_pp/blocks":
            return Respuesta({"data": [{
                "owner": self.did("Eggologic_r001"),
                "option": {"status": self.estado_alta},
                "document": {"credentialSubject": [{"field0": self.nombre_alta, "field1": "Restaurante"}]},
            }]})
        if ruta == "policies/policy-1/tag/project_grid_pp_2/blocks":
            return Respuesta({"data": [{"option": {"status": estado}} for estado in self.proyectos]})
        if metodo == "POST" and ruta == "policies/policy-1/tag/add_entity_report_btn/blocks":
            return Respuesta({})
        return Respuesta({"message": "Not Found"}, 404)


@override_settings(GUARDIAN_URL=URL, GUARDIAN_POLICY_ID="policy-1")
@patch.dict(os.environ, VARIABLES)
class SesionTests(TestCase):
    def test_clave_de_restaurante(self):
        self.assertEqual(clave_de_restaurante("R-001"), "R001")

    def test_login_abre_la_sesion_con_el_token_de_acceso(self):
        with patch.object(requests.Session, "request", autospec=True, side_effect=GuardianFalso()):
            sesion = Sesion("PROPONENTE")
        self.assertEqual(sesion.usuario, "Eggologic_Proponente")
        self.assertEqual(sesion.red, "testnet")
        self.assertEqual(sesion.http.headers["Authorization"], "Bearer acceso-Eggologic_Proponente")

    def test_enviar_hace_post_al_bloque_por_tag(self):
        guardian = GuardianFalso()
        with patch.object(requests.Session, "request", autospec=True, side_effect=guardian):
            Sesion("R001").enviar("add_entity_report_btn", {"document": {"field0": "x"}, "ref": None})
        self.assertEqual(
            guardian.pedidos[-1],
            ("POST", "policies/policy-1/tag/add_entity_report_btn/blocks", {"document": {"field0": "x"}, "ref": None}),
        )

    def test_login_fallido_no_muestra_la_contrasena(self):
        with patch.dict(os.environ, {"GUARDIAN_R001_PASSWORD": "clave-equivocada"}):
            with patch.object(requests.Session, "request", autospec=True, side_effect=GuardianFalso()):
                with self.assertRaises(ErrorGuardian) as error:
                    Sesion("R001")
        self.assertIn("401", str(error.exception))
        self.assertNotIn("clave-equivocada", str(error.exception))

    def test_sin_credenciales_nombra_las_variables_que_faltan(self):
        with self.assertRaisesMessage(ErrorGuardian, "GUARDIAN_R002_EMAIL"):
            Sesion("R002")

    def test_sin_red_da_error_de_guardian(self):
        with patch.object(requests.Session, "request", side_effect=requests.ConnectionError("sin red")):
            with self.assertRaisesMessage(ErrorGuardian, "No se pudo conectar"):
                Sesion("PROPONENTE")


@override_settings(GUARDIAN_URL=URL, GUARDIAN_POLICY_ID="policy-1")
@patch.dict(os.environ, VARIABLES)
class GuardianEstadoTests(TestCase):
    def setUp(self):
        Restaurante.objects.create(nombre="La Huerta", codigo="R-001")
        Restaurante.objects.create(nombre="Parrilla del Puerto", codigo="R-002")

    def correr(self, guardian):
        salida = StringIO()
        with patch.object(requests.Session, "request", autospec=True, side_effect=guardian):
            call_command("guardian_estado", stdout=salida)
        return salida.getvalue()

    def test_todo_en_orden(self):
        salida = self.correr(GuardianFalso(proyectos=["Validated"]))
        self.assertIn("Red: testnet", salida)
        self.assertIn("Alta aprobada por el Proponente", salida)
        self.assertIn("Sin usuario en Guardian (faltan GUARDIAN_R002_EMAIL", salida)
        self.assertIn("Hay un proyecto validado", salida)
        self.assertIn("Conexión con Guardian en orden", salida)

    def test_avisa_si_el_alta_no_usa_el_codigo_publico_sin_mostrar_el_nombre(self):
        salida = self.correr(GuardianFalso(nombre_alta="Nombre Comercial"))
        self.assertIn("debería ser R-001", salida)
        self.assertNotIn("Nombre Comercial", salida)

    def test_avisa_si_no_hay_proyecto_validado(self):
        salida = self.correr(GuardianFalso(proyectos=["Waiting to be Added"]))
        self.assertIn("Ningún proyecto validado", salida)

    def test_falla_si_no_es_testnet(self):
        with self.assertRaisesMessage(CommandError, "problema"):
            self.correr(GuardianFalso(red="mainnet"))

    def test_falla_si_falta_una_variable(self):
        with patch.dict(os.environ, {"GUARDIAN_POLICY_ID": ""}):
            with self.assertRaisesMessage(CommandError, "Faltan variables"):
                self.correr(GuardianFalso())

    def test_nunca_muestra_las_credenciales(self):
        salida = self.correr(GuardianFalso(proyectos=["Validated"]))
        for valor in VARIABLES.values():
            if "@" in valor or valor.startswith("clave"):
                self.assertNotIn(valor, salida)
