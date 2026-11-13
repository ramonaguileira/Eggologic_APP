# Eggo World — plan maestro

**Estado:** propuesta para que Ramón revise (13/11/2026). **No hay nada construido.** Todo lo que no confirmó Ramón está marcado `SUPUESTO`.

**Decisiones de Ramón (13/11):**

- El juego es **un toque de color**, no un pasatiempo: nada que deje a la gente colgada jugando. Simple, rápido y práctico.
- **Todo Eggo tiene valor real**, y la cuenta tiene que cerrar para no perder plata (punto 5).
- El aporte a larvas se resuelve de la forma más sencilla posible (punto 7).
- Orden de trabajo: el que se sugiere en el punto 14.

Eggo World es una app nueva para los clientes de Eggologic (personas que compran huevos y restaurantes): un mundo en pixel art donde cada uno tiene su gallina, la alimenta, cosecha, arma su maple, compra huevos, pide retiros de residuos, ve su impacto y junta y canjea Eggos. Es otra cara de la app que ya existe: usa los mismos usuarios, pedidos, retiros y fórmulas.

---

## 1. La idea en una página

**El mundo del cliente es un espejo en miniatura del circuito real.** Residuo → larva → gallina → huevo, igual que en Maldonado. Lo que hace especial a Eggo World frente a cualquier jueguito de granja es que **nada es inventado**: las larvas, los huevos y los Eggos del mundo salen de compras entregadas, kilos clasificados en planta y lotes reales.

Tres principios que ordenan todo el diseño:

1. **Lo real genera, el juego cosecha.** Los Eggos se ganan solo con acciones reales y verificadas (un pedido entregado, kilos clasificados, una adopción activa). El juego es la manera linda de *recibirlos*: la gallina los pone, vos los cosechás y los acomodás en el maple. Tocar la pantalla nunca fabrica Eggos. Es el mecanismo de Ant Forest (la app de Alipay con cientos de millones de usuarios): la energía sale de acciones reales y el usuario entra a juntarla.
2. **Sin culpa.** La gallina no se muere, no pasa hambre y no reta. Si no entrás, te espera con los huevos en el nido. Las mascotas que castigan la ausencia terminan echando al usuario; las que solo premian (Finch) retienen mejor.
3. **Treinta segundos.** Cada visita se resuelve con una mano y en medio minuto: entrar, cosechar, listo. Comprar un maple: tres toques.

4. **Color, no adicción.** No hay nada que obligue a entrar todos los días: ni rachas, ni misiones, ni cosas que se pierden. La gallina y el maple hacen simpático lo que el cliente igual venía a hacer (comprar, pedir un retiro, mirar su impacto).

**Qué NO es:** no es un videojuego, no es una billetera, no hay cripto a la vista, no hay inversión con ganancia en plata, y los Eggos no se transfieren ni se cambian por plata.

---

## 2. Quiénes la usan

| | Consumidor final | Restaurante |
| --- | --- | --- |
| Entra con | Google (un botón) o email | Google o email; Eggologic lo vincula a su ficha |
| Su mundo | Gallinero, nido, maple | Lo mismo + cocina, tachos y camioncito |
| Acción principal | Comprar maples | Pedir retiro de residuos (y comprar) |
| Gana Eggos por | Huevos comprados, adopción, apadrinar larvas | Kilos orgánicos clasificados + lo anterior |
| Su tablero | Huevos, residuo y larva detrás de sus huevos, nivel | Kilos entregados, composición, % de impropios, trazabilidad por lote |
| Tono | Juego y mascota | Mismo arte, más datos; modo "solo números" disponible |

SUPUESTO: es **una sola app con dos modos**; el modo lo define el rol que ya existe en `cuentas.Usuario` (cliente o restaurante).

---

## 3. Recorrido del usuario

### Primera vez (objetivo: menos de 60 segundos hasta tener gallina)

1. Pantalla de inicio: el logo, una gallina pixelada caminando y **un solo botón grande: "Entrar con Google"**. Abajo, chico: "Entrar con email" y "Soy un restaurante".
2. Un toque en Google → ya tiene cuenta. Sin formulario. (La dirección se pide recién en el primer pedido, como ya decidió Ramón el 12/10.)
3. Sale un huevo, se rompe y nace **su gallina**. Le pone nombre (o acepta el sugerido). Bono de bienvenida en Eggos.
4. Tutorial de tres toques dentro del mundo: dar una larva → la gallina pone → cosechar al maple.
5. Cartel: "Tu primer maple real te está esperando" → tienda.

Quien ya era cliente de la app actual y entra con el mismo email **encuentra su historial**: sus compras viejas ya se convirtieron en Eggos y larvas.

### Cada vez que entra (30 segundos)

No hace falta entrar todos los días. Cuando entra: la gallina puso (según lo que pasó en la realidad) → tocar para cosechar → los huevos van al maple → una novedad real de la granja ("Hoy las gallinas pusieron 212 huevos", "El Lote 7 dio 12 kg de larvas").

### Cada semana o quincena

Comprar un maple o pedir un retiro.

