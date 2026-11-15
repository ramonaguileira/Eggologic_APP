from decimal import Decimal

from django.db import migrations


def crear_productos(apps, schema_editor):
    """Sin productos, la tienda de la chacra no tiene nada para ofrecer.

    Solo los crea si no hay ninguno activo: donde ya están cargados (la app en uso) no toca nada.
    Los precios son los que dio Ramón el 15/11; después se cambian en Administración → Productos.
    """
    Producto = apps.get_model("tienda", "Producto")
    if Producto.objects.filter(activo=True).exists():
        return
    Producto.objects.create(
        nombre="Quincena", descripcion="15 huevos de gallinas regenerativas.", huevos=15, precio=Decimal("160"), orden=1
    )
    Producto.objects.create(
        nombre="Maple", descripcion="30 huevos, ideal para familias y cocinas.", huevos=30, precio=Decimal("310"), orden=2
    )


class Migration(migrations.Migration):
    dependencies = [("mundo", "0002_regalos"), ("tienda", "0003_pedido_de_eggo_world")]

    operations = [migrations.RunPython(crear_productos, migrations.RunPython.noop)]
