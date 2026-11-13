from datetime import date, datetime, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from cuentas.models import Usuario
from tienda.models import ItemPedido, Pedido, Producto

from . import reglas, servicio
from .models import Movimiento, Recarga


def crear_cliente(nombre="ana"):
    return Usuario.objects.create_user(username=nombre, email=f"{nombre}@example.com", rol=Usuario.Rol.CLIENTE)


def crear_quincena():
    return Producto.objects.create(nombre="Quincena", huevos=15, precio=Decimal("160"))


def mover_el(usuario, cantidad, dia):
    """Un movimiento con fecha vieja (la fecha se pone sola al crear, por eso se corrige después)."""
    movimiento = servicio.mover(usuario, cantidad, Movimiento.Motivo.AJUSTE)
    cuando = timezone.make_aware(datetime(dia.year, dia.month, dia.day, 12))
    Movimiento.objects.filter(pk=movimiento.pk).update(creado_en=cuando)


class ReglasTests(TestCase):
    def test_precio_en_eggos(self):
        # Quincena de $ 160: 5,5 % menos da 151; el socio, con 7,5 %, paga 148.
        self.assertEqual(reglas.precio_en_eggos(Decimal("160"), es_socio=False), 151)
        self.assertEqual(reglas.precio_en_eggos(Decimal("160"), es_socio=True), 148)

    def test_vuelta_pagando_con_plata(self):
        self.assertEqual(reglas.vuelta_en_eggos(Decimal("160")), 4)
        self.assertEqual(reglas.vuelta_en_eggos(Decimal("320")), 9)


class SaldoTests(TestCase):
    def setUp(self):
        self.ana = crear_cliente()

    def test_el_saldo_es_la_suma_de_los_movimientos(self):
        servicio.mover(self.ana, 500, Movimiento.Motivo.RECARGA)
        servicio.mover(self.ana, -151, Movimiento.Motivo.PEDIDO)
        self.assertEqual(servicio.saldo(self.ana), 349)

    def test_no_se_puede_gastar_lo_que_no_hay(self):
        with self.assertRaises(servicio.SaldoInsuficiente):
            servicio.mover(self.ana, -1, Movimiento.Motivo.PEDIDO)
        self.assertEqual(servicio.saldo(self.ana), 0)

    def test_la_misma_referencia_no_se_acredita_dos_veces(self):
        servicio.mover(self.ana, 100, Movimiento.Motivo.AJUSTE, referencia="una-sola-vez")
        self.assertIsNone(servicio.mover(self.ana, 100, Movimiento.Motivo.AJUSTE, referencia="una-sola-vez"))
        self.assertEqual(servicio.saldo(self.ana), 100)

    def test_una_recarga_se_acredita_una_sola_vez(self):
        recarga = Recarga.objects.create(usuario=self.ana, monto=500, medio=Recarga.Medio.TRANSFERENCIA)
        self.assertTrue(servicio.acreditar_recarga(recarga))
        self.assertFalse(servicio.acreditar_recarga(recarga))
        self.assertEqual(servicio.saldo(self.ana), 500)


class VueltaTests(TestCase):
    def setUp(self):
        self.ana = crear_cliente()
        self.quincena = crear_quincena()

    def pedido(self, forma_pago, estado=Pedido.Estado.ENTREGADO):
        pedido = Pedido.objects.create(usuario=self.ana, forma_pago=forma_pago, estado=estado, direccion="x", telefono="1")
        ItemPedido.objects.create(
            pedido=pedido, producto=self.quincena, cantidad=2, precio_unitario=Decimal("160"), huevos_por_unidad=15
        )
        return pedido

    def test_vuelve_el_3_por_ciento_de_lo_pagado_con_plata_y_entregado(self):
        self.pedido(Pedido.FormaPago.CONTRA_ENTREGA)
        servicio.acreditar_vueltas(self.ana)
        servicio.acreditar_vueltas(self.ana)
        self.assertEqual(servicio.saldo(self.ana), 9)

    def test_no_vuelve_nada_si_no_se_entrego_o_se_pago_con_eggos(self):
        self.pedido(Pedido.FormaPago.TRANSFERENCIA, estado=Pedido.Estado.RECIBIDO)
        self.pedido(Pedido.FormaPago.EGGOS)
        self.pedido(Pedido.FormaPago.GALLINA)
        servicio.acreditar_vueltas(self.ana)
        self.assertEqual(servicio.saldo(self.ana), 0)


class SocioTests(TestCase):
    def setUp(self):
        self.ana = crear_cliente()
        self.hoy = date(2026, 11, 13)

    def test_un_mes_entero_con_mil_eggos_o_mas(self):
        mover_el(self.ana, 1200, date(2026, 9, 20))
        self.assertTrue(servicio.es_socio(self.ana, self.hoy))

    def test_si_bajo_de_mil_durante_el_mes_no_es_socio(self):
        mover_el(self.ana, 1200, date(2026, 9, 20))
        mover_el(self.ana, -300, date(2026, 10, 10))
        mover_el(self.ana, 300, date(2026, 10, 11))
        self.assertFalse(servicio.es_socio(self.ana, self.hoy))

    def test_si_cargo_a_mitad_de_mes_todavia_no_es_socio(self):
        mover_el(self.ana, 2000, date(2026, 10, 2))
        self.assertFalse(servicio.es_socio(self.ana, self.hoy))
        # Al mes siguiente, sí.
        self.assertTrue(servicio.es_socio(self.ana, self.hoy + timedelta(days=30)))