### Cada mes

"Tu mes circular": resumen con una tarjeta linda para compartir por WhatsApp o Instagram.

---

## 4. Las pantallas

Cinco pestañas abajo, con íconos pixelados. Nada más.

| Pestaña | Qué tiene |
| --- | --- |
| **Mundo** | La granjita. Gallina(s), nido, maple, larvario, cartel de novedades. Para restaurantes suma el tacho y el camioncito. |
| **Tienda** | Comprar maples (los productos de `tienda.Producto`) y canjear Eggos. Mis pedidos. |
| **Residuos** | Pedir retiro, ver el estado, historial. Para restaurantes es la pestaña principal. |
| **Impacto** | Tablero: números grandes, gráficas simples, trazabilidad, nivel. |
| **Yo** | Perfil, Eggos y sus movimientos, adopciones, apadrinamientos, ajustes, ayuda. |

### El mundo

- **Gallina.** Estados: contenta, comiendo, poniendo, durmiendo (de noche, hora de Montevideo), de paseo (si hace mucho que no entrás). Nunca triste ni enferma.
- **Larvario.** Bandejas con las larvas del usuario. Las larvas son el **alimento** y representan lo real: aparecen por kilos de residuos entregados, por huevos comprados (la larva que hay detrás de cada huevo) y por apadrinar lotes.
- **Nido.** Donde aparecen los huevos dorados (Eggos) para cosechar. Tiene un tope visual, pero **nada se pierde**: lo que no entra queda guardado en el galpón.
- **Maple.** Treinta casilleros que se llenan a medida que crece el saldo de Eggos. **Maple completo = el saldo alcanza para el descuento máximo en el próximo pedido.** Es la barra de progreso más clara posible: el cliente ve cuánto le falta para su premio.
- **Camioncito** (restaurantes): llega cuando se confirma un retiro y se va cargado. Después "vuelve" con las larvas que salieron de esos residuos.
- **Cartel de la granja.** Novedades reales del circuito y totales de la comunidad.

### Dar de comer, cosechar, armar el maple

| Acción | En el juego | Qué hay atrás (real) |
| --- | --- | --- |
| Dar de comer | Tocar una larva; la gallina come y festeja | Solo un gesto simpático: no da ni quita nada. Las larvas que se ven representan las compras y los residuos reales |
| Poner | La gallina pone un huevo dorado | Se libera un Eggo ya ganado y pendiente de cosechar |
| Cosechar | Tocar el huevo; vuela al maple | El Eggo pasa de "pendiente" a "en tu saldo" |
| Armar el maple | Se llenan los 30 casilleros | El saldo de Eggos crece hacia el descuento máximo |

Nada de esto es obligatorio para cobrar. Si alguien no quiere jugar, hay un botón "Cosechar todo" y un modo sin animaciones. El juego es un regalo, no un peaje.

---

## 5. Eggos: cómo se ganan y se canjean

En pantalla siempre se dice **Eggos** (regla del proyecto: no se usa "coin", "cripto" ni "token"). "Ego Coins" queda como nombre de trabajo.

### 5.1 Reglas de la economía (decisión de Ramón, 13/11: valor real y que no se pierda plata)

- **1 Eggo = $ 1 de descuento en huevos de Eggologic.** Fácil de explicar y fácil de contar. (SUPUESTO: la equivalencia exacta.)
- Se ganan solo cuando la acción real quedó firme: pedido **entregado**, retiro **clasificado en planta**. **Jugar no da Eggos**: como cada Eggo es plata, no hay bonos por entrar, cosechar ni dar de comer.
- No se transfieren ni se cambian por plata. Solo se usan en huevos (y más adelante en otros productos de Eggologic).

### 5.2 Calculadora de Eggos (propuesta)

Todos los números son `SUPUESTO` y viven en un solo archivo (`eggos/reglas.py`): cambiarlos es editar una línea, y el cambio vale de ahí en adelante.

| Acción | Eggos | Cuándo se acreditan |
| --- | --- | --- |
| Comprar huevos (incluye la adopción con plan mensual) | **5 cada $ 100** (5 %) | Pedido entregado |
| Entregar residuos | **1 por kg orgánico** (restos vegetales + residuos de plato) | Retiro clasificado |
| Calidad de la separación | ×1,2 si los impropios son menos del 5 %; ×0,8 si pasan el 15 % | Con el retiro |
| Bandeja de larvas (ver 7) | Lo que pagó + 10 % | Pago confirmado |
| Referido (opcional) | 50 para cada uno | Primer pedido entregado del invitado |

Ejemplos: una Quincena ($ 160) da 8 Eggos. Un restaurante que entrega 500 kg orgánicos bien separados gana 600 Eggos, que son $ 600 en huevos.

### 5.3 Los candados para no perder plata

