"""Las pantallas de Eggologic para administrar Eggo World. Viven en la app de siempre."""

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from cuentas.models import Usuario
from cuentas.permisos import requiere
from eggos import servicio as eggos
from eggos.models import Movimiento, Recarga
from tienda.models import Pedido

from . import servicio
from .models import Ajustes, Gallina, Levante


class AjustesForm(forms.ModelForm):
    class Meta:
        model = Ajustes
        fields = ["huevos_disponibles", "horas_de_entrega", "gallinas_en_postura", "parte_de_socios", "sanidad"]


def _suma(movimientos):
    return movimientos.aggregate(total=Sum("cantidad"))["total"] or 0


@requiere(Usuario.es_admin)
def panel(request):
    ajustes = Ajustes.actuales()
    form = AjustesForm(request.POST or None, instance=ajustes)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ajustes guardados.")
        return redirect("mundo:panel")

    gallinas = list(servicio.gallinas_que_cuentan().select_related("usuario"))
    clientes = {gallina.usuario for gallina in gallinas}
    # Huevos que ya se pusieron y todavía no se pidieron: lo que se debe hoy.
    adeudados = sum(servicio.huevos_para_pedir(cliente) for cliente in clientes)
    movimientos = Movimiento.objects.all()
    con_saldo = Usuario.objects.filter(movimientos_eggos__isnull=False).distinct()
    economia = {
        "comprados": _suma(movimientos.filter(motivo=Movimiento.Motivo.RECARGA)),
        "ganados": _suma(movimientos.filter(motivo=Movimiento.Motivo.VUELTA)),
        "usados": -_suma(movimientos.filter(cantidad__lt=0)),
        # El saldo de todos los clientes: es lo que Eggologic debe en productos.
        "en_circulacion": _suma(movimientos),
    }
    contexto = {
        "form": form,
        "ajustes": ajustes,
        "cupo": ajustes.cupo_de_gallinas(),
        "gallinas": gallinas,
        "adeudados": adeudados,
        "economia": economia,
        "recargas": Recarga.objects.filter(estado=Recarga.Estado.PENDIENTE).select_related("usuario"),
        "levantes_pedidos": Levante.objects.filter(estado=Levante.Estado.PEDIDO).count(),
        "socios": [usuario for usuario in con_saldo if eggos.es_socio(usuario)],
    }
    return render(request, "mundo/panel.html", contexto)


@requiere(Usuario.es_admin)
@require_POST
def recarga_resolver(request, recarga_id):
    """Confirma que llegó una transferencia (y acredita los Eggos) o cancela la recarga."""
    recarga = get_object_or_404(Recarga, pk=recarga_id, estado=Recarga.Estado.PENDIENTE)
    if request.POST.get("accion") == "acreditar":
        servicio.acreditar_recarga(recarga)
        messages.success(request, f"Acreditados {recarga.monto} Eggos a {recarga.usuario}.")
    else:
        recarga.estado = Recarga.Estado.CANCELADA
        recarga.save()
        Gallina.objects.filter(recarga=recarga, estado=Gallina.Estado.PENDIENTE).update(
            estado=Gallina.Estado.CANCELADA
        )
        messages.success(request, "Recarga cancelada.")
    return redirect("mundo:panel")


@requiere(Usuario.es_admin)
@require_POST
def pedido_entrega(request, pedido_id):
    """Pone el día y la hora exactos de entrega de un pedido; el cliente lo ve actualizado."""
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    try:
        cuando = datetime.fromisoformat(request.POST.get("entrega_estimada", ""))
    except ValueError:
        messages.error(request, "Elegí el día y la hora de entrega.")
    else:
        pedido.entrega_estimada = timezone.make_aware(cuando) if timezone.is_naive(cuando) else cuando
        pedido.save()
        messages.success(request, "Entrega actualizada.")
    return redirect("tienda:pedido_admin_detalle", pedido_id=pedido.pk)


@requiere(Usuario.puede_retirar)
def levantes(request):
    """Lo que ve el chofer: los baldes que hay que pasar a buscar."""
    contexto = {
        "pedidos": Levante.objects.filter(estado=Levante.Estado.PEDIDO).select_related("usuario"),
        "retirados": Levante.objects.filter(estado=Levante.Estado.RETIRADO).select_related("usuario")[:20],
    }
    return render(request, "mundo/levantes.html", contexto)


@requiere(Usuario.puede_retirar)
@require_POST
def levante_retirar(request, levante_id):
    levante = get_object_or_404(Levante, pk=levante_id, estado=Levante.Estado.PEDIDO)
    try:
        kg = Decimal(request.POST.get("kg", "").replace(",", "."))
    except InvalidOperation:
        kg = Decimal("-1")
    if not 0 < kg < 1000:
        messages.error(request, "Anotá los kilos del balde.")
        return redirect("mundo:levantes")
    levante.kg = kg
    levante.estado = Levante.Estado.RETIRADO
    levante.retirado_en = timezone.now()
    levante.retirado_por = request.user
    levante.save()
    messages.success(request, f"Levante N.º {levante.pk} retirado: {kg} kg.")
    return redirect("mundo:levantes")


# --- Planillas -----------------------------------------------------------------------------


def _csv(nombre, encabezados, filas):
    respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
    # Con esta marca, Excel abre bien las tildes.
    respuesta.write("﻿")
    planilla = csv.writer(respuesta, delimiter=";")
    planilla.writerow(encabezados)
    planilla.writerows(filas)
    return respuesta


def _dia(valor):
    return timezone.localtime(valor).strftime("%d/%m/%Y %H:%M") if valor else ""


@requiere(Usuario.es_admin)
def exportar_movimientos(request):
    filas = [
        [_dia(m.creado_en), m.usuario.username, m.cantidad, m.get_motivo_display(), m.detalle]
        for m in Movimiento.objects.select_related("usuario").order_by("creado_en", "id")
    ]
    return _csv("eggos-movimientos.csv", ["Fecha", "Cliente", "Eggos", "Motivo", "Detalle"], filas)


@requiere(Usuario.es_admin)
def exportar_gallinas(request):
    filas = [
        [
            g.usuario.username, g.nombre, g.get_plan_display(), g.get_estado_display(),
            g.inicio or "", g.pago_hasta or "", g.huevos_puestos(), g.bono(),
        ]
        for g in Gallina.objects.select_related("usuario")
    ]
    encabezados = ["Cliente", "Gallina", "Plan", "Estado", "Inicio", "Pago hasta", "Huevos puestos", "Huevos por larvas"]
    return _csv("eggo-world-gallinas.csv", encabezados, filas)


@requiere(Usuario.es_admin)
def exportar_levantes(request):
    filas = [
        [_dia(l.pedido_en), l.usuario.username, l.get_estado_display(), l.kg or "", _dia(l.retirado_en), l.direccion]
        for l in Levante.objects.select_related("usuario").order_by("pedido_en")
    ]
    return _csv("eggo-world-levantes.csv", ["Pedido", "Cliente", "Estado", "kg", "Retirado", "Dirección"], filas)
