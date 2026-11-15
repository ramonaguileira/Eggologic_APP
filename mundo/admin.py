from django.contrib import admin

from .models import Ajustes, Gallina, HuevosRegalados, Levante


@admin.register(Ajustes)
class AjustesAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not Ajustes.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Gallina)
class GallinaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "usuario", "plan", "estado", "inicio", "pago_hasta", "regalada"]
    list_filter = ["plan", "estado", "regalada"]
    search_fields = ["nombre", "usuario__username", "usuario__email"]


@admin.register(Levante)
class LevanteAdmin(admin.ModelAdmin):
    list_display = ["pedido_en", "usuario", "estado", "kg", "direccion"]
    list_filter = ["estado"]


@admin.register(HuevosRegalados)
class HuevosRegaladosAdmin(admin.ModelAdmin):
    list_display = ["creado_en", "usuario", "cantidad", "nota", "regalados_por"]