1. **Los Eggos de premio cubren hasta el 50 % de un pedido** (SUPUESTO). Cada canje viene acompañado de una venta en plata; nadie se lleva huevos gratis sin comprar.
2. **Presupuesto mensual:** lo emitido como premio no pasa del 8 % de las ventas del mes (SUPUESTO). Si se acerca, el tablero avisa y se ajustan las tasas.
3. **Vencimiento:** los Eggos de premio vencen a los 12 meses de ganados (SUPUESTO). La deuda no crece para siempre.
4. **Un Eggo le cuesta a Eggologic menos de $ 1:** se paga en huevos, así que el costo real es el costo de producir esos huevos, no su precio de venta.
5. **Tablero "Economía de Eggos"** para Ramón: emitidos, canjeados, vencidos, saldo pendiente (la deuda en pesos) y porcentaje sobre ventas, mes a mes.
6. **Cada origen se acredita una sola vez** (lo garantiza la base), y un error se corrige con un movimiento contrario que queda a la vista.

**La cuenta, con un mes de ejemplo** (números inventados para mostrar el método):

| | |
| --- | --- |
| Ventas del mes | $ 100.000 |
| Eggos por compras (5 %) | 5.000 |
| Eggos por residuos (1.500 kg) | 1.500 |
| Total emitido | 6.500 Eggos = 6,5 % de las ventas (dentro del 8 %) |
| Costo real si se canjea todo, con un huevo que cuesta producir el 55 % de su precio | $ 3.575 = 3,6 % de las ventas |

Para cerrar las tasas con números de verdad hacen falta **tres datos de Ramón**: cuánto cuesta producir un huevo, cuánto se vende por mes, y cuánto vale para Eggologic un kilo de residuo (lo que ahorra en alimento menos lo que cuesta ir a buscarlo; y si el restaurante paga o no por el retiro). Con eso se confirma o se corrige el 5 % y el Eggo por kilo.

### 5.4 Relación con Guardian y FGET

**Eggo World no escribe nada en Guardian ni en Hedera.** Sigue todo como está: el reporte por restaurante mintea FGET.

- La cifra de Eggos por kilo del restaurante es la misma que Ramón decidió el 12/10 ("se calcula por kg en la app"). Hoy esa cuenta **no existe todavía en el código**; este plan la crea en `eggos/reglas.py` y pasa a ser el número del futuro mint compensatorio de la policy v2.
- Los Eggos de los consumidores quedan solo en la base de la app. Llevarlos al registro verificable es un tema de la v2, con CarboSur y Marcel.

### 5.5 Mercado de canje

- **Fase 1:** los Eggos se usan como **descuento al hacer un pedido** de huevos (hasta el 50 % con Eggos de premio). No hay una tienda aparte: es un casillero "Usar mis Eggos" en el pedido de siempre.
- **Más adelante:** frass (el abono que sale de los lotes, ya se registra en `Lote.kg_frass`) para plantas; **donar huevos** a un comedor u olla con los Eggos; productos con la gráfica del juego.

---

## 6. Adoptar una gallina

Dos niveles, para que nadie quede afuera y haya un producto real atrás:

1. **Gallina de bienvenida (gratis, una por cuenta).** Es la mascota y la compañera del juego. Todos la tienen desde el primer minuto.
2. **Adopción real (plan mensual).** Da Eggos como cualquier compra (5 %). SUPUESTO: el cliente paga una cuota mensual y recibe los huevos de "su" gallina (por ejemplo un maple por mes; una ponedora da entre 20 y 25 huevos al mes). Es una **suscripción de huevos** con cara de adopción: ingreso previsible para Eggologic y la producción vendida por adelantado. En el mundo, la gallina adoptada pone al ritmo real de la granja (huevos del período ÷ cantidad de gallinas).

Para la adopción real hace falta un dato que la app hoy no tiene: **cuántas gallinas hay**. Se suma como parámetro o como campo del registro de granja (que de todos modos pasa a ser por período, decisión del 24/10).

Se dice con honestidad: la gallina adoptada representa una parte del plantel, no un animal con caravana, salvo que Ramón quiera identificar gallinas reales (foto, nombre) — sería hermoso para pocos adoptantes y difícil de sostener para muchos.

---

## 7. Larvas: verlas y aportar a su producción

### Ver

- **Comunidad:** kilos de larva producidos (suma de `Lote.kg_larvas`), lotes en curso, residuo transformado.
- **Restaurante — trazabilidad real:** la app ya une cada retiro con su lote. Se puede contar la historia completa: *"Tus residuos del 14/10 entraron al Lote 7. El lote dio 12 kg de larvas y 30 kg de abono, y alimentó a las gallinas que pusieron 340 huevos."* Es lo más fuerte que tiene Eggologic para mostrar y ya está en los datos.
- **Consumidor:** la larva que hay detrás de sus huevos (gramos de larva por huevo × huevos comprados), ya calculado en `impacto/calculos.py`.

### Aportar a la producción: la "bandeja de larvas" (versión sencilla, decisión de Ramón 13/11)

Recibir plata del público prometiendo una ganancia es actividad regulada en Uruguay (Ley 19.820 y Banco Central; en 2025, tras las estafas de los fondos ganaderos, el BCU propuso regular también a las empresas productivas que captan fondos con promesa de rentabilidad). Por eso el aporte **no es una inversión: es una compra de huevos por adelantado**, que es lo más simple de explicar, de programar y de llevar en la contabilidad.

