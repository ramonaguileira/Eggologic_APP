# Etapa 1 — Captura de datos de campo

- **Fecha:** 05/10/2026
- **Estado:** lista para revisar.

## Qué se construyó

- **Usuarios y roles** (`cuentas/`):
  - roles: administración, operador de campo, restaurante, cliente y CarboSur (solo lectura);
  - restaurantes con un código público (`R-001`), que es lo único que va a salir de la app; nombre, contacto y dirección quedan en la base.
- **Retiros** (`captura/`): kg levantados por el chofer y su clasificación (impropios, restos vegetales, residuos de plato).
  - La clasificación se carga al levantar o después, en la planta.
  - Hay que completar los tres campos juntos, y no pueden sumar más que lo levantado.
- **Lotes BSF:** retiros clasificados que entran, bandejas generadas, neonatos (g) y, al cosechar, larvas y frass (kg).
  - Calcula los kg de residuo del lote y el rendimiento (kg de larva cada 100 kg de residuo).
- **Granja:** un registro por día con huevos producidos y kg de larvas usadas, y opcionalmente el lote del que salieron.
- **Panel:**
  - totales de los últimos 30 días;
  - retiros sin clasificar y lotes en curso;
  - accesos rápidos para cargar.
- **Exportación para CarboSur:** `retiros.csv`, `lotes.csv` y `granja.csv`, listos para Excel en español.
- **Administración:** todo se puede ver y corregir desde `/admin/`.
- **Datos de ejemplo:** `python manage.py cargar_demo` carga tres semanas ficticias para probar.

## Qué quedó afuera a propósito

- Fotos y GPS de los retiros: suman dependencias y almacenamiento. Se agregan si hacen falta.
- Gemelo digital, tienda, impacto para usuarios y Guardian: son otras etapas.

## Cómo correrlo

Ver la sección "Correr la app en tu computadora" del [README](../README.md).

## Tests

`python manage.py test` corre 23 tests:

- roles y permisos;
- validaciones de retiros, lotes y granja;
- asignación de retiros a lotes;
- cálculo del rendimiento;
- carga de un retiro desde la pantalla;
- totales del panel;
- formato del CSV.

## SUPUESTOS

1. Un solo rol "operador" para chofer, planta y granja.
2. La clasificación (impropios, vegetales, plato) puede sumar menos que lo levantado (merma), pero nunca más.
3. Un retiro entra entero a un solo lote.
4. Los neonatos se miden en gramos.
5. La granja tiene un registro por día.
6. La línea de base (kg que no entran a Eggologic) se informa, opcional, en cada retiro.
7. Equivalencias con el FLW Standard: restos vegetales ≈ partes no comestibles, residuos de plato ≈ alimento, destino = alimento animal. Lo valida CarboSur.
8. El CSV usa punto y coma, coma decimal y UTF-8 con BOM, pensado para Excel en español.

## Para que Marcel revise (al final)

- `captura/models.py`: modelos y validaciones. Es el corazón de esta etapa.
- `captura/forms.py`: `LoteForm.save()` asigna y libera retiros.
- `cuentas/permisos.py`: el control de acceso por rol.
- `captura/views.py`: el panel y la exportación CSV.
