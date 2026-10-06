from django.conf import settings
from django.db import models

from cuentas.models import Restaurante


class ReporteMensual(models.Model):
    """Reporte de un restaurante para un mes, verificado por una persona de Eggologic.

    Guarda los números tal como se verificaron. El comando guardian_enviar lo manda a Guardian:
    primero como el restaurante (Ground Entity Report) y después lo aprueba como Proponente,
    que es lo que dispara el mint.
    """

    class Estado(models.TextChoices):
        EN_COLA = "en_cola", "Verificado, por enviar"
        ENVIADO = "enviado", "Enviado, falta la aprobación"
        REGISTRADO = "registrado", "Registrado"

    restaurante = models.ForeignKey(Restaurante, on_delete=models.PROTECT, related_name="reportes")
    mes = models.DateField(help_text="Primer día del mes.")
    retiros = models.PositiveIntegerField()
    kg_organicos = models.DecimalField("kg orgánicos", max_digits=10, decimal_places=2)
    tco2e_linea_base = models.DecimalField("tCO2e línea de base", max_digits=10, decimal_places=2)
    tco2e_proyecto = models.DecimalField("tCO2e del proyecto", max_digits=10, decimal_places=2)
    tco2e_fugas = models.DecimalField("tCO2e de fugas", max_digits=10, decimal_places=2)
    tco2e_neto = models.DecimalField("tCO2e evitadas (neto)", max_digits=10, decimal_places=2)

    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.EN_COLA)
    verificado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    verificado_en = models.DateTimeField(auto_now_add=True)
    registrado_en = models.DateTimeField(null=True, blank=True)
    intentos = models.PositiveIntegerField("intentos fallidos", default=0)
    ultimo_error = models.TextField("último error", blank=True)

    class Meta:
        ordering = ["-mes", "restaurante__codigo"]
        verbose_name = "reporte mensual"
        verbose_name_plural = "reportes mensuales"
        constraints = [
            models.UniqueConstraint(fields=["restaurante", "mes"], name="un_reporte_por_restaurante_y_mes"),
        ]

    def __str__(self):
        return f"{self.restaurante.codigo} {self.mes:%m/%Y}"
