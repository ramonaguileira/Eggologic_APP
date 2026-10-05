from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def requiere(chequeo):
    """Exige estar logueado y que chequeo(usuario) sea verdadero; si no, responde 403.

    Uso: @requiere(Usuario.puede_capturar)
    """

    def decorador(vista):
        @wraps(vista)
        def vista_protegida(request, *args, **kwargs):
            if not chequeo(request.user):
                raise PermissionDenied
            return vista(request, *args, **kwargs)

        return login_required(vista_protegida)

    return decorador
