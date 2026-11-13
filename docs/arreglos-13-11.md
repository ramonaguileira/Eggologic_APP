# Arreglos tras el estudio de la app (etapa A)

- **Fecha:** 13/11/2026
- **Estado:** para revisar. En la rama `claude/keen-heisenberg-xon3e4`; no está en `main` ni en línea.
- **Base:** el estudio de la app del 12/11 y el reporte del panel de Render y de la app en línea del 12/11.

## Qué se hizo

1. **CarboSur ya no puede marcar pedidos como entregados.** Los pedidos de todos los ve y los entrega quien tiene el permiso nuevo `puede_gestionar_pedidos` (administración y operador). El menú **Pedidos** sale por ese permiso y no por el tilde `is_staff`.
2. **Errores 500 corregidos:**
   - `/primera-entrega/` para quien no es cliente (faltaba importar `Cliente`);
   - marcar un pedido sin permiso (faltaba importar `Http404`); ahora responde 403;
   - login con un email que comparten dos usuarios: entra aquel cuya contraseña coincide.
3. **Restaurante en la tienda.** Ya no se le crea un perfil de cliente ni se le pide la dirección: el pedido propone la que cargó Eggologic.
4. **`crear_admin`** vuelve a usar `DJANGO_SUPERUSER_USERNAME`; si no está, usa el email.
5. **Migración `cuentas/0005`:** teléfono y dirección del cliente opcionales. No cambia la base, solo pone al día el historial de migraciones.
6. **Traba del envío a Guardian.** Cada reporte queda tomado mientras se envía: dos toques al botón, o el botón junto con el comando, no aprueban dos veces. El envío sigue siendo mensual y manual (decisión de Ramón, 13/11).
7. **Fotos más livianas.** El celular achica la foto del retiro antes de mandarla (lado máximo de 1.600 px). Si falla, manda la original.
8. **`render.yaml`** dice los planes pagos que están en el panel.
9. **Tests automáticos en cada PR** (`.github/workflows/tests.yml`): corre los tests y revisa que no falten migraciones. Es una propuesta para Marcel.

**Quedó afuera:** registrar entrega, retiro por bultos, clasificación con foto, granja por período y Eggos en pantalla (etapas siguientes). La app de clientes nueva queda para después, a diseñar con Marcel.

## Cómo correrlo

```bash
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Tests

`python manage.py test`: **101 tests, todos pasan**, en SQLite y en PostgreSQL 16. `makemigrations --check` no encuentra cambios pendientes.

Nuevos: login con email y con email repetido, registro con email ya usado, primera entrega para quien no es cliente, restaurante en la tienda, y quién puede tocar los pedidos.

Probado a mano:

- **Traba:** en PostgreSQL, con dos envíos al mismo tiempo, el reporte se envió una sola vez.
- **Foto:** en Chromium, una foto de 9,3 MB quedó en 0,75 MB; un archivo que no es una foto se manda sin tocar. No se probó en un iPhone.

## SUPUESTOS

1. **Pedidos:** los gestionan administración y operador.
2. **Foto:** 1.600 px de lado máximo alcanzan para ver los bultos.
3. **`render.yaml`:** `starter` y `basic-256mb` son los nombres de los planes que muestra el panel (0,5 CPU / 512 MB y 0,1 CPU / 256 MB). Confirmar antes de sincronizar el Blueprint.

## Puntos para Marcel

- `guardian/reportes.py`, `enviar_pendientes()`: la traba es un `select_for_update(skip_locked=True)` dentro de una transacción que queda abierta mientras se habla con Guardian. Para un puñado de reportes por mes alcanza; con envíos frecuentes convendría otra cosa.
- `cuentas/forms.py`, `LoginForm`: con emails repetidos prueba cada usuario. La solución de fondo es que el email sea único.
- `.github/workflows/tests.yml`: si te sirve, se puede pedir en GitHub que `main` no acepte un PR en rojo.
- El Blueprint de Render sigue la rama `claude/peaceful-bardeen-4k285s` con sincronización automática, no `main`.

## Preguntas

1. **Clasificación que no suma lo levantado.** En los 13 retiros, impropios + vegetales + plato da menos que lo levantado (retiro 1: 18 kg de 25). ¿Qué es la diferencia?
2. **Blueprint de Render:** ¿lo apuntamos a `main` o le sacamos la sincronización automática?
3. **Respaldo:** hay uno solo, del 05/11. ¿Quedó activa la recuperación a un punto en el tiempo?
