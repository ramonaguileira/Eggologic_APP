"""Lo que pasa en la chacra de cada cliente: gallinas, huevos, larvas y levantes."""

from datetime import timedelta

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from eggos import reglas, servicio as eggos
from eggos.models import Movimiento, Recarga
from tienda.models import ItemPedido, Pedido, Producto

from .models import Ajustes, Gallina, Levante, RacionDeLarvas


class NoSePuede(Exception):
    """Un pedido que no se puede cumplir. El mensaje es para mostrarle al cliente."""


# --- Gallinas ----------------------------------------------------------------------------


def gallinas_que_cuentan():
    return Gallina.objects.exclude(estado=Gallina.Estado.CANCELADA)


def lugares_para_adoptar():
    return max(Ajustes.actuales().cupo_de_gallinas() - gallinas_que_cuentan().count(), 0)


def _activar(gallina, hoy=None):
    """Cobra la gallina del saldo y la pone a poner."""
    hoy = hoy or timezone.localdate()
    eggos.mover(
        gallina.usuario,
        -gallina.precio(),
        Movimiento.Motivo.GALLINA,
        f"{gallina.nombre}, plan {gallina.get_plan_display().lower()}",
        f"gallina-{gallina.pk}",
    )
    gallina.estado = Gallina.Estado.ACTIVA
    gallina.inicio = hoy
    gallina.pago_hasta = hoy + timedelta(days=reglas.PLANES[gallina.plan]["dias"])
    gallina.save()


@transaction.atomic
def adoptar(usuario, plan, nombre, color, medio=None):
    """Adopta una gallina. Si no alcanzan los Eggos, deja una recarga pendiente por la diferencia.

    Devuelve (gallina, recarga); la recarga es None si se pagó entera con el saldo.
    """
    if plan not in reglas.PLANES:
        raise NoSePuede("Ese plan no existe.")
    nombre = (nombre or "").strip()[:30]
    if not nombre:
        raise NoSePuede("Ponele un nombre a tu gallina.")
    if color not in Gallina.Color.values:
        color = Gallina.Color.BLANCA
    if gallinas_que_cuentan().filter(usuario=usuario).count() >= reglas.MAXIMO_DE_GALLINAS_POR_CUENTA:
        raise NoSePuede(f"Podés tener hasta {reglas.MAXIMO_DE_GALLINAS_POR_CUENTA} gallinas.")
    if lugares_para_adoptar() <= 0:
        raise NoSePuede("Por ahora no quedan gallinas para adoptar. Te avisamos cuando haya lugar.")

    gallina = Gallina.objects.create(usuario=usuario, plan=plan, nombre=nombre, color=color)
    falta = gallina.precio() - eggos.saldo(usuario)
    if falta <= 0:
        _activar(gallina)
        return gallina, None
    if medio not in Recarga.Medio.values:
        raise NoSePuede(f"Te faltan {falta} Eggos. Elegí cómo pagar la diferencia.")
    # Única recarga que no va en paquetes: acá se paga la diferencia exacta.
    gallina.recarga = Recarga.objects.create(usuario=usuario, monto=falta, medio=medio)
    gallina.save()
    return gallina, gallina.recarga


@transaction.atomic
def acreditar_recarga(recarga):
    """Acredita una recarga y, si era para una gallina, la activa."""
    if not eggos.acreditar_recarga(recarga):
        return False
    gallina = Gallina.objects.filter(recarga=recarga, estado=Gallina.Estado.PENDIENTE).first()
    if gallina and eggos.saldo(gallina.usuario) >= gallina.precio():
        _activar(gallina)
    return True


def cobrar_mensuales(usuario, hoy=None):
    """Renueva las gallinas mensuales vencidas si hay saldo; si no, quedan en pausa sin poner."""
    hoy = hoy or timezone.localdate()
    dias = reglas.PLANES[reglas.PLAN_MENSUAL]["dias"]
    vencidas = Gallina.objects.filter(
        usuario=usuario, plan=Gallina.Plan.MENSUAL, estado=Gallina.Estado.ACTIVA, pago_hasta__lte=hoy
    )
    for gallina in vencidas:
        try:
            eggos.mover(
                usuario,
                -gallina.precio(),
                Movimiento.Motivo.GALLINA,
                f"{gallina.nombre}, mes nuevo",
                f"gallina-{gallina.pk}-mes-{hoy.isoformat()}",
            )
        except eggos.SaldoInsuficiente:
            continue
        # Los días que estuvo en pausa no cuentan: se corre el inicio para que la cuenta siga de corrido.
        gallina.inicio += hoy - gallina.pago_hasta
        gallina.pago_hasta = hoy + timedelta(days=dias)
        gallina.save()


