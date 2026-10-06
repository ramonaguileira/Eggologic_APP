# Etapa 3 — Guardian

- **Fecha:** 05/10/2026
- **Estado:** lista para revisar (06/10). Envío de prueba real hecho en testnet; falta crear los servicios en Render.

## Qué se verificó (05/10)

1. **Variables de entorno.** Están las seis, con el formato esperado. Se miraron los nombres, nunca los valores.
2. **Login.** Los dos usuarios entran con `POST /accounts/loginByEmail` y después `POST /accounts/access-token`. En MGS la respuesta del login viene como `{ "success", "login": { "username", "did", "role", "refreshToken" } }`.
3. **La policy corre en testnet.**
   - Los DID de los usuarios son `did:hedera:testnet:…`.
   - Policy "Food Loss & Waste (International) - 1.0", versión 1.0.0, estado `PUBLISH`.
   - La instancia MGS corre Guardian 3.7.1-rc. El export de 2024 se importó y se publicó sin cambios, así que la pregunta H9 del análisis queda respondida.
   - Topics y tokens confirmados en el mirror node de testnet:

     | Qué | ID |
     | --- | --- |
     | Topic de la policy | `0.0.10879191` |
     | Topic de la instancia | `0.0.10879394` |
     | Token FGET (FoodGHGEntityToken): fungible, 2 decimales, supply 0 | `0.0.10879391` |
     | Token FLW-GET (FLWGHGEmissionToken): fungible, 2 decimales, supply 0 | `0.0.10879393` |

   - Los tokens se crearon al publicar la policy (decisión 2 de la Etapa 0).
   - Las cuentas de los usuarios aceptan tokens sin asociarlos antes (asociaciones automáticas ilimitadas). El mint no necesita un paso extra.
4. **Roles.**
   - `Eggologic_Proponente` tiene el rol Project_Proponent.
   - `Eggologic_r001` tiene el rol Project_Participating_Entity, con el alta aprobada por el Proponente.

## Qué se construyó

- `guardian/cliente.py`:
  - abre la sesión de un usuario de Guardian;
  - lee la policy y los bloques por tag;
  - envía datos a un bloque por tag.

  Las credenciales salen de las variables de entorno y no aparecen nunca en los mensajes de error.
- `python manage.py guardian_estado` repite los chequeos de arriba sin escribir nada en Guardian.
  - Falla si falta una variable, si un usuario no puede entrar, si la red no es testnet, si la policy no está publicada o si un rol no coincide.
  - Avisa, sin fallar, lo que está pendiente: restaurantes sin usuario en Guardian, un alta que no usa el código público, falta de un proyecto validado.
- `requests` en `requirements.txt` (estaba previsto en la Etapa 0).
- **Reporte mensual por restaurante** (06/10, con las decisiones de Ramón de abajo):
  - `guardian/models.py`: `ReporteMensual` guarda los números tal como se verificaron, quién los verificó y en qué paso está el envío;
  - `guardian/reportes.py`: arma el mes con los retiros, decide si se puede verificar, construye el documento para la policy y hace los pasos en Guardian;
  - pantalla **Reportes** (`/registro/reportes/`, solo administración): meses por verificar con sus números y un botón **Verificar** que pide confirmación; abajo, los verificados con su estado;
  - `python manage.py guardian_enviar`: la bandeja de salida prevista en la Etapa 0. Manda lo verificado y reintenta lo que falló; pensado para correr por cron;
  - `impacto/calculos.py`: `emisiones_evitadas()`, el factor provisorio de CO2e.

## Decisiones de Ramón (06/10)

1. Mientras CarboSur no dé factores, las tCO2e salen de un **factor provisorio**, marcado SUPUESTO.
2. **Un reporte por restaurante por mes.**
3. Lo verifica **una persona de Eggologic**.
4. El alta de R-001 **queda como está**, con el nombre comercial. Las altas nuevas van solo con el código.
5. Primer envío real: **un reporte de prueba** (no datos reales).
6. Hosting: **Render**, arrancando con **planes gratis** (06/10).
7. Otros restaurantes: lo propone Claude, como **resolución temporal** (ver "Alta de restaurantes"). Ramón la confirma: **no habrá restaurantes nuevos antes del 19/10**.

## Cómo funciona el reporte mensual

