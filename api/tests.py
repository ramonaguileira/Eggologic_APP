import json
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from cuentas.models import Cliente, Usuario
from eggos import pagos, servicio as eggos
from eggos.models import Movimiento, Recarga
from eggos.tests import crear_cliente, crear_quincena
from mundo.models import Ajustes, Gallina
from tienda.models import Pedido


def google_dice(email="lucia@example.com", **cambios):
    datos = {"email": email, "nombre": "Lucía"}
    datos.update(cambios)
    return patch("api.google.verificar", return_value=datos)


@override_settings(EGGO_WORLD_ACTIVO=True, GOOGLE_CLIENT_ID="cliente-de-prueba")
class ApiTests(TestCase):
    def setUp(self):
        self.ana = crear_cliente()
        Cliente.objects.create(usuario=self.ana, telefono="099", direccion="Calle 1")
        self.quincena = crear_quincena()

    def enviar(self, nombre, datos=None, args=None):
        return self.client.post(reverse(f"api:{nombre}", args=args), json.dumps(datos or {}), content_type="application/json")

    def cargar(self, cantidad):
        eggos.mover(self.ana, cantidad, Movimiento.Motivo.RECARGA)

    # --- Interruptor y acceso ---

    @override_settings(EGGO_WORLD_ACTIVO=False)
    def test_apagado_no_existe(self):
        self.client.force_login(self.ana)
        for nombre in ["chacra", "estado"]:
            self.assertEqual(self.client.get(reverse(f"api:{nombre}")).status_code, 404)
        self.assertEqual(self.enviar("pedir").status_code, 404)

    def test_la_pagina_lleva_el_identificador_de_google(self):
        self.assertContains(self.client.get(reverse("api:chacra")), "cliente-de-prueba")

    def test_sin_entrar_no_hay_datos(self):
        self.assertEqual(self.client.get(reverse("api:estado")).status_code, 401)
        self.assertEqual(self.enviar("pedir").status_code, 401)

    def test_el_equipo_y_los_restaurantes_no_entran(self):
        self.client.force_login(Usuario.objects.create_user(username="chofer", rol=Usuario.Rol.CHOFER))
        self.assertEqual(self.client.get(reverse("api:estado")).status_code, 401)

    # --- Entrar con Google ---

    def test_google_crea_la_cuenta_la_primera_vez(self):
        with google_dice():
            self.assertEqual(self.enviar("entrar_con_google", {"credential": "x"}).status_code, 200)
        lucia = Usuario.objects.get(email="lucia@example.com")
        self.assertEqual((lucia.rol, lucia.first_name), (Usuario.Rol.CLIENTE, "Lucía"))
        self.assertFalse(lucia.has_usable_password())
        self.assertEqual(self.client.get(reverse("api:estado")).status_code, 200)

    def test_google_entra_a_la_cuenta_que_ya_existia(self):
        with google_dice(email="ANA@example.com"):
            self.enviar("entrar_con_google", {"credential": "x"})
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.ana.pk)
        self.assertEqual(Usuario.objects.count(), 1)

    def test_google_no_abre_cuentas_del_equipo(self):
        Usuario.objects.create_user(username="ramon", email="jefe@example.com", rol=Usuario.Rol.ADMIN)
        with google_dice(email="jefe@example.com"):
            self.assertEqual(self.enviar("entrar_con_google", {"credential": "x"}).status_code, 403)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_un_comprobante_falso_no_entra(self):
        respuesta = lambda datos: type("R", (), {"status_code": 200, "json": lambda self: datos})()
        bueno = {"aud": "cliente-de-prueba", "iss": "accounts.google.com", "email_verified": "true", "exp": "99999999999", "email": "x@example.com"}
        for cambio in [{"aud": "otra-app"}, {"email_verified": "false"}, {"exp": "1"}, {"iss": "trucho.com"}]:
            with patch("api.google.requests.get", return_value=respuesta({**bueno, **cambio})):
                self.assertEqual(self.enviar("entrar_con_google", {"credential": "x"}).status_code, 400, cambio)
        with patch("api.google.requests.get", return_value=respuesta(bueno)):
            self.assertEqual(self.enviar("entrar_con_google", {"credential": "x"}).status_code, 200)

    # --- El estado y las acciones ---

    def test_el_estado_trae_todo_lo_que_muestra_la_chacra(self):
        self.client.force_login(self.ana)
        estado = self.client.get(reverse("api:estado")).json()
        self.assertEqual(estado["eggos"]["saldo"], 0)
        self.assertEqual(estado["productos"][0]["precio"], 160)
        self.assertEqual(estado["productos"][0]["precio_eggos"], 151)
        self.assertEqual(estado["adopcion"]["lugares"], 34)
        self.assertEqual(estado["tienda"]["huevos_disponibles"], 200)
        self.assertEqual([plan["precio"] for plan in estado["planes"]], [3600, 1900, 170])

    def test_adoptar_con_saldo(self):
        self.client.force_login(self.ana)
        self.cargar(2000)
        respuesta = self.enviar("adoptar", {"plan": "un_anio", "nombre": "Clota", "color": "colorada"}).json()
        self.assertIsNone(respuesta["pago"])
        self.assertEqual(respuesta["estado"]["gallinas"][0]["nombre"], "Clota")
        self.assertEqual(respuesta["estado"]["eggos"]["saldo"], 100)

    def test_adoptar_sin_saldo_pide_pagar_la_diferencia(self):
        self.client.force_login(self.ana)
        respuesta = self.enviar("adoptar", {"plan": "un_anio", "nombre": "Clota", "medio": "transferencia"}).json()
        self.assertEqual(respuesta["pago"]["transferir"]["monto"], 1900)
        self.assertEqual(respuesta["estado"]["gallinas"][0]["estado"], "pendiente")

    def test_no_se_puede_tocar_la_gallina_de_otro(self):
        beto = crear_cliente("beto")
        gallina = Gallina.objects.create(usuario=beto, nombre="Ajena", plan="un_anio")
        self.client.force_login(self.ana)
        self.assertEqual(self.enviar("renombrar", {"nombre": "Mía"}, [gallina.pk]).status_code, 400)
        self.assertEqual(self.enviar("dar_larvas", {"gallina": gallina.pk}).status_code, 400)
        gallina.refresh_from_db()
        self.assertEqual(gallina.nombre, "Ajena")

    def test_comprar_con_eggos_y_con_plata(self):
        self.client.force_login(self.ana)
        self.cargar(500)
        items = [{"producto": self.quincena.pk, "cantidad": 1}]
        respuesta = self.enviar("pedir", {"items": items, "forma_pago": "eggos"}).json()
        self.assertEqual(respuesta["estado"]["eggos"]["saldo"], 349)
        respuesta = self.enviar("pedir", {"items": items, "forma_pago": "contra_entrega"}).json()
        self.assertEqual([p["total"] for p in respuesta["estado"]["pedidos"]], [160, 151])
        self.assertEqual(Ajustes.actuales().huevos_disponibles, 170)

    def test_un_pedido_que_falla_avisa_y_no_deja_nada(self):
        self.client.force_login(self.ana)
        items = [{"producto": self.quincena.pk, "cantidad": 1}]
        respuesta = self.enviar("pedir", {"items": items, "forma_pago": "eggos"})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("Eggos", respuesta.json()["error"])
        self.assertFalse(Pedido.objects.exists())
        self.assertEqual(Ajustes.actuales().huevos_disponibles, 200)

    def test_el_primer_pedido_guarda_la_direccion(self):
        Cliente.objects.filter(usuario=self.ana).update(direccion="", telefono="")
        self.client.force_login(self.ana)
        items = [{"producto": self.quincena.pk, "cantidad": 1}]
        self.assertEqual(self.enviar("pedir", {"items": items, "forma_pago": "contra_entrega"}).status_code, 400)
        datos = {"items": items, "forma_pago": "contra_entrega", "direccion": "Ruta 10", "telefono": "098"}
        self.assertEqual(self.enviar("pedir", datos).status_code, 200)
        self.assertEqual(self.ana.cliente.__class__.objects.get(usuario=self.ana).direccion, "Ruta 10")

    def test_datos_raros_no_rompen_nada(self):
        self.client.force_login(self.ana)
        for nombre, datos in [
            ("dar_larvas", {"gallina": "x", "cantidad": "muchas"}),
            ("pedir_huevos", {"huevos": "quince"}),
            ("pedir", {"items": "no es una lista", "forma_pago": "eggos"}),
            ("pedir", {"items": [{"producto": self.quincena.pk, "cantidad": -3}], "forma_pago": "eggos"}),
            ("adoptar", {"plan": ["dos_anios"], "nombre": "Clota"}),
            ("recargar", {"paquete": "500", "medio": "transferencia"}),
        ]:
            self.assertEqual(self.enviar(nombre, datos).status_code, 400, (nombre, datos))
        self.assertFalse(Pedido.objects.exists())
        self.assertFalse(Gallina.objects.exists())

    def test_recargar_solo_en_paquetes(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.enviar("recargar", {"paquete": 123, "medio": "transferencia"}).status_code, 400)
        respuesta = self.enviar("recargar", {"paquete": 500, "medio": "transferencia"}).json()
        self.assertEqual(respuesta["pago"]["transferir"]["monto"], 500)
        self.assertEqual(respuesta["estado"]["eggos"]["saldo"], 0)
        self.assertEqual(len(respuesta["estado"]["eggos"]["recargas_pendientes"]), 1)

    def test_levante_y_perfil(self):
        self.client.force_login(self.ana)
        self.cargar(100)
        respuesta = self.enviar("pedir_levante", {"nota": "Timbre roto"}).json()
        self.assertEqual(respuesta["estado"]["levantes"][0]["paso"], "pedido")
        self.assertEqual(respuesta["estado"]["eggos"]["saldo"], 40)
        respuesta = self.enviar("guardar_perfil", {"nombre": "Ana María", "telefono": "091", "direccion": "Otra"}).json()
        self.assertEqual(respuesta["estado"]["yo"]["nombre"], "Ana María")

    # --- Mercado Pago ---

    @override_settings(MERCADOPAGO_ACCESS_TOKEN="credencial-de-prueba")
    def test_mercado_pago_acredita_la_recarga_una_sola_vez(self):
        self.client.force_login(self.ana)
        with patch("eggos.pagos.crear_pago", return_value="https://pagar.example/1") as crear:
            respuesta = self.enviar("recargar", {"paquete": 1000, "medio": "mercado_pago"}).json()
        self.assertEqual(respuesta["pago"]["ir_a"], "https://pagar.example/1")
        recarga = Recarga.objects.get()
        self.assertEqual(crear.call_args.args[2], f"recarga-{recarga.pk}")
        self.client.logout()
        pago = {"aprobado": True, "referencia": f"recarga-{recarga.pk}", "monto": 1000}
        with patch("eggos.pagos.consultar_pago", return_value=pago):
            for _ in range(2):
                aviso = self.client.post(reverse("api:aviso_de_mercado_pago"), json.dumps({"type": "payment", "data": {"id": "77"}}), content_type="application/json")
                self.assertEqual(aviso.status_code, 200)
        self.assertEqual(eggos.saldo(self.ana), 1000)

    @override_settings(MERCADOPAGO_ACCESS_TOKEN="credencial-de-prueba")
    def test_un_aviso_no_alcanza_si_el_pago_no_esta_aprobado_o_es_por_menos(self):
        recarga = Recarga.objects.create(usuario=self.ana, monto=1000, medio=Recarga.Medio.MERCADO_PAGO)
        for pago in [
            {"aprobado": False, "referencia": f"recarga-{recarga.pk}", "monto": 1000},
            {"aprobado": True, "referencia": f"recarga-{recarga.pk}", "monto": 10},
            {"aprobado": True, "referencia": "cualquier-cosa", "monto": 1000},
        ]:
            with patch("eggos.pagos.consultar_pago", return_value=pago):
                self.client.post(reverse("api:aviso_de_mercado_pago"), json.dumps({"type": "payment", "data": {"id": "77"}}), content_type="application/json")
        self.assertEqual(eggos.saldo(self.ana), 0)

    def test_sin_credencial_no_se_ofrece_mercado_pago(self):
        self.client.force_login(self.ana)
        self.assertFalse(self.client.get(reverse("api:estado")).json()["tienda"]["mercado_pago"])
        respuesta = self.enviar("recargar", {"paquete": 500, "medio": "mercado_pago"})
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(Recarga.objects.exists())

    @override_settings(MERCADOPAGO_ACCESS_TOKEN="credencial-de-prueba")
    def test_pedido_pagado_con_mercado_pago_queda_confirmado(self):
        self.client.force_login(self.ana)
        items = [{"producto": self.quincena.pk, "cantidad": 1}]
        with patch("eggos.pagos.crear_pago", return_value="https://pagar.example/2"):
            respuesta = self.enviar("pedir", {"items": items, "forma_pago": "mercado_pago"}).json()
        pedido = Pedido.objects.get(pk=respuesta["pedido"])
        pago = {"aprobado": True, "referencia": f"pedido-{pedido.pk}", "monto": 160}
        with patch("eggos.pagos.consultar_pago", return_value=pago):
            self.client.post(reverse("api:aviso_de_mercado_pago") + "?type=payment&data.id=5")
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.Estado.CONFIRMADO)
