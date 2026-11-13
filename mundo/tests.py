from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cuentas.models import Usuario
from eggos import servicio as eggos
from eggos.models import Movimiento, Recarga
from eggos.tests import crear_cliente, crear_quincena, mover_el
from tienda.models import Pedido, Producto

from . import servicio
from .models import Ajustes, Gallina, Levante


def con_saldo(usuario, cantidad):
    eggos.mover(usuario, cantidad, Movimiento.Motivo.RECARGA)


def levante_retirado(usuario, kg, hace_dias):
    return Levante.objects.create(
        usuario=usuario, direccion="x", kg=Decimal(kg), estado=Levante.Estado.RETIRADO,
        retirado_en=timezone.now() - timedelta(days=hace_dias),
    )


class AdoptarTests(TestCase):
    def setUp(self):
        self.ana = crear_cliente()

    def test_cupo_con_los_numeros_de_hoy(self):
        # 60 gallinas, 10 % a Camino Verde: hasta 34 adoptadas (plan, punto 3.4).
        self.assertEqual(Ajustes.actuales().cupo_de_gallinas(), 34)

    def test_con_saldo_se_cobra_y_empieza_a_poner(self):
        con_saldo(self.ana, 4000)
        gallina, recarga = servicio.adoptar(self.ana, "dos_anios", "Clota", "colorada")
        self.assertIsNone(recarga)
        self.assertEqual(gallina.estado, Gallina.Estado.ACTIVA)
        self.assertEqual(eggos.saldo(self.ana), 400)
        self.assertEqual(gallina.pago_hasta, gallina.inicio + timedelta(days=730))

    def test_sin_saldo_queda_pendiente_por_la_diferencia_exacta(self):
        con_saldo(self.ana, 100)
        gallina, recarga = servicio.adoptar(self.ana, "un_anio", "Pepa", "blanca", Recarga.Medio.TRANSFERENCIA)
        self.assertEqual(gallina.estado, Gallina.Estado.PENDIENTE)
        self.assertEqual(recarga.monto, 1800)
        # Cuando Eggologic confirma la transferencia, la gallina se activa sola.
        servicio.acreditar_recarga(recarga)
        gallina.refresh_from_db()
        self.assertEqual(gallina.estado, Gallina.Estado.ACTIVA)
        self.assertEqual(eggos.saldo(self.ana), 0)

    def test_sin_saldo_y_sin_medio_de_pago_no_queda_nada_creado(self):
        with self.assertRaises(servicio.NoSePuede):
            servicio.adoptar(self.ana, "un_anio", "Pepa", "blanca")
        self.assertFalse(Gallina.objects.exists())

    def test_maximo_por_cuenta_y_cupo(self):
        con_saldo(self.ana, 9000)
        for numero in range(4):
            servicio.adoptar(self.ana, "un_anio", f"G{numero}", "blanca")
        with self.assertRaises(servicio.NoSePuede):
            servicio.adoptar(self.ana, "un_anio", "Quinta", "blanca")
        ajustes = Ajustes.actuales()
        ajustes.gallinas_en_postura = 1
        ajustes.save()
        with self.assertRaises(servicio.NoSePuede):
            servicio.adoptar(crear_cliente("beto"), "un_anio", "Sin lugar", "blanca", Recarga.Medio.TRANSFERENCIA)


