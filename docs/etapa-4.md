# Etapa 4 — Entregables ANDE (demo del 19/10/2026)

- **Fecha:** 06/10/2026
- **Estado:** lista para revisar.
- **Base:** la Etapa 0 define esta etapa como "circuito trazable, línea de base e informe Fase 1". Ramón todavía no detalló qué espera ANDE, así que el alcance de abajo es SUPUESTO.

## Decisiones de Ramón (06/10)

1. **La demo muestra:** la captura de un retiro en vivo, la pantalla Reportes con octubre "en curso" y el reporte de prueba de setiembre ya registrado en Hedera, con sus 0,21 FGET.
2. **Las fotos se guardan en la base** mientras Render sea gratis. Quizás se pague Render al terminar el plan gratis.
3. No habrá restaurantes nuevos antes del 19/10.

## Qué se construyó

- **Informe del circuito** (`/captura/informe/`, menú **Informe**). Lo ven administración, operadores y CarboSur. Elige un período (por defecto, desde el primer retiro hasta hoy) y muestra:
  - **El circuito en números:** retiros, kg levantados y orgánicos, % de impropios, lotes cosechados, larvas, frass, larvas a las gallinas, huevos y CO2e evitado (provisorio);
  - **Por restaurante y línea de base:** kg entregados a Eggologic frente a lo que el restaurante descartó por otra vía, con el % que entra a Eggologic;
  - **Trazabilidad por lote:** de qué restaurantes salió el residuo de cada lote, qué rindió y cuántos huevos produjeron las gallinas con sus larvas;
  - **Registro verificable:** los reportes mensuales del período, con el enlace al registro público.

  Se imprime o se guarda como PDF desde el navegador: al imprimir se ocultan el menú y los botones. Como el informe sale de la app, **los restaurantes figuran solo con su código**.
- **Enlace al registro público:** cada reporte registrado guarda el topic de HCS y el timestamp de consenso de su mensaje, y muestra "Ver en el registro público" (HashScan, testnet) en Reportes y en el informe.
- **Fotos en la base** (`captura/almacen.py`): en Render gratis la web no tiene disco y los archivos se borran cada vez que se duerme. Las fotos se siguen viendo solo por la vista protegida `retiro_foto`.
- **Guion de la demo:** [demo-19-10.md](demo-19-10.md).
- **Guía para Marcel:** [para-marcel.md](para-marcel.md).

## Qué quedó afuera

- **El texto del informe Fase 1.** La app da los números; la redacción para ANDE la hace Eggologic.
- Una vista pública del circuito (sin login), para compartir con terceros.
- Mostrarles a clientes y restaurantes ("Mi impacto") los reportes registrados o los FGET.

## Cómo correrlo

Igual que antes. Con `cargar_demo`, entrar como `carbosur` o `admin` y abrir **Informe**.

## Tests

`python manage.py test` corre 76 tests. Los nuevos cubren:

- el informe: el resumen del período, la línea de base (calculada solo con los retiros que la informaron) y la trazabilidad de un lote hasta los huevos;
- que CarboSur vea el informe con códigos y sin nombres, y que un cliente no entre;
- que la foto de un retiro quede guardada en la base;
- el enlace público de un reporte registrado.

## SUPUESTOS

1. Alcance de la etapa: informe del circuito con trazabilidad, línea de base y números para el informe Fase 1. ANDE puede pedir otro formato.
2. El informe muestra solo códigos de restaurante, porque sale de la app.
3. El % que entra a Eggologic se calcula solo con los retiros que informaron la línea de base.
4. Los huevos de un día se atribuyen al lote del que salieron las larvas de ese día (el registro de granja tiene un lote opcional).
5. El lote entra al informe por su fecha de inicio; la cosecha, por su fecha de cosecha.
6. HashScan abre una transacción por su timestamp de consenso (`https://hashscan.io/testnet/transaction/<timestamp>`). No se pudo probar desde este entorno: hay que probar el enlace en el navegador antes de la demo.
7. Las fotos van a la base en todos los entornos. La base gratis tiene 1 GB, que alcanza para cientos de fotos.

## Para que Marcel revise (al final)

- `impacto/calculos.py`: `informe()`.
- `captura/almacen.py`: el almacenamiento de las fotos en la base.
- `guardian/reportes.py`: dónde se guarda la ubicación en HCS al registrar.

## Preguntas para Ramón

1. ¿Qué espera ANDE exactamente del "circuito trazable" y del informe Fase 1? ¿Les alcanza este informe impreso como anexo de números?
2. ¿El informe para ANDE puede llevar el nombre comercial de los restaurantes, o solo el código?
