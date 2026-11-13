# Larvas y granja: cargar solo lo que se anota

- **Fecha:** 13/11/2026
- **Estado:** para revisar. En la rama `claude/keen-heisenberg-xon3e4` (PR #12); no está en línea.
- **Base:** respuestas de Ramón del 13/11. Después de un mes de uso no había ningún lote ni registro de granja cargado: los formularios pedían más de lo que él anota.

## Qué se hizo

1. **Larvas, una carga por semana** (menú **Larvas**, antes **Lotes**). Pide la fecha, los huevos de larva recibidos en gramos, las bateas armadas y observaciones.
   - Ya no pide elegir los retiros que entran, ni la cosecha (kg de larvas y de frass).
2. **Granja, una carga por período** (menú **Granja**). Pide la granja, desde, hasta, los huevos producidos y observaciones.
   - **Granjas:** Camino Verde e Eguzquiza, donde están las gallinas. Se administran en **Administración → Granjas**.
   - Dos cargas de la misma granja no pueden pisarse en las fechas: los huevos se contarían dos veces.
   - Ya no pide los kg de larvas que comieron las gallinas ni el lote de las larvas.
3. **Panel, informe y "Mi impacto"** muestran lo que ahora se anota: gramos de huevos de larva, bateas armadas y huevos por granja. Se fueron los kg de larvas, el frass, el rendimiento y la trazabilidad por lote.
4. **La lista de retiros** ya no tiene la columna Lote.

**Se pierde por ahora** (decisión de Ramón): saber cuántos kg de larva salieron de cuánto residuo, y qué residuo terminó en qué huevos. El desvío que va a Guardian no cambia, porque sale de los retiros. Los campos viejos quedan en la base, sin uso, para cuando se retome.

**Quedó afuera:** la foto en la clasificación y los Eggos en pantalla.

## Cómo correrlo

```bash
python manage.py migrate        # captura/0007 y 0008
python manage.py cargar_demo --password "<contraseña de prueba>"
python manage.py runserver
```

- **Larvas:** entrar como `planta` u `operador` → **Larvas** → **+ Larvas de la semana**.
- **Granja:** entrar como `granja` u `operador` → **Granja** → **+ Huevos del período**.

## Tests

`python manage.py test`: **114 tests, todos pasan**, en SQLite y en PostgreSQL 16. `makemigrations --check` no encuentra cambios pendientes.

- La migración se probó en PostgreSQL sobre el esquema anterior con un registro de granja viejo: quedó asignado a Camino Verde, como período de un día.
- Probado en Chromium con tamaño de celular: una carga de larvas, una de huevos de Eguzquiza, panel, informe, los CSV y "Mi impacto" de cliente y de restaurante. Sin errores.

## SUPUESTOS

1. **Una carga de larvas por semana** es la costumbre, no una regla: la app no impide cargar dos.
2. **Un período de granja cuenta entero donde cae su último día** (en el panel de 30 días, en el informe y en el CSV).
3. **Los registros de granja anteriores** eran todos de Camino Verde.
4. **Eguzquiza queda activa desde ahora**, aunque todavía no empezó.
5. **Los kg de cada batea no se cargan:** se anota solo la cantidad.
6. **2 kg de larvas por batea** para el número que ven los clientes (dato de Ramón, sin pesar).

## Puntos para Marcel

- `captura/models.py`: modelo `Granja`; `RegistroGranja` gana `granja` y `desde`, y `fecha` pasa a ser el fin del período y deja de ser única. La validación de cargas que se pisan está en `RegistroGranja.clean()`.
- Quedan campos sin uso en las pantallas, marcados con un comentario: `Lote.fecha_cosecha`, `kg_larvas`, `kg_frass`, `Retiro.lote`, `RegistroGranja.kg_larvas` y `lote`. Si preferís sacarlos, es otra migración.
- `impacto/calculos.py`: `factores_del_circuito()` ya no devuelve gramos de larva por huevo; `informe()` devuelve `larvas` y `granjas` en lugar de `lotes`.
- Los CSV conservan las columnas anteriores; `granja.csv` suma `desde` y `granja` al final.

## Preguntas

Respondidas por Ramón el 13/11:

1. **Nombre de la granja:** Eguzquiza (es la ruta que pasa enfrente). También se le puede decir Miramar Acres, por el barrio, o La Nona. El nombre se cambia en **Administración → Granjas**.
2. **"Mi impacto"** sigue mostrando kg de larvas criadas, estimados a 2 kg por batea (`KG_LARVAS_POR_BATEA` en `impacto/calculos.py`).
