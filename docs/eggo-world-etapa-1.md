# Eggo World — primera construcción (13/11/2026)

Ramón pidió construir todo de una vez, sin revisiones intermedias, y recibir al final la lista de lo que falló o no se pudo. Este es ese resumen. El plan completo está en `docs/eggo-world-plan-maestro.md`.

## 1. Qué se construyó y qué quedó afuera

### Construido

**La chacra** (`eggo-world/`, se abre en `/mundo/`):

- Pantalla de carga con frases que cambian, y entrada con un botón de Google (más "Entrar con email", que usa el login de siempre).
- Una sola pantalla. Los botones son objetos del dibujo con su cartelito: granero (Tienda), gallinero (Gallinas), casita (Mi cuenta), nido (Huevos), brote (Impacto) y balde (Residuos). Cada uno abre un panel que sube desde abajo.
- Chacra vacía con pajarito y caracol; el cartel del gallinero invita a adoptar.
- Gallinas que andan solas: caminan, picotean, se echan, duermen de noche (hora de Montevideo) y corren a comerse un bichito cuando aparece. Se las puede acariciar y llamar al comedero y al bebedero. Todo eso es solo cariño: no cambia la producción.
- Arriba, siempre: Eggos, huevos juntados e insignia de socio.

**Lo que se puede hacer:**

- Adoptar una gallina (dos años, un año o mensual), con nombre y color. Si no alcanzan los Eggos, se paga la diferencia exacta.
- Ver los huevos que se van juntando (200 por año por gallina) y pedirlos de a 15 o 30.
- Comprar en la tienda con dos precios: con plata (precio lleno, vuelve el 3 % en Eggos al entregarse) o con Eggos (5,5 % menos; 7,5 % menos el socio).
- Recargar Eggos en paquetes de 500, 1.000 o 2.000.
- Pedir un levante de residuos (60 Eggos), seguir sus pasos y darles las larvas a las gallinas (1 huevo más por kilo, hasta 20 por año).
- Ver el impacto, el nivel y los totales de la comunidad.
- Editar los datos y ver los movimientos de Eggos. La dirección se pide recién en el primer pedido.
- Cada pedido muestra cuándo llega (cuenta regresiva de 24 horas, o el día y la hora que ponga Eggologic).

**En la app de siempre, para Eggologic:**

- Menú **Eggo World** (administración): huevos disponibles (arranca en 200), cupo de gallinas, pagos por transferencia para confirmar, gallinas adoptadas, economía de Eggos, socios del mes y tres planillas para Excel.
- Menú **Levantes** (chofer): baldes por retirar; anota los kilos.
- En el detalle de cada pedido: poner el día y la hora exactos de entrega.

**Arreglos previos:** los 2 tests que fallaban, dos imports que faltaban (daban error 500), el login cuando dos usuarios comparten email, y la migración pendiente de `Cliente`.

### Cómo quedó el código

| Carpeta | Qué es |
| --- | --- |
| `eggos/` | Saldo y movimientos, recargas, socio, Mercado Pago. **Todos los números están en `eggos/reglas.py`** |
| `mundo/` | Gallinas, huevos, larvas, levantes, ajustes y las pantallas de administración |
| `api/` | La puerta de entrada para la chacra y la entrada con Google |
| `eggo-world/` | La app del cliente: HTML, CSS y JavaScript sin compilar, más el arte |

Las apps de siempre no importan nada de estas (hay un test que lo verifica). En `tienda` se sumaron tres formas de pago y la fecha de entrega estimada.

### Lo que NO se hizo o quedó distinto al plan

**Hay que saberlo antes de prender:**

| Qué | Estado |
| --- | --- |
| Entrar con Google | Programado, con tests, y con el identificador de cliente real (`GOOGLE_CLIENT_ID`) ya generado por Ramón el 13/11. **Falta probarlo contra Google de verdad** después del merge |
| Mercado Pago | Programado y con tests. Ramón generó una aplicación y un Access Token **de prueba** el 13/11 (con su cuenta personal, hasta que la SAS tenga la suya). **Falta probarlo contra Mercado Pago de verdad** después del merge |
| Probado en celulares reales | No. Se probó en un navegador de escritorio simulando un celular. Falta probar en iPhone y Android |
| Tienda de siempre | No descuenta de los huevos disponibles; solo descuentan los pedidos de Eggo World |

