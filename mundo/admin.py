from django.contrib import admin

from .models import Ajustes, Gallina, Levante


@admin.register(Ajustes)
class AjustesAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not Ajustes.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Gallina)
class GallinaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "usuario", "plan", "estado", "inicio", "pago_hasta"]
    list_filter = ["plan", "estado"]
    search_fields = ["nombre", "usuario__username", "usuario__email"]


@admin.register(Levante)
class LevanteAdmin(admin.ModelAdmin):
    list_display = ["pedido_en", "usuario", "estado", "kg", "direccion"]
    list_filter = ["estado"]
