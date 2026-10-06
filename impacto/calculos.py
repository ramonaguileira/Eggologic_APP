"""Cálculos del impacto que ven clientes y restaurantes.

Todo sale de los datos de captura (retiros, lotes, granja) y de los pedidos entregados.
SUPUESTO: el impacto de cada huevo se calcula con el promedio de todo el circuito
(kg de residuo orgánico clasificado ÷ huevos producidos). Cuando CarboSur defina su método,
se reemplaza acá sin tocar el resto.
"""

from datetime import date
from decimal import ROUND_DOWN, Decimal

from django.db.models import F, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.utils.formats import date_format

from captura.models import Lote, RegistroGranja, Retiro
from tienda.models import ItemPedido, Pedido

MESES_EN_GRAFICA = 6
KG_ORGANICOS = F("kg_restos_vegetales") + F("kg_residuos_plato")

# Niveles de los clientes según los huevos recibidos (pedidos entregados). Definidos por Ramón el 05/10.
NIVELES = [(0, "Compra individual"), (100, "Sostenedor"), (500, "Regenerador"), (1000, "Guardián")]


# CO2e evitado, para el reporte mensual de cada restaurante en Guardian. Provisorio hasta que
# CarboSur dé sus factores (decisión de Ramón, 06/10).
# SUPUESTO: kg orgánicos × 0,70 (factor conservador del doc de julio) × 0,5 kg de CO2e por kg
# que no va a disposición final. Por ahora sin emisiones del proyecto ni fugas.
FACTOR_CONSERVADOR = Decimal("0.70")
KG_CO2E_POR_KG_DESVIADO = Decimal("0.5")
CENTESIMO = Decimal("0.01")


def emisiones_evitadas(kg_organicos):
    """tCO2e de un reporte: línea de base, proyecto, fugas y reducción neta, con 2 decimales.

    Se redondea hacia abajo: la reducción neta es lo que se mintea y no conviene inflarla.
    """
    linea_base = kg_organicos * FACTOR_CONSERVADOR * KG_CO2E_POR_KG_DESVIADO / 1000
    linea_base = linea_base.quantize(CENTESIMO, rounding=ROUND_DOWN)
    proyecto = fugas = Decimal("0.00")
    return {"linea_base": linea_base, "proyecto": proyecto, "fugas": fugas, "neto": linea_base - proyecto - fugas}


def factores_del_circuito():
    """Cuánto residuo y cuánta larva hay, en promedio, detrás de cada huevo. None si faltan datos."""
    kg_organicos = Retiro.objects.aggregate(total=Sum(KG_ORGANICOS))["total"]
    granja = RegistroGranja.objects.aggregate(huevos=Sum("huevos"), larvas=Sum("kg_larvas"))
    if not kg_organicos or not granja["huevos"]:
        return None
    return {
        "kg_residuo_por_huevo": kg_organicos / granja["huevos"],
        "g_larva_por_huevo": granja["larvas"] * 1000 / granja["huevos"],
    }


def totales_de_la_comunidad():
    return {
        "kg_rescatados": Retiro.objects.aggregate(total=Sum(KG_ORGANICOS))["total"] or 0,
        "kg_larvas": Lote.objects.aggregate(total=Sum("kg_larvas"))["total"] or 0,
        "huevos": RegistroGranja.objects.aggregate(total=Sum("huevos"))["total"] or 0,
        "restaurantes": Retiro.objects.values("restaurante").distinct().count(),
    }


def ultimos_meses(hoy=None):
    """Primer día de cada uno de los últimos meses, del más viejo al actual."""
    hoy = hoy or timezone.localdate()
    meses = []
    anio, mes = hoy.year, hoy.month
    for _ in range(MESES_EN_GRAFICA):
        meses.append(date(anio, mes, 1))
        anio, mes = (anio, mes - 1) if mes > 1 else (anio - 1, 12)
    return list(reversed(meses))


