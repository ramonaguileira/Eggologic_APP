import csv
from datetime import date, timedelta

from django.contrib import messages
from django.db.models import Count, F, Q, Sum
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.formats import number_format

from cuentas.models import Usuario
from cuentas.permisos import requiere
from guardian.models import ReporteMensual
from impacto import calculos

from .forms import LoteForm, RegistroGranjaForm, RetiroChoferForm, RetiroClasificacionForm
from .models import Lote, RegistroGranja, Retiro

DIAS_DEL_PANEL = 30
CANTIDAD_EN_LISTAS = 50


@requiere(Usuario.puede_ver_datos)
def panel(request):
    desde = timezone.now() - timedelta(days=DIAS_DEL_PANEL)
    # Los nombres de los totales no repiten los de los campos: Django los confundiría.
    retiros = Retiro.objects.filter(fecha__gte=desde).aggregate(
        cantidad=Count("id"),
        levantado=Sum("kg_levantados"),
        levantado_clasificado=Sum("kg_levantados", filter=Q(kg_impropios__isnull=False)),
        impropios=Sum("kg_impropios"),
        organicos=Sum(F("kg_restos_vegetales") + F("kg_residuos_plato")),
    )
    # El % de impropios se calcula solo sobre los retiros que ya están clasificados.
    if retiros["levantado_clasificado"]:
        retiros["pct_impropios"] = retiros["impropios"] / retiros["levantado_clasificado"] * 100
    lotes = Lote.objects.filter(fecha_cosecha__gte=desde.date()).aggregate(
        larvas=Sum("kg_larvas"), frass=Sum("kg_frass")
    )
    granja = RegistroGranja.objects.filter(fecha__gte=desde.date()).aggregate(
        huevos_producidos=Sum("huevos"), larvas_usadas=Sum("kg_larvas")
    )
    contexto = {
        "dias": DIAS_DEL_PANEL,
        "retiros": retiros,
        "lotes": lotes,
        "granja": granja,
        "sin_clasificar": Retiro.objects.filter(kg_impropios=None).count(),
        "lotes_en_curso": Lote.objects.filter(fecha_cosecha=None).prefetch_related("retiros"),
    }
    return render(request, "captura/panel.html", contexto)


@requiere(Usuario.puede_ver_datos)
def informe(request):
    """Informe del circuito entre dos fechas, para ANDE y CarboSur. Se imprime o se guarda como
    PDF desde el navegador. Por defecto, desde el primer retiro hasta hoy."""
    hoy = timezone.localdate()
    primero = Retiro.objects.order_by("fecha").first()
    desde = _fecha(request.GET.get("desde")) or (timezone.localtime(primero.fecha).date() if primero else hoy)
    hasta = _fecha(request.GET.get("hasta")) or hoy
    contexto = calculos.informe(desde, hasta)
    contexto.update({
        "desde": desde,
        "hasta": hasta,
        "reportes": ReporteMensual.objects.filter(mes__range=(desde.replace(day=1), hasta)).select_related("restaurante"),
    })
    return render(request, "captura/informe.html", contexto)


def _fecha(texto):
    try:
        return date.fromisoformat(texto or "")
    except ValueError:
        return None


# --- Listas -------------------------------------------------------------------


@requiere(Usuario.puede_ver_datos)
def retiros(request):
    lista = Retiro.objects.select_related("restaurante", "lote")[:CANTIDAD_EN_LISTAS]
    return render(request, "captura/retiros.html", {"retiros": lista})


@requiere(Usuario.puede_ver_datos)
def lotes(request):
    lista = Lote.objects.prefetch_related("retiros")[:CANTIDAD_EN_LISTAS]
    return render(request, "captura/lotes.html", {"lotes": lista})


@requiere(Usuario.puede_ver_datos)
def granja(request):
    lista = RegistroGranja.objects.select_related("lote")[:CANTIDAD_EN_LISTAS]
    return render(request, "captura/granja.html", {"registros": lista})


# --- Altas y ediciones --------------------------------------------------------


def _formulario(request, clase_form, instancia, titulo, volver_a, plantilla="captura/formulario.html"):
    """Muestra un formulario de alta o edición y, si es válido, lo guarda."""
    form = clase_form(request.POST or None, request.FILES or None, instance=instancia)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Guardado.")
        return redirect(volver_a)
    return render(request, plantilla, {"form": form, "titulo": titulo, "volver_a": volver_a})


@requiere(Usuario.puede_capturar)
def retiro_nuevo(request):
    retiro = Retiro(registrado_por=request.user)
    return _formulario(
        request, RetiroChoferForm, retiro, "Nuevo retiro", "captura:retiros", "captura/retiro_nuevo.html"
    )