**No construido:**

| Qué | Por qué |
| --- | --- |
| Suscripción con débito automático de Mercado Pago | La gallina mensual se cobra del saldo de Eggos cada 30 días; si no hay saldo, queda en pausa. Es más simple y no depende de Mercado Pago |
| Nodos y producción por período | Es un cambio grande en `captura`. El cupo sale de dos números que carga Ramón (gallinas en postura y % de socios). Las gallinas no están asignadas a un gallinero |
| Verduras y compost | Faltaba definir cómo se venden |
| Ventajas del socio fuera del descuento | La insignia y el 7,5 % están. Prioridad de stock y precio congelado, no |
| Vencimiento de los Eggos ganados a los 12 meses | No |
| Tope total de Eggos en circulación | Solo está el tope por cuenta (10.000) |
| Restaurantes en Eggo World | Decidido: por ahora solo consumidores |
| Avisos por email | No |
| Renovar o cancelar una gallina desde la app | No. Se hace desde Administración |
| Términos y política de privacidad | **Hecho el 14/11:** `/privacidad/` y `/terminos/`, enlazados en el pie de toda la app. Es un primer texto escrito por Claude, marcado como borrador; falta que lo revise un abogado |
| Tarjeta para compartir, premios visibles por nivel, sonido | No |
| Animación de la gallina poniendo el huevo, camioncito | No |
| Límite de pedidos por minuto en la API | No |

**Distinto al plan, a propósito:**

- **Sin React ni Vite.** La chacra es HTML, CSS y JavaScript directos, sin paso de compilación: menos código y más fácil de leer para Marcel.
- **La sirve la misma app** en `/mundo/`, no un sitio aparte. No hace falta otro servicio en Render ni un dominio nuevo, y se entra con la misma sesión.
- **Sin dependencias nuevas.** El comprobante de Google se verifica preguntándole a Google, y Mercado Pago se usa con `requests`.
- **Los levantes van en una tabla propia**, no en los retiros de restaurantes, para que no entren en los reportes a Guardian.
- **Cosechar no es un paso aparte:** los huevos se suman solos y se ven en el nido y en el maple.

## 2. Cómo correrlo

En la computadora:

```bash
EGGO_WORLD_ACTIVO=True python manage.py runserver
```

Y abrir `http://localhost:8000/mundo/`. Con `cargar_demo` hay un usuario `cliente` para probar.

**En Render:** nada cambia hasta prenderlo. Los pasos:

1. Mergear el PR. Corre las migraciones (tablas nuevas y dos campos en pedidos).
2. En el panel de Render, poner `EGGO_WORLD_ACTIVO` en `True`.
3. Entrar como administración a **Eggo World** y revisar los ajustes (huevos disponibles, gallinas en postura).
4. Para Google y Mercado Pago, cargar `GOOGLE_CLIENT_ID` y `MERCADOPAGO_ACCESS_TOKEN`. Sin ellos la app funciona igual, con entrada por email y pago por transferencia o al recibir.

**Conseguir el identificador de Google** (10 minutos, gratis):

1. Entrar a `console.cloud.google.com` con la cuenta de Eggologic y crear un proyecto.
2. "APIs y servicios" → "Pantalla de consentimiento de OAuth": tipo externo, nombre "Eggo World", el email de contacto.
3. "Credenciales" → "Crear credenciales" → "ID de cliente de OAuth" → "Aplicación web".
4. En "Orígenes autorizados de JavaScript" poner `https://eggologic.onrender.com`.
5. Copiar el "ID de cliente" y pegarlo en Render como `GOOGLE_CLIENT_ID`. No es secreto.

**Conseguir la credencial de Mercado Pago:**

