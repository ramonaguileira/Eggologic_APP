# Etapa 0 — Propuesta de stack, estructura y modelo de datos

- **Fecha:** 05/10/2026
- **Estado:** borrador para aprobar. Todavía no leí el repo del gemelo digital (no tengo acceso), así que la integración con él es preliminar.
- **Base:**
  - el [Plano de arquitectura](https://claude.ai/artifact/Fg1DT7HeNYqL5CmuaAiVad) (fuente de verdad);
  - el prompt maestro;
  - el [análisis de la policy FLW](guardian/analisis-policy-flw.md) (los H1–H9 que se citan abajo son sus hallazgos);
  - el repo del Apex 2026, `ramonaguileira/EggoLogic-Hedera-Hackathon`.

Lo marcado **SUPUESTO** espera confirmación.

## 1. Qué existe hoy

| Pieza | Dónde | Qué aporta | Cómo la usamos |
| --- | --- | --- | --- |
| Gemelo digital: lote de gallinas, nueve agentes, Shared Farm State (`farm_state_manager.py`) | **No lo encontré** entre tus repos de GitHub | Streams de Camino Verde (Nivel A): alimentación, sanitario con períodos de retiro, recolección de huevos, larvas consumidas. Interlock de inventario | Se integra, no se reconstruye (sección 5) |
| Policy EWD-RB v0.3 (Apex 2026) | `EggoLogic-Hedera-Hackathon/guardian/` | 8 schemas propios de Eggologic (proveedor, entrega de residuo, lote, producción, cálculo de impacto, registros de VVB, validación y emisión) y los cálculos de entrega | Base de los registros de captura y de los reportes de las fuentes |
| Dashboard del Apex | `EggoLogic-Hedera-Hackathon/dashboard/` | HTML + JS que habla con Guardian (MGS) desde el navegador, con el login de cada rol | Se reutiliza su lógica, no su arquitectura: con custodia de claves, las credenciales de Guardian no pueden estar en el navegador |
| Policy FLW Standard del hackathon de 2024 | Repo de Guardian | Dos niveles de reporte, dos tokens, informe principal con los términos de VM0046 | La que el plano manda adaptar (Etapa 2) |
| Cuenta nueva de Guardian (MGS, tier gratuito) | — | Donde se instala la policy | Etapa 2 |

### Tres hallazgos que cambian supuestos del plano y del prompt

1. **Los tokens "existentes" no los va a poder usar la cuenta nueva** (H7).
   - El plano y el prompt citan `0.0.8291816`/`0.0.8291820`, que salen del pitch deck.
   - El repo del Apex y sus registros de mint usan otro par: `0.0.8287358`/`0.0.8287362`.
   - Ese repo dice que se perdió el acceso a la cuenta Standard Registry que los creó, y Guardian solo mintea tokens creados desde la misma cuenta.
   - Resultado: la cuenta nueva va a crear tokens nuevos al publicar la policy.
2. **El plano no menciona EWD-RB.** Manda adaptar la policy FLW de 2024, que no calcula nada: las tCO2e se cargan a mano (H1). La EWD-RB propia ya modela el circuito de Eggologic y calcula.
   - **Propuesta:** seguir el plano, con la FLW como estructura de la policy y como placeholder del informe principal de CarboSur.
   - Pero los reportes de cada fuente se arman con los schemas de EWD-RB. Así no se reconstruye lo que existe.
3. **Groups no tiene precedente canónico** (H4). VM0042 y PWRM0001 tienen `policyGroups` vacío. El rol de entidad participante que ya trae la policy FLW alcanza para sumar fuentes sin re-registrar la policy.

## 2. Stack

| Pieza | Propuesta | Por qué |
| --- | --- | --- |
| Lenguaje | Python, la misma versión que el gemelo (SUPUESTO: 3.12) | El gemelo es Python, así que la integración es directa y Marcel lee un solo lenguaje |
| Framework | Django 5.2 LTS | Trae, sin sumar dependencias, lo que el piloto necesita: usuarios y permisos, panel de administración, formularios con validación, migraciones y tests. Es lo más convencional en Python |
| Interfaz | HTML renderizado en el servidor (templates de Django) y CSS simple, sin framework de JS | Un solo código para revisar, sin paso de build; funciona en el celular |
| Base de datos | PostgreSQL; SQLite para correr local | Estándar y gratis |
| Web o mobile | Web responsive, mobile-first en las pantallas de captura. Sin app nativa ni modo offline en Fase A (SUPUESTO) | Lo de Camino Verde ya lo captura el gemelo. Lo nuevo (retiros en restaurantes, planta BSF) es urbano. Si hace falta offline, se agrega después |
| Guardian | Módulo propio con `requests`. Cada registro se guarda primero en la base y entra a una bandeja de salida. Un comando (`python manage.py enviar_a_guardian`, por cron) lo envía y reintenta | La captura no se pierde si Guardian está lento o caído, y queda registro de qué se envió y qué respondió |
| Secretos | `.env` + `.env.example` | Regla del prompt |
| Tests | El runner de Django | Sin dependencias extra |

**Dependencias:** cuatro en total: Django, psycopg, requests y python-dotenv.

**Descartados:**

- Next.js/React con una API aparte: dos códigos, el ecosistema npm para revisar, y no se integra directo con el gemelo en Python.
- React Native/Expo (el doc de julio): obliga a distribuir una app y suma un código; no hace falta para la Fase A.
- Extender el dashboard del Apex: ver la tabla de la sección 1.

## 3. Estructura de carpetas

```text
Eggologic_APP/
├── manage.py
├── requirements.txt
├── .env.example
├── eggologic/          # configuración del proyecto Django (settings, urls)
├── cuentas/            # usuarios, roles y perfiles (Cliente, Restaurante)
├── captura/            # registros de campo: entregas de residuo, línea de base, planta BSF
├── gemelo/             # adaptador de solo lectura al gemelo digital (único punto de contacto)
├── guardian/           # cliente de la API, armado de documentos por schema, bandeja de salida
│   └── informe_principal/   # placeholder del schema de CarboSur, aislado para reemplazarlo
├── entregables/        # dashboard de entregables ANDE (Etapa 4)
├── comercial/          # productos, pedidos, inventario y certificados, cuando toque
└── docs/
```

Cada app sigue la estructura estándar de Django: `models.py`, `views.py`, `forms.py`, `admin.py`, `tests.py` y `templates/`.

## 4. Modelo de datos

Principios:

- **Un solo esquema para las tres fuentes.** Todo registro de campo comparte los mismos campos de cabecera: `id` (UUID), fuente, tipo de registro, cuándo ocurrió, cuándo y quién lo registró, evidencia y estado de envío a Guardian. Encima van los campos propios de cada stream.
- **Lo que ya captura el gemelo no se duplica:** se lee a través de `gemelo/`.
- **Trazabilidad por IDs:** entrega de residuo → lote BSF → envío de larva → lote de gallinas (gemelo) → recolección de huevos (gemelo) → pedido.
- **Los datos personales quedan solo en la base de la app.** A Guardian van IDs seudónimos, porque lo que se registra ahí queda público en IPFS (H5).

| Entidad | Qué es | Campos clave | Etapa · Nivel |
| --- | --- | --- | --- |
| Usuario | Un login por persona o comercio | email, rol (admin, cliente, restaurante, operador, CarboSur) | 1 |
| Restaurante | Aportante y comprador: es la fuente "Restaurantes aportantes" de Guardian | nombre comercial; razón social y contacto (privados); código seudónimo para Guardian; tipo (restaurante, catering…) | 1 · B |
| Cliente | Consumidor final | tier (Compra individual, Sostenedor, Regenerador, Guardián) y contacto (privado) | 1 (el tier es un dato, sin lógica de incentivos) |
| EntregaResiduo | Cada retiro en un restaurante o entrega de un cliente (equivale al Waste Delivery de EWD-RB) | aportante (restaurante o cliente); etiqueta del tacho; kg bruto e impropios; kg netos y ajustados (calculados); categoría A/B/R; corriente (pre-consumo, post-consumo, café, otra, con carne, lácteos y grasas por separado, como pide el brief de VM0046); confirmación del aportante; foto; GPS (SUPUESTO); mecanismo para clientes, retiro o punto de entrega (SUPUESTO) | 1 · B |
| LineaBaseResiduo | Los kg que **no** entran a Eggologic, desde el día uno | aportante; período o entrega asociada; kg; destino actual (recolección municipal, relleno…); método (pesado o estimado); evidencia | 1 · B |
| LoteBSF | Bioconversión (equivale al Waste Batch) | entregas incluidas con los kg asignados; ruta (BSF o compost); bandejas de 15 kg; kg recibidos y procesados; apertura y cierre | 1 · B |
| RegistroCriaBSF | Ciclo de la colonia | reproducción, cosecha de huevos BSF, neonatos, larva separada para incubar | 1 · B |
| ProduccionLote | Salida de un lote (equivale al Production Output) | larva, frass y compost en kg | 1 · B |
| EnvioLarva | Larva que va de la planta a Camino Verde | lote BSF, kg, fecha, lote de gallinas destino (ID del gemelo) | 1 · B |
| (datos del gemelo) | Lote de gallinas, alimentación, sanitario y retiros, recolección, larvas consumidas | se leen del gemelo, no se copian | 1 · A |
| EnvioGuardian | Bandeja de salida | registro de origen, tag del bloque, documento enviado, estado, respuesta, referencia en HCS | 2 |
| InformePrincipal | Placeholder del informe de CarboSur (schema genérico de la policy FLW) | período, actividades, resultado | 2 → 3 |
| Producto, Pedido, MovimientoInventario | Venta de huevos | el inventario se ata al lote de gallinas y respeta el interlock del gemelo | después de la Etapa 4 (SUPUESTO) |
| Certificado | Reducción de Residuos y Zero Waste | criterio y cadencia a definir | a definir |
| Eggos, CIN, cuentas Hedera por participante | Nivel D | solo queda el lugar previsto | — |

## 5. Integración

### Gemelo digital (pendiente de leer el código)

Propuesta preliminar:

- Todo pasa por `gemelo/`, que lee el Shared Farm State a través de `farm_state_manager` y nunca escribe.
- Antes de cualquier movimiento de inventario, consulta el interlock.

Cómo se conecta depende de dónde corre el gemelo:

- si corre en el mismo servidor, se importa `farm_state_manager` como librería;
- si corre en otra máquina, el gemelo expone su estado (un endpoint o un export periódico) y la app lo lee.

### Guardian (cuenta nueva en MGS)

- **Autenticación:** la app usa `POST /accounts/loginByEmail`, como el dashboard del Apex.
- **Envíos:** por tag de bloque (SUPUESTO). Es la misma API que pide el prompt, pero el tag no cambia entre versiones de la policy.
- **Custodia:**
  - una identidad de Guardian por fuente (Camino Verde, cada restaurante, Planta BSF), administrada por Eggologic;
  - las credenciales van en `.env` mientras sean pocas (SUPUESTO; la alternativa está en H6);
  - el restaurante entra a la app con un solo login, y la app firma en Guardian con su identidad.
- **Tokens:** la Etapa 2 prueba el mint del token de incentivo en testnet, como plomería. La emisión del CIN no se dispara (Nivel D).

### Repo del Apex

Se reutilizan los schemas y cálculos de EWD-RB y lo aprendido de la API de MGS. Su arquitectura no: ahí cada usuario se loguea en Guardian desde el navegador, y con custodia de claves las credenciales quedan en el servidor.

## 6. Plan por etapas

| Etapa | Qué incluye | Checkpoint de Marcel |
| --- | --- | --- |
| 1 | Proyecto Django, usuarios y roles, modelos y formularios de captura (entregas, línea de base, planta BSF, envío de larva), adaptador del gemelo, panel de administración y export CSV para CarboSur | El esquema calza con el gemelo |
| 2 | Cliente de Guardian, bandeja de salida y documentos por schema; primero en dry-run y después en testnet | HCS registra y HTS mintea |
| 3 | Schema de CarboSur en `guardian/informe_principal/` | El informe cumple el FLW Standard |
| 4 | Dashboard de entregables ANDE: circuito trazable, línea de base, informe Fase 1 | Revisión completa antes del 19/10 |

Pedidos, inventario, tiers y certificados no figuran en ninguna etapa del plano, así que van después de la 4, salvo que digas otra cosa. Con 14 días hasta el 19/10, las cuatro etapas ya son ajustadas.

## 7. SUPUESTOS

1. Python + Django 5.2 LTS + PostgreSQL, web responsive, sin modo offline en Fase A.
2. El gemelo es Python y la app puede leerlo (como librería o por un export).
3. Los reportes de las fuentes se basan en los schemas de EWD-RB. La policy FLW aporta la estructura y el placeholder del informe principal.
4. Rol de entidad participante en vez de Groups para la Fase A.
5. Una identidad de Guardian por fuente, con las credenciales en `.env`.
6. Envío por tag de bloque en vez de por UUID.
7. El factor 0,70 y los umbrales A/B/R de EWD-RB quedan como placeholder hasta que CarboSur defina.
8. Línea de base: un registro por aportante y período (o por entrega), con método pesado o estimado.
9. Pedidos, inventario y certificados van después de la Etapa 4.
10. En el código, los nombres del dominio van en español (`EntregaResiduo`, `LoteBSF`) y lo técnico como lo pide Django. Se ajusta a la convención del gemelo cuando lo vea.

## 8. Para que Marcel revise

- Si Django + PostgreSQL le cierra para mantener.
- La conexión con el gemelo (sección 5) y si el esquema común (sección 4) calza con lo que ya corre.
- Rol de entidad participante vs. Groups, y una identidad de Guardian por fuente (H4 y H6).
- La bandeja de salida con cron, en vez de colas o workers.

## 9. Preguntas para Ramón

1. **¿Dónde está el repo del gemelo digital?** No está entre tus 10 repos de GitHub. Si es de Marcel, necesito acceso o una copia del código.
2. ¿Dónde corre el gemelo: un servidor de Marcel, una máquina en Camino Verde, la nube?
3. ¿Cuál es el par de tokens vigente? ¿Se recuperó la cuenta Standard Registry del Apex?
4. ¿Seguimos el plano (policy FLW, con los schemas de EWD-RB para las fuentes, que es lo que recomiendo) o preferís reinstalar EWD-RB completa en la cuenta nueva? Para eso serviría el export de dry-run de EWD-RB que mencionan los docs del Apex: ¿lo tenés?
5. ¿Los pedidos y la venta de huevos entran antes del 19/10?
6. ¿Dónde alojamos la app para la demo?
7. Para la Etapa 2:
   - URL de la instancia MGS, ID de la policy instalada y quién la está instalando;
   - habilitar en este entorno `guardianservice.app` y `testnet.mirrornode.hedera.com`.
