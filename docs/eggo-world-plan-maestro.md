# Eggo World — plan maestro

**Estado:** propuesta para que Ramón revise (13/11/2026). **No hay nada construido.** Todo lo que no confirmó Ramón está marcado `SUPUESTO`.

Eggo World es una app nueva para los clientes de Eggologic (personas que compran huevos y restaurantes): un mundo en pixel art donde cada uno tiene su gallina, la alimenta, cosecha, arma su maple, compra huevos, pide retiros de residuos, ve su impacto y junta y canjea Eggos. Es otra cara de la app que ya existe: usa los mismos usuarios, pedidos, retiros y fórmulas.

---

## 1. La idea en una página

**El mundo del cliente es un espejo en miniatura del circuito real.** Residuo → larva → gallina → huevo, igual que en Maldonado. Lo que hace especial a Eggo World frente a cualquier jueguito de granja es que **nada es inventado**: las larvas, los huevos y los Eggos del mundo salen de compras entregadas, kilos clasificados en planta y lotes reales.

Tres principios que ordenan todo el diseño:

1. **Lo real genera, el juego cosecha.** Los Eggos se ganan solo con acciones reales y verificadas (un pedido entregado, kilos clasificados, una adopción activa). El juego es la manera linda de *recibirlos*: la gallina los pone, vos los cosechás y los acomodás en el maple. Tocar la pantalla nunca fabrica Eggos. Es el mecanismo de Ant Forest (la app de Alipay con cientos de millones de usuarios): la energía sale de acciones reales y el usuario entra a juntarla.
2. **Sin culpa.** La gallina no se muere, no pasa hambre y no reta. Si no entrás, te espera con los huevos en el nido. Las mascotas que castigan la ausencia terminan echando al usuario; las que solo premian (Finch) retienen mejor.
3. **Treinta segundos.** La visita diaria se resuelve con una mano y en medio minuto: entrar, cosechar, dar de comer, listo. Comprar un maple: tres toques.

**Qué NO es:** no es una billetera, no hay cripto a la vista, no hay inversión con ganancia en plata, y los Eggos no se compran ni se transfieren.

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

### Todos los días (30 segundos)

Entrar → la gallina puso (según lo que pasó en la realidad) → tocar para cosechar → los huevos van al maple → darle larvas → una novedad real de la granja ("Hoy las gallinas pusieron 212 huevos", "El Lote 7 dio 12 kg de larvas").

### Cada semana

Comprar un maple o pedir un retiro. Una misión semanal opcional.

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
- **Maple.** Treinta casilleros. Cada huevo cosechado ocupa uno. **Maple completo = se puede canjear por huevos de verdad.** Es la barra de progreso más clara posible: el cliente ve cuánto le falta para su premio.
- **Camioncito** (restaurantes): llega cuando se confirma un retiro y se va cargado. Después "vuelve" con las larvas que salieron de esos residuos.
- **Cartel de la granja.** Novedades reales del circuito y totales de la comunidad.

### Dar de comer, cosechar, armar el maple

| Acción | En el juego | Qué hay atrás (real) |
| --- | --- | --- |
| Dar de comer | Arrastrar o tocar una larva; la gallina come y festeja | Consume larvas del usuario, que salieron de compras o residuos reales |
| Poner | La gallina pone un huevo dorado | Se libera un Eggo ya ganado y pendiente de cosechar |
| Cosechar | Tocar el huevo; vuela al maple | El Eggo pasa de "pendiente" a "en tu saldo" |
| Armar el maple | Se llenan los 30 casilleros | Saldo suficiente para canjear |

SUPUESTO: dar de comer no es obligatorio para cobrar. Si alguien no quiere jugar, hay un botón "Cosechar todo" y un modo sin animaciones. El juego es un regalo, no un peaje.

---

## 5. Eggos: cómo se ganan y se canjean

En pantalla siempre se dice **Eggos** (regla del proyecto: no se usa "coin", "cripto" ni "token"). "Ego Coins" queda como nombre de trabajo.

### 5.1 Reglas de la economía

