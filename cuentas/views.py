from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistroClienteForm


@login_required
def inicio(request):
    """Lleva a cada usuario a su pantalla según el rol."""
    if request.user.puede_ver_datos():
        return redirect("captura:panel")
    return redirect("impacto:mi_impacto")


def registrarse(request):
    """Alta de clientes. Los restaurantes los da de alta Eggologic desde la administración."""
    form = RegistroClienteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, f"¡Bienvenido/a, {usuario.first_name}! Ya podés hacer tu primer pedido.")
        return redirect("tienda:tienda")
    return render(request, "registration/registrarse.html", {"form": form})
