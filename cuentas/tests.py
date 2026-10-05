from django.test import TestCase
from django.urls import reverse

from .models import Usuario


def crear_usuario(rol, **extra):
    return Usuario.objects.create_user(username=rol, password="clave-de-prueba-123", rol=rol, **extra)


class RolesTests(TestCase):
    def test_operador_captura_y_ve_datos(self):
        operador = crear_usuario(Usuario.Rol.OPERADOR)
        self.assertTrue(operador.puede_capturar())
        self.assertTrue(operador.puede_ver_datos())

    def test_carbosur_solo_ve_datos(self):
        carbosur = crear_usuario(Usuario.Rol.CARBOSUR)
        self.assertFalse(carbosur.puede_capturar())
        self.assertTrue(carbosur.puede_ver_datos())

    def test_cliente_no_ve_datos_de_campo(self):
        cliente = crear_usuario(Usuario.Rol.CLIENTE)
        self.assertFalse(cliente.puede_capturar())
        self.assertFalse(cliente.puede_ver_datos())

    def test_superusuario_es_admin_aunque_no_tenga_rol_admin(self):
        jefe = Usuario.objects.create_superuser(username="jefe", password="clave-de-prueba-123")
        self.assertTrue(jefe.es_admin())
        self.assertTrue(jefe.puede_capturar())


class InicioTests(TestCase):
    def test_sin_login_va_a_ingresar(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertRedirects(respuesta, reverse("login") + "?next=/")

    def test_operador_va_al_panel(self):
        self.client.force_login(crear_usuario(Usuario.Rol.OPERADOR))
        respuesta = self.client.get(reverse("inicio"))
        self.assertRedirects(respuesta, reverse("captura:panel"))

    def test_cliente_ve_su_inicio(self):
        self.client.force_login(crear_usuario(Usuario.Rol.CLIENTE))
        respuesta = self.client.get(reverse("inicio"))
        self.assertTemplateUsed(respuesta, "cuentas/inicio_usuario.html")


class PermisosTests(TestCase):
    def test_cliente_no_entra_al_panel(self):
        self.client.force_login(crear_usuario(Usuario.Rol.CLIENTE))
        self.assertEqual(self.client.get(reverse("captura:panel")).status_code, 403)

    def test_carbosur_no_puede_cargar_retiros(self):
        self.client.force_login(crear_usuario(Usuario.Rol.CARBOSUR))
        self.assertEqual(self.client.get(reverse("captura:retiro_nuevo")).status_code, 403)