**Cómo funciona:**

1. El cliente toca "Apadrinar una bandeja" y elige un monto fijo (SUPUESTO: $ 500, $ 1.000 o $ 2.000).
2. Paga por transferencia, como hoy. Una persona de Eggologic confirma el pago.
3. Recibe **ese monto + 10 % en Eggos** (paga $ 1.000, tiene 1.100 Eggos para huevos). Los Eggos pagados no tienen el tope del 50 % ni vencen (SUPUESTO): es plata del cliente.
4. En su mundo aparece la bandeja con su nombre, y puede ver el lote real al que se asignó: kilos de residuo, larvas y abono.

**Por qué cierra:** Eggologic recibe la plata hoy y la devuelve en huevos durante los meses siguientes; el costo es un 10 % de descuento. No hay promesa de ganancia en plata, ni intereses, ni devolución en dinero.

**Candados:** tope por persona, y un tope total de bandejas vendidas que no supere lo que la granja puede entregar en huevos (SUPUESTO: un mes de producción). Antes de lanzarlo, una consulta corta con el contador (cómo se factura un pago adelantado).

En la base, los Eggos pagados y los de premio se anotan con motivos distintos, aunque el cliente vea un solo saldo. Así el futuro pase al registro verificable (policy v2) puede contar solo los de premio por impacto.

**Fuera del plan:** cualquier aporte con retorno en plata, hasta tener asesoramiento legal.

---

## 8. Pedir retiro de residuos

**Restaurantes.** Botón "Pedir retiro": día preferido, cantidad aproximada de cajones y una nota. Estados: pedido → confirmado → retirado → clasificado (acá aparecen los kilos, la composición y los Eggos). Al chofer le aparece la lista de pedidos pendientes en la app actual: es el **único cambio visible** en las pantallas existentes, chico y en un PR aparte.

**Consumidores finales.** Hoy Eggologic no retira residuos de hogares, y la policy FLW solo contempla restaurantes. SUPUESTO para la primera versión: los hogares **no** piden retiros. Propuesta para probar después con pocos clientes: el **balde retornable** — el mismo viaje que entrega los huevos se lleva el balde de orgánicos. Sin logística nueva y cierra el círculo en la puerta del cliente. Esos kilos darían Eggos, quedarían solo en la app y no irían a Guardian.

---

## 9. Tablero de impacto y calculadoras

Regla del proyecto: **todas las fórmulas siguen en `impacto/calculos.py`**. Eggo World no calcula nada por su cuenta, solo muestra.

| Número | Para quién | Fórmula | Estado |
| --- | --- | --- | --- |
| Huevos recibidos | Todos | Suma de pedidos entregados | Ya existe |
| Residuo rescatado detrás de mis huevos | Consumidor | huevos × kg de residuo por huevo del circuito | Ya existe |
| Larva detrás de mis huevos | Consumidor | huevos × g de larva por huevo | Ya existe |
| Kilos entregados y composición | Restaurante | Suma de retiros clasificados | Ya existe |
| Huevos equivalentes a mis residuos | Restaurante | kg orgánicos ÷ kg de residuo por huevo | Ya existe |
| % de impropios y evolución | Restaurante | impropios ÷ clasificado, por mes | Parcial |
| Larvas y abono de mis residuos | Restaurante | Por los lotes de sus retiros, en proporción a sus kilos | Nuevo |
| CO2e evitado (provisorio) | Restaurante | `emisiones_evitadas` (factor provisorio hasta CarboSur) | Existe; falta mostrarlo |
| Eggos ganados, canjeados y saldo | Todos | Suma de movimientos | Nuevo |
| Nivel | Consumidor | Los niveles que definió Ramón (Sostenedor, Regenerador, Guardián) | Ya existe |
| Totales de la comunidad | Todos | Ya calculados | Ya existe |

**Cuidado con contar dos veces.** Los kilos desviados pertenecen al restaurante que los generó (es lo que va a Guardian). El número del consumidor es "lo que hay detrás de tus huevos": una historia verdadera, pero no un impacto adicional que se pueda sumar al del restaurante. En pantalla se rotula distinto ("detrás de tus huevos" contra "tus residuos transformados") y al consumidor **no se le muestra CO2e** hasta que CarboSur diga cómo atribuirlo (SUPUESTO).

Equivalencias simpáticas (bolsas de residuos, tachos) solo con factores que CarboSur apruebe.

---

## 10. El toque de juego (liviano a propósito)

Lo que hay:

- **La gallina con nombre** y sus pocos gestos (camina, pone, duerme, festeja).
- **Cosechar al maple**: el momento simpático de recibir los Eggos.
- **Niveles** (ya existen): cada nivel cambia algo visible en el mundo — un gallinero mejor, una gallina de otro color.
- **Novedades reales** de la granja en el cartel.
- **Tarjeta mensual** para compartir, con la gallina y los números.
- **Avisos**, pocos y útiles: "Tu pedido sale mañana", "Tus residuos ya son larvas". Nunca "tu gallina te extraña".

