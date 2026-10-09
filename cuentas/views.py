from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LoginForm, RegistroClienteForm


def ingresar(request):
    """Login con email en lugar de username."""
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, f"¡Bienvenido/a, {form.get_user().first_name}!")
            return redirect("inicio")
    else:
        form = LoginForm()
    return render(request, "registration/login.html", {"form": form})


@login_required
def inicio(request):
    """Lleva a cada usuario a su pantalla según el rol."""
    usuario = request.user
    if usuario.puede_ver_datos():
        return redirect("captura:panel")
    if usuario.puede_clasificar():
        return redirect("captura:retiros")
    if usuario.puede_cargar_granja():
        return redirect("captura:granja")
    if usuario.puede_retirar():
        return redirect("captura:retiro_nuevo")
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
