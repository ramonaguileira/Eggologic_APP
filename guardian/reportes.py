"""Reporte mensual de cada restaurante: se arma con sus retiros, lo verifica una persona de
Eggologic y se manda a la policy FLW.

En Guardian son dos pasos. El restaurante envía su Ground Entity Report (rol PPE) y el
Proponente lo aprueba, lo que mintea FGET por la reducción neta (field7) a la cuenta del
restaurante. Eggologic custodia las dos cuentas, así que la app hace los dos pasos.
"""

import calendar
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Count, DateField, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from captura.models import Retiro
from cuentas.models import Restaurante
from impacto.calculos import KG_ORGANICOS, emisiones_evitadas

from .cliente import ErrorGuardian, Sesion, clave_de_restaurante, tiene_credenciales
from .models import ReporteMensual

# SUPUESTO: en la policy, el restaurante es una actividad de consumo y el residuo, sin Eggologic,
# iría a disposición final. Las masas van en kg húmedos: el schema pide materia seca, sin unidad,
# y el factor de humedad lo define CarboSur.
TIPO_DE_ACTIVIDAD = "Consumption"
DESTINO_SIN_PROYECTO = "Disposición final (relleno sanitario)"
DESTINO_CON_PROYECTO = "Alimento animal: larva BSF para gallinas (Eggologic)"


def periodo(mes):
    """Primer y último día del mes."""
    return mes, date(mes.year, mes.month, calendar.monthrange(mes.year, mes.month)[1])


def revisar(restaurante, mes, hoy=None):
    """Números del mes de un restaurante y, si todavía no se puede verificar, el motivo."""
    hoy = hoy or timezone.localdate()
    desde, hasta = periodo(mes)
    totales = Retiro.objects.filter(restaurante=restaurante, fecha__date__range=(desde, hasta)).aggregate(
        cantidad=Count("id"),
        sin_clasificar=Count("id", filter=Q(kg_impropios=None)),
        organicos=Sum(KG_ORGANICOS),
    )
    kg_organicos = totales["organicos"] or Decimal("0")
    emisiones = emisiones_evitadas(kg_organicos)

    if mes >= hoy.replace(day=1):
        motivo = "Mes en curso"
    elif not totales["cantidad"]:
        motivo = "Sin retiros"
    elif totales["sin_clasificar"]:
        motivo = f"Faltan clasificar {totales['sin_clasificar']}"
    elif emisiones["neto"] <= 0:
        # Un mint de 0 no tiene sentido: hace falta al menos 0,01 tCO2e.
        motivo = "Muy pocos kg"
    elif not tiene_credenciales(clave_de_restaurante(restaurante.codigo)):
        motivo = "Sin usuario en el registro"
    else:
        motivo = ""
    return {
        "restaurante": restaurante,
        "mes": mes,
        "retiros": totales["cantidad"],
        "kg_organicos": kg_organicos,
        "emisiones": emisiones,
        "motivo": motivo,
    }


def meses_por_verificar(hoy=None):
    """Cada restaurante y mes con retiros que todavía no tiene reporte, del más nuevo al más viejo."""
    hoy = hoy or timezone.localdate()
    pares = list(
        Retiro.objects.filter(fecha__date__lt=hoy.replace(day=1))
        .annotate(mes=TruncMonth("fecha", output_field=DateField()))
        .order_by()  # sin el orden por fecha del modelo, que rompería el distinct
        .values_list("restaurante", "mes")
        .distinct()
    )
    verificados = set(ReporteMensual.objects.values_list("restaurante", "mes"))
    restaurantes = Restaurante.objects.in_bulk({restaurante for restaurante, _ in pares})
    filas = [
        revisar(restaurantes[restaurante], mes, hoy)
        for restaurante, mes in pares
        if (restaurante, mes) not in verificados
    ]
    return sorted(filas, key=lambda fila: (-fila["mes"].toordinal(), fila["restaurante"].codigo))


