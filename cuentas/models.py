from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMIN = "admin", "Administración"
        # Cada persona de campo ve solo lo suyo (pedido de Ramón, 06/10).
        CHOFER = "chofer", "Chofer (solo carga retiros)"
        PLANTA = "planta", "Planta (clasifica retiros y lleva los lotes)"
        GRANJA = "granja", "Granja (registro diario)"
        OPERADOR = "operador", "Operador de campo (todas las tareas de campo)"
        RESTAURANTE = "restaurante", "Restaurante"
        CLIENTE = "cliente", "Cliente"
        CARBOSUR = "carbosur", "CarboSur (solo lectura)"

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.CLIENTE)

    def es_admin(self):
        return self.is_superuser or self.rol == self.Rol.ADMIN

    def puede_retirar(self):
        return self.es_admin() or self.rol in (self.Rol.CHOFER, self.Rol.OPERADOR)

    def puede_clasificar(self):
        """Clasificar retiros y llevar los lotes BSF: el trabajo de la planta."""
        return self.es_admin() or self.rol in (self.Rol.PLANTA, self.Rol.OPERADOR)

    def puede_cargar_granja(self):
        return self.es_admin() or self.rol in (self.Rol.GRANJA, self.Rol.OPERADOR)

    def puede_ver_datos(self):
        """Panel, informe, exportaciones y todos los registros de campo."""
        return self.es_admin() or self.rol in (self.Rol.OPERADOR, self.Rol.CARBOSUR)

    def puede_ver_retiros_y_lotes(self):
        return self.puede_ver_datos() or self.puede_clasificar()

    def puede_ver_granja(self):
        return self.puede_ver_datos() or self.puede_cargar_granja()

    def puede_comprar(self):
        return self.rol in (self.Rol.CLIENTE, self.Rol.RESTAURANTE)


class Restaurante(models.Model):
    nombre = models.CharField("nombre comercial", max_length=120)
    codigo = models.CharField(
        "código público",
        max_length=20,
        unique=True,
        help_text="Identificador que se usa fuera de la app en lugar del nombre. Ej.: R-001.",
    )
    # Datos privados: quedan solo en la base de la app.
    razon_social = models.CharField(max_length=200, blank=True)
    contacto = models.CharField("persona de contacto", max_length=120, blank=True)
    telefono = models.CharField("teléfono", max_length=40, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.CharField("dirección", max_length=200, blank=True)

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="restaurante",
        help_text="Login del restaurante en la app (opcional por ahora).",
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Cliente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="cliente")
    telefono = models.CharField("teléfono", max_length=40)
    direccion = models.CharField("dirección de entrega", max_length=200)

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username
