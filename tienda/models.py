from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Producto(models.Model):
    nombre = models.CharField(max_length=80)
    descripcion = models.CharField("descripción", max_length=200, blank=True)
    huevos = models.PositiveIntegerField("huevos por unidad", validators=[MinValueValidator(1)])
    precio = models.DecimalField("precio ($)", max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0, help_text="Orden en la tienda (de menor a mayor).")

    class Meta:
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    class Estado(models.TextChoices):
        RECIBIDO = "recibido", "Recibido"
        CONFIRMADO = "confirmado", "Confirmado"
        ENTREGADO = "entregado", "Entregado"
        CANCELADO = "cancelado", "Cancelado"

    # Sin pago online por ahora.
    class FormaPago(models.TextChoices):
        CONTRA_ENTREGA = "contra_entrega", "Pago contra entrega"
        TRANSFERENCIA = "transferencia", "Transferencia bancaria"

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pedidos")
    creado_en = models.DateTimeField("fecha", auto_now_add=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.RECIBIDO)
    forma_pago = models.CharField("forma de pago", max_length=20, choices=FormaPago.choices)
    direccion = models.CharField("dirección de entrega", max_length=200)
    telefono = models.CharField("teléfono", max_length=40)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Pedido N.º {self.pk}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def huevos(self):
        return sum(item.huevos for item in self.items.all())


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    # Se copian del producto al comprar, para que un cambio de precio no altere pedidos viejos.
    precio_unitario = models.DecimalField("precio unitario ($)", max_digits=10, decimal_places=2)
    huevos_por_unidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cantidad} × {self.producto}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    @property
    def huevos(self):
        return self.cantidad * self.huevos_por_unidad
