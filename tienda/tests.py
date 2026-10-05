from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from cuentas.models import Cliente, Usuario

from .models import Pedido, Producto


class TiendaTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            username="lucia", password="clave-de-prueba-123", rol=Usuario.Rol.CLIENTE
        )
        Cliente.objects.create(usuario=self.cliente, telefono="099 123 456", direccion="Calle 1")
        self.docena = Producto.objects.create(nombre="Docena", huevos=12, precio=Decimal("280"))
        self.maple = Producto.objects.create(nombre="Maple", huevos=30, precio=Decimal("650"))
        self.client.force_login(self.cliente)

    def pedir(self, **cantidades):
        datos = {"direccion": "Calle 1", "telefono": "099 123 456", "forma_pago": "transferencia"}
        datos.update(cantidades)
        return self.client.post(reverse("tienda:tienda"), datos)

    def test_la_tienda_propone_la_direccion_del_cliente(self):
        respuesta = self.client.get(reverse("tienda:tienda"))
        self.assertEqual(respuesta.context["form"]["direccion"].value(), "Calle 1")

    def test_hacer_un_pedido(self):
        respuesta = self.pedir(**{f"cantidad_{self.docena.pk}": "2", f"cantidad_{self.maple.pk}": "1"})
        self.assertRedirects(respuesta, reverse("tienda:mis_pedidos"))
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.usuario, self.cliente)
        self.assertEqual(pedido.estado, Pedido.Estado.RECIBIDO)
        self.assertEqual(pedido.total, Decimal("1210"))
        self.assertEqual(pedido.huevos, 54)

    def test_un_pedido_vacio_no_se_guarda(self):
        respuesta = self.pedir()
        self.assertContains(respuesta, "Elegí al menos un producto.")
        self.assertFalse(Pedido.objects.exists())

    def test_un_cambio_de_precio_no_altera_pedidos_viejos(self):
        self.pedir(**{f"cantidad_{self.docena.pk}": "1"})
        self.docena.precio = Decimal("999")
        self.docena.save()
        self.assertEqual(Pedido.objects.get().total, Decimal("280"))

    def test_cada_uno_ve_solo_sus_pedidos(self):
        self.pedir(**{f"cantidad_{self.docena.pk}": "1"})
        otro = Usuario.objects.create_user(username="otro", password="clave-de-prueba-123", rol=Usuario.Rol.CLIENTE)
        self.client.force_login(otro)
        respuesta = self.client.get(reverse("tienda:mis_pedidos"))
        self.assertEqual(list(respuesta.context["pedidos"]), [])

    def test_el_operador_no_compra(self):
        operador = Usuario.objects.create_user(
            username="operador", password="clave-de-prueba-123", rol=Usuario.Rol.OPERADOR
        )
        self.client.force_login(operador)
        self.assertEqual(self.client.get(reverse("tienda:tienda")).status_code, 403)
