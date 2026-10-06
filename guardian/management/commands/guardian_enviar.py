from django.core.management.base import BaseCommand

from guardian.cliente import ErrorGuardian
from guardian.models import ReporteMensual
from guardian.reportes import enviar


class Command(BaseCommand):
    help = "Manda a Guardian los reportes mensuales verificados que falten. Pensado para correr por cron."

    def handle(self, *args, **opciones):
        pendientes = ReporteMensual.objects.exclude(estado=ReporteMensual.Estado.REGISTRADO)
        for reporte in pendientes.select_related("restaurante"):
            try:
                enviar(reporte)
            except ErrorGuardian as error:
                # Queda donde estaba: la próxima vuelta retoma desde el paso que falló.
                reporte.intentos += 1
                reporte.ultimo_error = str(error)
                reporte.save(update_fields=["intentos", "ultimo_error"])
                self.stdout.write(self.style.WARNING(f"{reporte}: {error}"))
            else:
                if reporte.estado == ReporteMensual.Estado.REGISTRADO:
                    self.stdout.write(self.style.SUCCESS(f"{reporte}: registrado"))
                else:
                    self.stdout.write(f"{reporte}: {reporte.get_estado_display().lower()}; sigue en la próxima vuelta")
        if not pendientes.exists():
            self.stdout.write("No quedan reportes por enviar.")
