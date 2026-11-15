"""Lo que se puede hacer con los Eggos: consultar el saldo, moverlos y saber quién es socio."""

from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from tienda.models import Pedido

from . import reglas
from .models import Movimiento, Recarga

FORMAS_DE_PAGO_CON_PLATA = [
    Pedido.FormaPago.CONTRA_ENTREGA,
    Pedido.FormaPago.TRANSFERENCIA,
    Pedido.FormaPago.MERCADO_PAGO,
]


class SaldoInsuficiente(Exception):
    pass


def saldo(usuario):
    return Movimiento.objects.filter(usuario=usuario).aggregate(total=Sum("cantidad"))["total"] or 0


@transaction.atomic
def mover(usuario, cantidad, motivo, detalle="", referencia=None):
    """Suma o resta Eggos. Con una referencia repetida no hace nada y devuelve None."""
    if cantidad == 0:
        return None
    if cantidad < 0 and saldo(usuario) + cantidad < 0:
        raise SaldoInsuficiente
    try:
        with transaction.atomic():
            return Movimiento.objects.create(
                usuario=usuario, cantidad=cantidad, motivo=motivo, detalle=detalle, referencia=referencia
            )
    except IntegrityError:
        return None


def es_socio(usuario, hoy=None):
    """Socio: pasó todo el mes calendario anterior con el saldo mínimo o más."""
    hoy = hoy or timezone.localdate()
    fin = date(hoy.year, hoy.month, 1)
    inicio = (fin - timedelta(days=1)).replace(day=1)
    movimientos = Movimiento.objects.filter(usuario=usuario)
    saldo_del_mes = (
        movimientos.filter(creado_en__date__lt=inicio).aggregate(total=Sum("cantidad"))["total"] or 0
    )
    minimo = saldo_del_mes
    del_mes = movimientos.filter(creado_en__date__gte=inicio, creado_en__date__lt=fin).order_by("creado_en", "id")
    for movimiento in del_mes:
        saldo_del_mes += movimiento.cantidad
        minimo = min(minimo, saldo_del_mes)
    return minimo >= reglas.SALDO_PARA_SER_SOCIO


def acreditar_vueltas(usuario):
    """Da los Eggos que vuelven por los pedidos entregados que se pagaron con plata.

    Se puede llamar todas las veces que haga falta: cada pedido se acredita una sola vez.
    Así no hace falta tocar el código de la tienda.
    """
    acreditados = Movimiento.objects.filter(usuario=usuario, motivo=Movimiento.Motivo.VUELTA).values_list(
        "referencia", flat=True
    )
    pedidos = Pedido.objects.filter(
        usuario=usuario, estado=Pedido.Estado.ENTREGADO, forma_pago__in=FORMAS_DE_PAGO_CON_PLATA
    ).prefetch_related("items")
    for pedido in pedidos:
        referencia = f"vuelta-pedido-{pedido.pk}"
        if referencia not in acreditados:
            mover(
                usuario,
                reglas.vuelta_en_eggos(pedido.total),
                Movimiento.Motivo.VUELTA,
                f"Pedido N.º {pedido.pk}",
                referencia,
            )


@transaction.atomic
def acreditar_recarga(recarga):
    """Convierte una recarga pendiente en Eggos. Devuelve False si ya estaba acreditada."""
    recarga = Recarga.objects.select_for_update().get(pk=recarga.pk)
    if recarga.estado != Recarga.Estado.PENDIENTE:
        return False
    recarga.estado = Recarga.Estado.ACREDITADA
    recarga.acreditada_en = timezone.now()
    recarga.save()
    mover(
        recarga.usuario,
        recarga.monto,
        Movimiento.Motivo.RECARGA,
        recarga.get_medio_display(),
        f"recarga-{recarga.pk}",
    )
    return True