- Los Eggos son **puntos de un programa de fidelidad**. No se compran con plata, no se pasan a otra persona, no se cambian por plata.
- Se ganan solo cuando la acción real quedó firme: pedido **entregado**, retiro **clasificado en planta**, adopción **activa**, apadrinamiento **confirmado**.
- Vencen a los 12 meses sin movimiento en la cuenta (SUPUESTO), para que no se acumule una deuda infinita de huevos.
- Los bonos de juego (bienvenida, misiones, referidos) tienen tope: no más del 10 % de lo emitido en el mes (SUPUESTO).

### 5.2 Calculadora de Eggos (propuesta)

Todos los números son `SUPUESTO` y viven en un solo archivo (`eggos/reglas.py`), para que cambiarlos sea editar una línea.

| Acción | Eggos | Cuándo se acreditan |
| --- | --- | --- |
| Comprar huevos | **1 por huevo** | Pedido entregado |
| Entregar residuos | **2 por kg orgánico** (restos vegetales + residuos de plato) | Retiro clasificado |
| Calidad de la separación | ×1,2 si los impropios son menos del 5 %; ×0,8 si pasan el 15 % | Con el retiro |
| Adoptar una gallina (plan mensual, ver 6) | 50 al empezar + 20 por mes activo | Cada mes |
| Apadrinar larvas (ver 7) | 1 cada $ 10 aportados | Aporte confirmado |
| Bienvenida | 20 | Al crear la gallina |
| Referido | 50 para cada uno | Primer pedido entregado del invitado |
| Misión semanal | 5 a 20 | Al cumplirla |

**Canje:** `20 Eggos = 1 huevo`. Un maple de 30 huevos = 600 Eggos. En el juego: cada casillero del maple de canje vale 20 Eggos.

### 5.3 Qué significan esos números

Con el precio actual (Quincena: 15 huevos a $ 160, unos $ 10,7 por huevo):

- 1 Eggo vale unos **$ 0,53** en huevos.
- Comprar da un **5 % de vuelta**: cada 20 maples comprados, uno gratis.
- Un restaurante que entrega 500 kg orgánicos en el mes gana 1.000 Eggos = **50 huevos** (unos $ 530).
- Una gallina adoptada da 20 Eggos por mes = 1 huevo extra por mes.

**La pregunta de fondo es de negocio, no técnica:** qué porcentaje de la producción de huevos está dispuesto Eggologic a entregar por canje. La app va a tener un tablero interno ("Economía de Eggos") con: emitidos, canjeados, pendientes (la deuda en huevos) y ese porcentaje, para ajustar las tasas con datos.

### 5.4 Relación con Guardian y FGET

**Eggo World no escribe nada en Guardian ni en Hedera.** Sigue todo como está: el reporte por restaurante mintea FGET.

- La cifra de Eggos por kilo del restaurante es la misma que Ramón decidió el 12/10 ("se calcula por kg en la app"). Hoy esa cuenta **no existe todavía en el código**; este plan la crea en `eggos/reglas.py` y pasa a ser el número del futuro mint compensatorio de la policy v2.
- Los Eggos de los consumidores quedan solo en la base de la app. Llevarlos al registro verificable es un tema de la v2, con CarboSur y Marcel.

### 5.5 Mercado de canje

- **Fase 1:** Eggos → huevos (media docena, quincena, maple). El canje crea un pedido común, que se entrega por el circuito de siempre.
- **Más adelante:** frass (el abono que sale de los lotes, ya se registra en `Lote.kg_frass`) para plantas; **donar huevos** a un comedor u olla con los Eggos; productos con la gráfica del juego.

---

## 6. Adoptar una gallina

Dos niveles, para que nadie quede afuera y haya un producto real atrás:

1. **Gallina de bienvenida (gratis, una por cuenta).** Es la mascota y la compañera del juego. Todos la tienen desde el primer minuto.
2. **Adopción real (plan mensual).** SUPUESTO: el cliente paga una cuota mensual y recibe los huevos de "su" gallina (por ejemplo un maple por mes; una ponedora da entre 20 y 25 huevos al mes). Es una **suscripción de huevos** con cara de adopción: ingreso previsible para Eggologic y la producción vendida por adelantado. En el mundo, la gallina adoptada pone al ritmo real de la granja (huevos del período ÷ cantidad de gallinas).