1. **Durante el mes** no cambia nada: el chofer carga retiros y la planta los clasifica.
2. **Cuando el mes termina**, en **Reportes** aparece una fila por restaurante con sus retiros, los kg orgánicos (restos vegetales + residuos de plato) y el CO2e evitado provisorio. Una fila no se puede verificar si:
   - el mes todavía no terminó;
   - hay retiros de ese mes sin clasificar;
   - los kg no llegan a 0,01 tCO2e (unos 29 kg);
   - el restaurante no tiene usuario en Guardian.
3. **Una persona de Eggologic revisa y toca Verificar.** Desde ese momento los números quedan fijos en el reporte, aunque después se corrija un retiro.
4. **`guardian_enviar` hace los dos pasos de la policy:**
   1. como el restaurante (rol PPE), envía el Ground Entity Report, vinculado al proyecto validado;
   2. como Proponente, lo aprueba (`approve_ppe_report_btn`, `Button_0`). Eso mintea FGET por la reducción neta a la cuenta del restaurante.

   Antes de cada paso se fija en Guardian si ya está hecho, así un corte a mitad de camino no duplica nada. Guardian procesa cada envío en segundo plano, así que el reporte recién enviado tarda en aparecerle al Proponente: la aprobación queda para la vuelta siguiente del cron, sin marcarlo como error. Si algo falla de verdad, el reporte queda donde estaba, con el error a la vista en la pantalla, y la próxima vuelta reintenta.

**Qué va a Guardian** (público): el nombre de la actividad con el código y el mes (`Retiros de residuo orgánico R-001 2026-09`), el tipo de actividad, un flujo sin proyecto (restaurante → disposición final) y uno con proyecto (restaurante → alimento animal), los dos con los kg orgánicos del mes, las cuatro cifras de tCO2e y el período. Nunca el nombre, la dirección ni el contacto del restaurante.

**Ejemplo.** Un restaurante con 600 kg orgánicos en setiembre: 600 × 0,70 × 0,5 / 1000 = 0,21 tCO2e evitadas, y se mintean 0,21 FGET a su cuenta.

## Envío de prueba real (06/10)

Con el OK de Ramón se mandó a la policy un reporte de R-001 con datos ficticios, usando las mismas funciones que `guardian_enviar`. Al nombre de la actividad se le agregó el prefijo `PRUEBA ·` desde un script aparte (no está en el código de la app), para que no choque con el reporte real de setiembre: la app busca los reportes por ese nombre.

| Qué | Resultado |
| --- | --- |
| Reporte | "PRUEBA · Retiros de residuo orgánico R-001 2026-09": 600 kg orgánicos, 0,21 tCO2e |
| Vuelta 1 (como restaurante) | Enviado en 2 s. Guardian lo procesó en segundo plano: el Proponente todavía no lo veía |
| Vuelta 2 (como Proponente) | Aprobado en 1 s |
| Registro en HCS | Topic `0.0.10880108`: reporte (`1791251261.916613122`), aprobación (`1791251311.571836104`) y mint (`1791251314.211543374`) |
| Mint | **0,21 FGET** (`0.0.10879391`) en la cuenta de R-001, confirmado en el mirror node de testnet. El supply total de FGET pasó de 0 a 0,21 |

Lo que se aprendió:

- Guardian procesa los envíos en segundo plano. La aprobación no puede ir en la misma vuelta que el envío: queda para la siguiente, y eso ya no se marca como error.
- **La policy deja el reporte original en "Waiting for Verification" aunque ya esté aprobado** (el bloque que aprueba no le cambia el estado). En la interfaz de MGS el Proponente lo sigue viendo como pendiente: **no hay que aprobar reportes desde MGS**, porque se mintearía dos veces. La app se fija en la copia aprobada (`approved_entity_report`) antes de aprobar.

## Hosting en Render

La configuración está en `render.yaml` (Blueprint), `build.sh` y `.python-version`. Arranca con planes gratis (decisión de Ramón):

| Servicio | Plan | Para qué |
| --- | --- | --- |
| `eggologic` (web) | Free | La app |
| `eggologic-db` (PostgreSQL) | Free | La base |

**Límites del plan gratis, a tener en cuenta para la demo:**

