import json as json_
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from captura.models import Retiro
from cuentas.models import Restaurante, Usuario

from .cliente import ErrorGuardian, Sesion, clave_de_restaurante
from .models import ReporteMensual
from .reportes import documento, enviar, meses_por_verificar, revisar, verificar

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
        self.reportes = []  # documentos de reportes de restaurantes, como los guarda Guardian
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
            datos = [{"type": "project", "option": {"status": estado}} for estado in self.proyectos]
            datos += [{"type": "approved_project", "option": {"status": "Validated"}} for estado in self.proyectos if estado == "Validated"]
            return Respuesta({"data": datos})
        if ruta == "policies/policy-1/tag/projects_grid_ppe/blocks":
            validado = {"id": "proyecto-1", "type": "approved_project", "option": {"status": "Validated"}}
            return Respuesta({"data": [validado] if "Validated" in self.proyectos else []})
        if metodo == "POST" and ruta == "policies/policy-1/tag/add_entity_report_btn/blocks":
            self.reportes.append(reporte_en_guardian(json["document"], "entity_report", "Waiting for Verification"))
            return Respuesta({})
        if ruta == "policies/policy-1/tag/entity_report_grid_ppe/blocks":
            return Respuesta({"data": [doc for doc in self.reportes if doc["type"] == "entity_report"]})
        if ruta == "policies/policy-1/tag/entity_report_grid_pp/blocks":
            return Respuesta({"data": self.reportes})
        if metodo == "POST" and ruta == "policies/policy-1/tag/approve_ppe_report_btn/blocks":
            campos = json["document"]["document"]["credentialSubject"][0]
            self.reportes.append(reporte_en_guardian(campos, "approved_entity_report", "Approved"))
            return Respuesta({})
        return Respuesta({"message": "Not Found"}, 404)


def reporte_en_guardian(campos, tipo, estado):
    return {
        "type": tipo, "option": {"status": estado}, "document": {"credentialSubject": [campos]},
        "topicId": "0.0.999", "messageId": "1791000000.000000001",
    }


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
        self.assertIn("1 proyecto(s) en estado Validated", salida)
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


HOY = date(2026, 10, 6)
AGOSTO = date(2026, 8, 1)


def guardian_falso(guardian):
    return patch.object(requests.Session, "request", autospec=True, side_effect=guardian)