Lo que **no** hay (decisión de Ramón, 13/11): rachas, misiones, rankings, colecciones, minijuegos, ni nada que premie pasar tiempo en la app o castigue no entrar.

---

## 11. Arquitectura: cómo se conecta sin marear a Marcel

### Decisión propuesta

```
┌──────────────────────────┐         ┌─────────────────────────────────────────┐
│  eggo-world (repo NUEVO)  │  HTTPS  │  Eggologic_APP (repo actual, Django)     │
│  App web instalable       │ ──────► │                                         │
│  Pixel art, pantallas     │  JSON   │  api/     ← única puerta de entrada      │
│  No guarda datos propios  │ ◄────── │  eggos/   ← movimientos y reglas         │
└──────────────────────────┘         │  mundo/   ← gallinas, larvas, misiones   │
                                     │  ─────────────────────────────────────  │
                                     │  cuentas, tienda, captura, impacto,      │
                                     │  guardian  (sin cambios)                 │
                                     └─────────────────────────────────────────┘
```

- **Repo nuevo `eggo-world`:** todo lo visual. Marcel no necesita abrirlo para revisar la app actual.
- **En el repo actual, tres apps Django nuevas y aisladas.** Regla estricta: las apps nuevas pueden leer de las viejas; **las viejas nunca importan de las nuevas**. Si un día se borra Eggo World, se borran tres carpetas y la app actual sigue igual.
- **Una sola base de datos y una sola verdad.** Usuarios, pedidos, retiros y Eggos viven en la base de siempre.

### Por qué no las otras opciones

| Opción | Por qué no |
| --- | --- |
| Hacerla adentro de la app actual, con plantillas | Mezcla el juego con la operación; justo lo que Ramón quiere evitar |
| App nueva con base propia que se sincroniza | Dos verdades sobre pedidos y Eggos; los errores de sincronización son los más difíciles de encontrar |
| App nativa para las tiendas desde el día uno | Cuentas de desarrollador, revisiones y el doble de trabajo. La app web instalable alcanza para validar; después se empaqueta |

### Las tres apps nuevas

- **`api/`** — endpoints JSON bajo `/api/v1/`, vistas como funciones (como el resto del proyecto). Es el contrato entre las dos apps; se documenta en un archivo.
- **`eggos/`** — `MovimientoEggos` (solo se agrega, nunca se edita: usuario, cantidad, motivo, referencia al origen, fecha) y `reglas.py`. El saldo es la suma. Un error se corrige con un movimiento contrario, igual que los reportes de corrección de Guardian.
- **`mundo/`** — la gallina, las bandejas apadrinadas, las adopciones y los pedidos de retiro.

**Cómo se acreditan los Eggos sin tocar el código actual:** una función repetible, `acreditar_pendientes(usuario)`, busca pedidos entregados y retiros clasificados que todavía no tengan su movimiento y los crea (cada origen puede acreditarse una sola vez, garantizado por la base). Corre cuando el usuario abre la app y por comando. Sin señales escondidas y sin cambios en `tienda` ni `captura`.

**El servidor manda.** La app del cliente nunca dice "sumame Eggos"; dice "coseché" y el servidor decide cuánto había. Así no se puede hacer trampa desde el teléfono.

### Cómo queda el código

**Repo nuevo `eggo-world`** (Marcel no necesita abrirlo):

```
eggo-world/
  src/
    pantallas/    inicio, mundo, tienda, residuos, impacto, yo
    mundo/        gallina, nido, maple (sprites y animaciones)
    api.ts        el ÚNICO archivo que habla con el servidor
  public/arte/    los dibujos en pixel art
  README.md
```

**Repo actual `Eggologic_APP`** — se agregan tres carpetas y se tocan tres archivos:

```
Eggologic_APP/
  cuentas/ captura/ tienda/ impacto/ guardian/    ← como están
  api/            NUEVA  vistas JSON bajo /api/v1/ (solo traducen; no tienen reglas)
  eggos/          NUEVA  MovimientoEggos + reglas.py (todas las tasas)
  mundo/          NUEVA  gallina, bandejas, pedidos de retiro
  docs/eggo-world/        el contrato de la API y un doc por etapa
```

Lo único que se toca del código existente:

| Archivo | Cambio |
| --- | --- |
| `eggologic/settings.py` | Sumar las tres apps y la configuración de Google y CORS |
| `eggologic/urls.py` | Una línea: `path("api/v1/", include("api.urls"))` |
| `requirements.txt` | Dos dependencias: `google-auth` y `django-cors-headers` |
| `tienda` (en W3, PR aparte) | El descuento con Eggos en el pedido |
| `captura` (en W4, PR aparte) | La lista de retiros pedidos para el chofer |

**Reglas para no marear a Marcel:**

