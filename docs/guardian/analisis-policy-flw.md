# Análisis de la policy FLW Standard del hackathon para Eggologic

- **Fecha:** 05/10/2026
- **Corresponde a:** primer ítem de "Próximos pasos propios" del [Plano de arquitectura](https://claude.ai/artifact/Fg1DT7HeNYqL5CmuaAiVad): *estudiar a fondo la policy FLW Standard del hackathon (roles, schemas, tokens) y listar qué hay que renombrar/ajustar para Eggologic*.
- **Alimenta:** Etapa 2 (integración con Guardian).
- **Fuente analizada:** `hashgraph/guardian` @ `e585ead1` (17/09/2026), carpeta [`Methodology Library/Community Contributions/2024-Hackathon/Food-Loss-Waste-International-Policy`](https://github.com/hashgraph/guardian/tree/main/Methodology%20Library/Community%20Contributions/2024-Hackathon/Food-Loss-Waste-International-Policy). Se desarmó el export `FWLI001.policy` (policy.json, 10 schemas, 2 tokens) y se contrastó contra el código fuente actual de Guardian.

Convención del plano: lo marcado **SUPUESTO** no está confirmado con Marcel/CarboSur.

## Resumen

1. **La policy no calcula nada.** Las tCO2e las tipea a mano quien reporta, y los tokens se mintean 1:1 sobre ese número. Sirve como plomería (roles, flujo de dos niveles, dos tokens, registro en HCS), pero para Eggologic el cálculo tiene que vivir en la policy (`customLogicBlock`), alimentado con kg medidos.
2. **Riesgo para Eggos.** FGET se mintea en proporción a tCO2e (1 token = 1 tCO2e, 2 decimales). Si Eggos = FGET tal cual, Eggos queda denominado en carbono, que es justo lo que el plano quiere evitar. Además, la misma reducción se tokeniza dos veces (FGET a la entidad y FLW-GET al Proponente), sin conciliación.
3. **El CIN como NFT tiene precedente canónico.** Las policies de Verra en Guardian (VM0042 v2.1 y PWRM0001) mintean tokens **no fungibles** (VCU, WCC) y calculan el monto con `customLogicBlock`.
4. **Corrección al plano (capa Guardian).** VM0042 v2.1 y PWRM0001 usan solo Proponent + VVB (+ Standard Registry como dueño), como dice el plano. Pero **ninguna usa Groups**: `policyGroups` está vacío en ambas. Además, el rol PPE de la policy del hackathon ya permite sumar entidades sin re-registrar la policy.
5. **Privacidad.** Lo que Guardian registra "en Hedera" es el VC completo, subido a IPFS y referenciado desde HCS, no solo un hash. Ningún schema que vaya a Guardian puede llevar datos personales.
6. **Integración.** Se confirmó `POST /api/v1/policies/{policyId}/blocks/{uuid}` y la variante por tag `POST /api/v1/policies/{policyId}/tag/{tag}/blocks` (recomendada: el tag es estable entre versiones, el UUID no). Hay modo **dry-run** para probar el flujo completo sin transacciones reales.

## 1. Qué trae la policy

| Aspecto | FLWI01 (hackathon) |
| --- | --- |
| Nombre | Food Loss & Waste (International) - 1.0 |
| Roles | `OWNER` ("Climate Authority", dueño/registry), `Project_Proponent` (PP), `VVB`, `Project_Participating_Entity` (PPE) |
| Groups | Ninguno (`policyGroups: []`) |
| Tokens | **FGET** (FoodGHGEntityToken) y **FLW-GET** (FLWGHGEmissionToken): fungibles, 2 decimales, supply inicial 0, wipe habilitado, sin KYC ni freeze |
| Topic HCS | Uno dinámico, `Project` (uno por proyecto) |
| Cálculos | Ninguno: no hay `customLogicBlock` ni `calculateContainerBlock` |
| Categorías | GHG emission avoidance · Waste handling and disposal · Small-Scale |
| Versión | Export de abril 2024 (`codeVersion` 1.5.1). Guardian `main` hoy: 3.7.1-rc |

### 1.1 Flujo de punta a punta

| # | Quién | Qué | Tag del bloque | ¿Queda en Hedera? |
| --- | --- | --- | --- | --- |
| 1 | PPE | Se registra (nombre + tipo) | `create_new_ppe` | Sí |
| 2 | PP | Aprueba/rechaza al PPE | `approve_ppe_documents_btn` | Sí |
| 3 | VVB | Se registra | `create_new_vvb` | Sí |
| 4 | OWNER | Aprueba/rechaza al VVB | `approve_documents_btn` | Sí |
| 5 | PP | Crea el proyecto (Project Description) | `add_project_bnt` | Sí |
| 6 | OWNER | Acepta el proyecto | `add_project` | No (solo base de datos) |
| 7 | PP | Asigna VVB al proyecto | `assign_vvb` | No (solo base de datos) |
| 8 | VVB | Valida el proyecto | `approve_project_btn` | Sí |
| 9 | PPE | Envía reporte micro-escala (Ground Entity Report) | `add_entity_report_btn` | Sí |
| 10 | PP | Verifica el reporte → **mint FGET** = `field7` | `approve_ppe_report_btn` → `mint_entity_report_token` | Sí |
| 11 | PP | Envía el informe principal (Main Monitoring Report) | `add_report_bnt` | Sí |
| 12 | VVB | Verifica el informe principal | `approve_report_btn` | Sí |
| 13 | OWNER | **Mint FLW-GET** = `field1` | `mint_token_climate_authority` → `mintToken` | Sí |

Cada PPE ve solo sus propios reportes y tokens (`onlyOwnDocuments: true`); el PP ve los de todos.

### 1.2 Qué captura cada documento

**Ground Entity Report by PPE** (micro-escala → FGET)

| Campo | Contenido |
| --- | --- |
| `field0` | Nombre de la actividad |
| `field1` | Tipo de actividad (Farm, Transport, Storage, Processing, Consumption) |
| `field2` | Flujos FLW de línea de base: origen, destino, ¿hay transporte?, "Dry Matter Content (Mass)" |
| `field3` | Emisiones totales de línea de base (tCO2e), **a mano** |
| `field4` | Flujos FLW de la actividad del proyecto (mismos subcampos) |
| `field5` | Emisiones totales del proyecto (tCO2e), **a mano** |
| `field6` | Fugas (tCO2e), **a mano** |
| `field7` | Reducción neta (tCO2e), **a mano** → **monto del FGET** |
| `field8` | Período (desde/hasta) |

**Main Monitoring Report** (Proponente → FLW-GET)

- `field0`, lista de actividades de reducción, cada una con: origen, destino, tipo de actividad, transporte (distancia, vehículo), masa seca recuperada, emisiones de línea de base del destino, emisiones de línea de base del transporte, emisiones del proyecto por transporte, emisiones del proyecto por energía/materiales, fugas por descartes, fugas por desvío de destinos con valorización, y la reducción total de la actividad.
- `field1`: reducción neta total (tCO2e), **a mano** → **monto del FLW-GET**.
- `field2`: período.

Los términos de `field0` reproducen los componentes de emisión de VM0046. Por eso es una buena base para el informe principal que estructura CarboSur.

**Project Description:** datos básicos del proyecto (nombre, categoría, escala, coordenadas/GeoJSON, organización y contacto del Proponente, metodologías, períodos de acreditación y monitoreo, plan de monitoreo), adicionalidad y una copia embebida del Main Monitoring Report.

**PPE User / VVB User:** solo nombre (y tipo, para PPE).

## 2. Hallazgos que cambian el diseño

### H1. Las tCO2e se cargan a mano

Ningún bloque calcula: el monto de cada mint es literalmente el número que escribió quien reporta. Para un sistema de MRV eso no alcanza. Los restaurantes, Camino Verde y la Planta BSF miden **kg**, no tCO2e.

**Ajuste:** los schemas de captura llevan kg medidos, y la policy calcula en `customLogicBlock`. Mientras no lleguen los factores de CarboSur, se usan placeholders marcados SUPUESTO. Ya hay una lógica definida en el doc de julio *"Flujo Operativo y Arquitectura de App"*:

- neto = bruto − impropios
- ajustado = neto × 0,70 (factor conservador)
- categoría de calidad según % de impropios (Cat A ≤ 5 %)
- bioconversión = bandejas × 15 kg

### H2. FGET está denominado en tCO2e, y hay doble tokenización

- FGET se mintea por `field7` (tCO2e). Si Eggos se construye sobre FGET sin cambios, cada Eggo representa carbono reducido. Eso choca con el plano ("evitar que se lea como un instrumento financiero o un crédito de carbono comercializable").
- La misma reducción se tokeniza dos veces: FGET a la entidad y FLW-GET al Proponente. El informe principal no se arma desde los reportes micro-escala (el propio README lo deja como TODO), así que nada concilia ambos montos.

**Ajuste (SUPUESTO, decisión pendiente del plano):**

- Eggos se mintea por **kg entregado/procesado o por participación**, nunca por tCO2e.
- El único instrumento ligado a reducciones verificadas es el CIN.

### H3. CIN: precedente canónico para NFT

| Policy | Roles propios | Groups | Token | Cálculo |
| --- | --- | --- | --- | --- |
| VM0042 v2.1 (Verra) | Project Proponent, VVB | No | VCU, **no fungible** | 3 `customLogicBlock` |
| PWRM0001 (Verra) | Project_Proponent, VVB | No | WCC, **no fungible** | 2 `customLogicBlock` |
| FLWI01 (hackathon) | PP, VVB, PPE | No | FGET + FLW-GET, fungibles | Ninguno |

**Ajuste (SUPUESTO):** FLW-GET pasa a ser el CIN como NFT: un token por informe verificado, con el período, las tCO2e verificadas y la referencia al informe como metadata. Se retira al redimirse (wipe ya está habilitado en el token), siguiendo ISO 22095-3.

### H4. Groups: corrección y alternativa más simple

- El plano dice que las policies canónicas resuelven múltiples sitios/entidades con **Groups**. En los exports de VM0042 v2.1 y PWRM0001 `policyGroups` está vacío. Groups es una función real y documentada de Guardian (`groupManagerBlock`, grupos *Global* o *Private*, un rol por grupo), pero usarla sería diseño propio, sin precedente canónico.
- El objetivo del plano ("sumar un restaurante o el Nodo 2 sin re-registrar la policy") **ya lo cumple el rol PPE**:
  - una fuente nueva es un usuario nuevo con rol PPE que el Proponente aprueba (pasos 1–2), sin re-publicar nada;
  - cada PPE ve solo sus documentos.
- Groups agrega valor recién si varias personas actúan por la misma entidad (p. ej. varios recolectores de un restaurante) o para aislar Nodo 1 de Nodo 2.

**Recomendación (SUPUESTO, a validar con Marcel):** para Fase A, mantener el rol PPE renombrado como "Fuente". Pasar a Groups en Fase B solo si aparece uno de esos casos.

### H5. Lo que va a Hedera es público (IPFS)

Los bloques `sendToGuardianBlock` con `dataSource: hedera` publican el VC **completo** en IPFS (opción `sendToIPFS`, activa por defecto) y lo referencian desde el topic HCS. Así que no es solo un hash, como asume el plano en la sección "Capa Hedera". El Project Description de la policy, por ejemplo, pide nombre y email del contacto del Proponente.

**Ajuste:**

- Los schemas que van a Guardian llevan IDs seudónimos (código de fuente, ID de entrega, ID de lote).
- Los datos personales (clientes, contactos, ubicación de domicilios) quedan solo en la base de la app.
- Hay que verificar qué opciones de cifrado aplica la instancia MGS.

### H6. A qué cuenta va cada mint, y quién firma

`mintDocumentBlock` decide la cuenta destino así:

- `default`: la cuenta del dueño del documento (quien lo firmó);
- con `accountId`: un campo de tipo cuenta Hedera dentro del documento;
- `custom-value`: una cuenta fija.

Con custodia de claves (recomendado en el plano) hay dos opciones:

| Opción | Cómo | A favor | En contra |
| --- | --- | --- | --- |
| A | Un usuario Guardian (cuenta + DID) por fuente, administrado por Eggologic | Cada fuente firma sus VCs (es lo que pedía el doc de julio: DID del recolector y del operador de planta) | N credenciales que custodiar |
| B | Un usuario de servicio que envía todo, más un campo de cuenta por fuente para dirigir el mint | Simple: una sola sesión | Todos los VCs los firma Eggologic: atribución más débil |

Decisión para Marcel.

### H7. Los tokens del hackathon probablemente no son los que va a mintear Guardian

Guardian crea cada token y guarda sus claves (treasury, admin, supply, wipe…) en su vault al crearlo. Solo puede mintear tokens propios. Si `0.0.8291816` (Eggos) y `0.0.8291820` (CIN) se crearon con el SDK durante Apex 2026 y no desde la cuenta de Guardian actual, la policy adaptada va a crear tokens nuevos al publicarse. No se pudo confirmar contra el mirror node de testnet porque este entorno lo tiene bloqueado.

### H8. Defectos de los schemas a corregir al adaptar

- **PPE User:** el título de `field0` dice "VVB Name" (copiado del schema del VVB).
- **Project Details:** campos que deberían ser texto (nombre de la organización, emails, dirección, fecha de inicio…) están tipados como lista.
- **"Dry Matter Content (Mass)":** no tiene unidad y pide **materia seca**. Los restaurantes pesan masa húmeda, y la conversión necesita un factor de humedad. Lo decide CarboSur.
- **Origen/destino:** son texto libre. Deberían ser listas cerradas con los destinos del FLW Standard; elegirlos es el paso 4 de CarboSur.
- **Falta la categoría de material.** El brief de VM0046 separa corrientes elegibles de las que requieren evaluación aparte: restos de plato, carne, lácteos, grasas.
- **Faltan IDs de trazabilidad:** entrega → lote BSF → plantel → huevos.
- **Falta el campo de kg que no entra a Eggologic** (línea de base), que es instrucción explícita de CarboSur.

### H9. Compatibilidad de versión

El export es de 2024. Lo primero de la Etapa 2 es importarlo en la instancia MGS en modo dry-run y ver si corre sin cambios.

## 3. Qué renombrar y ajustar (checklist para la Etapa 2)

| Hoy (FLWI01) | Propuesta Eggologic | Estado |
| --- | --- | --- |
| `OWNER` "Climate Authority" | Standard Registry = Eggologic SAS | SUPUESTO del plano |
| `Project_Proponent` | Eggologic SAS (operación Nodo 1) | SUPUESTO del plano |
| `VVB` | CarboSur, nombrado como "revisión interna/autoevaluación" (Fase A); VVB externo (Fase B) | Decidido en el plano |
| `Project_Participating_Entity` | "Fuente": Camino Verde, cada restaurante aportante, Planta BSF (y los clientes que entregan residuo, cuando se defina su stream) | Propuesta nueva (H4), validar con Marcel |
| Token FGET | **Eggos**: monto por kg o participación (no tCO2e), mint a la cuenta custodial de la fuente | Decisión pendiente (H2) |
| Token FLW-GET | **CIN** como NFT, uno por informe verificado, retiro al redimir | Decisión pendiente (H3) |
| Ground Entity Report (uno genérico) | Un schema por stream de la tabla de captura del plano: retiro de residuo (restaurante), ciclo BSF (planta), plantel (Camino Verde: alimentación, sanitario, recolección, larvas consumidas). En kg, con IDs de trazabilidad y sin datos personales | Lo define la Etapa 1 |
| tCO2e cargadas a mano | Calculadas en `customLogicBlock`: placeholders (H1) → factores de CarboSur | Etapa 2 → Etapa 3 |
| Origen/destino en texto libre | Listas cerradas con los destinos del FLW Standard | CarboSur |
| Main Monitoring Report | Schema genérico actual como placeholder → schema de CarboSur | Etapa 3 |
| Project Description | Datos del Nodo 1, tipos corregidos, sin datos personales | Etapa 2 |
| Nombre de la policy | p. ej. "Eggologic · FLW Nodo 1 (Maldonado)" | SUPUESTO |

## 4. Puntos de integración para la app (Etapa 2)

Verificado contra el código de Guardian `main` (3.7.1-rc). La instancia MGS puede correr otra versión: antes de programar hay que revisar su Swagger (`/api-docs/v1/`).

**Base:** `https://<instancia>/api/v1`

**Autenticación**

1. `POST /accounts/login` con `{ "username", "password" }` (más `otp` si la cuenta tiene 2FA): devuelve un `refreshToken`.
2. `POST /accounts/access-token` con `{ "refreshToken" }`: devuelve un `accessToken`, que se usa como `Authorization: Bearer <accessToken>`.

**Policy**

| Ruta | Para qué |
| --- | --- |
| `POST /policies/{policyId}/tag/{tag}/blocks` | Enviar datos a un bloque por tag (recomendado) |
| `POST /policies/{policyId}/blocks/{uuid}` | Lo mismo por UUID (la ruta que cita el plano) |
| `GET /policies/{policyId}/tag/{tag}/blocks` | Leer los datos de un bloque (p. ej. una grilla de documentos) |
| `GET /policies/{policyId}/tag-block-map` | Mapa tag → UUID |
| `GET`/`POST /policies/{policyId}/groups` | Listar/activar grupo (solo si se usan Groups) |
| `PUT /policies/{policyId}/dry-run` · `POST …/dry-run/user` · `POST …/dry-run/login` | Dry-run: policy, usuarios virtuales y login sin transacciones reales |

**Formato del body**

- Formularios (`requestVcDocumentBlock`): `{ "document": { …campos del schema… }, "ref": null }`.
- Botones de aprobar/rechazar (`buttonBlock`): `{ "tag": "Button_0", "document": <documento de la grilla> }`. `Button_0` aprueba/verifica y `Button_1` rechaza.

**Tags que usaría la app** (los de la policy actual; cambian si se renombran)

| Acción | Tag | Rol |
| --- | --- | --- |
| Alta de fuente / aprobación | `create_new_ppe` / `approve_ppe_documents_btn` | PPE / PP |
| Enviar reporte de una fuente | `add_entity_report_btn` | PPE |
| Verificar o rechazar ese reporte (dispara el mint del token de incentivo) | `approve_ppe_report_btn` | PP |
| Enviar el informe principal | `add_report_bnt` | PP |
| Verificar el informe principal | `approve_report_btn` | VVB |
| Mintear el token de impacto | `mint_token_climate_authority` | OWNER |

## 5. Preguntas abiertas

**Marcel**

1. ¿Rol PPE renombrado (recomendado para Fase A) o Groups? (H4)
2. Identidades: ¿un usuario Guardian por fuente o un usuario de servicio? (H6)
3. ¿La instancia MGS importa sin errores el export de 2024? (H9)

**CarboSur**

4. Factores para pasar de kg húmedos a tCO2e. ¿Hace falta materia seca? ¿Sigue vigente el factor 0,70 del doc de julio?
5. Destino FLW Standard para residuo → BSF → larva → alimento de gallinas.
6. ¿Qué datos de los restaurantes pueden ser públicos (nombre comercial, ubicación)? (H5)

**Ramón**

7. ¿`0.0.8291816` y `0.0.8291820` se crearon desde la cuenta de Guardian actual o con el SDK? (H7)
8. Base de emisión de Eggos: ¿kg, participación, tier? (H2)
9. URL de la instancia MGS y una cuenta de prueba para la Etapa 2.

## 6. Límites de esta revisión

- Es un análisis estático del export: no se importó en un Guardian, porque no hay instancia accesible desde este entorno.
- No se pudo consultar el mirror node de testnet: la política de red de este entorno lo bloquea.
- La API y el comportamiento de los bloques se verificaron en el código de Guardian `main`, no en la instancia MGS.

## Referencias

**Guardian (`hashgraph/guardian` @ `e585ead1`)**

- Policy analizada: `Methodology Library/Community Contributions/2024-Hackathon/Food-Loss-Waste-International-Policy/FWLI001.policy` y su `README.md`.
- Comparación de roles, groups y tokens:
  - `Methodology Library/Verra/Verified Carbon Standard (VCS)/VM0042/VM0042 V2.1/VM0042 V2.1.policy`
  - `Methodology Library/Verra/Plastic Waste Reduction Standard (PWRM)/PWRM0001/PWRM0001.policy`
- Otra policy de pérdida y desperdicio del mismo hackathon (con un token por etapa de la cadena), solo como referencia: `Methodology Library/Community Contributions/2024-Hackathon/Sector-Specific-Food-Loss-Waste-GHG-Reduction-Policy/SSFLWGRP001.policy`.
- Groups: `docs/guardian/workspace/policies/roles-and-groups.md`.
- API:
  - `api-gateway/src/api/service/policy.ts`
  - `api-gateway/src/api/service/account.ts`
  - `web-proxy/configs/default.conf` (prefijo `/api/v1/`, Swagger en `/api-docs/v1/`)
- Bloques:
  - `policy-service/src/policy-engine/blocks/mint-block.ts`
  - `policy-service/src/policy-engine/blocks/request-vc-document-block.ts`
  - `policy-service/src/policy-engine/blocks/button-block.ts`
- IPFS y tokens:
  - `common/src/hedera-modules/message/message-server.ts`
  - `guardian-service/src/api/token.service.ts`

**Documentos de Eggologic (Drive)**

- *Eggologic - Flujo Operativo y Arquitectura de App* (07/2026)
- *Eggologic – VM0046 & BSF Technical Eligibility Brief* (08/2026)
