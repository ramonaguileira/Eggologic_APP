from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from captura.models import RegistroGranja, Retiro
from cuentas.models import Restaurante, Usuario
from tienda.models import ItemPedido, Pedido, Producto

from . import calculos


class ImpactoTests(TestCase):
    def setUp(self):
        self.operador = Usuario.objects.create_user(
            username="operador", password="clave-de-prueba-123", rol=Usuario.Rol.OPERADOR
        )
        self.restaurante = Restaurante.objects.create(nombre="La Huerta", codigo="R-001")
        # 100 kg orgánicos (60 vegetales + 40 plato) y 200 huevos: 0,5 kg de residuo por huevo.
        Retiro.objects.create(
            restaurante=self.restaurante, registrado_por=self.operador, kg_levantados=Decimal("110"),
            kg_impropios=Decimal("10"), kg_restos_vegetales=Decimal("60"), kg_residuos_plato=Decimal("40"),
        )
        RegistroGranja.objects.create(
            registrado_por=self.operador, fecha=date(2026, 10, 1), huevos=200, kg_larvas=Decimal("4")
        )
        self.cliente = Usuario.objects.create_user(
            username="lucia", password="clave-de-prueba-123", rol=Usuario.Rol.CLIENTE
        )
        docena = Producto.objects.create(nombre="Docena", huevos=12, precio=Decimal("280"))
        for estado in [Pedido.Estado.ENTREGADO, Pedido.Estado.RECIBIDO]:
            pedido = Pedido.objects.create(
                usuario=self.cliente, estado=estado, forma_pago="contra_entrega", direccion="x", telefono="x"
            )
            ItemPedido.objects.create(
                pedido=pedido, producto=docena, cantidad=2, precio_unitario=docena.precio, huevos_por_unidad=12
            )

    def test_factores_del_circuito(self):
        factores = calculos.factores_del_circuito()
        self.assertEqual(factores["kg_residuo_por_huevo"], Decimal("0.5"))
        self.assertEqual(factores["g_larva_por_huevo"], Decimal("20"))

    def test_sin_datos_no_hay_factores(self):
        RegistroGranja.objects.all().delete()
        self.assertIsNone(calculos.factores_del_circuito())

    def test_el_cliente_suma_solo_pedidos_entregados(self):
        compras = calculos.impacto_de_compras(self.cliente, calculos.factores_del_circuito())
        self.assertEqual(compras["huevos"], 24)
        self.assertEqual(compras["kg_rescatados"], Decimal("12"))
        self.assertEqual(sum(barra["valor"] for barra in compras["por_mes"]), 24)

    def test_composicion_de_lo_que_entrega_un_restaurante(self):
        entregas = calculos.impacto_de_entregas(self.restaurante, calculos.factores_del_circuito())
        porcentajes = {parte["nombre"]: parte["porcentaje"] for parte in entregas["composicion"]}
        self.assertEqual(entregas["kg_organicos"], Decimal("100"))
        self.assertEqual(entregas["huevos_equivalentes"], 200)
        self.assertAlmostEqual(float(porcentajes["Impropios"]), 9.09, places=2)

    def test_barras_relativas_al_mes_mas_alto(self):
        serie = calculos.serie_mensual({calculos.ultimos_meses()[-1]: 50, calculos.ultimos_meses()[-2]: 100})
        self.assertEqual([barra["altura"] for barra in serie[-2:]], [100, 50])

    def test_pagina_del_cliente(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.get(reverse("impacto:mi_impacto"))
        self.assertContains(respuesta, "kg de residuos de restaurantes rescatados gracias a tus huevos")
        self.assertContains(respuesta, 'id="calculadora"')

    def test_pagina_del_restaurante(self):
        usuario = Usuario.objects.create_user(
            username="huerta", password="clave-de-prueba-123", rol=Usuario.Rol.RESTAURANTE
        )
        self.restaurante.usuario = usuario
        self.restaurante.save()
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("impacto:mi_impacto"))
        self.assertContains(respuesta, "El impacto de La Huerta")
        self.assertContains(respuesta, "¿Qué entregaste?")


class NivelesTests(TestCase):
    def test_niveles_segun_huevos_recibidos(self):
        self.assertEqual(calculos.nivel_del_cliente(0)["nombre"], "Compra individual")
        self.assertEqual(calculos.nivel_del_cliente(99)["nombre"], "Compra individual")
        self.assertEqual(calculos.nivel_del_cliente(100)["nombre"], "Sostenedor")
        self.assertEqual(calculos.nivel_del_cliente(500)["nombre"], "Regenerador")
        self.assertEqual(calculos.nivel_del_cliente(1000)["nombre"], "Guardián")

    def test_cuanto_falta_para_el_siguiente(self):
        nivel = calculos.nivel_del_cliente(300)
        self.assertEqual(nivel["siguiente"], "Regenerador")
        self.assertEqual(nivel["faltan"], 200)
        self.assertEqual(nivel["progreso"], 50)

    def test_el_nivel_mas_alto_no_tiene_siguiente(self):
        nivel = calculos.nivel_del_cliente(1500)
        self.assertIsNone(nivel["siguiente"])
        self.assertEqual(nivel["progreso"], 100)


class EmisionesEvitadasTests(TestCase):
    def test_factor_provisorio_redondeado_hacia_abajo(self):
        self.assertEqual(calculos.emisiones_evitadas(Decimal("1000"))["neto"], Decimal("0.35"))
        self.assertEqual(calculos.emisiones_evitadas(Decimal("57"))["neto"], Decimal("0.01"))  # 0,01995
        self.assertEqual(calculos.emisiones_evitadas(Decimal("0"))["neto"], Decimal("0.00"))
