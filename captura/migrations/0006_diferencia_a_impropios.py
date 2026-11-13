from django.db import migrations


def coma(valor):
    return f"{valor:.2f}".replace(".", ",")


def cargar_diferencias(apps, schema_editor):
    """Decisión de Ramón (13/11): en los retiros ya clasificados, lo que falta para llegar a lo
    levantado se suma a impropios como estimación. Lo que se había pesado queda en observaciones."""
    Retiro = apps.get_model("captura", "Retiro")
    clasificados = Retiro.objects.exclude(kg_impropios=None).exclude(kg_restos_vegetales=None).exclude(kg_residuos_plato=None)
    for retiro in clasificados:
        diferencia = retiro.kg_levantados - retiro.kg_impropios - retiro.kg_restos_vegetales - retiro.kg_residuos_plato
        if diferencia <= 0:
            continue
        nota = (
            f"Impropios pesados: {coma(retiro.kg_impropios)} kg. Se sumaron "
            f"{coma(diferencia)} kg de diferencia con lo levantado, como estimación."
        )
        retiro.kg_impropios += diferencia
        retiro.impropios_estimados = True
        retiro.observaciones = f"{retiro.observaciones}\n{nota}".strip()
        retiro.save(update_fields=["kg_impropios", "impropios_estimados", "observaciones"])


class Migration(migrations.Migration):
    dependencies = [("captura", "0005_bultos")]

    operations = [migrations.RunPython(cargar_diferencias, migrations.RunPython.noop)]
