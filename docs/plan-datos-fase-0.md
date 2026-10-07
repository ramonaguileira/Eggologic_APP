# Plan de datos — Fase 0: ajustes rápidos

- **Fecha:** 07/10/2026
- **Estado:** para revisar. Hecha en la rama `claude/eggologic-dapp-architecture-2duov2`. Todavía no está en Render (ver "Preguntas").
- **Base:** la auditoría de datos y el plan de implementación (docs de Claude que tiene Ramón). La Fase 0 no agrega datos nuevos: corrige lo que la auditoría encontró y es rápido de arreglar.

## Decisiones de Ramón (07/10)

1. **El pesaje se hace en la planta**, con balanza. El chofer anota solo el restaurante y la cantidad de bultos. Esto cambia la Fase 1, no la Fase 0.
2. **Balanza:** DingQi DQEH01301, de plataforma, 300 kg. Faltan su resolución, el certificado de calibración y la tara de la bolsa (Fase 1).
3. **Render:** la base pasa a un plan pago antes del 04/11/2026. El cambio se hace en el panel de Render; el código no cambia.

## Qué se hizo

1. **"Revisado" en lugar de "verificado"** (principio P-5 de la auditoría). "Verificado" queda para la verificación externa (UNIT, ISO 14064-3).
   - El botón **Verificar** de Reportes pasa a ser **Dar por revisado**. El estado "en cola" se muestra como "Revisado, por enviar".
   - Los campos `verificado_por` y `verificado_en` pasan a `revisado_por` y `revisado_en`. La migración `guardian/0003_revisado.py` los renombra sin perder datos.
   - El informe del circuito dice **"Estado de aseguramiento: no verificado por un tercero"**.
   - Los docs que describen la pantalla (README, CLAUDE.md, para-marcel, demo-19-10) usan la palabra nueva. `etapa-3.md` lleva una nota al principio.
   - "Registro verificable" sigue igual: es el nombre del registro en Hedera, no un estado del dato.
2. **Exportación por período y restaurante.** En el panel, la sección "Exportar para CarboSur" tiene desde, hasta y restaurante, y un botón por archivo. El informe ofrece los tres CSV del período que muestra.
   - **Retiros:** por fecha (día local de Montevideo) y por restaurante.
   - **Lotes:** los que empezaron en el período. Con un restaurante, los lotes donde entró residuo suyo.
   - **Granja:** solo por fecha.
   - Sin filtros sale todo el historial, como antes.
   - El nombre del archivo dice qué tiene adentro, por ejemplo `retiros_2026-09-01_2026-09-30_R-001.csv`.
3. **La hora con su zona.** Las fechas con hora salen como `2026-09-01 11:00-03:00`.
4. **Textos protegidos contra fórmulas de Excel.** Un nombre u observación que empieza con `=`, `+`, `-`, `@`, tabulador o retorno sale con un apóstrofo adelante.
5. **Lotes protegidos.** Un lote con retiros o con registros de granja no se puede borrar, tampoco desde la administración de Django. Antes se borraba y los retiros quedaban sueltos, sin rastro del lote. Migración `captura/0004_lotes_protegidos.py`.
6. **Dos errores que encontró la auditoría:**
   - **El informe con un período daba error 500 en Render.** Había dos funciones `_fecha` en `captura/views.py`, y la segunda (la del CSV) tapaba a la primera. Ahora son `_leer_fecha` y `_celda_fecha`.
   - **`cargar_demo` fallaba** desde que los productos pasaron a ser dos (Quincena y Maple). Los pedidos de prueba usan esos dos.

**Quedó afuera** (es de las fases siguientes): el pesaje con tara y neto, el estado de cada dato, las correcciones con historial, los datos del generador, los factores de emisión y el informe FLW.

## Cómo correrlo

```bash
python manage.py migrate        # aplica guardian/0003 y captura/0004
python manage.py cargar_demo --password "<contraseña de prueba>"
python manage.py runserver
```