def serie_mensual(valores_por_mes):
    """Arma las barras de la gráfica: etiqueta, valor y altura relativa (0 a 100)."""
    meses = ultimos_meses()
    valores = [valores_por_mes.get(mes, 0) for mes in meses]
    maximo = max(valores) or 1
    return [
        {"etiqueta": date_format(mes, "M"), "valor": valor, "altura": round(valor * 100 / maximo)}
        for mes, valor in zip(meses, valores)
    ]


def _por_mes(consulta, campo_fecha, campo_valor):
    filas = (
        consulta.annotate(mes=TruncMonth(campo_fecha))
        .values("mes")
        .annotate(total=Sum(campo_valor))
    )
    return {_a_fecha(fila["mes"]): fila["total"] for fila in filas}


def _a_fecha(valor):
    # TruncMonth sobre un DateTimeField devuelve datetime; las claves se comparan como date.
    return timezone.localtime(valor).date() if hasattr(valor, "hour") else valor


def nivel_del_cliente(huevos):
    """Nivel actual, el siguiente y cuánto falta para llegar."""
    actual = [nivel for nivel in NIVELES if huevos >= nivel[0]][-1]
    siguientes = [nivel for nivel in NIVELES if huevos < nivel[0]]
    if not siguientes:
        return {"nombre": actual[1], "siguiente": None, "faltan": 0, "progreso": 100}
    desde, hasta = actual[0], siguientes[0][0]
    return {
        "nombre": actual[1],
        "siguiente": siguientes[0][1],
        "faltan": hasta - huevos,
        "progreso": round((huevos - desde) * 100 / (hasta - desde)),
    }


def impacto_de_compras(usuario, factores):
    """Huevos que compró el usuario (pedidos entregados) y lo que representan."""
    items = ItemPedido.objects.filter(pedido__usuario=usuario, pedido__estado=Pedido.Estado.ENTREGADO)
    huevos = items.aggregate(total=Sum(F("cantidad") * F("huevos_por_unidad")))["total"] or 0
    huevos_por_mes = _por_mes(items, "pedido__creado_en", F("cantidad") * F("huevos_por_unidad"))
    return {
        "huevos": huevos,
        "kg_rescatados": huevos * factores["kg_residuo_por_huevo"] if factores else None,
        "kg_larva": huevos * factores["g_larva_por_huevo"] / 1000 if factores else None,
        "por_mes": serie_mensual(huevos_por_mes),
    }


def impacto_de_entregas(restaurante, factores):
    """Residuo que entregó un restaurante: total, composición y evolución."""
    retiros = Retiro.objects.filter(restaurante=restaurante)
    totales = retiros.aggregate(
        levantado=Sum("kg_levantados"),
        vegetales=Sum("kg_restos_vegetales"),
        plato=Sum("kg_residuos_plato"),
        impropios=Sum("kg_impropios"),
    )
    clasificado = sum(totales[clave] or 0 for clave in ["vegetales", "plato", "impropios"])
    composicion = [
        {"nombre": "Restos vegetales", "clase": "serie-1", "kg": totales["vegetales"] or 0},
        {"nombre": "Residuos de plato", "clase": "serie-2", "kg": totales["plato"] or 0},
        {"nombre": "Impropios", "clase": "serie-3", "kg": totales["impropios"] or 0},
    ]
    for parte in composicion:
        parte["porcentaje"] = parte["kg"] * 100 / clasificado if clasificado else 0
    kg_organicos = (totales["vegetales"] or 0) + (totales["plato"] or 0)
    return {
        "retiros": retiros.count(),
        "kg_levantados": totales["levantado"] or 0,
        "kg_organicos": kg_organicos,
        "composicion": composicion,
        "huevos_equivalentes": int(kg_organicos / factores["kg_residuo_por_huevo"]) if factores else None,
        "por_mes": serie_mensual(_por_mes(retiros, "fecha", "kg_levantados")),
    }