@override_settings(GUARDIAN_URL=URL, GUARDIAN_POLICY_ID="policy-1")
@patch.dict(os.environ, VARIABLES)
class ReporteMensualTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(username="admin", password="clave-de-prueba-123", rol=Usuario.Rol.ADMIN)
        self.huerta = Restaurante.objects.create(nombre="La Huerta", codigo="R-001")
        self.parrilla = Restaurante.objects.create(nombre="Parrilla del Puerto", codigo="R-002")  # sin usuario en Guardian

    def retiro(self, restaurante, dia, organicos="500", clasificado=True):
        mitad = Decimal(organicos) / 2
        return Retiro.objects.create(
            restaurante=restaurante, registrado_por=self.admin,
            fecha=timezone.make_aware(datetime.combine(dia, datetime.min.time()).replace(hour=12)),
            kg_levantados=Decimal(organicos) + 10,
            kg_impropios=Decimal("10") if clasificado else None,
            kg_restos_vegetales=mitad if clasificado else None,
            kg_residuos_plato=mitad if clasificado else None,
        )

    def test_revisar_suma_los_retiros_clasificados_del_mes(self):
        self.retiro(self.huerta, date(2026, 8, 3), "300")
        self.retiro(self.huerta, date(2026, 8, 31), "700")
        self.retiro(self.huerta, date(2026, 9, 1), "999")  # otro mes
        revision = revisar(self.huerta, AGOSTO, HOY)
        self.assertEqual(revision["retiros"], 2)
        self.assertEqual(revision["kg_organicos"], Decimal("1000"))
        self.assertEqual(revision["emisiones"]["neto"], Decimal("0.35"))  # 1000 × 0,70 × 0,5 / 1000
        self.assertEqual(revision["motivo"], "")

    def test_no_se_verifica_un_mes_abierto_ni_con_retiros_sin_clasificar(self):
        self.retiro(self.huerta, date(2026, 10, 2))
        self.assertEqual(revisar(self.huerta, date(2026, 10, 1), HOY)["motivo"], "Mes en curso")
        self.retiro(self.huerta, date(2026, 8, 3))
        self.retiro(self.huerta, date(2026, 8, 4), clasificado=False)
        self.assertEqual(revisar(self.huerta, AGOSTO, HOY)["motivo"], "Faltan clasificar 1")

    def test_no_se_verifica_sin_usuario_en_guardian_ni_con_muy_pocos_kg(self):
        self.retiro(self.parrilla, date(2026, 8, 3))
        self.assertEqual(revisar(self.parrilla, AGOSTO, HOY)["motivo"], "Sin usuario en el registro")
        self.retiro(self.huerta, date(2026, 8, 3), "20")  # 0,007 tCO2e: no llega a 0,01
        self.assertEqual(revisar(self.huerta, AGOSTO, HOY)["motivo"], "Muy pocos kg")

    def test_meses_por_verificar_saca_el_mes_en_curso_y_los_verificados(self):
        self.retiro(self.huerta, date(2026, 8, 3))
        self.retiro(self.huerta, date(2026, 9, 3))
        self.retiro(self.huerta, date(2026, 10, 3))
        verificar(self.huerta, AGOSTO, self.admin, HOY)
        meses = [(fila["restaurante"].codigo, fila["mes"]) for fila in meses_por_verificar(HOY)]
        self.assertEqual(meses, [("R-001", date(2026, 9, 1))])

    def test_verificar_guarda_los_numeros_una_sola_vez(self):
        self.retiro(self.huerta, date(2026, 8, 3), "1000")
        reporte = verificar(self.huerta, AGOSTO, self.admin, HOY)
        self.assertEqual((reporte.retiros, reporte.kg_organicos, reporte.tco2e_neto), (1, Decimal("1000"), Decimal("0.35")))
        self.assertEqual(reporte.estado, ReporteMensual.Estado.EN_COLA)
        with self.assertRaisesMessage(Exception, "ya está verificado"):
            verificar(self.huerta, AGOSTO, self.admin, HOY)

    def test_el_documento_lleva_el_codigo_y_nunca_el_nombre(self):
        self.retiro(self.huerta, date(2026, 8, 3), "1000")
        doc = documento(verificar(self.huerta, AGOSTO, self.admin, HOY))
        self.assertEqual(doc["field0"], "Retiros de residuo orgánico R-001 2026-08")
        self.assertEqual(doc["field7"], 0.35)
        self.assertEqual(doc["field8"], {"field0": "2026-08-01", "field1": "2026-08-31"})
        self.assertNotIn("Huerta", json_.dumps(doc, ensure_ascii=False))

    def test_enviar_manda_el_reporte_como_restaurante_y_lo_aprueba_como_proponente(self):
        self.retiro(self.huerta, date(2026, 8, 3), "1000")
        reporte = verificar(self.huerta, AGOSTO, self.admin, HOY)
        guardian = GuardianFalso(proyectos=["Validated"])
        with guardian_falso(guardian):
            enviar(reporte)
        self.assertEqual(reporte.estado, ReporteMensual.Estado.REGISTRADO)
        posts = [(ruta.split("/")[3], datos) for metodo, ruta, datos in guardian.pedidos if metodo == "POST" and "tag" in ruta]
        self.assertEqual([tag for tag, _ in posts], ["add_entity_report_btn", "approve_ppe_report_btn"])
        self.assertEqual(posts[0][1]["ref"]["id"], "proyecto-1")
        self.assertEqual(posts[1][1]["tag"], "Button_0")
        self.assertEqual(reporte.enlace_publico, "https://hashscan.io/testnet/transaction/1791000000.000000001")

    def test_enviar_de_nuevo_no_duplica_el_reporte(self):
        self.retiro(self.huerta, date(2026, 8, 3), "1000")
        reporte = verificar(self.huerta, AGOSTO, self.admin, HOY)
        guardian = GuardianFalso(proyectos=["Validated"])
        guardian.reportes.append(reporte_en_guardian(documento(reporte), "entity_report", "Waiting for Verification"))
        with guardian_falso(guardian):
            enviar(reporte)
        tags = [ruta.split("/")[3] for metodo, ruta, _ in guardian.pedidos if metodo == "POST" and "tag" in ruta]
        self.assertEqual(tags, ["approve_ppe_report_btn"])

    def test_si_el_reporte_todavia_no_aparece_espera_sin_error(self):
        # Guardian procesa el envío en segundo plano: el Proponente puede no verlo todavía.
        self.retiro(self.huerta, date(2026, 8, 3), "1000")
        reporte = verificar(self.huerta, AGOSTO, self.admin, HOY)
        reporte.estado = ReporteMensual.Estado.ENVIADO
        reporte.save()
        salida = StringIO()
        with guardian_falso(GuardianFalso(proyectos=["Validated"])):  # el Proponente no ve ningún reporte
            call_command("guardian_enviar", stdout=salida)
        reporte.refresh_from_db()
        self.assertEqual((reporte.estado, reporte.intentos, reporte.ultimo_error), (ReporteMensual.Estado.ENVIADO, 0, ""))
        self.assertIn("sigue en la próxima vuelta", salida.getvalue())

    def test_si_falla_el_comando_guarda_el_error_y_el_reporte_sigue_en_cola(self):
        self.retiro(self.huerta, date(2026, 8, 3), "1000")
        reporte = verificar(self.huerta, AGOSTO, self.admin, HOY)
        with guardian_falso(GuardianFalso(proyectos=[])):  # sin proyecto validado
            call_command("guardian_enviar", stdout=StringIO())
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, ReporteMensual.Estado.EN_COLA)
        self.assertEqual(reporte.intentos, 1)
        self.assertIn("ningún proyecto validado", reporte.ultimo_error)