class HuevosTests(TestCase):
    def setUp(self):
        self.ana = crear_cliente()
        self.hoy = timezone.localdate()

    def gallina(self, hace_dias, plan="dos_anios", dias_pagos=730):
        inicio = self.hoy - timedelta(days=hace_dias)
        return Gallina.objects.create(
            usuario=self.ana, nombre="Clota", plan=plan, estado=Gallina.Estado.ACTIVA,
            inicio=inicio, pago_hasta=inicio + timedelta(days=dias_pagos),
        )

    def test_200_huevos_por_anio(self):
        self.assertEqual(self.gallina(hace_dias=365).huevos_puestos(), 200)
        # Una quincena cada 27 o 28 días.
        self.assertEqual(Gallina.objects.get().huevos_puestos(self.hoy - timedelta(days=365 - 28)), 15)

    def test_deja_de_poner_cuando_termina_el_plan(self):
        gallina = self.gallina(hace_dias=900)
        self.assertEqual(gallina.huevos_puestos(), 400)

    def test_las_larvas_suman_huevos_hasta_el_tope_del_anio(self):
        gallina = self.gallina(hace_dias=100)
        levante_retirado(self.ana, "30", hace_dias=15)
        self.assertEqual(servicio.larvas_disponibles(self.ana), 30)
        antes = gallina.huevos_puestos()
        self.assertEqual(servicio.dar_larvas(self.ana, gallina, 30), 20)
        self.assertEqual(gallina.huevos_puestos(), antes + 20)
        self.assertEqual(gallina.produccion_anual(), 220)
        self.assertEqual(servicio.larvas_disponibles(self.ana), 10)
        with self.assertRaises(servicio.NoSePuede):
            servicio.dar_larvas(self.ana, gallina, 1)

    def test_las_larvas_tardan_14_dias_y_despues_la_gallina_come_sola(self):
        gallina = self.gallina(hace_dias=100)
        levante = levante_retirado(self.ana, "4.6", hace_dias=10)
        self.assertEqual(levante.paso(), "procesando")
        self.assertEqual(servicio.larvas_disponibles(self.ana), 0)
        Levante.objects.update(retirado_en=timezone.now() - timedelta(days=15))
        self.assertEqual(servicio.larvas_disponibles(self.ana), 4)
        servicio.comer_solas(self.ana)
        self.assertEqual(gallina.bono(), 0)
        Levante.objects.update(retirado_en=timezone.now() - timedelta(days=18))
        servicio.comer_solas(self.ana)
        self.assertEqual(gallina.bono(), 4)

    def test_pedir_los_huevos_de_la_gallina(self):
        crear_quincena()
        self.gallina(hace_dias=60)  # 32 huevos
        self.assertEqual(servicio.huevos_para_pedir(self.ana), 32)
        pedido = servicio.pedir_huevos(self.ana, 30, "Calle 1", "099")
        self.assertEqual(pedido.forma_pago, Pedido.FormaPago.GALLINA)
        self.assertEqual((pedido.huevos, pedido.total), (30, 0))
        self.assertEqual(servicio.huevos_para_pedir(self.ana), 2)
        self.assertEqual(Ajustes.actuales().huevos_disponibles, 170)
        with self.assertRaises(servicio.NoSePuede):
            servicio.pedir_huevos(self.ana, 15, "Calle 1", "099")

    def test_la_mensual_se_cobra_del_saldo_y_si_no_hay_queda_en_pausa(self):
        gallina = self.gallina(hace_dias=40, plan="mensual", dias_pagos=30)
        self.assertTrue(servicio.en_pausa(gallina))
        puestos = gallina.huevos_puestos()
        servicio.cobrar_mensuales(self.ana)
        gallina.refresh_from_db()
        self.assertTrue(servicio.en_pausa(gallina))
        con_saldo(self.ana, 200)
        servicio.cobrar_mensuales(self.ana)
        gallina.refresh_from_db()
        self.assertFalse(servicio.en_pausa(gallina))
        self.assertEqual(eggos.saldo(self.ana), 30)
        # Los días en pausa no cuentan: tiene los mismos huevos que antes de la pausa.
        self.assertEqual(gallina.huevos_puestos(), puestos)


class PedidosTests(TestCase):
    def setUp(self):
        self.ana = crear_cliente()
        self.quincena = crear_quincena()

    def test_con_eggos_paga_menos_y_se_descuenta_del_saldo(self):
        con_saldo(self.ana, 500)
        pedido = servicio.crear_pedido(self.ana, [(self.quincena, 2)], Pedido.FormaPago.EGGOS, "Calle 1", "099")
        self.assertEqual(pedido.total, 302)
        self.assertEqual(eggos.saldo(self.ana), 198)
        self.assertIsNotNone(pedido.entrega_estimada)

    def test_el_socio_paga_todavia_menos(self):
        mover_el(self.ana, 1500, date(2020, 1, 1))
        pedido = servicio.crear_pedido(self.ana, [(self.quincena, 1)], Pedido.FormaPago.EGGOS, "Calle 1", "099")
        self.assertEqual(pedido.total, 148)

    def test_sin_eggos_suficientes_no_queda_nada_a_medias(self):
        with self.assertRaises(servicio.NoSePuede):
            servicio.crear_pedido(self.ana, [(self.quincena, 1)], Pedido.FormaPago.EGGOS, "Calle 1", "099")
        self.assertFalse(Pedido.objects.exists())
        self.assertEqual(Ajustes.actuales().huevos_disponibles, 200)

    def test_con_plata_paga_el_precio_lleno(self):
        pedido = servicio.crear_pedido(self.ana, [(self.quincena, 1)], Pedido.FormaPago.CONTRA_ENTREGA, "Calle 1", "099")
        self.assertEqual(pedido.total, 160)
        self.assertEqual(Ajustes.actuales().huevos_disponibles, 185)

    def test_no_se_vende_mas_de_lo_disponible(self):
        with self.assertRaises(servicio.NoSePuede):
            servicio.crear_pedido(self.ana, [(self.quincena, 14)], Pedido.FormaPago.CONTRA_ENTREGA, "Calle 1", "099")


class LevanteTests(TestCase):
    def setUp(self):
        self.ana = crear_cliente()

    def test_cuesta_60_eggos_y_solo_uno_a_la_vez(self):
        with self.assertRaises(servicio.NoSePuede):
            servicio.pedir_levante(self.ana, "Calle 1", "099")
        self.assertFalse(Levante.objects.exists())
        con_saldo(self.ana, 100)
        servicio.pedir_levante(self.ana, "Calle 1", "099")
        self.assertEqual(eggos.saldo(self.ana), 40)
        with self.assertRaises(servicio.NoSePuede):
            servicio.pedir_levante(self.ana, "Calle 1", "099")