1. **Lo viejo nunca importa de lo nuevo.** `api`, `eggos` y `mundo` leen de `tienda`, `captura` e `impacto`; al revés, nunca. Un test automático lo verifica.
2. **Las fórmulas siguen en un solo lugar:** impacto en `impacto/calculos.py`, Eggos en `eggos/reglas.py`. La API no calcula nada.
3. **Un interruptor:** la variable `EGGO_WORLD_ACTIVO`. Apagada, la API no responde y la app actual funciona igual que hoy.
4. **PRs chicos y por etapa**, con tests, cada uno con su doc. Los dos cambios en pantallas existentes van en PRs separados y avisados.
5. **Mismo estilo:** vistas como funciones, Django convencional, comentarios solo para el "por qué".
6. **Migraciones solo de las apps nuevas** (tablas nuevas), salvo el descuento en el pedido.

Lo que Marcel tiene que revisar en total: la carpeta `eggos/` (un modelo y un archivo de reglas), la carpeta `mundo/` (tres modelos chicos), y `api/` (vistas cortas). El repo nuevo es opcional para él.

### Contrato de la API (borrador)

| Endpoint | Para qué |
| --- | --- |
| `POST /api/v1/auth/google`, `/auth/login`, `/auth/salir` | Entrar y salir |
| `GET /api/v1/yo` | Perfil, rol, saldo, nivel |
| `GET /api/v1/mundo` | Estado completo del mundo (acredita lo pendiente) |
| `POST /api/v1/mundo/gallina`, `/mundo/cosechar` | Ponerle nombre a la gallina; cosechar |
| `GET /api/v1/eggos/movimientos` | Historial |
| `GET /api/v1/tienda/productos`, `GET/POST /api/v1/tienda/pedidos` | Comprar (mismo `Pedido` de hoy) |
| `GET/POST /api/v1/retiros/solicitudes` | Pedir retiro y ver el estado |
| `GET /api/v1/impacto`, `/impacto/trazabilidad`, `/impacto/comunidad` | Tablero |
| `GET /api/v1/larvas/lotes`, `GET/POST /api/v1/larvas/bandejas` | Ver lotes; apadrinar una bandeja |
| `GET/POST /api/v1/adopciones` | Adopción real |

### Entrar con Google

1. El botón oficial de Google le da a la app un comprobante firmado.
2. La app lo manda a `/api/v1/auth/google`; el servidor lo verifica con la librería oficial `google-auth` (que sea para nuestra app, que el email esté verificado).
3. Si el email ya existe en `cuentas.Usuario`, se **vincula** a esa cuenta (el cliente conserva su historial). Si no, se crea un cliente nuevo.
4. El servidor devuelve una llave de sesión propia, que la app manda en cada pedido.

- Dependencias nuevas en Django: solo `google-auth` y `django-cors-headers`. SUPUESTO: se evita `django-allauth` por ser más grande de lo que hace falta; Marcel puede preferirlo.
- **Requisito previo:** emails únicos. Hoy `ramon` e `info@eggologic.org` comparten email (pendiente del 14/10); hay que resolverlo antes.
- **Restaurantes:** un restaurante no se crea solo. Entra con Google, toca "Soy un restaurante", y una persona de Eggologic vincula ese usuario con la ficha del restaurante. Así nadie se hace pasar por El Popu.
- Lo que da Google (nombre, email, foto) queda solo en la base de la app. A Guardian siguen yendo solo códigos.
- Hace falta crear un proyecto en Google Cloud con el dominio de Eggologic y la pantalla de consentimiento (lo hace Ramón con una guía paso a paso).

### Tecnología de la app nueva (SUPUESTO, a confirmar con Marcel)

- **App web instalable (PWA):** se abre desde un link o un QR en el maple, se agrega a la pantalla de inicio y funciona como una app. Sin tiendas al principio.
- **Vite + TypeScript + React** para las pantallas. **Sin motor de juegos:** como el juego es liviano, la gallina y el maple se animan con hojas de sprites y CSS. Menos dependencias y menos código.
- **Hosting:** sitio estático gratis en Render (mismo panel que ya usan), en `mundo.eggologic.org`; la API queda en la web actual. Al compartir dominio, la conexión es más simple y segura.
- **Tiendas de apps:** cuando el producto esté validado, se empaqueta la misma app con Capacitor.
- **Avisos:** notificaciones web (en iPhone funcionan solo con la app instalada en la pantalla de inicio) y email con la casilla que ya existe.

---

## 12. Arte y sonido

- **Guía de arte antes de programar:** paleta corta sacada del logo (el huevo con espiral), piezas de 16×16 o 32×32 píxeles escaladas siempre en múltiplos enteros para que no se vean borrosas, tipografía pixelada **que tenga tildes y ñ** para títulos y una tipografía común y legible para textos largos y números.
- **Qué hay que dibujar para la primera versión:** gallina (caminar, comer, poner, dormir, festejar), huevo y huevo dorado, larvas y bandeja, nido, maple, gallinero, fondo con día y noche, camioncito, tacho, íconos de las cinco pestañas, insignias de los cuatro niveles.
- **Quién lo dibuja** (decisión de Ramón): (a) un pixel artist contratado, idealmente local — el mejor resultado y una identidad propia; (b) un paquete de arte con licencia comercial, adaptado — más rápido y barato, menos único; (c) arte generado y retocado a mano — rápido para el prototipo, hay que cuidar la coherencia. Recomendación: **(c) para el prototipo, (a) para lo que sale a la calle.**
- **Sonido:** efectos cortos (cacareo, "pop" al cosechar), apagados por defecto.
- **Accesibilidad:** texto con buen contraste, botones grandes, opción de menos animación, nada que dependa solo del color.
- **Identidad:** la interfaz en español rioplatense, con humor de acá.

