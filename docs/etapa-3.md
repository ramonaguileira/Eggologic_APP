# Etapa 3 — Guardian

- **Fecha:** 05/10/2026
- **Estado:** en curso. La conexión con Guardian está verificada. El envío de reportes espera las respuestas de la sección "Preguntas".

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

## Hallazgos

### 1. R-001 figura en Guardian con su nombre comercial

El formulario de alta del restaurante (`create_new_ppe`) se completó con el nombre comercial y el tipo "Restaurante", no con `R-001`.

- Ese documento ya está publicado en IPFS y en un topic de Hedera, y no se puede borrar.
- La policy no deja corregir un alta aprobada. Si el Proponente la revoca, vuelve a "esperando aprobación" con el mismo documento.
- Para registrarlo como `R-001` habría que crear otro usuario de Guardian para el restaurante.

Los reportes del restaurante no van a llevar el nombre en ningún caso: solo el código.

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

### 3. Cada reporte del restaurante exige tCO2e

En el schema "Ground Entity Report by PPE" estos campos son obligatorios:

- `field3`: emisiones de la línea de base;
- `field5`: emisiones del proyecto;
- `field6`: fugas;
- `field7`: reducción neta.

Los cuatro van en tCO2e. `field7` es lo que se mintea en FGET cuando el Proponente verifica el reporte.

La policy publicada es la del hackathon sin cambios: no calcula nada (H1 del análisis) y FGET queda medido en tCO2e (H2). CarboSur todavía no dio factores, y la Etapa 2 dejó las emisiones afuera a propósito.

## SUPUESTOS

1. Las credenciales de cada restaurante se llaman `GUARDIAN_<código sin guion>_EMAIL` y `_PASSWORD` (`R-001` → `GUARDIAN_R001_…`), como las que cargó Ramón.

## Preguntas para Ramón

1. **Alta de R-001.** ¿Se deja como está o se crea otro usuario de Guardian registrado como `R-001`? Recomendación: dejarla, porque el documento ya es público y no se borra. Desde ahora, cada alta se hace solo con el código.
2. **Proyecto.** ¿Cargás el Project Description vos desde MGS? Recomendación: sí. Es una sola vez y no necesita código. Antes te paso la lista de datos para cada campo, sin datos personales. Después lo acepta el Standard Registry, el Proponente le asigna el VVB y el VVB lo valida.
3. **tCO2e.** Hasta que CarboSur dé los factores, ¿qué se manda en esos campos?
   - a) Un factor provisorio en `impacto/calculos.py`, marcado SUPUESTO. Permite mostrar el mint en la demo, pero el número es inventado y queda en un registro público, aunque sea testnet.
   - b) Adaptar la policy para que calcule y mintee por kg (`customLogicBlock`) y volver a publicarla. Es lo que recomienda el análisis, pero lleva trabajo en Guardian y crea tokens nuevos otra vez.
   - c) Mandar 0 y no mintear hasta tener los factores. Hay que probar si Guardian acepta un mint de 0.

   Recomendación: a) para la demo del 19/10, si tenés un factor de referencia (del doc de julio o del brief VM0046), y b) después.
4. **Frecuencia.** ¿Un reporte por retiro, o uno por restaurante por mes? Recomendación: uno por mes. Es como el FLW Standard pide el inventario (por período), y cada reporte necesita una verificación del Proponente.
5. **Verificación.** ¿Quién verifica los reportes? Recomendación: una persona de Eggologic, con un botón en la app. La app llama a Guardian como Proponente. Así la verificación no es automática.

## Cómo correrlo

```bash
python manage.py guardian_estado
```

Usa las variables de entorno de Guardian (ver `.env.example`) y los restaurantes activos de la base.

## Tests

`python manage.py test` corre 56 tests. Los 12 nuevos usan un Guardian falso, sin red, y cubren:

- login y sesión;
- envío a un bloque por tag;
- que la contraseña no aparezca en los errores;
- variables faltantes y error de conexión;
- el comando completo: testnet, alta, código público y proyecto.
