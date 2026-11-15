"""Entrar con Google: comprobar que el comprobante que manda el navegador es auténtico.

SUPUESTO: se le pregunta a Google (tokeninfo) en lugar de verificar la firma acá. Es más lento
pero no suma dependencias, y para el volumen del piloto alcanza. Si crece, pasar a `google-auth`.
"""

import time

import requests
from django.conf import settings

URL = "https://oauth2.googleapis.com/tokeninfo"
EMISORES = ["accounts.google.com", "https://accounts.google.com"]


class ComprobanteInvalido(Exception):
    pass


def verificar(comprobante):
    """Devuelve el email y el nombre de la cuenta de Google, o lanza ComprobanteInvalido."""
    if not settings.GOOGLE_CLIENT_ID or not comprobante:
        raise ComprobanteInvalido
    try:
        respuesta = requests.get(URL, params={"id_token": comprobante}, timeout=10)
        datos = respuesta.json() if respuesta.status_code == 200 else {}
    except (requests.RequestException, ValueError) as error:
        raise ComprobanteInvalido from error
    valido = (
        # Que el comprobante sea para nuestra app y no para otra.
        datos.get("aud") == settings.GOOGLE_CLIENT_ID
        and datos.get("iss") in EMISORES
        and str(datos.get("email_verified")).lower() == "true"
        and int(datos.get("exp", 0)) > time.time()
        and datos.get("email")
    )
    if not valido:
        raise ComprobanteInvalido
    return {"email": datos["email"].lower(), "nombre": datos.get("given_name") or datos.get("name") or ""}
