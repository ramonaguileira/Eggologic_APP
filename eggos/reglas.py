"""Todos los números de Eggo World, en un solo lugar.

Cambiar una regla es cambiar una línea de este archivo; el cambio vale de ahí en adelante.
Lo que confirmó Ramón (13/11) no lleva marca. Lo demás está marcado SUPUESTO.
El detalle de cada número está en docs/eggo-world-plan-maestro.md, punto 3.
"""

from decimal import ROUND_HALF_UP, Decimal

# --- Eggos -------------------------------------------------------------------------------
# 1 Eggo = $ 1. Es un saldo a favor que solo se usa en Eggologic.

# Quien paga con plata recibe este porcentaje del total en Eggos, cuando el pedido se entrega.
VUELTA_PAGANDO_CON_PLATA = Decimal("0.03")
# Quien paga con Eggos paga menos; el socio, menos todavía. No recibe Eggos de vuelta.
DESCUENTO_CON_EGGOS = Decimal("0.055")
DESCUENTO_SOCIO = Decimal("0.075")

# Los Eggos se cargan en paquetes: el precio más bajo es el premio por adelantar varias compras.
PAQUETES = [500, 1000, 2000]
# Socio: un mes calendario entero con este saldo o más. Vale para el mes siguiente.
SALDO_PARA_SER_SOCIO = 1000
# SUPUESTO: tope de saldo por cuenta. Es consumo de una familia, no un depósito.
TOPE_POR_CUENTA = 10000

# --- Gallinas ----------------------------------------------------------------------------
# Se promete el piso de la producción real (200 a 250 huevos por año), no el techo.
HUEVOS_POR_ANIO = 200
# Las larvas suben la producción: un huevo más por ración, hasta este tope por gallina por año.
HUEVOS_POR_RACION = 1
BONO_MAXIMO_POR_ANIO = 20

PLAN_DOS_ANIOS = "dos_anios"
PLAN_UN_ANIO = "un_anio"
PLAN_MENSUAL = "mensual"
# precio en Eggos; días que cubre cada pago.
PLANES = {
    PLAN_DOS_ANIOS: {"nombre": "Dos años", "precio": 3600, "dias": 730},
    PLAN_UN_ANIO: {"nombre": "Un año", "precio": 1900, "dias": 365},
    # SUPUESTO: el precio de la mensual. Se cobra del saldo de Eggos cada 30 días.
    PLAN_MENSUAL: {"nombre": "Mensual", "precio": 170, "dias": 30},
}
# SUPUESTO: es consumo de una familia, no una inversión.
MAXIMO_DE_GALLINAS_POR_CUENTA = 4
# Con esta cantidad de huevos juntados ya se puede pedir.
HUEVOS_PARA_PEDIR = 15

# Cupo de adopciones: los huevos prometidos (con el bono completo) no pasan de esta parte de lo
# que queda después de darle su porcentaje a los socios del gallinero. SUPUESTO.
PARTE_DE_LA_PRODUCCION_PARA_ADOPTANTES = Decimal("0.70")

# --- Residuos y larvas -------------------------------------------------------------------
PRECIO_DEL_LEVANTE = 60
# Una ración de larvas por cada kilo entero de residuos.
RACIONES_POR_KG = 1
DIAS_HASTA_LAS_LARVAS = 14
# SUPUESTO: si nadie se las da, a los pocos días la gallina se las come sola.
DIAS_HASTA_QUE_COME_SOLA = 3


def precio_en_eggos(precio, es_socio):
    """Precio de un producto pagando con Eggos, redondeado al peso."""
    descuento = DESCUENTO_SOCIO if es_socio else DESCUENTO_CON_EGGOS
    return int((Decimal(precio) * (1 - descuento)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def vuelta_en_eggos(total):
    """Eggos que vuelven por un pedido pagado con plata. Se redondea para abajo."""
    return int(Decimal(total) * VUELTA_PAGANDO_CON_PLATA)
