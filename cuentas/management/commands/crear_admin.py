import os

from django.core.management.base import BaseCommand

from cuentas.models import Usuario


class Command(BaseCommand):
    help = (
        "Crea el primer usuario de administración con DJANGO_SUPERUSER_USERNAME, _EMAIL y _PASSWORD, "
        "si todavía no existe. Lo corre build.sh en Render, donde el plan gratis no tiene consola."
    )

    def handle(self, *args, **opciones):
        usuario = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not usuario or not password:
            self.stdout.write("Sin DJANGO_SUPERUSER_USERNAME o DJANGO_SUPERUSER_PASSWORD: no se crea ningún usuario.")
            return
        if Usuario.objects.filter(username=usuario).exists():
            self.stdout.write(f"El usuario {usuario} ya existe.")
            return
        Usuario.objects.create_superuser(
            username=usuario, email=os.environ.get("DJANGO_SUPERUSER_EMAIL", ""), password=password,
            rol=Usuario.Rol.ADMIN,
        )
        self.stdout.write(f"Usuario de administración {usuario} creado.")
