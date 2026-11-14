from django.conf import settings
from django.db import models


class Movimiento(models.Model):
    """Una suma o una resta de Eggos. Solo se agregan: un error se corrige con otro movimiento."""

    class Motivo(models.TextChoices):
        RECARGA = "recarga", "Recarga"
        VUELTA = "vuelta", "Vuelta por una compra"
        PEDIDO = "pedido", "Pago de un pedido"
        GALLINA = "gallina", "Gallina"
        LEVANTE = "levante", "Levante de residuos"
        AJUSTE = "ajuste", "Ajuste de Eggologic"

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos_eggos")
    cantidad = models.IntegerField(help_text="Positivo suma, negativo resta.")
    motivo = models.CharField(max_length=20, choices=Motivo.choices)
    detalle = models.CharField(max_length=200, blank=True)
    # Lo que originó el movimiento (por ejemplo "vuelta-pedido-12"). Al ser único, la base
    # garantiza que el mismo origen no se acredite dos veces.
    referencia = models.CharField(max_length=80, unique=True, null=True, blank=True)
    creado_en = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        ordering = ["-creado_en", "-id"]

    def __str__(self):
        return f"{self.cantidad:+d} Eggos · {self.get_motivo_display()}"


class Recarga(models.Model):
    """Plata que entra para convertirse en Eggos. Se acredita cuando el pago está confirmado."""

    class Medio(models.TextChoices):
        MERCADO_PAGO = "mercado_pago", "Mercado Pago"
        TRANSFERENCIA = "transferencia", "Transferencia bancaria"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        ACREDITADA = "acreditada", "Acreditada"
        CANCELADA = "cancelada", "Cancelada"

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recargas")
    monto = models.PositiveIntegerField("monto ($)")
    medio = models.CharField(max_length=20, choices=Medio.choices)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    creado_en = models.DateTimeField("fecha", auto_now_add=True)
    acreditada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Recarga N.º {self.pk} · $ {self.monto}"