Para la adopción real hace falta un dato que la app hoy no tiene: **cuántas gallinas hay**. Se suma como parámetro o como campo del registro de granja (que de todos modos pasa a ser por período, decisión del 24/10).

Se dice con honestidad: la gallina adoptada representa una parte del plantel, no un animal con caravana, salvo que Ramón quiera identificar gallinas reales (foto, nombre) — sería hermoso para pocos adoptantes y difícil de sostener para muchos.

---

## 7. Larvas: verlas y aportar a su producción

### Ver

- **Comunidad:** kilos de larva producidos (suma de `Lote.kg_larvas`), lotes en curso, residuo transformado.
- **Restaurante — trazabilidad real:** la app ya une cada retiro con su lote. Se puede contar la historia completa: *"Tus residuos del 14/10 entraron al Lote 7. El lote dio 12 kg de larvas y 30 kg de abono, y alimentó a las gallinas que pusieron 340 huevos."* Es lo más fuerte que tiene Eggologic para mostrar y ya está en los datos.
- **Consumidor:** la larva que hay detrás de sus huevos (gramos de larva por huevo × huevos comprados), ya calculado en `impacto/calculos.py`.

### Aportar capital — hay que hacerlo con cuidado

Recibir plata del público prometiendo una ganancia es actividad regulada en Uruguay. La Ley 19.820 puso el financiamiento colectivo bajo el Banco Central (solo a través de plataformas autorizadas), y en 2025, después de las estafas de los fondos ganaderos, el BCU presentó un anteproyecto para regular también a las empresas productivas que captan fondos con promesa de rentabilidad. **No es un terreno para improvisar desde una app.**

La propuesta es llegar al mismo objetivo (que la comunidad financie larvas) por un camino que no es una inversión financiera:

| Nivel | Qué es | Qué recibe el cliente | Riesgo legal |
| --- | --- | --- | --- |
| **A. Apadrinar con Eggos** | El cliente destina Eggos a un lote | Su nombre en la bandeja, la historia del lote, insignia | Ninguno: no hay plata |
| **B. Apadrinar una bandeja** (compra anticipada) | Paga hoy un monto fijo que financia una bandeja de un lote | **Huevos** a futuro (un vale con algo de más: paga 10 maples, recibe 11), Eggos y el seguimiento del lote: kilos de residuo transformados, larvas, abono | Bajo: es una venta anticipada de producto, no una promesa de ganancia. Confirmar con contador (IVA del pago adelantado, condiciones del vale) |
| **C. Inversión con retorno en plata** | Aporte de capital con ganancia | Dinero | **Alto. Fuera de este plan** hasta tener asesoramiento legal; probablemente requiere plataforma autorizada por el BCU |

En el juego, apadrinar una bandeja la hace aparecer en el larvario con un cartelito, crece con el avance real del lote (inicio → cosecha) y al cosecharse "llueven" larvas al mundo del padrino.

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

## 10. Motivación: por qué alguien vuelve

- **Niveles** (ya existen): cada nivel desbloquea algo visible en el mundo — un gallinero mejor, un cartel, una gallina de otro color.
- **Colección:** razas de gallinas pixeladas, accesorios, decoración. Se ganan, no se compran.
- **Misiones semanales** atadas a conductas reales: "Semana con menos de 5 % de impropios" (restaurante), "Pedí antes del jueves" (ayuda a planificar el reparto), "Devolvé tu maple vacío".
- **Novedades reales** todos los días en el cartel: es contenido gratis que ya produce la operación.
- **Constancia sin castigo:** se cuenta "semanas activas", no días seguidos, y no se pierde nada por faltar.
- **Compartir:** tarjeta mensual con la gallina y los números.
- **Comunidad antes que competencia:** una meta colectiva del mes ("entre todos, 2.000 kg transformados") con premio para todos. Los rankings entre restaurantes, más adelante y solo si ellos quieren.
- **Avisos:** pocos y útiles: "Tu pedido sale mañana", "Tus residuos ya son larvas", "Tu maple está completo". Nunca "tu gallina te extraña".

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
- **`mundo/`** — gallinas, larvas disponibles, huevos pendientes de cosecha, misiones, apadrinamientos, adopciones, pedidos de retiro.

