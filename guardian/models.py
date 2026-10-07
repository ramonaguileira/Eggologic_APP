from django.conf import settings
from django.db import models

from cuentas.models import Restaurante


class ReporteMensual(models.Model):
    """Reporte de un restaurante para un mes, revisado por una persona de Eggologic.

    Guarda los números tal como se revisaron. El comando guardian_enviar lo manda a Guardian:
    primero como el restaurante (Ground Entity Report) y después lo aprueba como Proponente,
    que es lo que dispara el mint.
    """

    # "Revisado" y no "verificado": verificado queda reservado para la verificación externa
    # (UNIT, ISO 14064-3). Nada se muestra como verificado antes de eso.
    class Estado(models.TextChoices):
        EN_COLA = "en_cola", "Revisado, por enviar"
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
    revisado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    revisado_en = models.DateTimeField(auto_now_add=True)
    registrado_en = models.DateTimeField(null=True, blank=True)
    # Dónde quedó el reporte en Hedera: topic de HCS y timestamp de consenso del mensaje.
    topic_hcs = models.CharField("topic de HCS", max_length=30, blank=True)
    mensaje_hcs = models.CharField("mensaje en HCS", max_length=40, blank=True)
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

    @property
    def enlace_publico(self):
        """El mensaje del reporte en HashScan, el explorador público de Hedera (testnet)."""
        # SUPUESTO: HashScan abre una transacción por su timestamp de consenso. Probarlo en el navegador.
        if not self.mensaje_hcs:
            return ""
        return f"https://hashscan.io/testnet/transaction/{self.mensaje_hcs}"