1. Entrar a `mercadopago.com.uy/developers` con la cuenta de la empresa → "Tus integraciones" → crear una aplicación.
2. Copiar el "Access Token" **de prueba** y cargarlo en Render como `MERCADOPAGO_ACCESS_TOKEN`. Es secreto: va solo ahí.
3. Hacer una recarga de prueba y verificar que se acredite. Recién después cambiar al token de producción.

## 3. Tests

152 tests, todos en verde (antes había 93, con 2 fallando).

- `eggos`: precios, vuelta del 3 %, saldo, socio.
- `mundo`: adopción, cupo, huevos por año, larvas, gallina mensual, pedidos, levantes, administración, planillas, y que la app de siempre no dependa de Eggo World.
- `api`: interruptor, entrada con Google (con Google simulado), cada acción, datos mal formados, Mercado Pago (simulado).

La chacra se revisó a mano en un navegador: carga, entrada, chacra vacía, con gallinas, de noche, pantalla chica, y todos los paneles con sus acciones.

## 4. SUPUESTOS

Los números sin confirmar están marcados en `eggos/reglas.py`: precio de la gallina mensual ($ 170), 70 % de la producción para adoptantes, 3 días hasta que la gallina come sola.

Otros:

- Las cuentas del equipo y de restaurantes no entran a Eggo World.
- Si dos cuentas comparten email, Google entra a la que usa el email como nombre de usuario. Con eso no hace falta tocar las cuentas `ramon` e `info@`.
- El comprobante de Google se verifica consultando a Google (alcanza para el piloto).
- El arte nuevo (gallinas animadas, balde, árbol, bichos, sol, luna) lo dibujó Claude con `eggo-world/arte/dibujar.py`, en el estilo del paquete de Claude Design.
- La tipografía pixelada es Jersey 15, porque sus números se leen bien.

## 5. Puntos para Marcel

- `eggos/reglas.py` y `eggos/servicio.py`: las reglas y el saldo.
- `mundo/servicio.py`: adoptar, pedir, larvas. Las funciones que tocan plata son atómicas.
- `api/views.py`: el aviso de Mercado Pago no confía en lo que recibe; consulta el pago con la credencial.
- `api/google.py`: verificación con `tokeninfo` en vez de `google-auth`.
- La chacra sin compilar y servida desde `/mundo/`, en lugar de React en un sitio aparte.
- En `tienda`: tres formas de pago nuevas (la tienda de siempre sigue ofreciendo solo dos) y `entrega_estimada`.
- Los huevos de una gallina se calculan con las fechas; no se guarda nada por día.

## 6. Preguntas

1. ¿Probás la chacra y me decís qué cambiar del dibujo y de los textos?
2. ¿Qué sigue: nodos y producción por período, prioridad y precio congelado del socio, verduras, o avisos por email?

## 7. Segunda tanda (14/11/2026), mientras se espera el merge de Marcel

Con el PR #13 todavía sin mergear, Ramón pidió seguir con dos cosas que no dependían de eso.

### Cancelar un pedido ya devuelve lo que había descontado

Pantalla nueva en Administración, **Cancelar pedido** (en el detalle de cada pedido). Al cancelar:

- Si el pedido era de Eggo World, devuelve sus huevos al cupo disponible.
- Si se había pagado con Eggos, devuelve el saldo al cliente.
- Un pedido pagado con plata (transferencia, Mercado Pago, al recibir) no devuelve nada automático: esa devolución se sigue coordinando por fuera de la app, como siempre.
- Un pedido de la tienda de siempre (no de Eggo World) no toca el cupo de huevos disponibles al cancelarse, porque tampoco lo tocó al crearse.

Para que esto funcione, se sumó un campo `de_eggo_world` a `Pedido` (migración `tienda/0003`), que marca si un pedido pasó por `mundo.crear_pedido` (y por lo tanto descontó huevos disponibles) o si vino de la tienda de toda la vida.

La lógica vive en `mundo.servicio.cancelar_pedido`, y la pantalla en `mundo/views.py` (no en `tienda/views.py`, para no romper la regla de que las apps de siempre no dependan de las nuevas).

### Textos de privacidad y de términos

