import os

from django.core.management.base import BaseCommand, CommandError

from cuentas.models import Restaurante
from guardian.cliente import ErrorGuardian, Sesion, clave_de_restaurante, tiene_credenciales

VARIABLES = [
    "GUARDIAN_URL",
    "GUARDIAN_POLICY_ID",
    "GUARDIAN_PROPONENTE_EMAIL",
    "GUARDIAN_PROPONENTE_PASSWORD",
]


class Command(BaseCommand):
    help = (
        "Revisa la conexión con Guardian sin escribir nada: variables, login, red, policy, "
        "alta de cada restaurante y proyecto."
    )

    def handle(self, *args, **opciones):
        self.problemas = 0
        self.avisos = 0

        self.titulo("Variables de entorno")
        for nombre in VARIABLES:
            # Solo se mira que existan: los valores no se muestran nunca.
            if os.environ.get(nombre):
                self.bien(nombre)
            else:
                self.mal(f"{nombre}: falta")
        if self.problemas:
            raise CommandError("Faltan variables de entorno.")

        self.titulo("Proponente")
        try:
            proponente = Sesion("PROPONENTE")
        except ErrorGuardian as error:
            raise CommandError(str(error))
        self.revisar_usuario(proponente, "Project_Proponent")

        self.titulo("Restaurantes")
        altas = {doc.get("owner"): doc for doc in proponente.bloque("ppe_grid_pp").get("data", [])}
        for restaurante in Restaurante.objects.filter(activo=True).order_by("codigo"):
            self.revisar_restaurante(restaurante, altas)

        self.titulo("Proyecto")
        # Al validar, Guardian suma una copia del proyecto (approved_project): se cuentan los originales.
        documentos = proponente.bloque("project_grid_pp_2").get("data", [])
        proyectos = [doc for doc in documentos if doc.get("type") == "project"]
        estados = [estado(doc) for doc in proyectos]
        for nombre in sorted(set(estados)):
            self.stdout.write(f"  {estados.count(nombre)} proyecto(s) en estado {nombre}")
        if "Validated" in estados:
            self.bien("Hay un proyecto validado: los restaurantes pueden enviar reportes.")
        else:
            self.aviso(
                "Ningún proyecto validado: los restaurantes todavía no pueden enviar reportes. Falta que el "
                "Proponente cargue el Project Description, el Standard Registry lo acepte y el VVB lo valide."
            )

        if self.problemas:
            raise CommandError(f"{self.problemas} problema(s).")
        pendientes = f", con {self.avisos} aviso(s)" if self.avisos else ""
        self.stdout.write(self.style.SUCCESS(f"\nConexión con Guardian en orden{pendientes}."))

    def revisar_usuario(self, sesion, rol_esperado):
        self.bien(f"Login de {sesion.usuario}")
        if sesion.red == "testnet":
            self.bien("Red: testnet")
        else:
            self.mal(f"Red: {sesion.red}. La app solo trabaja en testnet.")

        policy = sesion.policy()
        if policy.get("status") == "PUBLISH":
            self.bien(f"Policy publicada: {policy.get('name')} {policy.get('version', '')}")
        else:
            self.mal(f"La policy está en estado {policy.get('status')}, no publicada.")
        if policy.get("userRole") == rol_esperado:
            self.bien(f"Rol en la policy: {rol_esperado}")
        else:
            self.mal(f"Rol en la policy: {policy.get('userRole')}; se esperaba {rol_esperado}.")

    def revisar_restaurante(self, restaurante, altas):
        clave = clave_de_restaurante(restaurante.codigo)
        self.stdout.write(f"  {restaurante.codigo}")
        if not tiene_credenciales(clave):
            self.aviso(f"Sin usuario en Guardian (faltan GUARDIAN_{clave}_EMAIL y GUARDIAN_{clave}_PASSWORD).")
            return
        try:
            sesion = Sesion(clave)
        except ErrorGuardian as error:
            self.mal(str(error))
            return
        self.revisar_usuario(sesion, "Project_Participating_Entity")

        alta = altas.get(sesion.did)
        if alta is None:
            self.mal("No completó el alta en la policy.")
            return
        if estado(alta) == "APPROVED":
            self.bien("Alta aprobada por el Proponente")
        else:
            self.aviso(f"Alta en estado {estado(alta)}.")
        nombre = alta["document"]["credentialSubject"][0].get("field0")
        if nombre != restaurante.codigo:
            # No se muestra el nombre: alcanza con saber que no es el código.
            self.aviso(
                f"En Guardian figura con un nombre que no es su código. Lo que va a Guardian es "
                f"público: debería ser {restaurante.codigo}."
            )

    def titulo(self, texto):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{texto}"))

    def bien(self, texto):
        self.stdout.write(f"  ✓ {texto}")

    def aviso(self, texto):
        self.avisos += 1
        self.stdout.write(self.style.WARNING(f"  ! {texto}"))

    def mal(self, texto):
        self.problemas += 1
        self.stdout.write(self.style.ERROR(f"  ✗ {texto}"))


def estado(documento):
    return (documento.get("option") or {}).get("status")