---

## 13. Seguridad, privacidad y cuestiones legales

- **Datos personales** (Ley 18.331): política de privacidad y términos antes de salir al público, consentimiento al registrarse, baja de cuenta a pedido. Revisar el registro de la base ante la URCDP.
- **Programa de Eggos:** bases y condiciones claras (cómo se ganan, cuánto valen, cuándo vencen, que no son dinero).
- **Aporte a larvas:** solo los niveles A y B del punto 7. Consulta con contador y abogado antes del nivel B.
- **Menores:** un juego de gallinas atrae chicos. SUPUESTO: cuenta solo para mayores de 18; los chicos juegan desde la cuenta de un adulto.
- **Trampas:** Eggos solo por hechos verificados; jugar no da Eggos; un referido vale cuando hay un pedido entregado; una gallina gratis por cuenta; límite de pedidos por minuto en la API; cada canje queda como pedido que una persona entrega.
- **Marca:** "Eggo" es una marca registrada de waffles de Kellogg's en otros países. Antes de invertir en la marca "Eggo World", consultar el registro en Uruguay (DNPI).
- **Secretos:** las claves de Google van en variables de entorno, nunca en los repos. El repo nuevo también se asume público.
- Sigue valiendo todo lo del proyecto: solo testnet, sin billeteras para usuarios, nada personal a Guardian.

---

## 14. Etapas

Mismo método de siempre: cada etapa termina con un resumen de checkpoint y se frena hasta que Ramón diga.

| Etapa | Qué se hace | Cómo se sabe que está |
| --- | --- | --- |
| **W0. Prototipo** | Guía de arte. Prototipo navegable **sin servidor** (datos de mentira) de inicio, mundo, cosecha y pedido. No toca la app actual ni necesita a Marcel | Ramón lo prueba en su celular y dice "es esto" |
| **W1. Cimientos** | Repo nuevo. App `api/`. Entrar con Google y con email. Perfil. Impacto de solo lectura con datos reales | Un cliente actual entra con Google y ve su historial |
| **W2. Mundo y Eggos** | Apps `eggos/` y `mundo/`. Gallina, cosecha, maple. Historial de Eggos. Tablero de economía | Un pedido entregado en la app actual aparece como huevos para cosechar |
| **W3. Tienda** | Comprar desde Eggo World y usar Eggos como descuento. Mis pedidos | Un pedido hecho en Eggo World aparece en Pedidos de la app actual |
| **W4. Restaurantes** | Pedir retiro (y la lista para el chofer). Tablero del restaurante. Trazabilidad por lote | El Popu pide un retiro, y después ve en qué lote terminó |
| **W5. Bandejas y adopción** | Bandeja de larvas. Adopción con plan mensual | Primera bandeja y primera adopción reales |
| **W6. Pulido y beta** | Niveles visibles, avisos, tarjeta para compartir, accesibilidad. Beta cerrada con unos 10 clientes y El Popu | Dos semanas de uso real sin errores graves |
| **Después** | Pago en línea, tiendas de apps, balde retornable para hogares, donaciones, Eggos en la policy v2 | — |

### Orden sugerido (Ramón pidió una sugerencia, 13/11)

1. **Ahora: W0, el prototipo.** Es barato, no toca nada de lo que funciona y sirve para saber si la idea gusta antes de gastar en ella.
2. **En paralelo y con prioridad en la app actual: los cambios de operación del 24/10** (retiro por bultos, clasificación con kilos y foto, producción por período, Guardian diario). Eggo World reparte Eggos, que son plata, según esos datos: si los kilos y las entregas no están bien cargados, se paga mal.
3. **Después: W1 en adelante**, una etapa por vez.

W0 a W3 dan una app completa para consumidores. W4 suma a los restaurantes.

### Qué tiene que estar resuelto antes en la app actual

- Emails únicos (pendiente del 14/10).
- Los arreglos pendientes de la tienda y la migración de `Cliente`.
- Producción de huevos por período y cantidad de gallinas (decisión del 24/10): necesario para la adopción real (W5), no antes.
- Los cambios de operación del 24/10 (Guardian diario, retiro por bultos, clasificación con foto) son independientes de Eggo World, pero compiten por el mismo tiempo: Ramón decide el orden.
- Este plan **reemplaza a la Etapa 5** ("experiencia de cliente y restaurante") del plan original.

---

## 15. Cómo medir si funciona

