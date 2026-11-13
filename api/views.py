"""La puerta de entrada de Eggo World: todo lo que la app del cliente le pide al servidor.

Estas vistas solo traducen entre JSON y los servicios. Las reglas están en eggos/reglas.py y
las cuentas en eggos/servicio.py, mundo/servicio.py e impacto/calculos.py.
"""

import json
from functools import wraps

from django.conf import settings
from django.contrib.auth import login, logout
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from cuentas.models import Cliente, Usuario
from eggos import pagos, reglas, servicio as eggos
from eggos.models import Movimiento, Recarga
from impacto import calculos
from mundo import servicio as mundo
from mundo.models import Ajustes, Gallina, Levante
from tienda.models import Pedido, Producto

from . import google


def activo(vista):
    """Con EGGO_WORLD_ACTIVO apagado, nada de esto existe y la app actual sigue igual."""

    @wraps(vista)
    def envuelta(request, *args, **kwargs):
        if not settings.EGGO_WORLD_ACTIVO:
            raise Http404
        return vista(request, *args, **kwargs)

    return envuelta


def cliente(vista):
    """Exige un cliente logueado y entrega el cuerpo del pedido como diccionario."""

    @wraps(vista)
    def envuelta(request, *args, **kwargs):
        # SUPUESTO: por ahora Eggo World es solo para consumidores (Ramón, 13/11).
        if not request.user.is_authenticated or request.user.rol != Usuario.Rol.CLIENTE:
            return JsonResponse({"error": "Entrá a tu cuenta para seguir."}, status=401)
        try:
            request.datos = json.loads(request.body or "{}")
        except ValueError:
            return JsonResponse({"error": "No entendimos el pedido."}, status=400)
        try:
            return vista(request, *args, **kwargs)
        except mundo.NoSePuede as error:
            return JsonResponse({"error": str(error)}, status=400)
        except (TypeError, ValueError, AttributeError):
            # Datos con una forma inesperada (un texto donde iba un número, por ejemplo).
            return JsonResponse({"error": "No entendimos el pedido."}, status=400)

    return activo(envuelta)


def _perfil(usuario):
    return Cliente.objects.get_or_create(usuario=usuario)[0]


def _fecha(valor):
    return timezone.localtime(valor).isoformat() if valor else None


# --- La página -----------------------------------------------------------------------------


@activo
@ensure_csrf_cookie
def chacra(request):
    """Entrega la app. Es una sola página; el resto lo hace el navegador hablando con la API."""
    pagina = (settings.BASE_DIR / "eggo-world" / "index.html").read_text(encoding="utf-8")
    return HttpResponse(pagina.replace("__GOOGLE_CLIENT_ID__", settings.GOOGLE_CLIENT_ID))


# --- Entrar y salir ------------------------------------------------------------------------


