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

- `cuentas/`: usuarios con rol, restaurantes (con código público) y clientes. Cada persona de campo ve solo su tarea (Ramón, 06/10): chofer (solo retiros), planta (clasificación y lotes), granja (registro diario); operador hace todo el campo; CarboSur ve todo sin editar.
- `captura/`:
  - retiros: el chofer carga kg, foto y GPS automático; la planta clasifica después;
  - lotes BSF, granja;
  - panel y exportación CSV para CarboSur;
  - informe del circuito (trazabilidad, línea de base, números para ANDE), con código y nombre de cada restaurante (no va a Guardian);
  - fotos de los retiros guardadas en la base (`captura/almacen.py`).
- `tienda/`: productos y pedidos (pago contra entrega o transferencia).
- `impacto/`: "Mi impacto" de clientes y restaurantes. Todas las fórmulas están en `impacto/calculos.py`, incluido el factor provisorio de CO2e.
- `guardian/`: cliente de la API de MGS, reporte mensual por restaurante (lo revisa una persona en **Reportes**) y los comandos `guardian_estado` y `guardian_enviar`.
- `docs/`:
  - propuesta aprobada (`etapa-0-propuesta.md`);
  - un doc por etapa, y uno por fase del plan de datos (`plan-datos-fase-0.md`);
  - guion de la demo del 19/10 (`demo-19-10.md`) y guía de revisión para Marcel (`para-marcel.md`);
  - análisis de la policy FLW (`guardian/analisis-policy-flw.md`);
  - respuestas sobre la API de Guardian/MGS (`guardian/respuestas-api-mgs.md`).

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
python manage.py guardian_enviar   # manda a Guardian los reportes revisados (escribe en el Guardian real)
```

## Estado (07/10/2026)

| Etapa | Contenido | Estado |
| --- | --- | --- |
| 0 | Propuesta | Aprobada |
| 1 | Captura | Aprobada |
| 2 | Tienda e impacto | Para revisar |
| 3 | Guardian | Para revisar; envío de prueba hecho |
| 4 | Entregables ANDE (demo 19/10/2026) | Para revisar |
| Datos | Plan de datos tras la auditoría (fases 0 a 5, hasta marzo de 2027) | Fase 0 para revisar y publicada en Render (`docs/plan-datos-fase-0.md`) |
| 5 | Experiencia de cliente y restaurante: más simple, clara y estética en el celular; que el cliente se arregle solo (recuperar contraseña por email, entrar con el email, registro más corto) | Después de la respuesta de Marcel |

Todas las etapas pasan a la revisión de Marcel (`docs/para-marcel.md`).

**Etapa 3 (Guardian).** Usa estas variables de entorno, cargadas según el instructivo que tiene Ramón:

- `GUARDIAN_URL`
- `GUARDIAN_POLICY_ID`
- `GUARDIAN_PROPONENTE_EMAIL` y `GUARDIAN_PROPONENTE_PASSWORD`
- `GUARDIAN_R001_EMAIL` y `GUARDIAN_R001_PASSWORD`

El MGS hace el login con `POST /accounts/loginByEmail`. Detalle de la API en `docs/guardian/analisis-policy-flw.md`.

Antes de escribir código, leé `docs/guardian/respuestas-api-mgs.md`, que trae lo que cambia el diseño:

- **Tokens:** el access token dura 60 s, así que el login se hace una vez por usuario y después solo se renueva el token.
- **Privacidad:** el mint publica los documentos de origen en IPFS, así que a Guardian van solo códigos seudónimos.
- **Versión nueva de la policy:** cada usuario vuelve a elegir su rol, salvo que se use la migración.
- **Dry Run:** no sirve para probar el login de varios usuarios.

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

**Reporte mensual (decisiones de Ramón, 06/10).** Un reporte por restaurante por mes. Lo revisa una persona de Eggologic, y la app lo manda como el restaurante y lo aprueba como Proponente, lo que mintea FGET. Las tCO2e usan un factor provisorio hasta que CarboSur dé el suyo. Detalle en `docs/etapa-3.md`.

**Hosting: Render, planes gratis** (decisiones de Ramón, 06/10). Configuración en `render.yaml`: web y PostgreSQL gratis. Sin cron (los reportes se mandan con el botón **Enviar al registro** de Reportes) y sin disco: las fotos de los retiros se guardan en la base (`captura/almacen.py`). En línea en https://eggologic.onrender.com desde el 06/10. **Desde el 13/10 Render publica la rama `main`**: todo lo que entra ahí sale en línea, así que se entra por PR con los tests en verde. La contraseña SMTP (`DJANGO_EMAIL_SMTP_PASSWORD`) está en el grupo `eggologic-guardian`. Ramón decidió pagar la base cerca del vencimiento, antes del 04/11. **La base gratis vence el 04/11/2026**: antes hay que pasarla a pago o exportar un respaldo. El primer admin lo crea `build.sh` con `crear_admin`. Las credenciales de Guardian van en el grupo de variables `eggologic-guardian` del panel, nunca en el repo. Pasos y cómo pasar a pago en `docs/etapa-3.md`.

**Plan de datos (decisiones de Ramón, 07/10).** El pesaje se hace en la planta, con una balanza DingQi DQEH01301 de plataforma de 300 kg. El chofer anota solo el restaurante y la cantidad de bultos, y sigue sacando la foto. Los bultos son cajones de leche de 2,2 kg vacíos: la tara es la cantidad de cajones por 2,2 kg. La base de Render pasa a un plan pago antes del 04/11/2026. En la app, la revisión de Eggologic se dice "revisado"; "verificado" queda para la verificación externa (UNIT).

**Respuestas a Marcel (decisiones de Ramón, 12/10).**
- Durante el piloto sigue la policy actual: FGET en tCO2e. La v2 por kg, con Eggos, llega cuando CarboSur dé sus factores.
- Mientras tanto, en la pantalla FGET se presenta como Eggos. Al migrar a la v2 se hace un mint compensatorio; la custodia es de Eggologic. La cifra de Eggos que ve el restaurante se calcula por kg en la app, no es el saldo de FGET en tCO2e, y el mint compensatorio usa ese número (Ramón, 12/10).
- El CIN queda para después del piloto (Nivel D).
- La dirección de envío se pide al hacer el primer pedido, no en el registro.
- Mails: dominio `eggologic.org`, casilla `info@eggologic.org` en Google Workspace. Kit se usa para campañas; falta elegir el servicio de mails transaccionales.
- Se esperan 5 restaurantes en los próximos meses: las credenciales de Guardian siguen en variables de entorno.
- Marcel decide la rama `main` con PRs y el login con usuario o email.

**En uso real desde el 14/10.** Primer retiro real de El Popu cargado por el chofer y clasificado por la planta. La web pasó a un plan pago de Render el 14/10 (en el gratis no salía el SMTP a Gmail) y la recuperación de contraseña funciona. Mañana (15/10): larvas (lotes BSF), granja y entregas de huevos a clientes.

**Pendientes (14/10).** Los PR #1, #2 y #4 de Marcel (login con email, recuperar contraseña, dirección en el primer pedido) entraron a `main` el 14/10. Prioridad de Ramón: registrar los retiros de El Popu y las entregas de huevos a El Popu y a otra clienta.
- **Pantalla "Registrar entrega"** para administración u operador: cliente o restaurante, producto, cantidad, fecha y forma de pago; queda como pedido entregado. Hoy un pedido solo lo crea el comprador desde la tienda, y desde el admin no se pueden cargar.
- **Arreglo de la tienda para restaurantes:** desde los PR de Marcel, un restaurante que entra a la tienda da error 500 (falta importar `Cliente`, y la redirección no contempla restaurantes).
- Falta la migración de `Cliente` (`telefono` y `direccion` opcionales), y hay 2 tests desactualizados (registro y `crear_admin`).
- Login con email: error 500 si dos usuarios comparten email. Registro con un email ya usado: error 500.
- **Pregunta abierta (Ramón, 14/10): ¿chofer y planta necesitan identidad (DID) en Guardian?** Hoy no: a Guardian solo va el reporte mensual por restaurante (usuario R-001) aprobado por el Proponente, y quién midió queda en la app. Firmar cada retiro con la identidad de quien lo midió sería un cambio de la policy (v2): decidir con CarboSur y Marcel.
- **Pregunta abierta (Ramón, 14/10): ¿cada retiro a Guardian el mismo día, o el reporte mensual?** Hoy van por mes y por restaurante (un mint por reporte). Registrar cada retiro sería un cambio de diseño, probablemente una policy v2 que acepte registros sin mintear. Decidir con Marcel y CarboSur.
- **Identidades en Guardian (16/10):** Standard Registry (`Eggologic_Standard`), Proponente, VVB (CarboSur), R-001 y, según Ramón, chofer y planta (creados el 16/10 para firmar por separado). La policy actual no tiene un rol para chofer ni planta: hasta que la v2 lo agregue, sus identidades no pueden firmar nada.
- **Decisión de Ramón (16/10): el envío a Guardian pasa a ser diario y automático.** A definir antes de programarlo: si se mantiene la revisión humana (P-5) o se reemplaza por alertas; cada envío mintea FGET, y un día de un restaurante puede dar tan pocas tCO2e que el mint redondee a cero según los decimales del token; el automático corre como Cron Job de Render con `guardian_enviar`.
- Usuarios en línea (14/10): `chofer`, `planta`, `granja`, `carbosur`, `ClienteTest1`, `ramon` e `info@eggologic.org`. `ramon` e `info@` comparten email: cambiar el de `ramon`. Falta el usuario Restaurante de El Popu.
- Mientras no exista la Fase 1: el chofer carga en kg el neto pesado en planta (bruto − cajones × 2,2 kg), y la planta anota cajones y bruto en observaciones.

**Hallazgos de uso real (Ramón, 24/10, tras dos semanas usando la app).** Decisiones:
1. **Guardian diario y automático, todos los días a las 18:00** (hora de Montevideo). Se reporta todo, aunque algún dato salga mal: los errores se corrigen con un reporte de corrección, nunca editando el original. Ramón no encontró en la app dónde se enviaba a mano.
2. **Retiro por bultos:** el chofer pesa de a un cajón (dos bolsas por cajón). Carga cada bulto con su peso, la app los suma, y al final saca una sola foto de todo y envía el retiro.
3. **Clasificación en planta con kg y foto:** la planta pesa kg de restos vegetales, de residuos de plato y de impropios, sube una foto y envía.
4. **Producción de huevos por período** (por ejemplo, del 1 al 30 de octubre, o 15 días), no por día. Ramón elige el período.
5. **Varios lotes de larva por período:** al cargar la producción del período se eligen los lotes que alimentaron a las gallinas.

**Restaurantes nuevos (resolución temporal, 06/10).** Se cargan en la app desde el primer día; el usuario en Guardian se crea cuando entran en serio al piloto, con el alta solo con el código. Mientras tanto sus meses esperan en **Reportes**. No habrá restaurantes nuevos antes del 19/10.