@override_settings(GUARDIAN_URL=URL, GUARDIAN_POLICY_ID="policy-1")
@patch.dict(os.environ, VARIABLES)
class PantallaDeReportesTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(username="admin", password="clave-de-prueba-123", rol=Usuario.Rol.ADMIN)
        self.huerta = Restaurante.objects.create(nombre="La Huerta", codigo="R-001")
        self.mes_pasado = (timezone.localdate().replace(day=1) - timedelta(days=1)).replace(day=1)
        Retiro.objects.create(
            restaurante=self.huerta, registrado_por=self.admin,
            fecha=timezone.make_aware(datetime.combine(self.mes_pasado, datetime.min.time()).replace(hour=12)),
            kg_levantados=Decimal("510"), kg_impropios=Decimal("10"),
            kg_restos_vegetales=Decimal("300"), kg_residuos_plato=Decimal("200"),
        )

    def test_solo_la_administracion_entra(self):
        operador = Usuario.objects.create_user(username="operador", password="clave-de-prueba-123", rol=Usuario.Rol.OPERADOR)
        self.client.force_login(operador)
        self.assertEqual(self.client.get(reverse("guardian:reportes")).status_code, 403)

    def test_enviar_al_registro_desde_la_pantalla(self):
        verificar(self.huerta, self.mes_pasado, self.admin)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("guardian:reportes")), "Enviar al registro")
        self.assertEqual(self.client.get(reverse("guardian:enviar_al_registro")).status_code, 405)
        with guardian_falso(GuardianFalso(proyectos=["Validated"])):
            respuesta = self.client.post(reverse("guardian:enviar_al_registro"), follow=True)
        self.assertContains(respuesta, "Registrados: 1.")
        self.assertEqual(ReporteMensual.objects.get().estado, ReporteMensual.Estado.REGISTRADO)
        self.assertNotContains(respuesta, "Enviar al registro</button>")

    def test_verificar_desde_la_pantalla(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("guardian:reportes"))
        self.assertContains(respuesta, "R-001 · La Huerta")
        respuesta = self.client.post(
            reverse("guardian:reportes"), {"restaurante": self.huerta.pk, "mes": self.mes_pasado.isoformat()}, follow=True
        )
        self.assertContains(respuesta, "queda en cola")
        reporte = ReporteMensual.objects.get()
        self.assertEqual((reporte.mes, reporte.verificado_por), (self.mes_pasado, self.admin))
