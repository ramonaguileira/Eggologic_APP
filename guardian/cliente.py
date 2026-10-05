"""Conexión con Guardian (Managed Guardian Service, MGS).

La app nunca escribe a Hedera directo: le manda documentos a la policy FLW por la API de
Guardian, y Guardian los firma, los publica y mintea. Detalle de la API y de los tags de la
policy en docs/guardian/analisis-policy-flw.md.
"""

import os

import requests
from django.conf import settings

SEGUNDOS_MAXIMO = 30


class ErrorGuardian(Exception):
    pass


def clave_de_restaurante(codigo):
    """'R-001' -> 'R001': el prefijo de sus variables (GUARDIAN_R001_EMAIL, GUARDIAN_R001_PASSWORD)."""
    return codigo.replace("-", "").upper()


def credenciales(clave):
    """Email y contraseña de un usuario de Guardian. clave es 'PROPONENTE' o la de un restaurante."""
    email = os.environ.get(f"GUARDIAN_{clave}_EMAIL", "")
    password = os.environ.get(f"GUARDIAN_{clave}_PASSWORD", "")
    if not email or not password:
        raise ErrorGuardian(f"Faltan GUARDIAN_{clave}_EMAIL o GUARDIAN_{clave}_PASSWORD.")
    return email, password


class Sesion:
    """Un usuario de Guardian con la sesión abierta.

    Eggologic custodia todas las cuentas: cada restaurante tiene su usuario (rol PPE) y firma
    sus propios documentos, pero las credenciales viven en las variables de entorno.
    """

    def __init__(self, clave):
        if not settings.GUARDIAN_URL or not settings.GUARDIAN_POLICY_ID:
            raise ErrorGuardian("Faltan GUARDIAN_URL o GUARDIAN_POLICY_ID.")
        self.base = settings.GUARDIAN_URL.rstrip("/")
        self.ruta_policy = f"policies/{settings.GUARDIAN_POLICY_ID}"
        self.http = requests.Session()

        email, password = credenciales(clave)
        # En MGS el login es por email; en el Guardian open source es POST /accounts/login.
        login = self._pedir("POST", "accounts/loginByEmail", {"email": email, "password": password})["login"]
        acceso = self._pedir("POST", "accounts/access-token", {"refreshToken": login["refreshToken"]})
        self.http.headers["Authorization"] = f"Bearer {acceso['accessToken']}"
        self.usuario = login["username"]
        self.did = login["did"]  # did:hedera:<red>:...

    @property
    def red(self):
        return self.did.split(":")[2]

    def policy(self):
        return self._pedir("GET", self.ruta_policy)

    def bloque(self, tag):
        """Lo que ve este usuario en un bloque de la policy (por ejemplo, una grilla de documentos)."""
        return self._pedir("GET", f"{self.ruta_policy}/tag/{tag}/blocks")

    def enviar(self, tag, datos):
        """Manda datos a un bloque: un formulario ({"document": ..., "ref": ...}) o un botón."""
        return self._pedir("POST", f"{self.ruta_policy}/tag/{tag}/blocks", datos)

    def _pedir(self, metodo, ruta, datos=None):
        try:
            respuesta = self.http.request(metodo, f"{self.base}/{ruta}", json=datos, timeout=SEGUNDOS_MAXIMO)
        except requests.RequestException as error:
            raise ErrorGuardian(f"No se pudo conectar con Guardian ({error.__class__.__name__}).") from error
        if not respuesta.ok:
            # El error nunca repite lo que se mandó: en el login va la contraseña.
            try:
                detalle = respuesta.json().get("message", "")
            except ValueError:
                detalle = ""
            raise ErrorGuardian(f"Guardian respondió {respuesta.status_code} a {metodo} {ruta}. {detalle}".strip())
        return respuesta.json()