**Cómo se acreditan los Eggos sin tocar el código actual:** una función repetible, `acreditar_pendientes(usuario)`, busca pedidos entregados y retiros clasificados que todavía no tengan su movimiento y los crea (cada origen puede acreditarse una sola vez, garantizado por la base). Corre cuando el usuario abre la app y por comando. Sin señales escondidas y sin cambios en `tienda` ni `captura`.

**El servidor manda.** La app del cliente nunca dice "sumame Eggos"; dice "coseché" y el servidor decide cuánto había. Así no se puede hacer trampa desde el teléfono.

### Contrato de la API (borrador)

| Endpoint | Para qué |
| --- | --- |
| `POST /api/v1/auth/google`, `/auth/login`, `/auth/salir` | Entrar y salir |
| `GET /api/v1/yo` | Perfil, rol, saldo, nivel |
| `GET /api/v1/mundo` | Estado completo del mundo (acredita lo pendiente) |
| `POST /api/v1/mundo/gallinas`, `/mundo/alimentar`, `/mundo/cosechar` | Acciones del juego |
| `GET /api/v1/eggos/movimientos` | Historial |
| `GET /api/v1/tienda/productos`, `GET/POST /api/v1/tienda/pedidos` | Comprar (mismo `Pedido` de hoy) |
| `GET /api/v1/canjes/catalogo`, `POST /api/v1/canjes` | Canjear |
| `GET/POST /api/v1/retiros/solicitudes` | Pedir retiro y ver el estado |
| `GET /api/v1/impacto`, `/impacto/trazabilidad`, `/impacto/comunidad` | Tablero |
| `GET/POST /api/v1/larvas/lotes`, `/larvas/apadrinar` | Larvas |
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
- **Vite + TypeScript + React** para las pantallas, y **Phaser 3** (motor de juegos 2D, maduro y bien documentado) solo para la escena del mundo, aislado en su carpeta.
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
- **Trampas:** Eggos solo por hechos verificados; topes en bonos; un referido vale cuando hay un pedido entregado; una gallina gratis por cuenta; límite de pedidos por minuto en la API; cada canje queda como pedido que una persona entrega.
- **Marca:** "Eggo" es una marca registrada de waffles de Kellogg's en otros países. Antes de invertir en la marca "Eggo World", consultar el registro en Uruguay (DNPI).
- **Secretos:** las claves de Google van en variables de entorno, nunca en los repos. El repo nuevo también se asume público.
- Sigue valiendo todo lo del proyecto: solo testnet, sin billeteras para usuarios, nada personal a Guardian.

---

## 14. Etapas

Mismo método de siempre: cada etapa termina con un resumen de checkpoint y se frena hasta que Ramón diga.

| Etapa | Qué se hace | Cómo se sabe que está |
| --- | --- | --- |
| **W0. Decisiones y prototipo** | Respuestas a las preguntas del punto 17. Guía de arte. Prototipo navegable **sin servidor** (datos de mentira) de inicio, mundo y cosecha | Ramón lo prueba en su celular y dice "es esto" |
| **W1. Cimientos** | Repo nuevo. App `api/`. Entrar con Google y con email. Perfil. Impacto de solo lectura con datos reales | Un cliente actual entra con Google y ve su historial |
| **W2. Mundo y Eggos** | Apps `eggos/` y `mundo/`. Gallina, larvas, cosecha, maple. Historial de Eggos. Tablero interno de economía | Un pedido entregado en la app actual aparece como huevos para cosechar |
| **W3. Tienda y canje** | Comprar maples desde Eggo World. Canjear Eggos. Mis pedidos | Un pedido hecho en Eggo World aparece en Pedidos de la app actual, y un canje también |
| **W4. Restaurantes** | Pedir retiro (y la lista para el chofer). Tablero del restaurante. Trazabilidad por lote | El Popu pide un retiro, y después ve en qué lote terminó |
| **W5. Adopción y larvas** | Adopción real (plan mensual). Apadrinar con Eggos (A) y bandejas (B) | Primera adopción y primer apadrinamiento reales |
| **W6. Pulido y beta** | Misiones, niveles con premios visibles, avisos, tarjeta para compartir, sonido, accesibilidad. Beta cerrada con unos 10 clientes y El Popu | Dos semanas de uso real sin errores graves |
| **Después** | Pago en línea, tiendas de apps, balde retornable para hogares, donaciones, metas colectivas, Eggos en la policy v2 | — |

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

