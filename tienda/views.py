from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from cuentas.permisos import requiere
from impacto.calculos import factores_del_circuito

from .forms import PedidoForm
from .models import Pedido, Producto
from cuentas.models import Cliente, Usuario


def _datos_de_entrega(usuario):
    """Dirección y teléfono guardados, para no tener que escribirlos en cada pedido."""
    perfil = getattr(usuario, "restaurante", None) or getattr(usuario, "cliente", None)
    if perfil is None:
        return {}
    return {"direccion": perfil.direccion, "telefono": perfil.telefono}


@requiere(Usuario.puede_comprar)
def tienda(request):
    """Página de la tienda."""
    # El cliente carga su dirección y teléfono antes del primer pedido. Al restaurante no se le
    # pide: sus datos los cargó Eggologic, y el formulario del pedido los deja corregir.
    if request.user.rol == Usuario.Rol.CLIENTE:
        cliente, _ = Cliente.objects.get_or_create(usuario=request.user)
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

@requiere(Usuario.puede_gestionar_pedidos)
def pedido_entregado(request, pedido_id):
    """Marca un pedido como entregado."""
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == "POST":
        pedido.estado = Pedido.Estado.ENTREGADO
        pedido.save()
        messages.success(request, "El pedido se marcó como entregado.")
        return redirect("tienda:pedidos_admin")
    return render(request, "tienda/pedido_entregado.html", {"pedido": pedido})


@requiere(Usuario.puede_gestionar_pedidos)
def pedidos_admin(request):
    """Todos los pedidos, para quien los prepara y los entrega."""
    pedidos = Pedido.objects.select_related("usuario").prefetch_related("items").order_by("-creado_en")
    return render(request, "tienda/pedidos_admin.html", {"pedidos": pedidos})


@requiere(Usuario.puede_gestionar_pedidos)
def pedido_admin_detalle(request, pedido_id):
    pedido = get_object_or_404(Pedido.objects.select_related("usuario").prefetch_related("items"), pk=pedido_id)
    return render(request, "tienda/pedido_admin_detalle.html", {"pedido": pedido})
