from django.contrib import admin

from .models import Movimiento, Recarga


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ["creado_en", "usuario", "cantidad", "motivo", "detalle"]
    list_filter = ["motivo"]
    search_fields = ["usuario__username", "usuario__email", "detalle"]

    # Los movimientos no se editan ni se borran: se corrige con un ajuste nuevo.
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Recarga)
class RecargaAdmin(admin.ModelAdmin):
    list_display = ["creado_en", "usuario", "monto", "medio", "estado"]
    list_filter = ["estado", "medio"]
    readonly_fields = ["estado", "acreditada_en"]