Las que cambian el diseño:

1. **Presupuesto de canje:** ¿qué porcentaje de la producción de huevos puede irse en canjes? Con eso se ajustan las tasas del punto 5.2.
2. **Adopción:** ¿gratis y simbólica, o también el plan mensual con huevos (suscripción)? Si hay plan: ¿precio, cuántos huevos, cuántas gallinas hay hoy?
3. **Aporte a larvas:** ¿arrancamos con A (Eggos) y B (compra anticipada con huevos de vuelta), dejando afuera el retorno en plata hasta tener asesoramiento?
4. **Residuos de hogares:** ¿fuera de la primera versión? ¿Te interesa probar el balde retornable más adelante?
5. **Arte:** ¿contratamos un pixel artist, o arrancamos con arte generado para el prototipo?
6. **Nombre:** ¿"Eggo World" queda? (Ver la nota de marca en el punto 13.)
7. **Pago en línea** (Mercado Pago u otro): ¿después de la beta, o lo necesitás antes?
8. **Orden:** ¿Eggo World arranca ya con W0, o primero los cambios de operación del 24/10?

## 18. Puntos para Marcel

- ¿Está de acuerdo con repo aparte + tres apps aisladas (`api`, `eggos`, `mundo`) y la regla "lo viejo no importa de lo nuevo"?
- API con vistas como funciones y `JsonResponse`, o prefiere Django REST Framework.
- Login: verificación propia con `google-auth` + llave de sesión, o `django-allauth`.
- React + Phaser para la app nueva, o algo más liviano.
- Acreditación de Eggos con una función repetible en vez de señales.
- El canje como `Pedido` con una forma de pago nueva ("canje"): es el único cambio de modelo en `tienda`.

## 19. Referencias

- Ant Forest (Alipay): acciones reales generan energía que se junta en un juego, y la empresa planta árboles de verdad. [ONU Cambio Climático](https://unfccc.int/node/199777) · [Dialogue Earth](https://dialogue.earth/en/business/11672-can-mobile-payment-apps-spur-green-living/)
- Mascotas y constancia sin culpa: [análisis de Finch](https://www.deconstructoroffun.com/blog/x0hd2ssr80y5n7gv0w967pg7hwd7tl) · [estudio de 859 diseños de rachas](https://mobbin.com/blog/streaks-are-about-losing-a-study-of-859-streak-designs) · [por qué la gamificación mal hecha mata productos](https://www.mindtheproduct.com/why-gamification-kills-the-products-its-supposed-to-save/)
- Financiamiento colectivo en Uruguay: [BCU, plataformas autorizadas](https://www.bcu.gub.uy/Servicios-Financieros-SSF/Paginas/Empresas-Administradoras-de-Plataformas-de-Financiamiento-Colectivo.aspx) · [Ferrere, reglamentación](https://www.ferrere.com/es/novedades/el-banco-central-del-uruguay-emite-la-nueva-reglamentacion-para-regular-el-crowdfunding/) · [Ferrere, anteproyecto sobre empresas productivas que ofrecen rentabilidad](https://www.ferrere.com/es/novedades/bcu-propone-regular-empresas-de-giro-productivo-que-ofrezcan-rentabilidad-financiera/) · [El Observador](https://www.elobservador.com.uy/economia-y-empresas/bcu-presento-anteproyecto-ley-regular-fondos-ganaderos-y-fortalecer-proteccion-inversores-n6012681)
- Entrar con Google: [Google Identity Services](https://developers.google.com/identity/gsi/web)

Las notas legales de este documento son orientativas y no reemplazan una consulta profesional. No se verificó si el anteproyecto del BCU de 2025 ya es ley.