def en_pausa(gallina, hoy=None):
    return gallina.estado == Gallina.Estado.ACTIVA and gallina.pago_hasta <= (hoy or timezone.localdate())


# --- Huevos ------------------------------------------------------------------------------


def huevos_pedidos(usuario):
    """Huevos de sus gallinas que el cliente ya pidió."""
    items = ItemPedido.objects.filter(pedido__usuario=usuario, pedido__forma_pago=Pedido.FormaPago.GALLINA)
    items = items.exclude(pedido__estado=Pedido.Estado.CANCELADO)
    return items.aggregate(total=Sum(F("cantidad") * F("huevos_por_unidad")))["total"] or 0


def huevos_para_pedir(usuario, hoy=None):
    puestos = sum(gallina.huevos_puestos(hoy) for gallina in Gallina.objects.filter(usuario=usuario))
    return puestos - huevos_pedidos(usuario)


# --- Pedidos -----------------------------------------------------------------------------


def _descontar_disponibles(huevos):
    ajustes = Ajustes.objects.select_for_update().get(pk=Ajustes.actuales().pk)
    if huevos > ajustes.huevos_disponibles:
        raise NoSePuede(f"Ahora hay {ajustes.huevos_disponibles} huevos disponibles. Probá con menos.")
    ajustes.huevos_disponibles -= huevos
    ajustes.save()
    return ajustes


@transaction.atomic
def crear_pedido(usuario, items, forma_pago, direccion, telefono, notas=""):
    """Crea un pedido desde Eggo World. `items` es una lista de (producto, cantidad)."""
    items = [(producto, cantidad) for producto, cantidad in items if cantidad > 0]
    if not items:
        raise NoSePuede("Elegí al menos un producto.")
    if not direccion or not telefono:
        raise NoSePuede("Necesitamos tu dirección y tu teléfono para la entrega.")
    if forma_pago not in Pedido.FormaPago.values:
        raise NoSePuede("Elegí una forma de pago.")
    huevos = sum(producto.huevos * cantidad for producto, cantidad in items)

    if forma_pago == Pedido.FormaPago.GALLINA:
        if huevos > huevos_para_pedir(usuario):
            raise NoSePuede("Tus gallinas todavía no juntaron tantos huevos.")
        precios = {producto.pk: 0 for producto, _ in items}
    elif forma_pago == Pedido.FormaPago.EGGOS:
        socio = eggos.es_socio(usuario)
        precios = {producto.pk: reglas.precio_en_eggos(producto.precio, socio) for producto, _ in items}
    else:
        precios = {producto.pk: producto.precio for producto, _ in items}

    ajustes = _descontar_disponibles(huevos)
    pedido = Pedido.objects.create(
        usuario=usuario,
        forma_pago=forma_pago,
        direccion=direccion,
        telefono=telefono,
        notas=notas,
        entrega_estimada=timezone.now() + timedelta(hours=ajustes.horas_de_entrega),
    )
    for producto, cantidad in items:
        ItemPedido.objects.create(
            pedido=pedido,
            producto=producto,
            cantidad=cantidad,
            # Se guarda lo que realmente se cobró: el precio en Eggos, o cero si son huevos de la gallina.
            precio_unitario=precios[producto.pk],
            huevos_por_unidad=producto.huevos,
        )
    if forma_pago == Pedido.FormaPago.EGGOS:
        try:
            eggos.mover(
                usuario, -int(pedido.total), Movimiento.Motivo.PEDIDO, f"Pedido N.º {pedido.pk}", f"pedido-{pedido.pk}"
            )
        except eggos.SaldoInsuficiente:
            raise NoSePuede("No te alcanzan los Eggos. Podés recargar o pagar con plata.")
    return pedido


