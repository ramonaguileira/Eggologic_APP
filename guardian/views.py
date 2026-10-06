from datetime import date

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cuentas.models import Restaurante, Usuario
from cuentas.permisos import requiere

from .models import ReporteMensual
from .reportes import enviar_pendientes, meses_por_verificar, verificar

CANTIDAD_VERIFICADOS = 50


# SUPUESTO: verifica solo administración (Ramón: "una persona en Eggologic").
@requiere(Usuario.es_admin)
def reportes(request):
    if request.method == "POST":
        restaurante = get_object_or_404(Restaurante, pk=request.POST.get("restaurante"))
        try:
            mes = date.fromisoformat(request.POST.get("mes", "")).replace(day=1)
        except ValueError:
            raise Http404
        try:
            verificar(restaurante, mes, request.user)
        except ValidationError as error:
            messages.error(request, f"No se pudo verificar {restaurante.codigo} de {mes:%m/%Y}: {error.messages[0]}.")
        else:
            messages.success(
                request, f"Reporte de {restaurante.codigo} de {mes:%m/%Y} verificado: queda en cola para el registro."
            )
        return redirect("guardian:reportes")

    contexto = {
        "por_verificar": meses_por_verificar(),
        "verificados": ReporteMensual.objects.select_related("restaurante", "verificado_por")[:CANTIDAD_VERIFICADOS],
        "hay_por_enviar": ReporteMensual.objects.exclude(estado=ReporteMensual.Estado.REGISTRADO).exists(),
    }
    return render(request, "guardian/reportes.html", contexto)


@require_POST
@requiere(Usuario.es_admin)
def enviar_al_registro(request):
    """Lo mismo que el comando guardian_enviar, desde la pantalla (en Render gratis no hay cron)."""
    resultados = enviar_pendientes()
    registrados = sum(1 for reporte, error in resultados if reporte.estado == ReporteMensual.Estado.REGISTRADO)
    con_error = sum(1 for _, error in resultados if error)
    esperando = len(resultados) - registrados - con_error
    if registrados:
        messages.success(request, f"Registrados: {registrados}.")
    if esperando:
        messages.info(request, f"Enviados, falta la aprobación: {esperando}. Volvé a tocar Enviar en un minuto.")
    if con_error:
        messages.error(request, f"Con error: {con_error}. El detalle está en la tabla.")
    return redirect("guardian:reportes")
