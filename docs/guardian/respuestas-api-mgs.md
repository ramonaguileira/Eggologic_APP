# Guardian y MGS: respuestas para la Etapa 3

- **Fecha:** 06/10/2026
- **Origen:** preguntas preparadas para la community call de Guardian. Ramón trajo las respuestas, investigadas en la documentación oficial y en el código de `hashgraph/guardian` (rama main).
- **Verificado en el código** (06/10/2026): la duración de los tokens y el VP público del mint.
- **Sin publicar:** lo propio de MGS no está documentado y queda como pregunta para soporte de MGS (sección 6).

## 1. Qué cambia para Eggologic

1. **Login.** Una vez por usuario custodial. Después, se pide un access token antes de cada operación. Nunca un login por request.
2. **Privacidad.** Al mintear, Guardian publica un VP con los documentos de origen completos. A Guardian solo van códigos seudónimos (`R-001`) y, si hace falta, un hash con sal del registro de la app.
3. **Versión nueva de la policy (v2).** La v2 es otra policy: cada usuario vuelve a elegir su rol, salvo que se use la migración oficial. Los usuarios de Guardian no se recrean.
4. **CIN.** El NFT no lleva metadata propia. Los datos del certificado van en el VC/VP, y el NFT apunta a ellos.
5. **Dry Run.** Sirve para probar payloads, flujo y cálculos, pero no el login de varios usuarios a la vez. Eso se prueba en testnet.

## 2. Versión nueva de la policy

- Las cuentas viven en el tenant y en el Standard Registry, no en la policy. El Proponente y los restaurantes no se registran de nuevo.
- Cada policy publicada tiene sus propios roles y su propio topic. En la v2, cada usuario vuelve a elegir su rol.
- La migración oficial se llama **Live Project Data Migration**:
  - pasa VPs, VCs, roles, grupos, tokens y estado de bloques entre policies o versiones;
  - funciona con policies publicadas y en Dry Run, y se puede reintentar.
- Si se renombran los tokens, son tokens nuevos de Hedera. Los saldos del token viejo no se convierten.
- Guardian permite **parámetros editables sin republicar** (Policy Configurator → "Parameter Settings"). Conviene usarlos para el factor kg → Eggos de la v2. Hay que confirmar que la versión de Guardian de MGS lo tenga.

## 3. Autenticación del backend

Flujo:

1. `POST /api/v1/accounts/loginByEmail` devuelve el `refreshToken`.
2. `POST /api/v1/accounts/access-token`, con ese `refreshToken`, devuelve el `accessToken`.
3. Cada llamada lleva `Authorization: Bearer <accessToken>`.

Duración por defecto, según `auth-service/src/utils/user-access-token.ts`:

| Token | Duración | Constante |
| --- | --- | --- |
| Access | 60 segundos | `ACCESS_TOKEN_UPDATE_INTERVAL = '60000'` |
| Refresh | 30 días | `REFRESH_TOKEN_UPDATE_INTERVAL = '2592000000'` |

Las dos se configuran por variable de entorno, así que MGS puede usar otros valores. Al implementar, leer `expireAt` del JWT en lugar de suponerlo.

Reglas para la app:

- Guardar el refresh token de cada usuario. Dónde se guarda (base o caché) se decide en la Etapa 3.
- Pedir un access token nuevo antes de cada operación, o reintentar ante un 401.
- Cada login crea otro refresh token, y los anteriores siguen válidos. Por eso no se hace login en cada request.
- Las cuentas custodiales no pueden tener MFA: el login pediría un código y el backend quedaría bloqueado.
- El API gateway open-source no limita la tasa de llamadas, pero MGS no publica sus límites. El backend hace backoff ante 429 y 5xx y envía las llamadas de a una por usuario.

## 4. Privacidad

- `sendToGuardianBlock` con `dataSource: hedera` publica el VC completo en IPFS (ver H5 en `analisis-policy-flw.md`).
- Hay **VC cifrado** (Selective Disclosure, "Encrypted Verifiable Credential"):
  - los campos privados se publican cifrados con AES-GCM y se quitan de los VPs;
  - en MGS, la clave la tiene MGS, porque las cuentas son custodiales.
- Con `dataSource: database`, el documento queda solo en la base de Guardian, pero pierde el anclaje público.
- **La trampa, verificada en `policy-engine/blocks/mint-block.ts`:** al mintear, Guardian arma un VP con `[...documents, mintVC]` y lo publica en IPFS (`sendToIPFS: true`). Los documentos de origen quedan públicos aunque se hayan guardado solo en base. La excepción es usar un VC de reporte (`reportVC`), que reemplaza los documentos por referencias.

Decisión para la app:

- A Guardian van solo códigos seudónimos y cantidades.
- Opcional: un hash con sal del registro de la app, para demostrar integridad sin exponer datos.
- Los datos personales quedan en la base de Django.
- El VC cifrado se usa solo si aparece un dato sensible que tenga que estar en Guardian, y antes se prueba en Dry Run.

## 5. Cálculo por kg, Eggos y CIN (para la v2)

Flujo: informe (VC con kg) → aprobación del VVB → `customLogicBlock` → `mintDocumentBlock` (Eggos) → `mintDocumentBlock` (CIN).

