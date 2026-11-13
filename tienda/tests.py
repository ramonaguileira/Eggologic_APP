from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cuentas.models import Cliente, Restaurante, Usuario

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


def crear_usuario(rol):
    return Usuario.objects.create_user(username=rol, password="clave-de-prueba-123", rol=rol)


class RestauranteEnLaTiendaTests(TestCase):
    def test_el_restaurante_compra_con_sus_datos_sin_pasar_por_primera_entrega(self):
        usuario = crear_usuario(Usuario.Rol.RESTAURANTE)
        Restaurante.objects.create(nombre="El Popu", codigo="R-001", usuario=usuario, direccion="Calle 2", telefono="42 123")
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("tienda:tienda"))
        self.assertEqual(respuesta.context["form"]["direccion"].value(), "Calle 2")
        self.assertFalse(Cliente.objects.exists())

    def test_el_cliente_sin_direccion_la_carga_antes_del_primer_pedido(self):
        self.client.force_login(crear_usuario(Usuario.Rol.CLIENTE))
        self.assertRedirects(self.client.get(reverse("tienda:tienda")), reverse("primera_entrega"))


class PedidosDeAdministracionTests(TestCase):
    def setUp(self):
        cliente = crear_usuario(Usuario.Rol.CLIENTE)
        self.pedido = Pedido.objects.create(usuario=cliente, forma_pago="contra_entrega", direccion="d", telefono="t")
        self.entregar = reverse("tienda:pedido_entregado", args=[self.pedido.pk])

    def test_administracion_y_operador_marcan_un_pedido_como_entregado(self):
        for rol in (Usuario.Rol.ADMIN, Usuario.Rol.OPERADOR):
            Pedido.objects.update(estado=Pedido.Estado.RECIBIDO)
            self.client.force_login(crear_usuario(rol))
            self.assertEqual(self.client.get(reverse("tienda:pedidos_admin")).status_code, 200)
            self.assertRedirects(self.client.post(self.entregar), reverse("tienda:pedidos_admin"))
            self.pedido.refresh_from_db()
            self.assertEqual(self.pedido.estado, Pedido.Estado.ENTREGADO)

    def test_carbosur_y_los_clientes_no_tocan_los_pedidos(self):
        for rol in (Usuario.Rol.CARBOSUR, Usuario.Rol.RESTAURANTE):
            self.client.force_login(crear_usuario(rol))
            self.assertEqual(self.client.post(self.entregar).status_code, 403)
            self.assertEqual(self.client.get(reverse("tienda:pedidos_admin")).status_code, 403)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.RECIBIDO)

    def test_al_marcar_entregado_queda_la_fecha(self):
        self.client.force_login(crear_usuario(Usuario.Rol.ADMIN))
        self.client.post(self.entregar)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.entregado_en, timezone.localdate())


class RegistrarEntregaTests(TestCase):
    def setUp(self):
        self.operador = crear_usuario(Usuario.Rol.OPERADOR)
        self.maple = Producto.objects.create(nombre="Maple", huevos=30, precio=Decimal("650"))
        self.url = reverse("tienda:entrega_nueva")
        self.ayer = timezone.localdate() - timedelta(days=1)
        self.client.force_login(self.operador)

    def registrar(self, **datos):
        base = {"fecha": self.ayer.isoformat(), "forma_pago": "contra_entrega", f"cantidad_{self.maple.pk}": "2"}
        return self.client.post(self.url, {**base, **datos})

    def test_entrega_a_un_restaurante_queda_como_pedido_entregado(self):
        usuario = crear_usuario(Usuario.Rol.RESTAURANTE)
        Restaurante.objects.create(nombre="El Popu", codigo="R-001", usuario=usuario, direccion="Calle 2", telefono="42 123")
        self.assertContains(self.client.get(self.url), "El Popu (restaurante)")
        self.assertRedirects(self.registrar(comprador=usuario.pk), reverse("tienda:pedidos_admin"))
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.usuario, usuario)
        self.assertEqual(pedido.estado, Pedido.Estado.ENTREGADO)
        self.assertEqual(pedido.entregado_en, self.ayer)
        self.assertEqual(pedido.cargado_por, self.operador)
        self.assertEqual(pedido.huevos, 60)
        self.assertEqual(pedido.direccion, "Calle 2")

    def test_entrega_a_un_cliente_nuevo_le_crea_la_cuenta(self):
        self.registrar(nombre_nuevo="Ana", email_nuevo="ana@example.com")
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.usuario.first_name, "Ana")
        self.assertEqual(pedido.usuario.rol, Usuario.Rol.CLIENTE)
        self.assertTrue(Cliente.objects.filter(usuario=pedido.usuario).exists())
        # Con contraseña (que nadie conoce) para que pueda entrar con "Olvidé mi contraseña".
        self.assertTrue(pedido.usuario.has_usable_password())

    def test_hay_que_elegir_a_alguien_y_la_fecha_no_puede_ser_futura(self):
        self.assertContains(self.registrar(), "Elegí un cliente o restaurante")
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        self.assertContains(self.registrar(nombre_nuevo="Ana", fecha=manana), "fecha futura")
        self.assertFalse(Pedido.objects.exists())

    def test_carbosur_no_registra_entregas(self):
        self.client.force_login(crear_usuario(Usuario.Rol.CARBOSUR))
        self.assertEqual(self.client.get(self.url).status_code, 403)
