from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import ItemPedido, Pedido

MAXIMO_POR_PRODUCTO = 50


class PedidoForm(forms.Form):
    """Elegir cantidades de cada producto y los datos de entrega, en una sola pantalla."""

    direccion = forms.CharField(label="Dirección de entrega", max_length=200)
    telefono = forms.CharField(label="Teléfono", max_length=40)
    forma_pago = forms.ChoiceField(
        label="Forma de pago",
        choices=Pedido.FormaPago.choices,
        widget=forms.RadioSelect,
        initial=Pedido.FormaPago.CONTRA_ENTREGA,
    )
    notas = forms.CharField(label="Notas", required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, productos, **kwargs):
        super().__init__(*args, **kwargs)
        self.productos = list(productos)
        for producto in self.productos:
            self.fields[self._nombre_campo(producto)] = forms.IntegerField(
                label=producto.nombre,
                min_value=0,
                max_value=MAXIMO_POR_PRODUCTO,
                initial=0,
                required=False,
            )

    @staticmethod
    def _nombre_campo(producto):
        return f"cantidad_{producto.pk}"

    def campos_de_productos(self):
        """Pares (producto, campo de cantidad) para mostrar en la plantilla."""
        return [(producto, self[self._nombre_campo(producto)]) for producto in self.productos]

    def productos_elegidos(self):
        elegidos = []
        for producto in self.productos:
            cantidad = self.cleaned_data.get(self._nombre_campo(producto)) or 0
            if cantidad > 0:
                elegidos.append((producto, cantidad))
        return elegidos

    def clean(self):
        datos = super().clean()
        if not self.productos_elegidos():
            raise ValidationError("Elegí al menos un producto.")
        return datos

    @transaction.atomic
    def crear_pedido(self, usuario):
        pedido = Pedido.objects.create(
            usuario=usuario,
            forma_pago=self.cleaned_data["forma_pago"],
            direccion=self.cleaned_data["direccion"],
            telefono=self.cleaned_data["telefono"],
            notas=self.cleaned_data["notas"],
        )
        for producto, cantidad in self.productos_elegidos():
            ItemPedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                huevos_por_unidad=producto.huevos,
            )
        return pedido
