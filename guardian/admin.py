from django.contrib import admin

from .models import ReporteMensual


@admin.register(ReporteMensual)
class ReporteMensualAdmin(admin.ModelAdmin):
    list_display = ["restaurante", "mes", "kg_organicos", "tco2e_neto", "estado", "revisado_por", "intentos"]
    list_filter = ["estado", "restaurante"]
    readonly_fields = ["revisado_en", "registrado_en"]
