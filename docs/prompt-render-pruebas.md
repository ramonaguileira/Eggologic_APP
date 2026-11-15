# Prompt para Claude in Chrome: servicio de prueba en Render

Copiar todo lo que está debajo de la línea y pegarlo en Claude in Chrome, en una pestaña con `dashboard.render.com`.

---

Vas a ayudarme a crear un **segundo servicio web en Render**, solo para probar, al lado del real. Soy Ramón, el dueño.

## Reglas

1. **Frená y pedime confirmación antes de:** crear el servicio (el paso final, con el botón que lo deja andando), y cualquier cosa que implique pagar o cambiar un plan.
2. Si ves en algún paso que Render pide tarjeta o pasar a un plan pago, frená y avisame: tiene que quedar todo en el plan gratis.
3. **No toques el servicio que ya existe, "eggologic".** Esto es un servicio nuevo y separado.
4. Hacé de a un paso. Al terminar cada uno, decime en una línea qué quedó y esperá mi "seguí".

## Datos

- Repositorio: `ramonaguileira/Eggologic_APP`
- Rama a publicar: `claude/jolly-hypatia-9geupy` (**no** `main`)
- Nombre del servicio nuevo: `eggologic-pruebas`
- Comando de build: `./build.sh`
- Comando de arranque: `gunicorn eggologic.wsgi:application`
- Ruta de salud: `/ingresar/`

## Pasos

1. Desde el panel de Render, "New +" → "Web Service".
2. Elegí el repositorio `ramonaguileira/Eggologic_APP` (ya debería estar conectado, porque el servicio real usa el mismo repo).
3. **Importante:** en la rama (Branch), elegí `claude/jolly-hypatia-9geupy`, no `main`.
4. Nombre del servicio: `eggologic-pruebas`.
5. Región: Virginia (la misma que usa el servicio real).
6. Plan: **Free**. Si no aparece la opción gratis o pide tarjeta, frená y avisame.
7. Build command: `./build.sh`. Start command: `gunicorn eggologic.wsgi:application`.
8. Antes de crear el servicio, andá a "Advanced" o a las variables de entorno y cargá estas (te las voy dictando una por una; las que digo "secreta" las escribo yo, vos solo creás el nombre de la variable):

   | Variable | Valor |
   | --- | --- |
   | `DJANGO_SECRET_KEY` | que Render la genere sola (hay un botón "Generate") |
   | `DJANGO_DEBUG` | `False` |
   | `EGGO_WORLD_ACTIVO` | `True` |
   | `GOOGLE_CLIENT_ID` | `393751276365-tocgdb8jmlaedri6j722psa4rcefqrau.apps.googleusercontent.com` |
   | `MERCADOPAGO_ACCESS_TOKEN` | secreta: creá la variable vacía y avisame, la pego yo |
   | `DJANGO_SUPERUSER_EMAIL` | secreta: creá la variable vacía y avisame, la pego yo |
   | `DJANGO_SUPERUSER_PASSWORD` | secreta: creá la variable vacía y avisame, la pego yo |
   | `TIENDA_DATOS_TRANSFERENCIA` | `Esto es de prueba, no transferir plata de verdad.` |

   **No cargues** `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` ni `DB_PORT`: sin esas variables, la app usa una base SQLite propia del servicio, que se reinicia sola en cada despliegue. Es lo que queremos para un entorno de prueba.

9. Mostrame la dirección que va a quedar (algo como `eggologic-pruebas.onrender.com`) **antes** de crear el servicio, y recién ahí pedime el "sí" para el botón final ("Create Web Service" o como se llame).
10. Cuando el primer despliegue termine, decime si quedó "Live" o si falló, y si falló, copiame las últimas líneas del registro.

## Cuando esté andando

Avisame la dirección final. Con eso voy a:

- Agregar esa dirección a los orígenes permitidos del proyecto de Google (un paso en Google Cloud, no en Render).
- Entrar como administración por primera vez, con el usuario y la contraseña que vas a crear en el paso 8, y revisar los ajustes de Eggo World.

## Para borrarlo cuando terminemos de probar

Cuando yo te diga "borralo": entrá al servicio `eggologic-pruebas` en Render → "Settings" → abajo de todo, "Delete Web Service". Confirmalo escribiendo el nombre del servicio donde lo pida. No toques ningún otro servicio.
