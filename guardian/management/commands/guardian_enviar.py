from django.core.management.base import BaseCommand

from guardian.models import ReporteMensual
from guardian.reportes import enviar_pendientes


class Command(BaseCommand):
    help = "Manda a Guardian los reportes mensuales revisados que falten. Pensado para correr por cron."

    def handle(self, *args, **opciones):
        resultados = enviar_pendientes()
        for reporte, error in resultados:
            if error:
                self.stdout.write(self.style.WARNING(f"{reporte}: {error}"))
            elif reporte.estado == ReporteMensual.Estado.REGISTRADO:
                self.stdout.write(self.style.SUCCESS(f"{reporte}: registrado"))
            else:
                self.stdout.write(f"{reporte}: {reporte.get_estado_display().lower()}; sigue en la próxima vuelta")
        if not resultados:
            self.stdout.write("No quedan reportes por enviar.")
