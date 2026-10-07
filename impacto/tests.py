from datetime import date, datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from captura.models import Lote, RegistroGranja, Retiro
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


class InformeTests(TestCase):
    def setUp(self):
        operador = Usuario.objects.create_user(username="operador", password="clave-de-prueba-123", rol=Usuario.Rol.OPERADOR)
        r001 = Restaurante.objects.create(nombre="La Huerta", codigo="R-001")
        r002 = Restaurante.objects.create(nombre="Parrilla", codigo="R-002")

        def retiro(restaurante, dia, levantado, impropios, vegetales, plato, no_ingresa=None, mes=8):
            return Retiro.objects.create(
                restaurante=restaurante, registrado_por=operador, fecha=timezone.make_aware(datetime(2026, mes, dia, 12)),
                kg_levantados=Decimal(levantado), kg_impropios=Decimal(impropios),
                kg_restos_vegetales=Decimal(vegetales), kg_residuos_plato=Decimal(plato),
                kg_no_ingresa=None if no_ingresa is None else Decimal(no_ingresa),
            )

        con_linea_base = retiro(r001, 3, "110", "10", "60", "40", no_ingresa="50")
        retiro(r001, 10, "60", "0", "30", "30")
        de_r002 = retiro(r002, 5, "55", "5", "25", "25", no_ingresa="0")
        retiro(r001, 2, "999", "0", "500", "499", mes=9)  # fuera del período
        self.lote = Lote.objects.create(
            registrado_por=operador, fecha_inicio=date(2026, 8, 12), bandejas=4, g_neonatos=Decimal("10"),
            fecha_cosecha=date(2026, 8, 30), kg_larvas=Decimal("20"), kg_frass=Decimal("50"),
        )
        Retiro.objects.filter(pk__in=[con_linea_base.pk, de_r002.pk]).update(lote=self.lote)
        RegistroGranja.objects.create(
            registrado_por=operador, fecha=date(2026, 8, 31), huevos=100, kg_larvas=Decimal("5"), lote=self.lote
        )
        self.datos = calculos.informe(date(2026, 8, 1), date(2026, 8, 31))

    def test_resumen_del_periodo(self):
        resumen = self.datos["resumen"]
        self.assertEqual((resumen["retiros"], resumen["kg_levantados"], resumen["kg_organicos"]), (3, Decimal("225"), Decimal("210")))
        self.assertAlmostEqual(float(resumen["pct_impropios"]), 15 / 225 * 100, places=2)
        self.assertEqual((resumen["lotes_cosechados"], resumen["kg_larvas"], resumen["huevos"]), (1, Decimal("20"), 100))
        self.assertEqual(resumen["tco2e_provisorio"], Decimal("0.07"))  # 210 × 0,70 × 0,5 / 1000 = 0,0735

    def test_linea_base_solo_con_los_retiros_que_la_informaron(self):
        r001, r002 = self.datos["restaurantes"]
        self.assertEqual((r001["restaurante__codigo"], r001["retiros"], r001["con_linea_base"]), ("R-001", 2, 1))
        self.assertAlmostEqual(float(r001["pct_a_eggologic"]), 110 / 160 * 100)
        self.assertEqual(r002["pct_a_eggologic"], 100)

    def test_trazabilidad_del_lote_hasta_los_huevos(self):
        (fila,) = self.datos["lotes"]
        self.assertEqual((fila["retiros"], fila["restaurantes"], fila["huevos"]), (2, ["R-001", "R-002"], 100))
