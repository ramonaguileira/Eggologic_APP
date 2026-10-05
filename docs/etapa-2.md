# Etapa 2 — Tienda de huevos e impacto para usuarios

- **Fecha:** 05/10/2026
- **Estado:** lista para revisar.

## Qué se construyó

**Ajuste de la Etapa 1, pedido por Ramón**

- El chofer solo carga restaurante, kg levantados y una **foto** (en el celular se abre directo la cámara).
- La fecha y la **ubicación GPS** se toman solas.
- La clasificación (impropios, restos vegetales, residuos de plato) se completa después, en la planta, desde "Clasificar".
- Las fotos no se publican por URL: solo las ve quien tiene acceso a los datos de campo.

**Tienda** (`tienda/`)

- Productos (media docena, docena, maple) con precio, editables desde la administración.
- Pedido en una sola pantalla:
  - botones + y −, con el total en vivo;
  - cuántos residuos ayuda a rescatar el pedido;
  - dirección, teléfono y forma de pago: **contra entrega o transferencia**, sin pago online.
- "Mis pedidos": cada usuario ve los suyos con su estado. Si eligió transferencia, ve los datos para transferir.
- Eggologic gestiona los pedidos desde la administración: cambia el estado (recibido → confirmado → entregado) desde la lista.
- Registro de clientes en `/registrarse/`. Los restaurantes los sigue dando de alta Eggologic.

**Mi impacto** (`impacto/`)

- **Cliente:**
  - número principal: kg de residuos rescatados gracias a sus huevos, con una animación que cuenta hasta el valor;
  - el circuito residuo → larvas → huevos con sus números;
  - huevos por mes;
  - una calculadora con deslizador ("si compro N docenas por mes, rescato X kg por año");
  - su nivel.
- **Restaurante:**
  - kg orgánicos entregados;
  - huevos que ayudó a producir;
  - kg por mes;
  - de qué está hecho lo que entrega (vegetales, plato, impropios).
- **Entre todos:** totales de toda la comunidad.
- Todos los cálculos están en un solo archivo, `impacto/calculos.py`, para cambiarlos fácil cuando CarboSur defina su método.

## Gráficas

- Se hacen con HTML y CSS desde el servidor, sin librerías: cero dependencias nuevas.
- Cada barra o segmento muestra su valor al pasar el mouse o al tocarlo, y cada gráfica se puede ver como tabla.
- **Colores:** verde `#1f8a4c`, yema `#e0a526` y violeta `#4a3aa7`.
  - Se validaron con un verificador para daltonismo (separación entre colores vecinos y saturación mínima).
  - El verde de marca y el gris no pasaban, por eso no se usan en la composición.
  - El yema tiene poco contraste sobre blanco, así que la composición siempre lleva leyenda con los valores.

## Qué quedó afuera a propósito

- Pago online y control de stock.
- Emisiones de CO2e: no se muestran hasta que CarboSur defina los factores.
- Certificados de Reducción de Residuos y Zero Waste: falta el criterio.

## Cómo correrlo

Igual que antes (ver el [README](../README.md)). `cargar_demo` ahora carga cuatro meses de datos, productos, un cliente (`cliente`) y un restaurante (`restaurante`, vinculado a La Huerta), con pedidos.

## Tests

`python manage.py test` corre 41 tests. Cubren, además de lo anterior:

- foto obligatoria y GPS opcional;
- clasificación en planta y acceso a las fotos;
- registro de clientes;
- pedidos (total, pedido vacío, precio congelado, cada uno ve los suyos);
- cálculos del impacto y las páginas de cliente y restaurante.

## SUPUESTOS

1. El impacto de cada huevo es el promedio de todo el circuito: kg de residuo orgánico clasificado ÷ huevos producidos (hoy da unos 0,34 kg por huevo con los datos de ejemplo). Lo define CarboSur.
2. Para el impacto del cliente cuentan solo los pedidos entregados.
3. El nivel del cliente (Compra individual, Sostenedor, Regenerador, Guardián) lo asigna Eggologic desde la administración. Falta el criterio.
4. Sin control de stock: Eggologic confirma cada pedido a mano.
5. Los productos y precios de `cargar_demo` son de ejemplo.
6. Los datos para transferir son un texto configurable (`TIENDA_DATOS_TRANSFERENCIA` en el `.env`).
7. Las fotos se guardan en el disco del servidor.
8. Si el celular no da la ubicación, el retiro se guarda igual, sin GPS. **El GPS solo funciona si la app está en `https`.**

## Para que Marcel revise (al final)

- `impacto/calculos.py`: de dónde sale cada número que ve un usuario.
- `tienda/forms.py`: `PedidoForm`, que arma el pedido y congela precios.
- `captura/views.py`: `retiro_foto`, cómo se protegen las fotos.
- `static/js/`: tres archivos chicos (GPS, tienda, impacto). La app funciona sin JavaScript, salvo la toma automática de GPS.