def verificar(restaurante, mes, usuario, hoy=None):
    """Una persona de Eggologic revisó los números: el reporte queda en cola para Guardian."""
    revision = revisar(restaurante, mes, hoy)
    if revision["motivo"]:
        raise ValidationError(revision["motivo"])
    if ReporteMensual.objects.filter(restaurante=restaurante, mes=mes).exists():
        raise ValidationError("Ese mes ya está verificado.")
    emisiones = revision["emisiones"]
    return ReporteMensual.objects.create(
        restaurante=restaurante,
        mes=mes,
        retiros=revision["retiros"],
        kg_organicos=revision["kg_organicos"],
        tco2e_linea_base=emisiones["linea_base"],
        tco2e_proyecto=emisiones["proyecto"],
        tco2e_fugas=emisiones["fugas"],
        tco2e_neto=emisiones["neto"],
        verificado_por=usuario,
    )


def nombre_de_actividad(reporte):
    """Identifica el reporte en Guardian. Lleva el código del restaurante, nunca el nombre."""
    return f"Retiros de residuo orgánico {reporte.restaurante.codigo} {reporte.mes:%Y-%m}"


def documento(reporte):
    """El Ground Entity Report de la policy FLW. Todo lo que va acá queda público."""
    desde, hasta = periodo(reporte.mes)
    origen = f"Restaurante {reporte.restaurante.codigo}, Maldonado"
    kg = float(reporte.kg_organicos)
    return {
        "field0": nombre_de_actividad(reporte),
        "field1": [TIPO_DE_ACTIVIDAD],
        "field2": [{"field0": origen, "field1": DESTINO_SIN_PROYECTO, "field2": "Yes", "field3": kg}],
        "field3": float(reporte.tco2e_linea_base),
        "field4": [{"field0": origen, "field1": DESTINO_CON_PROYECTO, "field2": "Yes", "field3": kg}],
        "field5": float(reporte.tco2e_proyecto),
        "field6": float(reporte.tco2e_fugas),
        "field7": float(reporte.tco2e_neto),
        "field8": {"field0": desde.isoformat(), "field1": hasta.isoformat()},
    }


def enviar(reporte):
    """Hace en Guardian los pasos que le faltan al reporte.

    Se puede repetir: antes de cada paso se fija si ya está hecho, así un corte a mitad de
    camino no duplica el reporte ni la aprobación.
    """
    nombre = nombre_de_actividad(reporte)

    if reporte.estado == ReporteMensual.Estado.EN_COLA:
        restaurante = Sesion(clave_de_restaurante(reporte.restaurante.codigo))
        if not _buscar(restaurante.bloque("entity_report_grid_ppe"), nombre, "entity_report"):
            proyectos = restaurante.bloque("projects_grid_ppe").get("data", [])
            if not proyectos:
                raise ErrorGuardian("El restaurante no ve ningún proyecto validado.")
            # SUPUESTO: hay un solo proyecto validado (Nodo 1). Se manda la fila entera, como la interfaz.
            restaurante.enviar("add_entity_report_btn", {"document": documento(reporte), "ref": proyectos[0]})
        reporte.estado = ReporteMensual.Estado.ENVIADO
        reporte.save(update_fields=["estado"])

    if reporte.estado == ReporteMensual.Estado.ENVIADO:
        proponente = Sesion("PROPONENTE")
        grilla = proponente.bloque("entity_report_grid_pp")
        if not _buscar(grilla, nombre, "approved_entity_report"):
            pendiente = _buscar(grilla, nombre, "entity_report", "Waiting for Verification")
            if pendiente is None:
                raise ErrorGuardian("El reporte todavía no aparece para aprobar. Se reintenta en la próxima vuelta.")
            proponente.enviar("approve_ppe_report_btn", {"tag": "Button_0", "document": pendiente})
        reporte.estado = ReporteMensual.Estado.REGISTRADO
        reporte.registrado_en = timezone.now()
        reporte.ultimo_error = ""
        reporte.save(update_fields=["estado", "registrado_en", "ultimo_error"])


def _buscar(bloque, nombre, tipo, estado=None):
    """El documento de una grilla de Guardian con ese nombre de actividad y tipo, o None."""
    for doc in bloque.get("data", []):
        campos = doc["document"]["credentialSubject"]
        campos = campos[0] if isinstance(campos, list) else campos
        if campos.get("field0") != nombre or doc.get("type") != tipo:
            continue
        if estado is None or (doc.get("option") or {}).get("status") == estado:
            return doc
    return None
