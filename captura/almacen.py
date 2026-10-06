"""Guarda los archivos subidos (las fotos de los retiros) en la base de datos.

SUPUESTO (decisión de Ramón, 06/10): en Render gratis la web no tiene disco y los archivos se
borran cada vez que se duerme, así que las fotos van a la base. Si se pasa a un plan con disco,
alcanza con volver a FileSystemStorage en STORAGES["default"] (eggologic/settings.py).
"""

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from .models import Archivo


@deconstructible
class AlmacenEnLaBase(Storage):
    def _save(self, name, content):
        Archivo.objects.create(nombre=name, contenido=b"".join(content.chunks()))
        return name

    def _open(self, name, mode="rb"):
        archivo = Archivo.objects.filter(nombre=name).first()
        if archivo is None:
            raise FileNotFoundError(name)
        return ContentFile(bytes(archivo.contenido), name=name)

    def exists(self, name):
        return Archivo.objects.filter(nombre=name).exists()

    def delete(self, name):
        Archivo.objects.filter(nombre=name).delete()

    def size(self, name):
        return self._open(name).size

    def url(self, name):
        # Las fotos no tienen URL pública: se ven por captura.views.retiro_foto, con login.
        raise NotImplementedError("Las fotos se sirven por la vista retiro_foto.")
