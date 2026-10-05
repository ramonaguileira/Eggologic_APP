from django.shortcuts import render

from cuentas.models import Usuario
from cuentas.permisos import requiere

from . import calculos


@requiere(Usuario.puede_comprar)
def mi_impacto(request):
    factores = calculos.factores_del_circuito()
    restaurante = getattr(request.user, "restaurante", None)
    compras = calculos.impacto_de_compras(request.user, factores)
    contexto = {
        "factores": factores,
        "compras": compras,
        "entregas": calculos.impacto_de_entregas(restaurante, factores) if restaurante else None,
        "restaurante": restaurante,
        # Los niveles son para clientes, no para restaurantes.
        "nivel": None if restaurante else calculos.nivel_del_cliente(compras["huevos"]),
        "comunidad": calculos.totales_de_la_comunidad(),
    }
    return render(request, "impacto/mi_impacto.html", contexto)
