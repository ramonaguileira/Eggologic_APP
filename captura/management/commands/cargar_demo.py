import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from captura.models import Lote, RegistroGranja, Retiro
from cuentas.models import Restaurante, Usuario

RESTAURANTES = [("R-001", "La Huerta"), ("R-002", "Parrilla del Puerto"), ("R-003", "Café Botánico")]
DIAS = 21


def kg(valor):
    return Decimal(str(round(valor, 1)))


class Command(BaseCommand):
    help = "Carga usuarios, restaurantes y tres semanas de datos ficticios para probar la app."

    def add_arguments(self, parser):
        parser.add_argument("--password", required=True, help="Contraseña para los usuarios de prueba.")

    def handle(self, *args, **opciones):
        if not settings.DEBUG:
            raise CommandError("Solo se puede usar con DJANGO_DEBUG=True (datos ficticios).")
        if Retiro.objects.exists():
            raise CommandError("La base ya tiene retiros: no cargo datos de prueba encima.")

        admin = self.crear_usuario("admin", Usuario.Rol.ADMIN, opciones["password"], superusuario=True)
        operador = self.crear_usuario("operador", Usuario.Rol.OPERADOR, opciones["password"])
        self.crear_usuario("carbosur", Usuario.Rol.CARBOSUR, opciones["password"])
        restaurantes = [
            Restaurante.objects.get_or_create(codigo=codigo, defaults={"nombre": nombre})[0]
            for codigo, nombre in RESTAURANTES
        ]

        azar = random.Random(42)  # siempre los mismos datos
        hoy = timezone.localdate()
        retiros_por_semana = {}
        for dias_atras in range(DIAS, 0, -1):
            dia = hoy - timedelta(days=dias_atras)
            for restaurante in restaurantes:
                if dias_atras % 2:  # cada restaurante se retira día por medio
                    continue
                levantado = kg(azar.uniform(25, 60))
                impropios = kg(float(levantado) * azar.uniform(0.02, 0.09))
                vegetales = kg(float(levantado - impropios) * azar.uniform(0.5, 0.7))
                retiro = Retiro.objects.create(
                    restaurante=restaurante,
                    registrado_por=operador,
                    fecha=timezone.make_aware(datetime.combine(dia, time(11, 0))),
                    kg_levantados=levantado,
                    kg_impropios=impropios,
                    kg_restos_vegetales=vegetales,
                    kg_residuos_plato=levantado - impropios - vegetales,
                    kg_no_ingresa=kg(float(levantado) * azar.uniform(0.1, 0.3)),
                    no_ingresa_estimado=True,
                )
                retiros_por_semana.setdefault(dias_atras // 7, []).append(retiro)

        # Un lote por semana; los de las semanas anteriores ya están cosechados.
        for semana, retiros in sorted(retiros_por_semana.items(), reverse=True):
            inicio = retiros[0].fecha.date()
            lote = Lote.objects.create(
                registrado_por=operador,
                fecha_inicio=inicio,
                bandejas=len(retiros) * 2,
                g_neonatos=kg(len(retiros) * 2.5),
            )
            Retiro.objects.filter(pk__in=[r.pk for r in retiros]).update(lote=lote)
            if semana > 0:
                lote.fecha_cosecha = inicio + timedelta(days=14)
                lote.kg_larvas = kg(float(lote.kg_residuo) * azar.uniform(0.12, 0.18))
                lote.kg_frass = kg(float(lote.kg_residuo) * azar.uniform(0.3, 0.4))
                lote.save()

        primer_lote = Lote.objects.filter(fecha_cosecha__isnull=False).order_by("fecha_inicio").first()
        for dias_atras in range(DIAS, 0, -1):
            RegistroGranja.objects.create(
                registrado_por=operador,
                fecha=hoy - timedelta(days=dias_atras),
                huevos=azar.randint(160, 200),
                kg_larvas=kg(azar.uniform(2, 4)),
                lote=primer_lote,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Listo: usuarios {admin.username}, operador y carbosur; {Retiro.objects.count()} retiros, "
            f"{Lote.objects.count()} lotes y {RegistroGranja.objects.count()} días de granja."
        ))

    def crear_usuario(self, nombre, rol, password, superusuario=False):
        usuario, creado = Usuario.objects.get_or_create(
            username=nombre, defaults={"rol": rol, "is_staff": superusuario, "is_superuser": superusuario}
        )
        if creado:
            usuario.set_password(password)
            usuario.save()
        return usuario