@requiere(Usuario.puede_capturar)
def retiro_clasificar(request, pk):
    retiro = get_object_or_404(Retiro.objects.select_related("restaurante"), pk=pk)
    kg = number_format(retiro.kg_levantados, 1)
    titulo = f"Clasificar retiro N.º {pk} · {retiro.restaurante.nombre} · {kg} kg levantados"
    return _formulario(request, RetiroClasificacionForm, retiro, titulo, "captura:retiros")


@requiere(Usuario.puede_ver_datos)
def retiro_foto(request, pk):
    """Las fotos no se publican por URL: solo las ve quien tiene acceso a los datos de campo."""
    retiro = get_object_or_404(Retiro, pk=pk)
    if not retiro.foto:
        raise Http404
    return FileResponse(retiro.foto.open("rb"))


@requiere(Usuario.puede_capturar)
def lote_nuevo(request):
    lote = Lote(registrado_por=request.user)
    return _formulario(request, LoteForm, lote, "Nuevo lote", "captura:lotes")


@requiere(Usuario.puede_capturar)
def lote_editar(request, pk):
    lote = get_object_or_404(Lote, pk=pk)
    return _formulario(request, LoteForm, lote, f"Lote N.º {pk}", "captura:lotes")


@requiere(Usuario.puede_capturar)
def granja_nuevo(request):
    registro = RegistroGranja(registrado_por=request.user)
    return _formulario(request, RegistroGranjaForm, registro, "Registro de granja", "captura:granja")


@requiere(Usuario.puede_capturar)
def granja_editar(request, pk):
    registro = get_object_or_404(RegistroGranja, pk=pk)
    return _formulario(request, RegistroGranjaForm, registro, "Registro de granja", "captura:granja")


# --- Exportación para CarboSur ------------------------------------------------
# SUPUESTO: CarboSur abre los archivos en Excel en español, así que se usa punto y coma como
# separador, coma decimal y UTF-8 con BOM (para que Excel muestre bien los acentos).


def _numero(valor):
    return "" if valor is None else str(valor).replace(".", ",")


def _fecha(valor):
    if valor is None:
        return ""
    if hasattr(valor, "hour"):
        return timezone.localtime(valor).strftime("%Y-%m-%d %H:%M")
    return valor.strftime("%Y-%m-%d")


def _respuesta_csv(nombre_archivo, encabezados, filas):
    respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    respuesta.write("﻿")
    escritor = csv.writer(respuesta, delimiter=";")
    escritor.writerow(encabezados)
    escritor.writerows(filas)
    return respuesta


@requiere(Usuario.puede_ver_datos)
def exportar_retiros(request):
    filas = (
        [
            r.pk,
            _fecha(r.fecha),
            r.restaurante.codigo,
            r.restaurante.nombre,
            _numero(r.kg_levantados),
            _numero(r.kg_impropios),
            _numero(r.kg_restos_vegetales),
            _numero(r.kg_residuos_plato),
            _numero(r.kg_no_ingresa),
            "sí" if r.no_ingresa_estimado else "no",
            r.lote_id or "",
            _numero(r.latitud),
            _numero(r.longitud),
            "sí" if r.foto else "no",
            r.observaciones,
        ]
        for r in Retiro.objects.select_related("restaurante").order_by("fecha")
    )
    encabezados = [
        "retiro",
        "fecha",
        "restaurante_codigo",
        "restaurante",
        "kg_levantados",
        "kg_impropios",
        "kg_restos_vegetales",
        "kg_residuos_plato",
        "kg_no_ingresa",
        "no_ingresa_estimado",
        "lote",
        "latitud",
        "longitud",
        "tiene_foto",
        "observaciones",
    ]
    return _respuesta_csv("retiros.csv", encabezados, filas)


@requiere(Usuario.puede_ver_datos)
def exportar_lotes(request):
    filas = (
        [
            lote.pk,
            _fecha(lote.fecha_inicio),
            ",".join(str(r.pk) for r in lote.retiros.all()),
            _numero(lote.kg_residuo),
            lote.bandejas,
            _numero(lote.g_neonatos),
            _fecha(lote.fecha_cosecha),
            _numero(lote.kg_larvas),
            _numero(lote.kg_frass),
            lote.observaciones,
        ]
        for lote in Lote.objects.prefetch_related("retiros").order_by("fecha_inicio", "id")
    )
    encabezados = [
        "lote",
        "fecha_inicio",
        "retiros",
        "kg_residuo_organico",
        "bandejas",
        "g_neonatos",
        "fecha_cosecha",
        "kg_larvas",
        "kg_frass",
        "observaciones",
    ]
    return _respuesta_csv("lotes.csv", encabezados, filas)


@requiere(Usuario.puede_ver_datos)
def exportar_granja(request):
    filas = (
        [_fecha(g.fecha), g.huevos, _numero(g.kg_larvas), g.lote_id or "", g.observaciones]
        for g in RegistroGranja.objects.order_by("fecha")
    )
    encabezados = ["fecha", "huevos", "kg_larvas", "lote", "observaciones"]
    return _respuesta_csv("granja.csv", encabezados, filas)
