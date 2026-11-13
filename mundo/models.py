from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from eggos import reglas
from eggos.models import Recarga


class Ajustes(models.Model):
    """Los números que Eggologic va corrigiendo a mano. Hay una sola fila."""

    huevos_disponibles = models.PositiveIntegerField(
        "huevos disponibles para vender", default=200, help_text="Cada pedido descuenta de acá."
    )
    gallinas_en_postura = models.PositiveIntegerField("gallinas en postura", default=60)
    parte_de_socios = models.PositiveIntegerField(
        "% de la producción que va a socios del gallinero", default=10
    )
    horas_de_entrega = models.PositiveIntegerField(
        "horas estimadas hasta la entrega", default=24, help_text="Con esto arranca la cuenta regresiva de cada pedido."
    )
    sanidad = models.CharField(
        "estado del plantel", max_length=200, default="Plantel sano. Comen larvas y pastorean todos los días."
    )

    class Meta:
        verbose_name = "ajustes de Eggo World"
        verbose_name_plural = "ajustes de Eggo World"

    def __str__(self):
        return "Ajustes de Eggo World"

    @classmethod
    def actuales(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def cupo_de_gallinas(self):
        """Cuántas gallinas se pueden tener adoptadas a la vez (ver el plan, punto 3.4)."""
        produccion = self.gallinas_en_postura * reglas.HUEVOS_POR_ANIO
        para_eggologic = produccion * (100 - self.parte_de_socios) / Decimal(100)
        prometido_por_gallina = reglas.HUEVOS_POR_ANIO + reglas.BONO_MAXIMO_POR_ANIO
        return int(para_eggologic * reglas.PARTE_DE_LA_PRODUCCION_PARA_ADOPTANTES / prometido_por_gallina)


class Gallina(models.Model):
    """Una gallina adoptada: el derecho a recibir su producción mientras dure el plan."""

    class Plan(models.TextChoices):
        DOS_ANIOS = reglas.PLAN_DOS_ANIOS, "Dos años"
        UN_ANIO = reglas.PLAN_UN_ANIO, "Un año"
        MENSUAL = reglas.PLAN_MENSUAL, "Mensual"

    class Color(models.TextChoices):
        BLANCA = "blanca", "Blanca"
        COLORADA = "colorada", "Colorada"
        NEGRA = "negra", "Negra"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Esperando el pago"
        ACTIVA = "activa", "Activa"
        CANCELADA = "cancelada", "Cancelada"

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="gallinas")
    nombre = models.CharField(max_length=30)
    color = models.CharField(max_length=10, choices=Color.choices, default=Color.BLANCA)
    plan = models.CharField(max_length=10, choices=Plan.choices)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    inicio = models.DateField(null=True, blank=True)
    # Hasta cuándo está pago. En las prepagas es el final del plan; en la mensual se va corriendo.
    pago_hasta = models.DateField(null=True, blank=True)
    # Si no alcanzaban los Eggos, la recarga por la diferencia. Al acreditarse, la gallina se activa.
    recarga = models.OneToOneField(Recarga, on_delete=models.SET_NULL, null=True, blank=True, related_name="gallina")
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creada_en"]

    def __str__(self):
        return f"{self.nombre} ({self.get_plan_display()})"

    def precio(self):
        return reglas.PLANES[self.plan]["precio"]

    def dias_puestos(self, hoy=None):
        if self.estado != self.Estado.ACTIVA or not self.inicio:
            return 0
        hasta = min(hoy or timezone.localdate(), self.pago_hasta)
        return max((hasta - self.inicio).days, 0)

    def bono(self):
        return self.raciones.aggregate(total=Sum("cantidad"))["total"] or 0

    def bono_de_este_anio(self, hoy=None):
        """Huevos extra por larvas en el año en curso de la gallina (los años se cuentan desde el inicio)."""
        if not self.inicio:
            return 0
        hoy = hoy or timezone.localdate()
        comienzo = self.inicio + timedelta(days=365 * ((hoy - self.inicio).days // 365))
        total = self.raciones.filter(fecha__gte=comienzo).aggregate(total=Sum("cantidad"))["total"] or 0
        return total * reglas.HUEVOS_POR_RACION

    def lugar_para_larvas(self, hoy=None):
        if self.estado != self.Estado.ACTIVA:
            return 0
        return max(reglas.BONO_MAXIMO_POR_ANIO - self.bono_de_este_anio(hoy), 0) // reglas.HUEVOS_POR_RACION

    def huevos_puestos(self, hoy=None):
        """Se calcula con las fechas y la regla; no se guarda nada por día."""
        base = self.dias_puestos(hoy) * reglas.HUEVOS_POR_ANIO // 365
        return base + self.bono() * reglas.HUEVOS_POR_RACION

    def produccion_anual(self, hoy=None):
        return reglas.HUEVOS_POR_ANIO + self.bono_de_este_anio(hoy)


class RacionDeLarvas(models.Model):
    """Larvas que comió una gallina. Cada ración es un huevo más."""

    gallina = models.ForeignKey(Gallina, on_delete=models.CASCADE, related_name="raciones")
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    fecha = models.DateField(default=timezone.localdate)

    class Meta:
        verbose_name = "ración de larvas"
        verbose_name_plural = "raciones de larvas"


class Levante(models.Model):
    """Un cliente pide que le retiren sus residuos orgánicos.

    SUPUESTO: va en una tabla propia y no en captura.Retiro, que es de restaurantes y alimenta
    los reportes a Guardian. Los residuos de hogares no van al registro por ahora.
    """

    class Estado(models.TextChoices):
        PEDIDO = "pedido", "Pedido"
        RETIRADO = "retirado", "Retirado"
        CANCELADO = "cancelado", "Cancelado"

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="levantes")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PEDIDO)
    direccion = models.CharField("dirección", max_length=200)
    telefono = models.CharField("teléfono", max_length=40, blank=True)
    nota = models.CharField(max_length=200, blank=True)
    pedido_en = models.DateTimeField(auto_now_add=True)
    # Lo pesa el chofer al retirar el balde; no pasa por la clasificación de planta.
    kg = models.DecimalField("kg retirados", max_digits=6, decimal_places=2, null=True, blank=True)
    retirado_en = models.DateTimeField(null=True, blank=True)
    retirado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="levantes_retirados"
    )

    class Meta:
        ordering = ["-pedido_en"]

    def __str__(self):
        return f"Levante N.º {self.pk}"

    def raciones(self):
        return int((self.kg or 0) * reglas.RACIONES_POR_KG)

    def larvas_listas_el(self):
        if self.estado != self.Estado.RETIRADO or not self.retirado_en:
            return None
        return timezone.localtime(self.retirado_en).date() + timedelta(days=reglas.DIAS_HASTA_LAS_LARVAS)

    def paso(self, hoy=None):
        """En qué paso está, para mostrarle al cliente: pedido, retirado, procesando o larvas."""
        if self.estado != self.Estado.RETIRADO:
            return self.estado
        hoy = hoy or timezone.localdate()
        if hoy >= self.larvas_listas_el():
            return "larvas"
        return "procesando" if hoy > timezone.localtime(self.retirado_en).date() else "retirado"