- **La base vence a los 30 días de creada.** Antes hay que pasarla a un plan pago o se pierden los datos (hay 14 días de gracia para hacerlo).
- **La web se duerme a los 15 minutos sin uso** y tarda alrededor de un minuto en despertar: conviene abrirla un rato antes de la demo.
- **Sin disco:** los archivos de la web se borran cada vez que se duerme o se redeploya. Por eso **las fotos de los retiros se guardan en la base** (`captura/almacen.py`, decisión de Ramón del 06/10). La base gratis tiene 1 GB: alcanza para cientos de fotos.
- **Sin cron:** los reportes verificados se mandan con el botón **Enviar al registro** de la pantalla Reportes. Hace lo mismo que `guardian_enviar`: si un reporte queda "Enviado, falta la aprobación", se vuelve a tocar en un minuto.
- **Sin consola:** el primer usuario de administración lo crea `build.sh` (comando `crear_admin`) con las variables `DJANGO_SUPERUSER_*`.
- **Diagnóstico en cada deploy:** `build.sh` corre `guardian_estado` (solo lee). El log del deploy muestra si Guardian responde, sin frenar el deploy si falla.

Render da `https` en `eggologic.onrender.com` (o el dominio que asigne), que es lo que necesita el GPS del celular. Región Virginia, la más cercana a Uruguay entre las de Render (SUPUESTO).

**Pasos para crearlo** (los hace Ramón; este entorno no tiene acceso a Render):

1. Mergear la rama a `main` (o elegir esta rama al crear el Blueprint).
2. En Render: **New → Blueprint**, elegir el repo `Eggologic_APP`. Va a pedir `TIENDA_DATOS_TRANSFERENCIA` y los datos del primer usuario de administración: `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD` (una contraseña larga).
3. En **Env Groups → eggologic-guardian**, sumar `GUARDIAN_POLICY_ID`, `GUARDIAN_PROPONENTE_EMAIL`, `GUARDIAN_PROPONENTE_PASSWORD`, `GUARDIAN_R001_EMAIL` y `GUARDIAN_R001_PASSWORD`. Render no pide las variables de un grupo, por eso se cargan a mano. Después, **Manual Deploy** del servicio web para que las tome.
4. Entrar con el usuario de administración y cargar desde la administración el restaurante R-001 (con su nombre real y código `R-001`), los usuarios de chofer y planta, y los productos con sus precios.

**Para pasar a pago** (después de la demo): base basic-256mb (las fotos pueden seguir en la base) y un servicio cron cada 15 minutos que corra `python manage.py guardian_enviar`. Si más adelante se prefieren las fotos en disco: plan Starter en la web, un disco montado en `/var/data`, `DJANGO_MEDIA_ROOT=/var/data/media` y `FileSystemStorage` en `STORAGES["default"]`.

`python manage.py check --deploy` deja tres avisos esperables: la clave secreta local de prueba (Render genera una fuerte), la redirección a https (la hace Render) y HSTS, que conviene activar recién con el dominio definitivo.

## Alta de restaurantes (resolución temporal, 06/10)

Propuesta de Claude, a confirmar:

- **Cada restaurante se carga en la app desde el primer día** (código `R-00X`), y sus retiros se capturan normalmente.
- **Su usuario en Guardian se crea cuando entra en serio al piloto.** Mientras no lo tenga, sus meses quedan en **Reportes** como "Sin usuario en el registro": no se pierde nada. Cuando se crea el usuario, se verifican los meses atrasados, que siguen en la lista.
- **Para la demo del 19/10 alcanza con R-001.** Si hay un segundo restaurante activo, conviene darlo de alta antes, para mostrar que sumar uno no requiere volver a publicar la policy.
- Las credenciales en variables de entorno alcanzan para los pocos restaurantes del piloto. Para muchos restaurantes hará falta otra forma de guardarlas; queda para después.

**Pasos para dar de alta un restaurante en Guardian:**

1. Desde la cuenta de administración del tenant de MGS, invitar un usuario nuevo con un email de Eggologic (un alias tipo `r002@…`), no el del restaurante: Eggologic custodia la cuenta.
2. Darle el rol de permisos `Default policy user` y asignarle la policy.
3. Entrar con ese usuario, elegir el rol `Project_Participating_Entity` y completar el alta **solo con el código** (`R-002`) y el tipo "Restaurante".
4. Con `Eggologic_Proponente`, aprobar el alta.
5. Sumar `GUARDIAN_R002_EMAIL` y `GUARDIAN_R002_PASSWORD` al grupo `eggologic-guardian` de Render (y al entorno de Claude Code, si se va a probar desde acá).
6. Correr `python manage.py guardian_estado`: tiene que mostrar el alta aprobada y sin aviso de nombre.

