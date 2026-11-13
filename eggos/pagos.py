"""Mercado Pago: crear un pago y averiguar si se pagó.

Se usa la API con `requests`, sin sumar otra dependencia. La credencial va en la variable de
entorno MERCADOPAGO_ACCESS_TOKEN; sin ella, pagar con Mercado Pago no está disponible.
"""

import requests
from django.conf import settings

URL = "https://api.mercadopago.com"
ESPERA = 15


class MercadoPagoNoDisponible(Exception):
    pass


def disponible():
    return bool(settings.MERCADOPAGO_ACCESS_TOKEN)


def _encabezados():
    if not disponible():
        raise MercadoPagoNoDisponible
    return {"Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"}


def crear_pago(titulo, monto, referencia, volver_a, avisar_a):
    """Arma el pago y devuelve la dirección a la que hay que mandar al cliente para que pague."""
    datos = {
        "items": [{"title": titulo, "quantity": 1, "unit_price": float(monto), "currency_id": "UYU"}],
        # Con esto, cuando Mercado Pago avisa, sabemos a qué recarga o pedido corresponde.
        "external_reference": referencia,
        "back_urls": {"success": volver_a, "pending": volver_a, "failure": volver_a},
        "auto_return": "approved",
        "notification_url": avisar_a,
    }
    try:
        respuesta = requests.post(f"{URL}/checkout/preferences", json=datos, headers=_encabezados(), timeout=ESPERA)
        respuesta.raise_for_status()
        return respuesta.json()["init_point"]
    except (requests.RequestException, KeyError, ValueError) as error:
        raise MercadoPagoNoDisponible from error


def consultar_pago(pago_id):
    """Le pregunta a Mercado Pago por un pago. No se confía en lo que diga el aviso: se verifica acá."""
    try:
        respuesta = requests.get(f"{URL}/v1/payments/{pago_id}", headers=_encabezados(), timeout=ESPERA)
        respuesta.raise_for_status()
        pago = respuesta.json()
    except (requests.RequestException, ValueError) as error:
        raise MercadoPagoNoDisponible from error
    return {
        "aprobado": pago.get("status") == "approved",
        "referencia": pago.get("external_reference") or "",
        "monto": pago.get("transaction_amount") or 0,
    }
