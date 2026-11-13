from django.db import migrations


def crear_granjas(apps, schema_editor):
    """Las dos granjas de Ramón (13/11). Los registros anteriores eran todos de Camino Verde y de
    un solo día."""
    Granja = apps.get_model("captura", "Granja")
    RegistroGranja = apps.get_model("captura", "RegistroGranja")
    camino_verde, _ = Granja.objects.get_or_create(nombre="Camino Verde")
    Granja.objects.get_or_create(nombre="Eguzquiza")
    for registro in RegistroGranja.objects.filter(granja=None):
        registro.granja = camino_verde
        registro.desde = registro.fecha
        registro.save(update_fields=["granja", "desde"])


class Migration(migrations.Migration):
    dependencies = [("captura", "0007_granjas_y_periodos")]

    operations = [migrations.RunPython(crear_granjas, migrations.RunPython.noop)]