- **Cálculo:** el `customLogicBlock` (JavaScript o Python) lee el `credentialSubject`, calcula y devuelve un VC nuevo con el schema de salida:
  ```js
  const cs = documents[0].document.credentialSubject[0];
  done({ ...cs, eggos: Number(cs.kg_procesados) * FACTOR });
  ```
- **Mint de Eggos (fungible):**
  - la regla del mint es `eggos`;
  - mathjs la evalúa en cada documento y suma los resultados;
  - el total se multiplica por 10^decimales y se redondea según el método elegido.
- **Mint del CIN (NFT):**
  - segundo `mintDocumentBlock` con regla `1`: un serial por documento;
  - si entran varios documentos, salen varios NFTs;
  - el bloque de mint pasa los documentos al siguiente, así que se pueden encadenar los dos (confirmar en Dry Run).
- **Metadata del NFT:** Guardian no permite metadata propia. Cada serial lleva el ID del mensaje del VP (su timestamp de consenso). Se rastrea así: NFT → mensaje del topic → IPFS. Una metadata estilo HIP-412, con imagen o JSON propio, exigiría mintear fuera de Guardian, y eso queda afuera porque la app no escribe a Hedera directo.

## 6. Dry Run y plan de prueba de MGS

- En Dry Run, documentos, transacciones y archivos quedan en la base local. No hay fees ni nada va a Hedera o IPFS.
- Todo se maneja por API:
  - `PUT /policies/{id}/dry-run`;
  - `POST .../dry-run/user` crea usuarios virtuales;
  - `POST .../dry-run/login` cambia de usuario;
  - `POST .../dry-run/restart` reinicia;
  - más los endpoints para ver transacciones, artefactos e IPFS.
- **Límite:** el Standard Registry actúa como un usuario virtual a la vez, y va cambiando de usuario. Dry Run no prueba el login de varios usuarios custodiales: eso se prueba en testnet.
- **Cupo:** el tenant de prueba muestra "2 policies en ejecución". Si Dry Run cuenta para ese límite, la v1 y la v2 ya lo llenan. El orden práctico sería:
  1. probar la v2 en Dry Run;
  2. migrar;
  3. discontinuar la v1.

## 7. Preguntas para soporte de MGS

1. ¿Cuánto duran el access token y el refresh token en MGS?
2. ¿Qué límites de tasa tiene el API?
3. ¿Una policy en Dry Run cuenta para el límite de 2 policies en ejecución?
4. ¿Quién paga los fees de testnet del tenant?
5. ¿Qué versión de Guardian corre MGS 1.6.1? Sirve para confirmar los parámetros editables y la migración.

## Fuentes

- [Live Project Data Migration](https://guardian.hedera.com/docs/develop/guardian/platform/live-project-data-migration.md) · [Migration Reference](https://guardian.hedera.com/docs/develop/guardian/platform/live-project-data-migration/live-project-data-migration-ui.md) · [Discontinuing Policy](https://guardian.hedera.com/docs/develop/guardian/workspace/policies/discontinuing-policy-workflow/user-guide.md)
- [Editing Policy Parameters at Runtime](https://guardian.hedera.com/docs/develop/guardian/workspace/policies/5539-editing-policy-parameters-at-runtime.md)
- [Handbook, cap. 23: API Integration](https://docs.hedera.com/guardian/methodology-digitization/methodology-digitization-handbook/part-6/chapter-23)
- Código de autenticación: [user-access-token.ts](https://github.com/hashgraph/guardian/blob/main/auth-service/src/utils/user-access-token.ts) · [account-service.ts](https://github.com/hashgraph/guardian/blob/main/auth-service/src/api/account-service.ts) · [api-gateway app.ts](https://github.com/hashgraph/guardian/blob/main/api-gateway/src/app.ts)
- [sendToGuardianBlock](https://guardian.hedera.com/docs/develop/guardian/workspace/policies/policy-creation/introduction/send-workflow-block.md) · [Selective Disclosure Reference](https://guardian.hedera.com/docs/develop/security-identity-and-privacy/selective-disclosure/selective-disclosure-reference.md)
- [mintDocumentBlock](https://guardian.hedera.com/docs/develop/guardian/workspace/policies/policy-creation/introduction/mintdocumentblock.md) · [customLogicBlock](https://guardian.hedera.com/docs/develop/guardian/workspace/policies/policy-creation/introduction/customlogicblock.md)
- Código del mint: [mint-block.ts](https://github.com/hashgraph/guardian/blob/main/policy-service/src/policy-engine/blocks/mint-block.ts) · [mint-service.ts](https://github.com/hashgraph/guardian/blob/main/policy-service/src/policy-engine/mint/mint-service.ts) · [utils.ts](https://github.com/hashgraph/guardian/blob/main/policy-service/src/policy-engine/helpers/utils.ts) · [custom-logic-block.ts](https://github.com/hashgraph/guardian/blob/main/policy-service/src/policy-engine/blocks/custom-logic-block.ts)
- [Guardian FAQs](https://guardian.hedera.com/docs/develop/community-and-contributing/faqs) (metadata del NFT = ID del mensaje del VP)
- [Dry Run Mode](https://guardian.hedera.com/docs/develop/guardian/workspace/policies/dry-run/demo-guide-on-dry-run-operations.md) · [Dry Run Virtual Users](https://guardian.hedera.com/docs/develop/guardian/workspace/policies/dry-run/3642-dry-run-virtual-users.md)
