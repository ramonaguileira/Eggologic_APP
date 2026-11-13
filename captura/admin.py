from django.contrib import admin

from .models import Bulto, Lote, RegistroGranja, Retiro


class RegistroAdmin(admin.ModelAdmin):
    """Completa quién registró el dato cuando se carga desde el admin."""

    readonly_fields = ["registrado_por", "creado_en", "actualizado_en"]

    def save_model(self, request, obj, form, change):
        if not obj.registrado_por_id:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)


class BultoInline(admin.TabularInline):
    model = Bulto
    extra = 0
    readonly_fields = ["kg", "foto", "creado_en"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Retiro)
class RetiroAdmin(RegistroAdmin):
    inlines = [BultoInline]
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
