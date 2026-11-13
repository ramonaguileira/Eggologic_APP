# Plan de trabajo: planillas de contabilidad y huevos (13/11/2026)

Sale del análisis de dos planillas de Ramón:

- `EGGOLOGIC_Contabilidad_07-10-26_v14` (contabilidad);
- `Control_de_huevos_Camino_Verde_corregido` (huevos y reparto del 10% a las chicas).

Las planillas no se editan desde acá: Ramón pega las correcciones. Lo que sí se construye es la parte de la app.

## Etapas

| Etapa | Qué | Quién | Estado |
| --- | --- | --- | --- |
| A | Corregir fórmulas y datos de la contabilidad | Ramón pega; Claude entrega las fórmulas | **Hecha (este doc)** |
| B | Completar y ordenar datos de las dos planillas | Ramón | Pendiente |
| C | Reparto del 10% a las chicas dentro de la app (producción de huevos por período) | Claude | Espera respuestas de Ramón |
| D | Pendientes ya anotados en `CLAUDE.md` (Registrar entrega, tienda de restaurantes, migración de `Cliente`, emails duplicados) | Claude | Después de C, o antes si Ramón prefiere |

Cada etapa termina con un checkpoint y se frena hasta que Ramón diga cómo seguir.

## Etapa A: correcciones a la contabilidad

**Causa raíz:** la hoja Egresos creció (el total pasó de la fila 139 a la 169) y varias hojas siguen apuntando a las filas viejas.

### A1. Punto de Equilibrio (hoy dice "−0,88 meses")

| Celda | Hoy | Poner |
| --- | --- | --- |
| `C6` | `='💸 Egresos'!H139` | `='💸 Egresos'!H169` |
| `C7` | `='💸 Egresos'!H155` | `='💸 Egresos'!H185` |
| `C8` | `='💸 Egresos'!H156` | `='💸 Egresos'!H186` |

Con esto:
- egresos acumulados dan 790.311 en vez de 2.500;
- la inversión neta a recuperar da unos 759.781;
- el resultado operativo (`C12 = ventas − OPEX`) da unos −185.880.

### A2. Resumen Locales (tres totales distintos)

Todas las fórmulas usan `$4:$138`. Cambiar a `$4:$168`, igual que el Dashboard (`Ctrl+H`, buscar `$138`, reemplazar por `$168`, solo en esa hoja).

Además:
- `D5` (sin asignar) → `='💸 Egresos'!$H$169-B5`. Así lo que no tiene local (hoy las filas 144 a 151) aparece, en vez de perderse.
- Agregar "Planta BSF" como local, o reasignar esa fila (la 140, balanza de 3.951) a un local existente. Hoy no está en ninguna columna.

### A3. Dashboard: separar ventas de aportes

El "RESULTADO NETO" de 81.176 mezcla los 840.957 de aportes del inversor con las ventas.

- `B5`: renombrar a "INGRESOS (con aportes)".
- Agregar una tarjeta "VENTAS" con `='💰 Ingresos'!H53-'💰 Ingresos'!H61` (30.530).
- `D6` (resultado): `=(B6-F6)-C6`, y titularlo "RESULTADO SIN APORTES". Da −759.781.
- Opcional: dejar el resultado actual como "Caja generada", porque sirve para ver cuánto del capital queda.

### A4. Egresos: filas sin clasificar o mal clasificadas

| Fila | Concepto | Problema | Propuesta (SUPUESTO, Ramón confirma) |
| --- | --- | --- | --- |
| 141 | 8 bolsas comida 2 cascarillas (4.200) | Categoría Infraestructura, CAPEX | Alimentación/Insumos, OPEX |
| 142 | Nafta (4.000) | CAPEX | OPEX |
| 143 | Aporte UTE oct (4.000) | CAPEX | OPEX |
| 144 a 151 | Compras de octubre y noviembre | Sin local ni CAPEX/OPEX | Completar local y OPEX |
| 150 y 151 | Nafta 14/11 y huevos de reventa 15/11 | Fecha futura; la 151 sin estado "Pagado" | Corregir fecha o pasar a Presupuestado |
| 145 | Compras Meval 21 bolsas comida (14.500) | Sin local | Completar |
| 135 (dos filas) | Número repetido | El `#` está duplicado | Renumerar |

Con las 8 filas clasificadas, CAPEX + OPEX debería sumar 790.311 (hoy faltan 26.590).

### A5. Supuestos del punto de equilibrio

