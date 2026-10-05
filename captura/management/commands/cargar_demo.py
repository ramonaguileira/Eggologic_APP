import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from captura.models import Lote, RegistroGranja, Retiro
from cuentas.models import Cliente, Restaurante, Usuario
from tienda.models import ItemPedido, Pedido, Producto

RESTAURANTES = [("R-001", "La Huerta"), ("R-002", "Parrilla del Puerto"), ("R-003", "Café Botánico")]
# SUPUESTO: productos y precios de ejemplo, se cambian desde la administración.
PRODUCTOS = [
    ("Media docena", "6 huevos de gallinas regenerativas.", 6, "150"),
    ("Docena", "12 huevos de gallinas regenerativas.", 12, "280"),
    ("Maple", "30 huevos, ideal para familias y cocinas.", 30, "650"),
]
DIAS = 120


def kg(valor):
    return Decimal(str(round(valor, 1)))


class Command(BaseCommand):
    help = "Carga usuarios, restaurantes, productos y cuatro meses de datos ficticios para probar la app."

    def add_arguments(self, parser):
        parser.add_argument("--password", required=True, help="Contraseña para los usuarios de prueba.")

    def handle(self, *args, **opciones):
        if not settings.DEBUG:
            raise CommandError("Solo se puede usar con DJANGO_DEBUG=True (datos ficticios).")
        if Retiro.objects.exists():
            raise CommandError("La base ya tiene retiros: no cargo datos de prueba encima.")

        password = opciones["password"]
        self.azar = random.Random(42)  # siempre los mismos datos
        self.hoy = timezone.localdate()

        self.crear_usuario("admin", Usuario.Rol.ADMIN, password, superusuario=True)
        operador = self.crear_usuario("operador", Usuario.Rol.OPERADOR, password)
        self.crear_usuario("carbosur", Usuario.Rol.CARBOSUR, password)
        restaurantes = [
            Restaurante.objects.get_or_create(codigo=codigo, defaults={"nombre": nombre})[0]
            for codigo, nombre in RESTAURANTES
        ]

        self.cargar_captura(operador, restaurantes)
        self.cargar_tienda(password, restaurantes[0])

        self.stdout.write(self.style.SUCCESS(
            f"Listo: usuarios admin, operador, carbosur, cliente y restaurante; "
            f"{Retiro.objects.count()} retiros, {Lote.objects.count()} lotes, "
            f"{RegistroGranja.objects.count()} días de granja y {Pedido.objects.count()} pedidos."
        ))

    def cargar_captura(self, operador, restaurantes):
        retiros_por_semana = {}
        for dias_atras in range(DIAS, 0, -1):
            dia = self.hoy - timedelta(days=dias_atras)
            for restaurante in restaurantes:
                if dias_atras % 2:  # cada restaurante se retira día por medio
                    continue
                levantado = kg(self.azar.uniform(25, 60))
                impropios = kg(float(levantado) * self.azar.uniform(0.02, 0.09))
                vegetales = kg(float(levantado - impropios) * self.azar.uniform(0.5, 0.7))
                retiro = Retiro.objects.create(
                    restaurante=restaurante,
                    registrado_por=operador,
                    fecha=timezone.make_aware(datetime.combine(dia, time(11, 0))),
                    kg_levantados=levantado,
                    kg_impropios=impropios,
                    kg_restos_vegetales=vegetales,
                    kg_residuos_plato=levantado - impropios - vegetales,
                    kg_no_ingresa=kg(float(levantado) * self.azar.uniform(0.1, 0.3)),
                    no_ingresa_estimado=True,
                )
                retiros_por_semana.setdefault(dias_atras // 7, []).append(retiro)

        # Un lote por semana; los de hace más de dos semanas ya están cosechados.
        for semana, retiros in sorted(retiros_por_semana.items(), reverse=True):
            inicio = timezone.localtime(retiros[0].fecha).date()
            lote = Lote.objects.create(
                registrado_por=operador,
                fecha_inicio=inicio,
                bandejas=len(retiros) * 2,
                g_neonatos=kg(len(retiros) * 2.5),
            )
            Retiro.objects.filter(pk__in=[r.pk for r in retiros]).update(lote=lote)
            if semana > 1:
                lote.fecha_cosecha = inicio + timedelta(days=14)
                lote.kg_larvas = kg(float(lote.kg_residuo) * self.azar.uniform(0.12, 0.18))
                lote.kg_frass = kg(float(lote.kg_residuo) * self.azar.uniform(0.3, 0.4))
                lote.save()

        for dias_atras in range(DIAS, 0, -1):
            dia = self.hoy - timedelta(days=dias_atras)
            lote = Lote.objects.filter(fecha_cosecha__lte=dia).order_by("-fecha_cosecha").first()
            RegistroGranja.objects.create(
                registrado_por=operador,
                fecha=dia,
                huevos=self.azar.randint(160, 200),
                kg_larvas=kg(self.azar.uniform(2, 4)),
                lote=lote,
            )

    def cargar_tienda(self, password, restaurante):
        productos = [
            Producto.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": descripcion, "huevos": huevos, "precio": Decimal(precio), "orden": orden},
            )[0]
            for orden, (nombre, descripcion, huevos, precio) in enumerate(PRODUCTOS)
        ]
        media_docena, docena, maple = productos

        cliente = self.crear_usuario("cliente", Usuario.Rol.CLIENTE, password, nombre="Lucía")
        Cliente.objects.get_or_create(
            usuario=cliente,
            defaults={"telefono": "099 000 000", "direccion": "Calle Ficticia 123, Maldonado"},
        )
        # Un pedido cada diez días; el último todavía no se entregó.
        for dias_atras in range(DIAS - 5, 0, -10):
            producto = docena if dias_atras % 20 else maple
            estado = Pedido.Estado.ENTREGADO if dias_atras > 10 else Pedido.Estado.RECIBIDO
            self.crear_pedido(cliente, [(producto, 1), (media_docena, dias_atras % 3)], dias_atras, estado)

        usuario_restaurante = self.crear_usuario(
            "restaurante", Usuario.Rol.RESTAURANTE, password, nombre=restaurante.nombre
        )
        restaurante.usuario = usuario_restaurante
        restaurante.direccion = "Rambla Ficticia 456, Punta del Este"
        restaurante.telefono = "4222 0000"
        restaurante.save()
        for dias_atras in range(DIAS - 10, 0, -30):
            self.crear_pedido(usuario_restaurante, [(maple, 2)], dias_atras, Pedido.Estado.ENTREGADO)

    def crear_pedido(self, usuario, productos_y_cantidades, dias_atras, estado):
        pedido = Pedido.objects.create(
            usuario=usuario,
            estado=estado,
            forma_pago=Pedido.FormaPago.TRANSFERENCIA if dias_atras % 2 else Pedido.FormaPago.CONTRA_ENTREGA,
            direccion="Dirección de prueba",
            telefono="099 000 000",
        )
        for producto, cantidad in productos_y_cantidades:
            if cantidad:
                ItemPedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                    huevos_por_unidad=producto.huevos,
                )
        # creado_en se completa solo al crear; para los datos de ejemplo se lleva al pasado.
        fecha = timezone.make_aware(datetime.combine(self.hoy - timedelta(days=dias_atras), time(10, 0)))
        Pedido.objects.filter(pk=pedido.pk).update(creado_en=fecha)

    def crear_usuario(self, nombre_usuario, rol, password, superusuario=False, nombre=""):
        usuario, creado = Usuario.objects.get_or_create(
            username=nombre_usuario,
            defaults={"rol": rol, "first_name": nombre, "is_staff": superusuario, "is_superuser": superusuario},
        )
        if creado:
            usuario.set_password(password)
            usuario.save()
        return usuario
