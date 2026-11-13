from django.db import migrations
from django.utils import timezone


def completar_fecha(apps, schema_editor):
    """Los pedidos ya entregados no tenían fecha de entrega: se toma la del pedido."""
    Pedido = apps.get_model("tienda", "Pedido")
    for pedido in Pedido.objects.filter(estado="entregado", entregado_en=None):
        pedido.entregado_en = timezone.localtime(pedido.creado_en).date()
        pedido.save(update_fields=["entregado_en"])


class Migration(migrations.Migration):
    dependencies = [("tienda", "0002_entregas")]

    operations = [migrations.RunPython(completar_fecha, migrations.RunPython.noop)]