Dos páginas públicas (no hace falta estar logueado), enlazadas en el pie de toda la app:

- `/privacidad/`: qué datos se guardan, para qué se usan, con quién se comparten (Google, Mercado Pago, y el registro verificable del impacto, al que nunca van datos personales) y cómo pedir que se borren.
- `/terminos/`: qué es la app, cómo funcionan los Eggos, que adoptar una gallina es comprar producto por adelantado y no una inversión, cancelaciones y contacto.

**Es un primer texto, escrito por Claude y marcado como borrador en el propio HTML (comentario `SUPUESTO`).** Hace falta que un abogado lo revise antes de que la app tenga mucho uso, y antes de publicar la app de Google (que pide un enlace a la política de privacidad en su página de marca).

### Tests

160 (antes 152): 6 nuevos de cancelar pedidos y 2 de las páginas legales. Todos en verde.

## 8. Tercera tanda (15/11/2026): tienda por pasos, recorrido, huevos para juntar y regalos

Ramón probó la chacra en el servicio de prueba y pidió estos cambios.

### 1. Qué se construyó y qué quedó afuera

**En la chacra:**

- **Recorrido de la primera vez** (`eggo-world/js/tour.js`): nueve carteles que van resaltando cada botón y dicen para qué sirve. Se puede saltar, y se vuelve a ver desde Mi cuenta ("Ver el recorrido de nuevo").
- **Botón "Quiero encargar huevos"**, arriba y siempre a la vista. Va derecho a elegir la cantidad.
- **Tienda por pasos**, de a una pregunta por pantalla:
  1. Rubros: Huevos prendido; Huerta, Carnes, Hierbas, Frutas y Miel apagados ("pronto").
  2. ¿Cuántos huevos?: quincena o maple, y la cantidad con − y +. Botón **Elegir**.
  3. ¿Dónde te los llevamos?: si ya hay dirección, "En mi dirección" u "Otra dirección"; si no, se pide dirección y teléfono. Botón **Elegir**.
  4. ¿Cómo pagás?: Efectivo, Transferencia, Tarjeta y Eggos (con "5,5 % off" chiquito). Botón **Encargar**.
  5. "¡Pedido hecho!", con cuándo llega.
  Lo ya elegido queda arriba en una línea, y tocándolo se cambia.
- **Pagar con Eggos sin saldo** abre sola la pantalla **Cargar Eggos**, con cuánto falta y un "Volver al pedido".
- **La vuelta del 3 % ya no se menciona** en ninguna pantalla.
- **"Huevos" pasó a llamarse "Canjear huevos"**, con un maple de 15 que se va llenando (los maples ya completos se cuentan aparte).
- **Huevos para juntar:** cada huevo nuevo aparece suelto en el pasto; al tocarlo vuela al nido y suma al maple.
- Pantallas nuevas **Mis pedidos** y **Cargar Eggos** (antes estaban al final de la tienda).

**En la app de siempre (Administración → Eggo World → "Regalar o cargar"):**

- Regalar Eggos, cargar Eggos que el cliente ya pagó por fuera, regalar huevos y regalar una gallina (empieza a poner ese día, sin cobrar).
- El panel suma la cifra de Eggos regalados.

**Quedó afuera, anotado en el plan maestro (punto 10):** que Ramón cargue productos nuevos y libere rubros desde Administración, y los pasos de compra de cada rubro. Pedido expreso de Ramón: primero se termina lo de los huevos.

### 2. Cómo correrlo

Igual que antes. Hay dos migraciones nuevas (`eggos/0002_regalos`, `mundo/0002_regalos`), que Render corre solo al publicar.

### 3. Tests

172, todos en verde (antes 165): regalos (5) y dirección y conteo de huevos (2). El recorrido, la tienda por pasos y los huevos para juntar se probaron a mano en un navegador con tamaño de celular; no tienen tests automáticos porque son JavaScript.

### 4. SUPUESTOS

