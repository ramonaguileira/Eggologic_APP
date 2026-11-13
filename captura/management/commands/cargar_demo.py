import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from captura.models import Granja, Lote, RegistroGranja, Retiro
from cuentas.models import Cliente, Restaurante, Usuario
from tienda.models import ItemPedido, Pedido, Producto

RESTAURANTES = [("R-001", "La Huerta"), ("R-002", "Parrilla del Puerto"), ("R-003", "Café Botánico")]
# Productos y precios reales (Ramón, 06/10). Se cambian desde la administración.
PRODUCTOS = [
    ("Quincena", "15 huevos de gallinas regenerativas.", 15, "160"),
    ("Maple", "30 huevos, ideal para familias y cocinas.", 30, "310"),
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
        for rol in (Usuario.Rol.CHOFER, Usuario.Rol.PLANTA, Usuario.Rol.GRANJA):
            self.crear_usuario(rol, rol, password)
        self.crear_usuario("carbosur", Usuario.Rol.CARBOSUR, password)
        restaurantes = [
            Restaurante.objects.get_or_create(codigo=codigo, defaults={"nombre": nombre})[0]
            for codigo, nombre in RESTAURANTES
        ]

        self.cargar_captura(operador, restaurantes)
        self.cargar_tienda(password, restaurantes[0])

        self.stdout.write(self.style.SUCCESS(
            f"Listo: usuarios admin, operador, chofer, planta, granja, carbosur, cliente y restaurante; "
            f"{Retiro.objects.count()} retiros, {Lote.objects.count()} cargas de larvas, "
            f"{RegistroGranja.objects.count()} semanas de granja y {Pedido.objects.count()} pedidos."
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

        # Una carga de larvas y una de huevos por semana, como las anota Ramón.
        camino_verde, _ = Granja.objects.get_or_create(nombre="Camino Verde")
        for semana, retiros in sorted(retiros_por_semana.items(), reverse=True):
            fin = self.hoy - timedelta(days=semana * 7 + 1)
            Lote.objects.create(
                registrado_por=operador,
                fecha_inicio=fin,
                bandejas=len(retiros) * 2,
                g_neonatos=kg(len(retiros) * 2.5),
            )
            RegistroGranja.objects.create(
                registrado_por=operador,
                granja=camino_verde,
                desde=fin - timedelta(days=6),
                fecha=fin,
                huevos=self.azar.randint(1100, 1400),
            )

    def cargar_tienda(self, password, restaurante):
        productos = [
            Producto.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": descripcion, "huevos": huevos, "precio": Decimal(precio), "orden": orden},
            )[0]
            for orden, (nombre, descripcion, huevos, precio) in enumerate(PRODUCTOS)
        ]
        quincena, maple = productos

        cliente = self.crear_usuario("cliente", Usuario.Rol.CLIENTE, password, nombre="Lucía")
        Cliente.objects.get_or_create(
            usuario=cliente,
            defaults={"telefono": "099 000 000", "direccion": "Calle Ficticia 123, Maldonado"},
        )
        # Un pedido cada diez días; el último todavía no se entregó.
        for dias_atras in range(DIAS - 5, 0, -10):
            producto = quincena if dias_atras % 20 else maple
            estado = Pedido.Estado.ENTREGADO if dias_atras > 10 else Pedido.Estado.RECIBIDO
            self.crear_pedido(cliente, [(producto, 1 + dias_atras % 3)], dias_atras, estado)

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
        entregado_en = fecha.date() if estado == Pedido.Estado.ENTREGADO else None
        Pedido.objects.filter(pk=pedido.pk).update(creado_en=fecha, entregado_en=entregado_en)

    def crear_usuario(self, nombre_usuario, rol, password, superusuario=False, nombre=""):
        usuario, creado = Usuario.objects.get_or_create(
            username=nombre_usuario,
            defaults={"rol": rol, "first_name": nombre, "is_staff": superusuario, "is_superuser": superusuario},
        )
        if creado:
            usuario.set_password(password)
            usuario.save()
        return usuario