class AdministracionTests(TestCase):
    def setUp(self):
        self.ana = crear_cliente()
        self.admin = Usuario.objects.create_user(username="admin", rol=Usuario.Rol.ADMIN)
        self.chofer = Usuario.objects.create_user(username="chofer", rol=Usuario.Rol.CHOFER)

    def test_solo_administracion_ve_el_panel(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(reverse("mundo:panel")).status_code, 403)
        self.client.force_login(self.admin)
        con_saldo(self.ana, 4000)
        servicio.adoptar(self.ana, "dos_anios", "Clota", "blanca")
        respuesta = self.client.get(reverse("mundo:panel"))
        self.assertContains(respuesta, "Clota")
        self.assertContains(respuesta, "1 de 34")

    def test_cambiar_los_huevos_disponibles(self):
        self.client.force_login(self.admin)
        datos = {"huevos_disponibles": 120, "horas_de_entrega": 48, "gallinas_en_postura": 60, "parte_de_socios": 10, "sanidad": "Bien"}
        self.client.post(reverse("mundo:panel"), datos)
        self.assertEqual(Ajustes.actuales().huevos_disponibles, 120)

    def test_confirmar_una_transferencia_activa_la_gallina(self):
        gallina, recarga = servicio.adoptar(self.ana, "un_anio", "Pepa", "blanca", Recarga.Medio.TRANSFERENCIA)
        self.client.force_login(self.admin)
        self.client.post(reverse("mundo:recarga_resolver", args=[recarga.pk]), {"accion": "acreditar"})
        gallina.refresh_from_db()
        self.assertEqual(gallina.estado, Gallina.Estado.ACTIVA)

    def test_cancelar_una_recarga_libera_el_lugar(self):
        gallina, recarga = servicio.adoptar(self.ana, "un_anio", "Pepa", "blanca", Recarga.Medio.TRANSFERENCIA)
        self.client.force_login(self.admin)
        self.client.post(reverse("mundo:recarga_resolver", args=[recarga.pk]), {"accion": "cancelar"})
        gallina.refresh_from_db()
        self.assertEqual(gallina.estado, Gallina.Estado.CANCELADA)
        self.assertEqual(eggos.saldo(self.ana), 0)

    def test_el_chofer_pesa_el_balde(self):
        con_saldo(self.ana, 100)
        levante = servicio.pedir_levante(self.ana, "Calle 1", "099")
        self.client.force_login(self.chofer)
        self.assertContains(self.client.get(reverse("mundo:levantes")), "Calle 1")
        self.client.post(reverse("mundo:levante_retirar", args=[levante.pk]), {"kg": "8,5"})
        levante.refresh_from_db()
        self.assertEqual((levante.estado, levante.kg, levante.raciones()), (Levante.Estado.RETIRADO, Decimal("8.5"), 8))

    def test_poner_el_dia_y_la_hora_de_entrega(self):
        pedido = servicio.crear_pedido(self.ana, [(crear_quincena(), 1)], Pedido.FormaPago.CONTRA_ENTREGA, "Calle 1", "099")
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("tienda:pedido_admin_detalle", args=[pedido.pk])), "Día y hora exactos")
        self.client.post(reverse("mundo:pedido_entrega", args=[pedido.pk]), {"entrega_estimada": "2026-11-17T11:00"})
        pedido.refresh_from_db()
        self.assertEqual(timezone.localtime(pedido.entrega_estimada).strftime("%d/%m %H:%M"), "17/11 11:00")

    def test_planillas(self):
        con_saldo(self.ana, 4000)
        servicio.adoptar(self.ana, "dos_anios", "Clota", "blanca")
        self.client.force_login(self.admin)
        for nombre in ["exportar_movimientos", "exportar_gallinas", "exportar_levantes"]:
            respuesta = self.client.get(reverse(f"mundo:{nombre}"))
            self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Clota", self.client.get(reverse("mundo:exportar_gallinas")).content.decode())


class SeparacionTests(TestCase):
    def test_la_app_de_siempre_no_importa_nada_de_eggo_world(self):
        """Si un día se borra Eggo World, el resto tiene que seguir andando."""
        from pathlib import Path

        from django.conf import settings

        for app in ["cuentas", "captura", "tienda", "impacto", "guardian"]:
            for archivo in (settings.BASE_DIR / app).rglob("*.py"):
                texto = archivo.read_text(encoding="utf-8")
                for nueva in ["eggos", "mundo", "api"]:
                    self.assertNotIn(f"from {nueva}", texto, archivo)
                    self.assertNotIn(f"import {nueva}", texto, archivo)