- **Exportar:** entrar como `carbosur` u `operador` → **Panel** → "Exportar para CarboSur" → elegir fechas y restaurante → tocar el archivo.
- **Informe:** **Informe** → elegir el período → **Ver**. Abajo del formulario están los tres CSV de ese período.
- **Reportes:** entrar como `admin` → **Reportes**. Dice "Por revisar", "Dar por revisado" y "Revisados".

En Render, `build.sh` corre las migraciones en cada publicación.

## Tests

`python manage.py test`: **93 tests, todos pasan.** `makemigrations --check` no encuentra cambios pendientes.

Nuevos:

- `captura.tests.FaseCeroTests`:
  - el informe acepta un período (el error 500);
  - retiros por período y restaurante, con un retiro a las 22:30 del último día;
  - sin filtros sale todo;
  - el código del restaurante no puede meter texto en el nombre del archivo;
  - lotes por restaurante;
  - granja solo por fecha;
  - texto que parece fórmula;
  - lote con retiros o granja que no se puede borrar.
- `captura.tests.CargarDemoTests`: `cargar_demo` corre entero y crea un usuario de cada rol.
- `guardian.tests`: la pantalla Reportes dice "Revisado" y no "Verificado". Los tests anteriores usan los nombres nuevos.

También se probó en el navegador, con los datos de `cargar_demo`:

- la exportación de setiembre de R-001 bajó 15 retiros, con la hora y la zona;
- el informe con período abrió bien, con el estado de aseguramiento;
- no hubo errores de JavaScript.

## SUPUESTOS

1. **Formato de la hora:** ISO con la zona (`2026-09-01 11:00-03:00`). Excel la muestra como texto, pero no se presta a confusión.
2. **Lotes protegidos:** el plan decía "un lote cosechado". Se protege cualquier lote con retiros o registros de granja, porque borrar uno en curso también rompe la trazabilidad. Un lote vacío se puede borrar.
3. **Lotes por restaurante:** el archivo muestra el lote completo, con los retiros de todos los restaurantes que entraron. No reparte la cosecha por restaurante.
4. **Granja:** se filtra solo por fecha. Es una sola para todos los restaurantes.
5. **Restaurante en la dirección:** el código solo admite letras, números y guiones. Cualquier otro carácter se descarta.

## Puntos para Marcel

- `guardian/migrations/0003_revisado.py` está escrita a mano: dos `RenameField` y un `AlterField` de los `choices`. Conviene mirar que en PostgreSQL renombre la columna y no la recree.
- `captura/views.py`: `_filtros`, `_nombre_archivo` y `_texto`. La lista de caracteres de `_texto` sigue la recomendación de OWASP sobre CSV injection.
- `exportar_lotes` con restaurante usa `.distinct()`, porque un lote puede tener varios retiros del mismo restaurante.
- `on_delete=PROTECT` en `Retiro.lote` y `RegistroGranja.lote`: borrar un lote con datos levanta `ProtectedError`. Hoy la app no tiene un botón para borrar lotes; solo la administración de Django.

## Preguntas

1. **Pasar la Fase 0 a Render.** Render publica la rama `claude/peaceful-bardeen-4k285s`: lo que entra ahí sale en línea solo. La Fase 0 está en esta rama, que ya tiene todo lo de Render. Para publicarla hay dos caminos:
   - unir esta rama a `claude/peaceful-bardeen-4k285s`, desde GitHub o pidiéndomelo;
   - cambiar en Render la rama que se publica.

   El error del informe está hoy en línea, así que conviene publicarla antes del 19/10.
2. **Fase 1:** ¿el chofer sigue sacando la foto del retiro, o la foto pasa al pesaje en la planta?
3. **Fase 1:** ¿qué bolsa o contenedor se usa, y cuánto pesa vacío? Con eso se calcula la tara.
