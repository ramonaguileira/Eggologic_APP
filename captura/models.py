from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.formats import date_format, number_format

from cuentas.models import Restaurante

CERO = Decimal("0")
NO_NEGATIVO = [MinValueValidator(CERO)]
FOTO_MAXIMO_MB = 15


def validar_tamano_foto(archivo):
    if archivo.size > FOTO_MAXIMO_MB * 1024 * 1024:
        raise ValidationError(f"La foto no puede pesar más de {FOTO_MAXIMO_MB} MB.")


def campo_kg(nombre, **opciones):
    return models.DecimalField(nombre, max_digits=8, decimal_places=2, validators=NO_NEGATIVO, **opciones)


class RegistroBase(models.Model):
    """Campos que comparten todos los registros de campo (la misma cabecera para todas las fuentes)."""

    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", editable=False
    )
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Retiro(RegistroBase):
    """Residuo que el chofer levanta en un restaurante, y cómo se clasifica.

    El chofer carga el restaurante, los kg y una foto; la fecha y la ubicación se toman solas.
    La clasificación se completa después, en la planta. En términos del FLW Standard: los
    restos vegetales se acercan a "partes no comestibles asociadas", los residuos de plato a
    "alimento", y los impropios quedan fuera del inventario (SUPUESTO, lo define CarboSur).
    """

    restaurante = models.ForeignKey(Restaurante, on_delete=models.PROTECT, related_name="retiros")
    fecha = models.DateTimeField(default=timezone.now)
    kg_levantados = campo_kg("levantado (kg)")
    foto = models.FileField(
        upload_to="retiros/%Y/%m/",
        blank=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp", "heic", "heif"]),
            validar_tamano_foto,
        ],
    )
    # Las toma el celular del chofer al abrir el formulario. Quedan vacías si no dio permiso.
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    precision_m = models.PositiveIntegerField("precisión de la ubicación (m)", null=True, blank=True)

    kg_impropios = campo_kg("impropios (kg)", null=True, blank=True)
    kg_restos_vegetales = campo_kg("restos vegetales (kg)", null=True, blank=True)
    kg_residuos_plato = campo_kg("residuos de plato (kg)", null=True, blank=True)

    # Línea de base para CarboSur: lo que el restaurante descartó por otra vía (basura común)
    # desde el retiro anterior. Opcional. SUPUESTO: se informa en cada retiro.
    kg_no_ingresa = campo_kg("no entra a Eggologic (kg)", null=True, blank=True)
    no_ingresa_estimado = models.BooleanField("ese dato es una estimación", default=False)

    # SUPUESTO: un retiro entra entero a un solo lote. Se asigna desde el formulario del lote.
    lote = models.ForeignKey(
        "Lote", on_delete=models.SET_NULL, null=True, blank=True, related_name="retiros", editable=False
    )

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        fecha = date_format(timezone.localtime(self.fecha), "d/m H:i")
        texto = f"N.º {self.pk} · {fecha} · {self.restaurante.codigo}"
        if self.clasificado:
            texto += f" · {number_format(self.kg_organicos, 1)} kg orgánicos"
        return texto

    def _clasificacion(self):
        return [self.kg_impropios, self.kg_restos_vegetales, self.kg_residuos_plato]

    @property
    def clasificado(self):
        return None not in self._clasificacion()

    @property
    def kg_organicos(self):
        """Lo que va a bioconversión: restos vegetales + residuos de plato."""
        if not self.clasificado:
            return None
        return self.kg_restos_vegetales + self.kg_residuos_plato

    def clean(self):
        valores = self._clasificacion()
        cargados = [v for v in valores if v is not None]
        if cargados and len(cargados) < len(valores):
            raise ValidationError(
                "Para clasificar hay que completar impropios, restos vegetales y residuos de plato "
                "(pueden ser 0)."
            )
        if cargados and self.kg_levantados is not None and sum(cargados) > self.kg_levantados:
            raise ValidationError("La clasificación suma más kg que lo levantado.")
        if self.lote_id and not self.clasificado:
            raise ValidationError("Este retiro está en un lote: la clasificación no se puede borrar.")


class Lote(RegistroBase):
    """Lote de bioconversión BSF: el residuo clasificado entra en bandejas con neonatos y sale
    como larva y frass."""

    fecha_inicio = models.DateField("fecha de inicio", default=timezone.localdate)
    bandejas = models.PositiveIntegerField("bandejas generadas")
    # SUPUESTO: los neonatos se miden en gramos.
    g_neonatos = models.DecimalField(
        "neonatos utilizados (g)", max_digits=8, decimal_places=1, validators=NO_NEGATIVO
    )

    # Se completan al cosechar.
    fecha_cosecha = models.DateField("fecha de cosecha", null=True, blank=True)
    kg_larvas = campo_kg("larvas (kg)", null=True, blank=True)
    kg_frass = campo_kg("frass (kg)", null=True, blank=True)

    class Meta:
        ordering = ["-fecha_inicio", "-id"]

    def __str__(self):
        return f"Lote N.º {self.pk} ({date_format(self.fecha_inicio, 'd/m/Y')})"

    @property
    def cosechado(self):
        return self.fecha_cosecha is not None

    @property
    def kg_residuo(self):
        """kg orgánicos que entraron al lote (suma de sus retiros)."""
        return sum((retiro.kg_organicos or CERO for retiro in self.retiros.all()), CERO)

    @property
    def rendimiento(self):
        """kg de larva por cada 100 kg de residuo orgánico."""
        if self.kg_larvas is None or not self.kg_residuo:
            return None
        return self.kg_larvas / self.kg_residuo * 100

    def clean(self):
        cosecha = [self.fecha_cosecha, self.kg_larvas, self.kg_frass]
        if any(v is not None for v in cosecha) and None in cosecha:
            raise ValidationError(
                "Para registrar la cosecha hay que completar fecha, kg de larvas y kg de frass."
            )
        if self.fecha_cosecha and self.fecha_inicio and self.fecha_cosecha < self.fecha_inicio:
            raise ValidationError("La cosecha no puede ser anterior al inicio del lote.")


class RegistroGranja(RegistroBase):
    """Producción del día en la granja (Camino Verde)."""

    # SUPUESTO: un solo registro por día para toda la granja.
    fecha = models.DateField(default=timezone.localdate, unique=True)
    huevos = models.PositiveIntegerField("huevos producidos")
    kg_larvas = campo_kg("larvas para las gallinas (kg)")
    lote = models.ForeignKey(
        Lote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_granja",
        verbose_name="lote de las larvas",
        help_text="Opcional: de qué lote salieron las larvas.",
    )

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "registro de granja"
        verbose_name_plural = "registros de granja"

    def __str__(self):
        return f"Granja {date_format(self.fecha, 'd/m/Y')}"


class Archivo(models.Model):
    """Contenido de un archivo subido (hoy, las fotos de los retiros). Lo usa captura.almacen."""

    nombre = models.CharField(max_length=255, unique=True)
    contenido = models.BinaryField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