@activo
@require_POST
def entrar_con_google(request):
    try:
        datos = google.verificar(json.loads(request.body or "{}").get("credential"))
    except (google.ComprobanteInvalido, ValueError):
        return JsonResponse({"error": "No pudimos entrar con Google. Probá de nuevo."}, status=400)
    # Si ya había una cuenta con ese email, se entra a esa: el cliente conserva su historial.
    # Si hubiera más de una, se prefiere la que usa el email como nombre de usuario.
    conocidos = Usuario.objects.filter(email__iexact=datos["email"]).order_by("pk")
    usuario = conocidos.filter(username__iexact=datos["email"]).first() or conocidos.first()
    if usuario is None:
        usuario = Usuario(username=datos["email"], email=datos["email"], first_name=datos["nombre"])
        usuario.rol = Usuario.Rol.CLIENTE
        usuario.set_unusable_password()
        usuario.save()
        Cliente.objects.create(usuario=usuario)
    elif usuario.rol != Usuario.Rol.CLIENTE or not usuario.is_active:
        # Las cuentas del equipo y de restaurantes no entran por acá.
        return JsonResponse({"error": "Esa cuenta entra por la app de Eggologic de siempre."}, status=403)
    login(request, usuario, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse({"ok": True})


@activo
@require_POST
def salir(request):
    logout(request)
    return JsonResponse({"ok": True})


# --- El estado completo --------------------------------------------------------------------


def _pedido(pedido):
    return {
        "id": pedido.pk,
        "estado": pedido.estado,
        "estado_texto": pedido.get_estado_display(),
        "forma_pago": pedido.forma_pago,
        "forma_pago_texto": pedido.get_forma_pago_display(),
        "total": int(pedido.total),
        "huevos": pedido.huevos,
        "items": [f"{item.cantidad} × {item.producto.nombre}" for item in pedido.items.all()],
        "fecha": _fecha(pedido.creado_en),
        "entrega_estimada": _fecha(pedido.entrega_estimada),
    }


def _gallina(gallina):
    return {
        "id": gallina.pk,
        "nombre": gallina.nombre,
        "color": gallina.color,
        "plan": gallina.plan,
        "plan_texto": gallina.get_plan_display(),
        "estado": gallina.estado,
        "en_pausa": gallina.estado == Gallina.Estado.ACTIVA and mundo.en_pausa(gallina),
        "inicio": gallina.inicio.isoformat() if gallina.inicio else None,
        "pago_hasta": gallina.pago_hasta.isoformat() if gallina.pago_hasta else None,
        "huevos_puestos": gallina.huevos_puestos(),
        "produccion_anual": gallina.produccion_anual(),
        "lugar_para_larvas": gallina.lugar_para_larvas(),
    }


def _levante(levante):
    listas = levante.larvas_listas_el()
    return {
        "id": levante.pk,
        "paso": levante.paso(),
        "kg": float(levante.kg) if levante.kg is not None else None,
        "raciones": levante.raciones(),
        "pedido_en": _fecha(levante.pedido_en),
        "larvas_listas_el": listas.isoformat() if listas else None,
    }


def _impacto(usuario):
    factores = calculos.factores_del_circuito()
    compras = calculos.impacto_de_compras(usuario, factores)
    levantes = Levante.objects.filter(usuario=usuario, estado=Levante.Estado.RETIRADO)
    gallinas = Gallina.objects.filter(usuario=usuario)
    return {
        "huevos_recibidos": compras["huevos"],
        "kg_detras_de_mis_huevos": float(compras["kg_rescatados"]) if compras["kg_rescatados"] is not None else None,
        "kg_larva_detras_de_mis_huevos": float(compras["kg_larva"]) if compras["kg_larva"] is not None else None,
        "nivel": calculos.nivel_del_cliente(compras["huevos"]),
        "kg_residuos_entregados": float(sum(levante.kg or 0 for levante in levantes)),
        "huevos_extra_por_larvas": sum(gallina.bono() for gallina in gallinas) * reglas.HUEVOS_POR_RACION,
        "comunidad": {clave: float(valor) for clave, valor in calculos.totales_de_la_comunidad().items()},
    }


def _estado(usuario):
    mundo.poner_al_dia(usuario)
    perfil = _perfil(usuario)
    ajustes = Ajustes.actuales()
    socio = eggos.es_socio(usuario)
    productos = Producto.objects.filter(activo=True)
    pedidos = Pedido.objects.filter(usuario=usuario).prefetch_related("items__producto")[:10]
    return {
        "yo": {
            "nombre": usuario.first_name or usuario.username,
            "email": usuario.email,
            "telefono": perfil.telefono,
            "direccion": perfil.direccion,
        },
        "eggos": {
            "saldo": eggos.saldo(usuario),
            "socio": socio,
            "saldo_para_ser_socio": reglas.SALDO_PARA_SER_SOCIO,
            "paquetes": reglas.PAQUETES,
            "descuento": float((reglas.DESCUENTO_SOCIO if socio else reglas.DESCUENTO_CON_EGGOS) * 100),
            "descuento_socio": float(reglas.DESCUENTO_SOCIO * 100),
            "vuelta": float(reglas.VUELTA_PAGANDO_CON_PLATA * 100),
            "movimientos": [
                {"cantidad": m.cantidad, "motivo": m.get_motivo_display(), "detalle": m.detalle, "fecha": _fecha(m.creado_en)}
                for m in Movimiento.objects.filter(usuario=usuario)[:20]
            ],
            "recargas_pendientes": [
                {"id": r.pk, "monto": r.monto, "medio": r.get_medio_display()}
                for r in Recarga.objects.filter(usuario=usuario, estado=Recarga.Estado.PENDIENTE)
            ],
        },
        "gallinas": [_gallina(g) for g in mundo.gallinas_que_cuentan().filter(usuario=usuario)],
        "planes": [
            {"plan": plan, "nombre": datos["nombre"], "precio": datos["precio"], "dias": datos["dias"]}
            for plan, datos in reglas.PLANES.items()
        ],
        "adopcion": {
            "lugares": mundo.lugares_para_adoptar(),
            "maximo_por_cuenta": reglas.MAXIMO_DE_GALLINAS_POR_CUENTA,
            "huevos_por_anio": reglas.HUEVOS_POR_ANIO,
            "bono_maximo": reglas.BONO_MAXIMO_POR_ANIO,
        },
        "huevos": {"para_pedir": mundo.huevos_para_pedir(usuario), "minimo": reglas.HUEVOS_PARA_PEDIR},
        "larvas": mundo.larvas_disponibles(usuario),
        "levantes": [_levante(l) for l in Levante.objects.filter(usuario=usuario)[:5]],
        "precio_del_levante": reglas.PRECIO_DEL_LEVANTE,
        "productos": [
            {
                "id": p.pk,
                "nombre": p.nombre,
                "descripcion": p.descripcion,
                "huevos": p.huevos,
                "precio": int(p.precio),
                "precio_eggos": reglas.precio_en_eggos(p.precio, socio),
            }
            for p in productos
        ],
        "pedidos": [_pedido(p) for p in pedidos],
        "tienda": {
            "huevos_disponibles": ajustes.huevos_disponibles,
            "mercado_pago": pagos.disponible(),
            "datos_transferencia": settings.TIENDA_DATOS_TRANSFERENCIA,
        },
        "granja": {"sanidad": ajustes.sanidad},
        "impacto": _impacto(usuario),
    }


@activo
@require_GET
def estado(request):
    """Todo lo que la chacra necesita mostrar, en un solo pedido."""
    if not request.user.is_authenticated or request.user.rol != Usuario.Rol.CLIENTE:
        return JsonResponse({"error": "Entrá a tu cuenta para seguir."}, status=401)
    return JsonResponse(_estado(request.user))


def _listo(request, **extra):
    return JsonResponse({"ok": True, **extra, "estado": _estado(request.user)})


# --- Acciones ------------------------------------------------------------------------------


def _pago(request, titulo, monto, referencia, medio):
    """Qué tiene que hacer el cliente para pagar: ir a Mercado Pago o transferir."""
    if medio == Recarga.Medio.MERCADO_PAGO:
        try:
            volver_a = request.build_absolute_uri(reverse("api:chacra"))
            avisar_a = request.build_absolute_uri(reverse("api:aviso_de_mercado_pago"))
            return {"ir_a": pagos.crear_pago(titulo, monto, referencia, volver_a, avisar_a)}
        except pagos.MercadoPagoNoDisponible:
            raise mundo.NoSePuede("Mercado Pago no está disponible ahora. Podés pagar por transferencia.")
    return {"transferir": {"monto": monto, "datos": settings.TIENDA_DATOS_TRANSFERENCIA}}


@cliente
@require_POST
def guardar_perfil(request):
    perfil = _perfil(request.user)
    request.user.first_name = str(request.datos.get("nombre") or request.user.first_name)[:150]
    request.user.save()
    perfil.telefono = str(request.datos.get("telefono") or "")[:40]
    perfil.direccion = str(request.datos.get("direccion") or "")[:200]
    perfil.save()
    return _listo(request)


@cliente
@require_POST
@transaction.atomic
def adoptar(request):
    datos = request.datos
    gallina, recarga = mundo.adoptar(
        request.user, datos.get("plan"), datos.get("nombre"), datos.get("color"), datos.get("medio")
    )
    pago = None
    if recarga:
        pago = _pago(request, f"Gallina {gallina.nombre}", recarga.monto, f"recarga-{recarga.pk}", recarga.medio)
    return _listo(request, pago=pago)


@cliente
@require_POST
def renombrar(request, gallina_id):
    nombre = str(request.datos.get("nombre") or "").strip()[:30]
    gallina = Gallina.objects.filter(pk=gallina_id, usuario=request.user).first()
    if not gallina or not nombre:
        raise mundo.NoSePuede("Ponele un nombre a tu gallina.")
    gallina.nombre = nombre
    gallina.save()
    return _listo(request)


@cliente
@require_POST
def dar_larvas(request):
    gallina = Gallina.objects.filter(pk=request.datos.get("gallina"), usuario=request.user).first()
    if not gallina:
        raise mundo.NoSePuede("No encontramos esa gallina.")
    dadas = mundo.dar_larvas(request.user, gallina, int(request.datos.get("cantidad") or 1))
    return _listo(request, dadas=dadas)


def _datos_de_entrega(request):
    """La dirección y el teléfono se piden en el primer pedido y quedan guardados."""
    perfil = _perfil(request.user)
    direccion = str(request.datos.get("direccion") or perfil.direccion).strip()[:200]
    telefono = str(request.datos.get("telefono") or perfil.telefono).strip()[:40]
    if direccion and telefono and (direccion, telefono) != (perfil.direccion, perfil.telefono):
        perfil.direccion, perfil.telefono = direccion, telefono
        perfil.save()
    return direccion, telefono


@cliente
@require_POST
@transaction.atomic
def pedir(request):
    datos = request.datos
    direccion, telefono = _datos_de_entrega(request)
    productos = {p.pk: p for p in Producto.objects.filter(activo=True)}
    try:
        items = [
            (productos[int(item["producto"])], min(int(item["cantidad"]), 50)) for item in datos.get("items", [])
        ]
    except (KeyError, TypeError, ValueError):
        raise mundo.NoSePuede("Elegí al menos un producto.")
    forma_pago = datos.get("forma_pago")
    if forma_pago == Pedido.FormaPago.GALLINA:
        raise mundo.NoSePuede("Los huevos de tus gallinas se piden desde el nido.")
    pedido = mundo.crear_pedido(request.user, items, forma_pago, direccion, telefono, str(datos.get("notas") or ""))
    pago = None
    if forma_pago == Pedido.FormaPago.MERCADO_PAGO:
        pago = _pago(request, f"Pedido N.º {pedido.pk}", int(pedido.total), f"pedido-{pedido.pk}", forma_pago)
    elif forma_pago == Pedido.FormaPago.TRANSFERENCIA:
        pago = _pago(request, "", int(pedido.total), "", forma_pago)
    return _listo(request, pedido=pedido.pk, pago=pago)


@cliente
@require_POST
def pedir_huevos(request):
    direccion, telefono = _datos_de_entrega(request)
    pedido = mundo.pedir_huevos(request.user, int(request.datos.get("huevos") or 0), direccion, telefono)
    return _listo(request, pedido=pedido.pk)


@cliente
@require_POST
@transaction.atomic
def recargar(request):
    paquete, medio = request.datos.get("paquete"), request.datos.get("medio")
    if paquete not in reglas.PAQUETES or medio not in Recarga.Medio.values:
        raise mundo.NoSePuede("Elegí un paquete y cómo pagarlo.")
    if eggos.saldo(request.user) + paquete > reglas.TOPE_POR_CUENTA:
        raise mundo.NoSePuede(f"El saldo máximo es de {reglas.TOPE_POR_CUENTA} Eggos.")
    recarga = Recarga.objects.create(usuario=request.user, monto=paquete, medio=medio)
    pago = _pago(request, f"{paquete} Eggos", paquete, f"recarga-{recarga.pk}", medio)
    return _listo(request, pago=pago)


@cliente
@require_POST
@transaction.atomic
def pedir_levante(request):
    direccion, telefono = _datos_de_entrega(request)
    mundo.pedir_levante(request.user, direccion, telefono, str(request.datos.get("nota") or ""))
    return _listo(request)


# --- Mercado Pago avisa --------------------------------------------------------------------


@activo
@csrf_exempt
@require_POST
def aviso_de_mercado_pago(request):
    """Mercado Pago llama acá cuando cambia un pago.

    Cualquiera puede llamar a esta dirección, así que el aviso solo sirve de timbre: el estado
    del pago se le pregunta a Mercado Pago con nuestra credencial.
    """
    try:
        cuerpo = json.loads(request.body or "{}")
    except ValueError:
        cuerpo = {}
    pago_id = (cuerpo.get("data") or {}).get("id") or request.GET.get("data.id") or request.GET.get("id")
    es_pago = "payment" in (cuerpo.get("type"), request.GET.get("type"), request.GET.get("topic"))
    if not pago_id or not es_pago:
        return HttpResponse(status=200)
    try:
        pago = pagos.consultar_pago(pago_id)
    except pagos.MercadoPagoNoDisponible:
        # Con un error, Mercado Pago vuelve a avisar más tarde.
        return HttpResponse(status=503)
    tipo, _, numero = pago["referencia"].partition("-")
    if pago["aprobado"] and numero.isdigit():
        if tipo == "recarga":
            recarga = Recarga.objects.filter(pk=numero, estado=Recarga.Estado.PENDIENTE).first()
            if recarga and pago["monto"] >= recarga.monto:
                mundo.acreditar_recarga(recarga)
        elif tipo == "pedido":
            pedido = Pedido.objects.filter(pk=numero, estado=Pedido.Estado.RECIBIDO).first()
            if pedido and pago["monto"] >= pedido.total:
                pedido.estado = Pedido.Estado.CONFIRMADO
                pedido.save()
    return HttpResponse(status=200)
