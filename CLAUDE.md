# Eggologic App — guía para Claude Code

App piloto de Eggologic (Nodo 1, Maldonado): registra el circuito residuo de restaurantes → larva BSF → gallinas → huevos, vende huevos y muestra el impacto. Informa a Hedera **solo a través de Guardian** (policy FLW Standard). La app nunca escribe a Hedera directo.

## Cómo trabajamos

- **Por etapas.** Al terminar cada etapa, entregá un resumen de checkpoint y **detenete** hasta que Ramón diga cómo seguir. El resumen tiene seis puntos:
  1. qué se construyó y qué quedó afuera;
  2. cómo correrlo;
  3. tests;
  4. SUPUESTOS;
  5. puntos para Marcel;
  6. preguntas.
- **SUPUESTO.** Toda decisión no confirmada por Ramón se marca `SUPUESTO`, en el código como comentario y en el doc de la etapa.
- **Código simple.** Marcel revisa todo a mano al final. Django convencional, vistas como funciones, pocas dependencias, comentarios solo para el "por qué".
- **Preguntá antes de inventar** si el dato cambia el diseño. Si es menor, decidí, marcalo SUPUESTO y seguí.

## Reglas

- **Interfaz en español rioplatense, sin jerga cripto.** Nada de "blockchain", "coin", "crypto" ni "crédito de carbono". Se dice "registro verificable" o "notaría digital del impacto".
  - El token de incentivos se llama **Eggos**.
  - El CIN es un certificado de impacto circular, no un crédito de carbono.
  - En el código y los docs técnicos sí se puede decir Hedera, HCS, HTS, token o NFT.
- **Solo testnet.**
- **Custodia de claves:** Eggologic administra las cuentas de Guardian; los usuarios no tienen wallet.
- **Secretos solo en variables de entorno** (`.env` local, o el entorno de Claude Code). Nunca en el código ni en commits: **el repo es público**.
- **Datos personales solo en la base de la app.** Lo que va a Guardian queda público en IPFS: se mandan códigos seudónimos (`R-001`), nunca nombres, emails ni direcciones.
- **Policy:** FLW Standard del hackathon de Guardian, con cada restaurante como entidad participante (rol PPE). Sin Groups, sin EWD-RB y sin gemelo digital por ahora (decisiones de Ramón, 05/10/2026).
- **Nivel D no se implementa:** programa de incentivos a escala, emisión del CIN, modelo no custodial.

## Estructura

- `cuentas/`: usuarios con rol, restaurantes (con código público) y clientes.
- `captura/`:
  - retiros: el chofer carga kg, foto y GPS automático; la planta clasifica después;
  - lotes BSF, granja;
  - panel y exportación CSV para CarboSur.
- `tienda/`: productos y pedidos (pago contra entrega o transferencia).
- `impacto/`: "Mi impacto" de clientes y restaurantes. Todas las fórmulas están en `impacto/calculos.py`, incluido el factor provisorio de CO2e.
- `guardian/`: cliente de la API de MGS, reporte mensual por restaurante (lo verifica una persona en **Reportes**) y los comandos `guardian_estado` y `guardian_enviar`.
- `docs/`:
  - propuesta aprobada (`etapa-0-propuesta.md`);
  - un doc por etapa;
  - análisis de la policy FLW (`guardian/analisis-policy-flw.md`).

