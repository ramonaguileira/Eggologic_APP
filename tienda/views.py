from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone

from cuentas.permisos import requiere
from impacto.calculos import factores_del_circuito

from .forms import PedidoForm, PedidoEntregadoForm
from .models import Pedido, Producto
from cuentas.models import Cliente, Usuario


def _datos_de_entrega(usuario):
    """Dirección y teléfono guardados, para no tener que escribirlos en cada pedido."""
    perfil = getattr(usuario, "cliente", None) or getattr(usuario, "restaurante", None)
    if perfil is None:
        return {}
    return {"direccion": perfil.direccion, "telefono": perfil.telefono}


@requiere(Usuario.puede_comprar)
def tienda(request):
    """Página de la tienda."""
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        # Si no tiene Cliente, crear uno y redirigir a impacto
        Cliente.objects.create(usuario=request.user)
        return redirect("impacto:mi_impacto")

    # Si no tiene datos de entrega, redirigir a primera entrega
    if not cliente.telefono or not cliente.direccion:
        return redirect("primera_entrega")

    productos = Producto.objects.filter(activo=True)
    form = PedidoForm(request.POST or None, productos=productos, initial=_datos_de_entrega(request.user))
    if request.method == "POST" and form.is_valid():
        pedido = form.crear_pedido(request.user)

        messages.success(
            request, f"¡Listo! Recibimos tu pedido N.º {pedido.pk}. Te contactamos para coordinar la entrega."
        )
        return redirect("tienda:mis_pedidos")
    factores = factores_del_circuito()
    kg_por_huevo = factores["kg_residuo_por_huevo"] if factores else None
    return render(request, "tienda/tienda.html", {"form": form, "kg_por_huevo": kg_por_huevo})


@requiere(Usuario.puede_comprar)
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).prefetch_related("items__producto")
    contexto = {
        "pedidos": pedidos,
        "datos_transferencia": settings.TIENDA_DATOS_TRANSFERENCIA,
        "transferencia": Pedido.FormaPago.TRANSFERENCIA,
        "pendientes": [Pedido.Estado.RECIBIDO, Pedido.Estado.CONFIRMADO],
    }
    return render(request, "tienda/mis_pedidos.html", contexto)

@login_required
def pedido_entregado(request, pedido_id):
    """Marca un pedido como entregado."""
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    # Solo administradores o personal autorizado pueden marcar pedidos como entregados
    if not (request.user.es_admin() or request.user.puede_ver_datos()):
        raise Http404("No tienes permiso para realizar esta acción.")

    form = PedidoEntregadoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        pedido.estado = Pedido.Estado.ENTREGADO
        entregado_en = form.cleaned_data.get("entregado_en")
        if entregado_en:
            pedido.entregado_en = entregado_en
        else:
            pedido.entregado_en = timezone.now()
        pedido.save()
        messages.success(request, "El pedido se marcó como entregado.")
        return redirect("tienda:pedidos_admin")

    return render(request, "tienda/pedido_entregado.html", {
        "pedido": pedido,
        "form": form,
    })


@login_required
def pedidos_admin(request):
    """Muestra todos los pedidos para administradores."""
    if not (request.user.es_admin() or request.user.is_staff):
        return redirect("tienda:mis_pedidos")

    estado_filter = request.GET.get("estado", Pedido.Estado.RECIBIDO)
    pedidos = Pedido.objects.all()

    if estado_filter:
        pedidos = pedidos.filter(estado=estado_filter)

    pedidos = pedidos.select_related("usuario").prefetch_related("items").order_by("-creado_en")

    estados_choices = Pedido.Estado.choices
    return render(request, "tienda/pedidos_admin.html", {
        "pedidos": pedidos,
        "estado_filter": estado_filter,
        "estados_choices": estados_choices,
    })



@login_required
def pedido_admin_detalle(request, pedido_id):
    """Muestra los detalles de un pedido específico para administradores."""
    pedido = get_object_or_404(Pedido.objects.select_related("usuario").prefetch_related("items"), pk=pedido_id)

    if not (request.user.es_admin() or request.user.is_staff):
        return redirect("tienda:mis_pedidos")

    return render(request, "tienda/pedido_admin_detalle.html", {
        "pedido": pedido,
    })
