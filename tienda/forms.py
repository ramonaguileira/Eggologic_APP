import secrets

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from cuentas.models import Cliente, Usuario

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
        self._crear_items(pedido)
        return pedido

    def _crear_items(self, pedido):
        for producto, cantidad in self.productos_elegidos():
            ItemPedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                huevos_por_unidad=producto.huevos,
            )


class CampoComprador(forms.ModelChoiceField):
    def label_from_instance(self, usuario):
        restaurante = getattr(usuario, "restaurante", None)
        if restaurante:
            return f"{restaurante.nombre} (restaurante)"
        return usuario.get_full_name() or usuario.username


class EntregaForm(PedidoForm):
    """Una entrega ya hecha, que carga Eggologic: queda como pedido entregado."""

    direccion = None
    telefono = None
    comprador = CampoComprador(
        label="Cliente o restaurante",
        required=False,
        queryset=Usuario.objects.filter(
            is_active=True, rol__in=[Usuario.Rol.CLIENTE, Usuario.Rol.RESTAURANTE]
        ).select_related("restaurante").order_by("first_name", "username"),
    )
    nombre_nuevo = forms.CharField(label="O un cliente nuevo: nombre", required=False, max_length=150)
    email_nuevo = forms.EmailField(label="Email del cliente nuevo (opcional)", required=False)
    fecha = forms.DateField(
        label="Fecha de la entrega",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    def clean(self):
        datos = super().clean()
        if bool(datos.get("comprador")) == bool(datos.get("nombre_nuevo")):
            raise ValidationError("Elegí un cliente o restaurante de la lista, o escribí el nombre de uno nuevo.")
        email = datos.get("email_nuevo")
        if email and Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya hay una cuenta con ese email: elegila de la lista.")
        if datos.get("fecha") and datos["fecha"] > timezone.localdate():
            raise ValidationError("La entrega no puede tener una fecha futura.")
        return datos

    def _cliente_nuevo(self):
        """Un cliente que todavía no tiene cuenta. Si dejó su email, después puede entrar con
        "Olvidé mi contraseña"."""
        email = self.cleaned_data["email_nuevo"]
        usuario = Usuario.objects.create_user(
            username=email or f"cliente-{secrets.token_hex(4)}",
            email=email,
            password=secrets.token_urlsafe(16),
            first_name=self.cleaned_data["nombre_nuevo"],
            rol=Usuario.Rol.CLIENTE,
        )
        Cliente.objects.create(usuario=usuario)
        return usuario

    @transaction.atomic
    def crear_entrega(self, cargado_por):
        comprador = self.cleaned_data["comprador"] or self._cliente_nuevo()
        perfil = getattr(comprador, "restaurante", None) or getattr(comprador, "cliente", None)
        pedido = Pedido.objects.create(
            usuario=comprador,
            estado=Pedido.Estado.ENTREGADO,
            entregado_en=self.cleaned_data["fecha"],
            cargado_por=cargado_por,
            forma_pago=self.cleaned_data["forma_pago"],
            direccion=perfil.direccion if perfil else "",
            telefono=perfil.telefono if perfil else "",
            notas=self.cleaned_data["notas"],
        )
        self._crear_items(pedido)
        return pedido