## Comandos

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # completar DJANGO_SECRET_KEY
python manage.py migrate
python manage.py cargar_demo --password "<contraseña de prueba>"
python manage.py test
python manage.py runserver
python manage.py guardian_estado   # revisa la conexión con Guardian sin escribir nada
python manage.py guardian_enviar   # manda a Guardian los reportes verificados (escribe en el Guardian real)
```

## Estado (06/10/2026)

| Etapa | Contenido | Estado |
| --- | --- | --- |
| 0 | Propuesta | Aprobada |
| 1 | Captura | Aprobada |
| 2 | Tienda e impacto | Para revisar |
| 3 | Guardian | Para revisar; envío de prueba hecho, falta crear Render |
| 4 | Entregables ANDE (demo 19/10/2026) | Pendiente |

**Etapa 3 (Guardian).** Usa estas variables de entorno, cargadas según el instructivo que tiene Ramón:

- `GUARDIAN_URL`
- `GUARDIAN_POLICY_ID`
- `GUARDIAN_PROPONENTE_EMAIL` y `GUARDIAN_PROPONENTE_PASSWORD`
- `GUARDIAN_R001_EMAIL` y `GUARDIAN_R001_PASSWORD`

El MGS hace el login con `POST /accounts/loginByEmail`. Detalle de la API en `docs/guardian/analisis-policy-flw.md`.

Lo que Ramón dejó hecho en Guardian (MGS 1.6.1), según el instructivo, el 05/10/2026:

- Policy FLW (`FWLI001.policy`) importada y publicada con la cuenta Standard Registry `Eggologic_Standard`.
- Usuarios, cada uno con el rol de permisos `Default policy user` y la policy asignada:

  | Usuario | Rol en la policy |
  | --- | --- |
  | `Eggologic_Proponente` | Project_Proponent |
  | `Eggologic_vvb` | VVB (CarboSur) |
  | `Eggologic_r001` | Project_Participating_Entity. El alta quedó con el nombre comercial, no `R-001` (ver `docs/etapa-3.md`) |

- El Proponente aprobó al restaurante y el Standard Registry aprobó al VVB.
- Red del entorno: `guardianservice.app` y `testnet.mirrornode.hedera.com` permitidos.

Lo primero en la Etapa 3:

1. Comprobar que las seis variables existen. Mirar solo los nombres, nunca imprimir los valores.
2. Probar el login de los dos usuarios.
3. Confirmar que la policy corre en testnet.

Cosas de MGS que aprendimos:

- Las invitaciones se mandan desde la cuenta de administrador del tenant, no desde el Standard Registry.
- Un usuario sin el rol `Default policy user` recibe "Access Restricted" y errores 403.
- La policy no deja corregir un alta aprobada: si se revoca, vuelve a "esperando aprobación" con el mismo documento.
- El restaurante solo puede enviar reportes cuando hay un proyecto validado. El proyecto "Eggologic · FLW Nodo 1 (Maldonado)" quedó validado el 06/10/2026.
- Al validar un proyecto, Guardian guarda una copia (`approved_project`) además del original (`project`).
- Guardian procesa los envíos en segundo plano: un reporte recién enviado tarda en aparecerle al Proponente.
- La policy deja el reporte del restaurante en "Waiting for Verification" aunque ya esté aprobado. **No aprobar reportes desde MGS**: se mintearía dos veces. La app se fija en la copia `approved_entity_report`.
- Envío de prueba real hecho el 06/10: "PRUEBA · … R-001 2026-09", 0,21 FGET minteados a R-001.

**Reporte mensual (decisiones de Ramón, 06/10).** Un reporte por restaurante por mes. Lo verifica una persona de Eggologic, y la app lo manda como el restaurante y lo aprueba como Proponente, lo que mintea FGET. Las tCO2e usan un factor provisorio hasta que CarboSur dé el suyo. Detalle en `docs/etapa-3.md`.

**Hosting: Render, planes gratis** (decisiones de Ramón, 06/10). Configuración en `render.yaml`: web y PostgreSQL gratis. Sin cron (los reportes se mandan con el botón **Enviar al registro** de Reportes) y sin disco: las fotos de los retiros se guardan en la base (`captura/almacen.py`). La base gratis vence a los 30 días. El primer admin lo crea `build.sh` con `crear_admin`. Las credenciales de Guardian van en el grupo de variables `eggologic-guardian` del panel, nunca en el repo. Pasos y cómo pasar a pago en `docs/etapa-3.md`.

**Restaurantes nuevos (resolución temporal, 06/10).** Se cargan en la app desde el primer día; el usuario en Guardian se crea cuando entran en serio al piloto, con el alta solo con el código. Mientras tanto sus meses esperan en **Reportes**. No habrá restaurantes nuevos antes del 19/10.