- **La vuelta del 3 % se sigue acreditando**; solo se dejó de anunciar. El cliente la ve en sus movimientos como "Vuelta por una compra".
- **Juntar huevos es un juego:** qué huevos ya se juntaron se recuerda en el teléfono, no en el servidor. Como mucho quedan 5 por juntar; si se acumulan más, los demás se juntan solos. En un teléfono nuevo vuelven a aparecer hasta 5.
- **Los huevos sueltos no se pueden canjear hasta juntarlos** (el contador y el maple no los cuentan).
- "Efectivo" es el pago al recibir. "Tarjeta" es Mercado Pago, y se ve apagada mientras no esté la credencial.
- **"Otra dirección" vale para ese pedido** y no cambia la guardada, que se edita en Mi cuenta. Usa el teléfono guardado.
- Un pedido es de un solo envase (tantas quincenas o tantos maples), no mezclado.
- **Los regalos no miran el cupo de adopciones, el máximo de gallinas por cuenta ni el tope de 10.000 Eggos.** La gallina mensual regalada es un mes gratis; después se cobra del saldo como cualquiera.
- Los huevos regalados se canjean desde el nido, como los de una gallina, y descuentan de los huevos disponibles recién al canjearse.
- Un regalo no se borra desde la pantalla: se corrige con un ajuste.

### 5. Puntos para Marcel

- `api/views.py`, `_datos_de_entrega`: la dirección del pedido ya no pisa la del perfil si el perfil estaba completo.
- `mundo/servicio.py`: `huevos_juntados` (gallinas + regalados) y las tres funciones de regalo.
- `mundo/models.py`: `HuevosRegalados` y `Gallina.regalada`. `eggos/models.py`: motivo `REGALO`.
- `eggo-world/js/app.js`: el conteo de huevos sueltos con `localStorage`.

### 6. Preguntas

1. ¿La vuelta del 3 % se sigue dando sin anunciarla, o se elimina?
2. ¿Los huevos sin juntar bloquean el canje, como quedó, o se canjean igual?
3. ¿El recorrido dice lo que querés? Los textos están en `eggo-world/js/tour.js`.

### Ajustes del mismo día (Ramón, 15/11)

- **Tope de adopción: 15 gallinas por cuenta** (antes un supuesto de 4). **Tope de Eggos: 10.000 por cuenta**, confirmado. Los dos dejaron de ser supuestos en `eggos/reglas.py`.
- **Pila de maples a la vista, al lado del nido**, sin abrir nada: cada 15 huevos juntados se apila un maple de 15; con dos, se atan en un maple de 30 (con una cinta amarilla) y arriba se vuelve a formar otro de 15. Un cartelito dice cuántos hay ("2 de 30 + 1 de 15"). Tocar la pila abre **Canjear huevos**.
- Con 15 huevos o más, el cartel del nido cambia a **"¡Canjeá!"** y se mueve.
- Los huevos sueltos quedan siempre por encima de las gallinas, para que ninguna los tape.
- Dibujos nuevos: `maple-15.png` y `maple-30.png` (en `eggo-world/arte/dibujar.py`).

SUPUESTOS: en la chacra se dibujan hasta 4 maples de 30; si hay más, el cartelito dice cuántos. **Para mirar:** con el cupo total de hoy (34 gallinas), dos o tres cuentas con 15 cada una se lo llevan entero.

- **La gallina adoptada pone entre 17 y 18 huevos por mes** (Ramón, 15/11): `HUEVOS_POR_ANIO` pasó de 200 a 210. Son 420 huevos en dos años y una quincena cada 27 días. Los textos de la chacra salen de ese número. **Para mirar:** las cuentas de margen del plan maestro (punto 3.4) están hechas con 200 y no se rehicieron.
- **Precios:** Quincena $ 160 y Maple $ 310 (Ramón, 15/11). En el código (`cargar_demo`) ya estaban así; en Render los precios son datos y se cambian en Administración → Productos.
- **Huevos por defecto** (Ramón, 15/11): en una base sin productos, la tienda de la chacra decía "no quedan huevos". La migración `mundo/0003` crea Quincena ($ 160) y Maple ($ 310) si no hay ningún producto activo; donde ya hay productos no toca nada.

Tests: 173 en verde.
