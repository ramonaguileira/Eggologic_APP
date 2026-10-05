from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Restaurante, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ["username", "first_name", "last_name", "email", "rol", "is_active"]
    list_filter = ["rol", "is_active"]
    fieldsets = UserAdmin.fieldsets + (("Rol en Eggologic", {"fields": ["rol"]}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Rol en Eggologic", {"fields": ["rol"]}),)


@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "codigo", "contacto", "telefono", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre", "codigo", "razon_social"]
