from django.contrib import admin

from .models import ItemPedido, Pedido, Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "huevos", "precio", "activo", "orden"]
    list_editable = ["precio", "activo", "orden"]


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ["producto", "cantidad", "precio_unitario", "huevos_por_unidad"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ["__str__", "creado_en", "usuario", "total", "forma_pago", "estado"]
    list_editable = ["estado"]
    list_filter = ["estado", "forma_pago"]
    search_fields = ["usuario__username", "usuario__first_name", "direccion", "telefono"]
    inlines = [ItemPedidoInline]
    readonly_fields = ["usuario", "creado_en"]