| Qué | Meta inicial (SUPUESTO) |
| --- | --- |
| Tiempo desde abrir la app hasta tener gallina | Menos de 60 segundos |
| Registrados que hacen su primer pedido | 40 % |
| Clientes que vuelven a comprar dentro de los 30 días | 60 % |
| Usuarios activos a los 7 y a los 30 días | 35 % y 20 % |
| Pedidos que entran por Eggo World | La mayoría a los 3 meses |
| % de impropios de los restaurantes | Que baje mes a mes |
| Eggos canjeados sobre emitidos, y huevos comprometidos | Dentro del presupuesto que fije Ramón |

---

## 16. Riesgos

| Riesgo | Cómo se cuida |
| --- | --- |
| El juego distrae de la operación real, que recién arranca | Etapas cortas; W0 es solo prototipo; la operación tiene prioridad |
| La economía de Eggos regala demasiado (o muy poco) | Tasas en un solo archivo, tablero de economía, vencimiento, topes |
| El aporte a larvas se interpreta como inversión | Solo en especie (huevos); asesoramiento antes del nivel B; nunca prometer ganancia |
| El arte queda genérico | Guía de arte y artista para la versión pública |
| Dos apps para mantener | Una base, una API chica y documentada, apps aisladas |
| El cliente espera huevos y no hay stock | El canje y la adopción miran la producción real; cupos |
| La gallina virtual se confunde con un animal real | Decirlo claro en la adopción |
| Promesas ambientales exageradas | Solo números que salen de `impacto/calculos.py`; CO2e solo con factores de CarboSur |

---

## 17. Preguntas para Ramón

Respondidas el 13/11: aporte a larvas (sencillo: bandeja como compra anticipada), valor de los Eggos (valor real, con candados) y orden de trabajo (el sugerido en el punto 14).

Siguen abiertas:

1. **Tres números para cerrar las tasas:** cuánto cuesta producir un huevo, cuánto se vende por mes, y cuánto vale un kilo de residuo para Eggologic (¿el restaurante paga por el retiro?).
2. **¿1 Eggo = $ 1 te cierra?** ¿Y el tope de 50 % del pedido con Eggos de premio?
3. **Adopción:** ¿solo la gallina gratis de bienvenida, o también el plan mensual con huevos? Si hay plan: precio, cantidad de huevos y cuántas gallinas hay hoy.
4. **Residuos de hogares:** ¿fuera de la primera versión?
5. **Arte:** ¿pixel artist contratado, o arte generado para el prototipo?
6. **Nombre:** ¿"Eggo World" queda? (Ver la nota de marca en el punto 13.)
7. **Pago en línea:** ¿después de la beta, o antes?

## 18. Puntos para Marcel

- ¿Está de acuerdo con repo aparte + tres apps aisladas (`api`, `eggos`, `mundo`) y la regla "lo viejo no importa de lo nuevo"?
- API con vistas como funciones y `JsonResponse`, o prefiere Django REST Framework.
- Login: verificación propia con `google-auth` + llave de sesión, o `django-allauth`.
- React sin motor de juegos para la app nueva, o prefiere otra cosa.
- Acreditación de Eggos con una función repetible en vez de señales.
- El descuento con Eggos en el `Pedido`: es el único cambio de modelo en `tienda`.

## 19. Referencias

- Ant Forest (Alipay): acciones reales generan energía que se junta en un juego, y la empresa planta árboles de verdad. [ONU Cambio Climático](https://unfccc.int/node/199777) · [Dialogue Earth](https://dialogue.earth/en/business/11672-can-mobile-payment-apps-spur-green-living/)
- Mascotas y constancia sin culpa: [análisis de Finch](https://www.deconstructoroffun.com/blog/x0hd2ssr80y5n7gv0w967pg7hwd7tl) · [estudio de 859 diseños de rachas](https://mobbin.com/blog/streaks-are-about-losing-a-study-of-859-streak-designs) · [por qué la gamificación mal hecha mata productos](https://www.mindtheproduct.com/why-gamification-kills-the-products-its-supposed-to-save/)
- Financiamiento colectivo en Uruguay: [BCU, plataformas autorizadas](https://www.bcu.gub.uy/Servicios-Financieros-SSF/Paginas/Empresas-Administradoras-de-Plataformas-de-Financiamiento-Colectivo.aspx) · [Ferrere, reglamentación](https://www.ferrere.com/es/novedades/el-banco-central-del-uruguay-emite-la-nueva-reglamentacion-para-regular-el-crowdfunding/) · [Ferrere, anteproyecto sobre empresas productivas que ofrecen rentabilidad](https://www.ferrere.com/es/novedades/bcu-propone-regular-empresas-de-giro-productivo-que-ofrezcan-rentabilidad-financiera/) · [El Observador](https://www.elobservador.com.uy/economia-y-empresas/bcu-presento-anteproyecto-ley-regular-fondos-ganaderos-y-fortalecer-proteccion-inversores-n6012681)
- Entrar con Google: [Google Identity Services](https://developers.google.com/identity/gsi/web)

Las notas legales de este documento son orientativas y no reemplazan una consulta profesional. No se verificó si el anteproyecto del BCU de 2025 ya es ley.