## Hallazgos

### 1. R-001 figura en Guardian con su nombre comercial

El formulario de alta del restaurante (`create_new_ppe`) se completó con el nombre comercial y el tipo "Restaurante", no con `R-001`.

- Ese documento ya está publicado en IPFS y en un topic de Hedera, y no se puede borrar.
- La policy no deja corregir un alta aprobada. Si el Proponente la revoca, vuelve a "esperando aprobación" con el mismo documento.
- Para registrarlo como `R-001` habría que crear otro usuario de Guardian para el restaurante.

Los reportes del restaurante no van a llevar el nombre en ningún caso: solo el código. Ramón decidió dejar el alta como está (06/10).

### 2. Sin proyecto validado no hay reportes

El botón con el que un restaurante envía su reporte ("Add Entity Ground Report") está en la grilla de proyectos validados, y hoy no hay ningún proyecto. Antes del primer reporte faltan los pasos 5 a 8 del análisis:

| # | Quién | Qué | Tag |
| --- | --- | --- | --- |
| 5 | Proponente | Carga el Project Description | `add_project_bnt` |
| 6 | Standard Registry | Acepta el proyecto | `add_project` |
| 7 | Proponente | Le asigna el VVB | `assign_vvb` |
| 8 | VVB | Valida el proyecto | `approve_project_btn` |

- La app no tiene credenciales del Standard Registry ni del VVB, así que los pasos 6 y 8 se hacen desde la interfaz de MGS.
- El Project Description queda público. Entre los campos obligatorios están dos emails de contacto, nombre y dirección de la organización, coordenadas, metodologías y períodos. Tienen que ser datos de la organización, nunca personales.

**Avance al 06/10.** Ramón hizo los pasos 5 a 8 desde MGS. El proyecto está validado (topic `0.0.10881088`), y R-001 ya lo ve en su grilla: puede enviar reportes.

Datos del Project Description, revisados contra el documento publicado (sin datos personales):

| Campo | Valor |
| --- | --- |
| Project Name | Eggologic · FLW Nodo 1 (Maldonado) |
| Category / Scale | Waste handling and disposal / Small-Scale |
| Activities | Consumption, Transport, Processing, Farm |
| Ubicación | Centro de Maldonado (-34.90, -54.95), sin la dirección de la planta |
| Organización | Lisbor SAS, Maldonado, Uruguay |
| Contacto | "Coordinación Nodo 1", con el email genérico de la organización |
| Inicio y períodos | Inicio 05/10/2026; acreditación y monitoreo del 05/10/2026 al 30/09/2027 |
| Additionality | Sí: sin el proyecto, el residuo va con la basura común a disposición final |
| Methodology, Data Format & Calculations | Vacía a propósito: pide tCO2e a mano (ver hallazgo 3) |

### 3. Cada reporte del restaurante exige tCO2e

En el schema "Ground Entity Report by PPE" estos campos son obligatorios:

- `field3`: emisiones de la línea de base;
- `field5`: emisiones del proyecto;
- `field6`: fugas;
- `field7`: reducción neta.

Los cuatro van en tCO2e. `field7` es lo que se mintea en FGET cuando el Proponente verifica el reporte.

La policy publicada es la del hackathon sin cambios: no calcula nada (H1 del análisis) y FGET queda medido en tCO2e (H2). CarboSur todavía no dio factores, y la Etapa 2 dejó las emisiones afuera a propósito.

Resuelto con un factor provisorio (decisión 1). Las emisiones solo se muestran en la pantalla de administración, marcadas como provisorias; los clientes y restaurantes no las ven.

## SUPUESTOS

