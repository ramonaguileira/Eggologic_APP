from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from cuentas.permisos import requiere
from impacto.calculos import factores_del_circuito

from .forms import PedidoForm
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

    print("def tienda")
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
