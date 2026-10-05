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
- `impacto/`: "Mi impacto" de clientes y restaurantes. Todas las fórmulas están en `impacto/calculos.py`.
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
```

## Estado (05/10/2026)

| Etapa | Contenido | Estado |
| --- | --- | --- |
| 0 | Propuesta | Aprobada |
| 1 | Captura | Aprobada |
| 2 | Tienda e impacto | Para revisar |
| 3 | Guardian | Pendiente |
| 4 | Entregables ANDE (demo 19/10/2026) | Pendiente |

**Etapa 3 (Guardian).** Usa estas variables de entorno, cargadas según el instructivo que tiene Ramón:

- `GUARDIAN_URL`
- `GUARDIAN_POLICY_ID`
- `GUARDIAN_PROPONENTE_EMAIL` y `GUARDIAN_PROPONENTE_PASSWORD`
- `GUARDIAN_R001_EMAIL` y `GUARDIAN_R001_PASSWORD`

El MGS hace el login con `POST /accounts/loginByEmail`. Detalle de la API en `docs/guardian/analisis-policy-flw.md`.

**Hosting.** Netlify no puede correr Django, así que falta elegir un hosting de Python con `https` (el GPS del celular lo necesita).