- Precio por docena: 280 contra unos 160 reales (4 quincenas = 640). Cargar el precio real.
- Gallinas en postura: 150 (supuesto). El Dashboard cuenta 176 aves, pero la mayoría todavía es recría.
- La nota de `Plantel Proyectado!B24` dice que se satura en julio. Los datos dicen noviembre (faltan 9 plazas) y diciembre (faltan 59). Actualizar el texto.

### A6. Saldo en caja −41.583

Es el único problema que no se arregla con una fórmula. La Caja arranca con saldo inicial 0, y un saldo negativo puede querer decir:
- que faltan ingresos cargados en Caja, o
- que se pagaron gastos con plata de otro bolsillo.

Hay que revisar movimiento por movimiento contra el banco o el efectivo.

Lo que se ve en la planilla (13/11): la Caja tiene 156 movimientos y el último es del 07/10, mientras que Ingresos y Egresos llegan a noviembre. Sus egresos suman 905.070, más que los 786.211 pagados en la hoja Egresos. Falta cargar lo posterior al 07/10 y conciliar la diferencia.

## Etapa B: datos a completar

- Control de huevos, septiembre: faltan datos del 1 al 10/09 y el 25/09. Si fueron días sin producción, cargar `0`; si no, completarlos.
- Regla: `0` = no hubo huevos, vacío = no se cargó.
- Control de huevos: ocultar o limpiar el estado "Retiraron de más" en los meses futuros.
- Clientes: cargar contacto de Carlos Chapuis (falta).

## Etapa C: reparto del 10% a las chicas en la app

**Qué existe hoy:** `RegistroGranja` guarda un registro por día con `huevos` y `kg_larvas`. No sabe quién se llevó los huevos ni tiene el concepto de "las chicas".

**Qué falta** para reemplazar la planilla de huevos:

- por período (la decisión del 24/10): huevos cosechados, retirados por Ramón, retirados por las chicas y descartados;
- saldo acumulado del 10%, con el arrastre entre períodos;
- aviso cuando las chicas retiraron de más.

**Decisiones de Ramón (13/11):**

- Las chicas son Ashley y Fiorella, de Camino Verde. El 10% es un **pago en especie**.
- El período lo elige Ramón cada vez.
- La planilla de huevos **se sigue llevando**: es lo que usan con las chicas. La app se conecta a la planilla, no la reemplaza.

**Propuesta de diseño (SUPUESTO, Ramón corrige):**

1. Un modelo nuevo `PeriodoHuevos` con desde, hasta, cosechados, retira Ramón, retiran las chicas y descartados. Validación: lo retirado más lo descartado no puede superar lo cosechado.
2. **Conexión con la planilla:** un botón "Traer de la planilla" que lee la planilla en modo lectura (exportación CSV de la hoja compartida) y suma los días del período elegido. La app **no escribe** en la planilla.
   - Sin dependencias nuevas ni claves de Google.
   - Si la planilla cambia de forma, falla con un mensaje claro y se cargan los números a mano.
   - Alternativa más pesada: la API de Google con cuenta de servicio, que necesita una clave en variables de entorno. Solo si hace falta escribir.
3. La tasa del 10% vive en un solo lugar (`impacto/calculos.py`).
4. El saldo se calcula, no se guarda: 10% de lo cosechado de todos los períodos, menos lo retirado por las chicas.
5. El saldo se ve en la pantalla de granja, solo para operador y administración.
6. **Privacidad:** los nombres de Ashley y Fiorella quedan solo en la base de la app. A Guardian y a "Mi impacto" no va ningún nombre.
7. **Impacto (SUPUESTO):** lo que se llevan las chicas cuenta dentro de la producción total de huevos, pero **no** como huevos vendidos o entregados a clientes, ni genera Eggos. En el informe del circuito aparece como línea aparte, "pago en especie".

## Etapa D: pendientes de la app (ya anotados)

En el orden de prioridad de Ramón (14/10):

1. Pantalla "Registrar entrega".
2. Arreglo de la tienda para restaurantes (error 500).
3. Migración de `Cliente` (`telefono` y `direccion` opcionales) y los 2 tests desactualizados.
4. Email duplicado en login y registro (error 500).

## Riesgos

- **Datos personales:** la planilla de contabilidad tiene nombres, WhatsApp y zonas de clientes. Si se migran a la app, quedan solo en la base de la app.
- **Las planillas son de Ramón:** no se editan sin que él las pegue.
- **Render publica `main`:** todo cambio de la app entra por PR con los tests en verde.
