import os
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Usuario


def crear_usuario(rol, **extra):
    return Usuario.objects.create_user(username=rol, password="clave-de-prueba-123", rol=rol, **extra)


class RolesTests(TestCase):
    def permisos(self, usuario):
        return {
            "retirar": usuario.puede_retirar(),
            "clasificar": usuario.puede_clasificar(),
            "granja": usuario.puede_cargar_granja(),
            "ver_datos": usuario.puede_ver_datos(),
        }

    def test_cada_persona_de_campo_hace_solo_lo_suyo(self):
        todo_no = {"retirar": False, "clasificar": False, "granja": False, "ver_datos": False}
        self.assertEqual(self.permisos(crear_usuario(Usuario.Rol.CHOFER)), {**todo_no, "retirar": True})
        self.assertEqual(self.permisos(crear_usuario(Usuario.Rol.PLANTA)), {**todo_no, "clasificar": True})
        self.assertEqual(self.permisos(crear_usuario(Usuario.Rol.GRANJA)), {**todo_no, "granja": True})

    def test_operador_hace_todo_el_campo(self):
        operador = crear_usuario(Usuario.Rol.OPERADOR)
        self.assertEqual(self.permisos(operador), {"retirar": True, "clasificar": True, "granja": True, "ver_datos": True})

    def test_carbosur_solo_ve_datos(self):
        carbosur = crear_usuario(Usuario.Rol.CARBOSUR)
        self.assertEqual(self.permisos(carbosur), {"retirar": False, "clasificar": False, "granja": False, "ver_datos": True})

    def test_cliente_no_ve_datos_de_campo(self):
        cliente = crear_usuario(Usuario.Rol.CLIENTE)
        self.assertFalse(any(self.permisos(cliente).values()))

    def test_superusuario_es_admin_aunque_no_tenga_rol_admin(self):
        jefe = Usuario.objects.create_superuser(username="jefe", password="clave-de-prueba-123")
        self.assertTrue(jefe.es_admin())
        self.assertTrue(all(self.permisos(jefe).values()))


class InicioTests(TestCase):
    def test_sin_login_va_a_ingresar(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertRedirects(respuesta, reverse("login") + "?next=/")

    def test_operador_va_al_panel(self):
        self.client.force_login(crear_usuario(Usuario.Rol.OPERADOR))
        respuesta = self.client.get(reverse("inicio"))
        self.assertRedirects(respuesta, reverse("captura:panel"))

    def test_cada_persona_de_campo_va_a_su_pantalla(self):
        destinos = {
            Usuario.Rol.CHOFER: "captura:retiro_nuevo",
            Usuario.Rol.PLANTA: "captura:retiros",
            Usuario.Rol.GRANJA: "captura:granja",
        }
        for rol, destino in destinos.items():
            self.client.force_login(crear_usuario(rol))
            self.assertRedirects(self.client.get(reverse("inicio")), reverse(destino), fetch_redirect_response=False)

    def test_cliente_va_a_su_impacto(self):
        self.client.force_login(crear_usuario(Usuario.Rol.CLIENTE))
        respuesta = self.client.get(reverse("inicio"))
        self.assertRedirects(respuesta, reverse("impacto:mi_impacto"))


class RegistroTests(TestCase):
    def test_un_cliente_se_registra_y_queda_logueado(self):
        respuesta = self.client.post(
            reverse("registrarse"),
            {
                "username": "lucia",
                "first_name": "Lucía",
                "email": "lucia@example.com",
                "telefono": "099 123 456",
                "direccion": "Calle 1, Maldonado",
                "password1": "una-clave-bastante-larga",
                "password2": "una-clave-bastante-larga",
            },
        )
        self.assertRedirects(respuesta, reverse("tienda:tienda"))
        usuario = Usuario.objects.get(username="lucia")
        self.assertEqual(usuario.rol, Usuario.Rol.CLIENTE)
        self.assertEqual(usuario.cliente.direccion, "Calle 1, Maldonado")
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)


class PermisosTests(TestCase):
    def test_cliente_no_entra_al_panel(self):
        self.client.force_login(crear_usuario(Usuario.Rol.CLIENTE))
        self.assertEqual(self.client.get(reverse("captura:panel")).status_code, 403)

    def test_carbosur_no_puede_cargar_retiros(self):
        self.client.force_login(crear_usuario(Usuario.Rol.CARBOSUR))
        self.assertEqual(self.client.get(reverse("captura:retiro_nuevo")).status_code, 403)


class CrearAdminTests(TestCase):
    def test_crea_el_admin_una_sola_vez_y_solo_con_las_variables(self):
        call_command("crear_admin", stdout=StringIO())
        self.assertFalse(Usuario.objects.exists())
        variables = {"DJANGO_SUPERUSER_USERNAME": "ramon", "DJANGO_SUPERUSER_PASSWORD": "clave-larga-de-prueba-123"}
        with patch.dict(os.environ, variables):
            call_command("crear_admin", stdout=StringIO())
            call_command("crear_admin", stdout=StringIO())
        admin = Usuario.objects.get()
        self.assertTrue(admin.is_superuser and admin.es_admin())
        self.assertTrue(admin.check_password("clave-larga-de-prueba-123"))
