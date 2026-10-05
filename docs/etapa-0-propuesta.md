# Etapa 0 — Propuesta aprobada: stack, estructura y modelo de datos

- **Aprobada:** 05/10/2026, con los ajustes de Ramón que se listan abajo.
- **Base:** el [Plano de arquitectura](https://claude.ai/artifact/Fg1DT7HeNYqL5CmuaAiVad), el prompt maestro y el [análisis de la policy FLW](guardian/analisis-policy-flw.md).

Lo marcado **SUPUESTO** espera confirmación.

## Decisiones de Ramón (05/10)

1. **Solo FLW Standard.** La policy EWD-RB del Apex 2026 fue para el hackathon y no se usa.
2. **Tokens nuevos**, creados desde la cuenta nueva de Guardian al publicar la policy FLW.
3. **Sin gemelo digital por ahora.** Lo más simple posible: los datos de la granja se cargan en la app.
4. **Roles en Guardian:** lo que más se ajuste al FLW Standard (ver abajo).
5. **Marcel revisa todo junto al final**, no en cada etapa.
6. **La venta de huevos entra antes del 19/10**, junto con el sector de usuarios (comprar huevos y ver el impacto, con gráficas).
7. Django, sin modo offline, una identidad de Guardian por fuente: aprobados.

## Stack

| Pieza | Decisión |
| --- | --- |
| Lenguaje y framework | Python 3.11 o más nuevo, Django 5.2 LTS |
| Interfaz | HTML renderizado en el servidor, CSS propio, pensado primero para el celular. Sin app nativa ni modo offline |
| Base de datos | PostgreSQL en el servidor; SQLite para correr local |
| Guardian | Cada registro se guarda primero en la base y entra a una bandeja de salida; un comando por cron lo envía y reintenta (etapa de Guardian) |
| Secretos | `.env` + `.env.example`, nunca en el repo |
| Dependencias | Django, python-dotenv y psycopg. `requests` se suma en la etapa de Guardian; una librería de gráficas, en la de usuarios |

## Datos que se capturan

| Quién | Qué | En la app |
| --- | --- | --- |
| Chofer | Residuo levantado en cada restaurante (kg) | `Retiro` |
| Chofer o planta | Clasificación del retiro: impropios, restos vegetales (cáscaras, etc.) y residuos de plato (kg) | `Retiro` |
| Planta BSF | Bandejas generadas y neonatos utilizados (g) | `Lote` |
| Planta BSF | Rendimiento del lote: larvas y frass (kg) | `Lote`, al cosechar |
| Granja | Huevos producidos y larvas usadas para alimentar a las gallinas (kg) | `RegistroGranja` |
| Restaurante (opcional) | Lo que no entra a Eggologic: línea de base para CarboSur (kg) | `Retiro` |

La línea de base no estaba en tu lista, pero el plano y el prompt dicen que no se puede agregar después. Por eso quedó como un dato **opcional** en cada retiro (SUPUESTO). Si CarboSur ya no la necesita, se saca.

## Cómo se alinea con el FLW Standard

El FLW Standard pide que cada inventario declare su alcance: período, tipo de material, destino y límites. Los datos de arriba lo cubren así (SUPUESTO; lo valida CarboSur):

- **Período:** la fecha de cada retiro.
- **Tipo de material:**
  - restos vegetales ≈ partes no comestibles asociadas;
  - residuos de plato ≈ alimento;
  - impropios: no son pérdida ni desperdicio de alimentos, y quedan fuera del inventario.
- **Destino:** alimento animal (larva BSF para gallinas). El frass se registra aparte.
- **Límites:** cada restaurante es una entidad, en la etapa de consumo, en Maldonado.

**Roles en Guardian.** El FLW Standard se reporta por entidad, cada una con su propio inventario. Lo más fiel es dejar a cada restaurante como **entidad participante (rol PPE)** con su propia identidad, que es como ya viene la policy FLW del hackathon. Eggologic queda como Proponente, y CarboSur ocupa el VVB como revisión interna en la Fase A. No se usan Groups.

## Estructura de carpetas

```text
Eggologic_APP/
├── manage.py
├── requirements.txt
├── .env.example
├── eggologic/     # configuración del proyecto Django
├── cuentas/       # usuarios, roles y restaurantes
├── captura/       # retiros, lotes BSF y granja; exportación para CarboSur
├── templates/
├── static/
└── docs/
```

En las próximas etapas se suman `tienda/` (pedidos), `impacto/` (gráficas para usuarios) y `guardian/` (registro verificable).

## Etapas

| Etapa | Qué incluye | Estado |
| --- | --- | --- |
| 1 | Captura: usuarios y roles, retiros, lotes BSF, granja, panel, exportación CSV | Lista, para revisar |
| 2 | Sector de usuarios: tienda de huevos (pedidos) e impacto interactivo con gráficas para clientes y restaurantes | Propuesta |
| 3 | Guardian: policy FLW en la cuenta nueva, envío de reportes por restaurante, tokens nuevos en testnet | Propuesta |
| 4 | Entregables ANDE: circuito trazable, línea de base, informe Fase 1 | Propuesta |

SUPUESTO: la tienda va antes que Guardian porque no depende de nada externo. Guardian necesita la cuenta, la policy instalada y habilitar la red.

## Cuenta de Guardian: cómo pasármela

Nunca por el chat. Se cargan como variables de entorno en la configuración del entorno cloud (menú del entorno en la barra de título de la sesión → Edit), y una sesión nueva las toma:

| Variable | Qué es |
| --- | --- |
| `GUARDIAN_URL` | URL de la API, p. ej. `https://guardianservice.app/api/v1` |
| `GUARDIAN_POLICY_ID` | ID de la policy FLW publicada |
| `GUARDIAN_PROPONENTE_EMAIL` / `GUARDIAN_PROPONENTE_PASSWORD` | Usuario de Eggologic como Proponente |

Para cada restaurante se suma un par email/contraseña de su usuario PPE. Los nombres se definen en esa etapa.

En la misma pantalla, en **Network access**, hay que permitir `guardianservice.app` y `testnet.mirrornode.hedera.com`. Los pasos están en <https://code.claude.com/docs/en/cloud-environments#network-access>.
