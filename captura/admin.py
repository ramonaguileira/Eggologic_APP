from django.contrib import admin

from .models import Lote, RegistroGranja, Retiro


class RegistroAdmin(admin.ModelAdmin):
    """Completa quién registró el dato cuando se carga desde el admin."""

    readonly_fields = ["registrado_por", "creado_en", "actualizado_en"]

    def save_model(self, request, obj, form, change):
        if not obj.registrado_por_id:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Retiro)
class RetiroAdmin(RegistroAdmin):
    list_display = ["id", "fecha", "restaurante", "kg_levantados", "kg_impropios", "lote"]
    list_filter = ["restaurante"]
    date_hierarchy = "fecha"
    readonly_fields = RegistroAdmin.readonly_fields + ["lote"]


@admin.register(Lote)
class LoteAdmin(RegistroAdmin):
    list_display = ["id", "fecha_inicio", "bandejas", "fecha_cosecha", "kg_larvas", "kg_frass"]
    date_hierarchy = "fecha_inicio"


@admin.register(RegistroGranja)
class RegistroGranjaAdmin(RegistroAdmin):
    list_display = ["fecha", "huevos", "kg_larvas", "lote"]
    date_hierarchy = "fecha"