def pedir_huevos(usuario, huevos, direccion, telefono):
    """Pide huevos de las gallinas. Se arma con los productos de la tienda (quincena, maple...)."""
    productos = sorted(Producto.objects.filter(activo=True), key=lambda producto: -producto.huevos)
    items, resto = [], huevos
    for producto in productos:
        cantidad, resto = divmod(resto, producto.huevos)
        items.append((producto, cantidad))
    if huevos < reglas.HUEVOS_PARA_PEDIR or resto:
        raise NoSePuede("Esa cantidad no se puede armar con los envases que tenemos.")
    return crear_pedido(usuario, items, Pedido.FormaPago.GALLINA, direccion, telefono)


# --- Residuos y larvas -------------------------------------------------------------------


@transaction.atomic
def pedir_levante(usuario, direccion, telefono, nota=""):
    if not direccion:
        raise NoSePuede("Decinos dónde pasamos a buscar el balde.")
    if Levante.objects.filter(usuario=usuario, estado=Levante.Estado.PEDIDO).exists():
        raise NoSePuede("Ya tenés un levante pedido. Cuando lo retiremos podés pedir otro.")
    levante = Levante.objects.create(usuario=usuario, direccion=direccion, telefono=telefono, nota=nota[:200])
    try:
        eggos.mover(
            usuario,
            -reglas.PRECIO_DEL_LEVANTE,
            Movimiento.Motivo.LEVANTE,
            f"Levante N.º {levante.pk}",
            f"levante-{levante.pk}",
        )
    except eggos.SaldoInsuficiente:
        raise NoSePuede(f"El levante cuesta {reglas.PRECIO_DEL_LEVANTE} Eggos y no te alcanzan. Podés recargar.")
    return levante


def larvas_disponibles(usuario, hoy=None):
    hoy = hoy or timezone.localdate()
    listas = sum(
        levante.raciones()
        for levante in Levante.objects.filter(usuario=usuario, estado=Levante.Estado.RETIRADO)
        if levante.larvas_listas_el() <= hoy
    )
    dadas = RacionDeLarvas.objects.filter(gallina__usuario=usuario).aggregate(total=Sum("cantidad"))["total"] or 0
    return listas - dadas


@transaction.atomic
def dar_larvas(usuario, gallina, cantidad, hoy=None):
    cantidad = min(cantidad, larvas_disponibles(usuario, hoy), gallina.lugar_para_larvas(hoy))
    if gallina.usuario_id != usuario.pk or cantidad <= 0:
        raise NoSePuede("Esta gallina ya comió todas las larvas que puede este año, o no te quedan larvas.")
    RacionDeLarvas.objects.create(gallina=gallina, cantidad=cantidad, fecha=hoy or timezone.localdate())
    return cantidad


def comer_solas(usuario, hoy=None):
    """Si las larvas llevan días esperando, las gallinas se las comen solas. Nada se pierde por no entrar."""
    hoy = hoy or timezone.localdate()
    limite = hoy - timedelta(days=reglas.DIAS_HASTA_QUE_COME_SOLA)
    viejas = sum(
        levante.raciones()
        for levante in Levante.objects.filter(usuario=usuario, estado=Levante.Estado.RETIRADO)
        if levante.larvas_listas_el() <= limite
    )
    dadas = RacionDeLarvas.objects.filter(gallina__usuario=usuario).aggregate(total=Sum("cantidad"))["total"] or 0
    pendientes = viejas - dadas
    for gallina in Gallina.objects.filter(usuario=usuario, estado=Gallina.Estado.ACTIVA):
        if pendientes <= 0:
            break
        cantidad = min(pendientes, gallina.lugar_para_larvas(hoy))
        if cantidad > 0:
            RacionDeLarvas.objects.create(gallina=gallina, cantidad=cantidad, fecha=hoy)
            pendientes -= cantidad


def poner_al_dia(usuario):
    """Todo lo que se acomoda solo cuando el cliente abre la app."""
    eggos.acreditar_vueltas(usuario)
    cobrar_mensuales(usuario)
    comer_solas(usuario)
