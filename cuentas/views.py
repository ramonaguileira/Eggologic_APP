from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def inicio(request):
    """Lleva a cada usuario a su pantalla según el rol."""
    if request.user.puede_ver_datos():
        return redirect("captura:panel")
    # Restaurantes y clientes: su sector (tienda e impacto) llega en una etapa siguiente.
    return render(request, "cuentas/inicio_usuario.html")
