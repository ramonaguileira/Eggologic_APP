# "Revisado" en lugar de "verificado" para la revisión interna de Eggologic (Fase 0 del plan de datos).
# Se renombran los campos: los datos se conservan.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("guardian", "0002_ubicacion_en_hcs"),
    ]

    operations = [
        migrations.RenameField(model_name="reportemensual", old_name="verificado_por", new_name="revisado_por"),
        migrations.RenameField(model_name="reportemensual", old_name="verificado_en", new_name="revisado_en"),
        migrations.AlterField(
            model_name="reportemensual",
            name="estado",
            field=models.CharField(
                choices=[
                    ("en_cola", "Revisado, por enviar"),
                    ("enviado", "Enviado, falta la aprobación"),
                    ("registrado", "Registrado"),
                ],
                default="en_cola",
                max_length=20,
            ),
        ),
    ]