1. Las credenciales de cada restaurante se llaman `GUARDIAN_<código sin guion>_EMAIL` y `_PASSWORD` (`R-001` → `GUARDIAN_R001_…`), como las que cargó Ramón.
2. Los períodos de acreditación y monitoreo del proyecto cubren un año de piloto (05/10/2026 a 30/09/2027).
3. Metodología declarada en el proyecto: FLW Standard (FLW Protocol, 2016), con VM0046 de Verra como referencia para la cuantificación. Lo valida CarboSur.
4. **Factor provisorio de CO2e:** kg orgánicos × 0,70 (factor conservador del doc de julio) × 0,5 kg de CO2e por kg que no va a disposición final. Emisiones del proyecto y fugas en 0. Se redondea hacia abajo a 2 decimales, que son los de FGET.
5. En la policy, el restaurante es una actividad de tipo `Consumption`, y el destino sin Eggologic es la disposición final (relleno sanitario).
6. Las masas van en kg húmedos. El schema pide "Dry Matter Content (Mass)" sin unidad; el factor de humedad lo define CarboSur (H8).
7. Hay un solo proyecto validado (Nodo 1), y todos los reportes se vinculan a él.
8. Solo la administración ve **Reportes** y verifica.
9. Un mes se puede verificar recién cuando terminó y con todos sus retiros clasificados. Los meses se cuentan en hora de Montevideo.
10. Render en la región Virginia, con planes gratis para la demo (sin disco ni cron: botón "Enviar al registro").
11. Resolución temporal para restaurantes nuevos: se cargan en la app desde el primer día, y el usuario en Guardian se crea cuando entran en serio al piloto.
12. El usuario de Guardian de cada restaurante usa un email de Eggologic (alias), no el del restaurante.

## Para que Marcel revise (al final)

- `guardian/reportes.py`: `enviar()` y su idempotencia. Antes de cada paso busca el reporte en la grilla de Guardian por el nombre de la actividad (código + mes).
- `guardian/reportes.py`: `documento()`, que es exactamente lo que queda público.
- `impacto/calculos.py`: `emisiones_evitadas()`, el factor provisorio.
- Un caso borde conocido: Guardian procesa los envíos en segundo plano (confirmado en testnet). Si el cron vuelve a correr antes de que el reporte recién enviado aparezca en la grilla del restaurante, y el estado no llegó a guardarse como "enviado" (un corte justo en ese momento), podría enviarlo dos veces. Con el cron cada 15 minutos es muy improbable.
- La policy deja el reporte original en "Waiting for Verification" aun aprobado: `enviar()` se fija en la copia `approved_entity_report` para no aprobar dos veces.
- `eggologic/settings.py`: lo nuevo para producción (WhiteNoise, https detrás del proxy de Render, carpeta de fotos configurable, errores a la consola).
- `cuentas/management/commands/crear_admin.py`: crea el primer administrador en el build, solo si no existe.
- Un retiro de un mes ya verificado se puede seguir editando: el reporte guarda los números verificados, pero la app no avisa la diferencia.
- FGET se mintea por tCO2e provisorias. Si FGET va a ser Eggos, Eggos queda medido en carbono (H2 del análisis): sigue pendiente.

## Preguntas para Ramón

1. **Qué muestra la demo de Guardian.** El 19/10 octubre todavía no terminó, así que no va a haber un reporte mensual real para verificar. Propuesta: mostrar la captura en vivo, la pantalla Reportes con octubre "en curso" y el reporte de prueba de setiembre ya registrado en Hedera, con su mint de FGET.
2. ~~**Fotos en Render gratis**~~ Resuelto: se guardan en la base (06/10).

## Cómo correrlo

```bash
python manage.py guardian_estado   # revisa la conexión, sin escribir nada
python manage.py guardian_enviar   # manda los reportes verificados que falten (por cron)
```

Usan las variables de entorno de Guardian (ver `.env.example`) y la base de la app. La pantalla de verificación está en **Reportes** (`/registro/reportes/`), con un usuario de administración. Con `cargar_demo`, R-001 tiene meses cerrados para probar la verificación. **Ojo:** `guardian_enviar` escribe en el Guardian real si las variables están cargadas.

## Tests

`python manage.py test` corre 71 tests. Los de esta etapa usan un Guardian simulado, sin red, y cubren:

- login y sesión, y que la contraseña no aparezca en los errores;
- variables faltantes y error de conexión;
- `guardian_estado`: testnet, alta, código público y proyecto;
- el factor provisorio y su redondeo;
- qué entra en el mes, y cuándo no se puede verificar (mes en curso, sin clasificar, sin usuario, pocos kg);
- verificar una sola vez, desde la pantalla, y solo con administración; el botón **Enviar al registro**;
- `crear_admin`: crea el administrador una sola vez y solo con las variables;
- que el documento lleve el código y nunca el nombre;
- el envío completo (como restaurante y como Proponente), sin duplicar si se repite, la espera sin error cuando el reporte todavía no aparece, y el error guardado cuando falla.
