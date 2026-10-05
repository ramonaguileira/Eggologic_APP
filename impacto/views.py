from django.shortcuts import render

from cuentas.models import Usuario
from cuentas.permisos import requiere

from . import calculos


@requiere(Usuario.puede_comprar)
def mi_impacto(request):
    factores = calculos.factores_del_circuito()
    restaurante = getattr(request.user, "restaurante", None)
    cliente = getattr(request.user, "cliente", None)
    contexto = {
        "factores": factores,
        "compras": calculos.impacto_de_compras(request.user, factores),
        "entregas": calculos.impacto_de_entregas(restaurante, factores) if restaurante else None,
        "restaurante": restaurante,
        "nivel": cliente.get_nivel_display() if cliente else None,
        "comunidad": calculos.totales_de_la_comunidad(),
    }
    return render(request, "impacto/mi_impacto.html", contexto)
