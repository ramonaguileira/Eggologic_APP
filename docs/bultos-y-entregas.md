# Retiro por bultos, impropios estimados y registrar entrega

- **Fecha:** 13/11/2026
- **Estado:** para revisar. En la rama `claude/keen-heisenberg-xon3e4` (PR #12); no está en línea.
- **Base:** decisiones de Ramón del 13/11, después de un mes de uso real.

## Qué se hizo

1. **Retiro por bultos.** Los cajones no se pueden apilar en la balanza: se pesa uno, se le saca la foto y se carga; después el siguiente.
   - **Nuevo retiro** pide el restaurante y el primer bulto (peso y foto). Después se abre el retiro, con la lista de bultos, el total sumado, **+ Agregar bulto** y **Terminar retiro**.
   - Un bulto mal cargado se puede quitar antes de terminar. El último no.
   - Mientras no se termina, el retiro dice "En carga" y la planta no lo puede clasificar. Si el chofer sale y vuelve a entrar, la app lo lleva al retiro que dejó abierto.
   - **Un solo retiro por restaurante y por día:** si se carga otro bulto el mismo día y el retiro todavía no está clasificado, se suma a ese.
   - Los pesos son netos: la balanza se tara con un cajón vacío. La app no descuenta tara.
   - Los 13 retiros anteriores quedan como están (uno por bulto).
2. **La diferencia va a impropios.** Si impropios + vegetales + plato suma menos que lo levantado, la diferencia se suma a impropios y queda marcada como estimación ("est." en la lista, columna `impropios_estimados` en el CSV). Lo que se había pesado queda escrito en las observaciones.
   - La migración `captura/0006` aplica la misma regla a los retiros ya clasificados. Los kg orgánicos no cambian, así que el reporte de octubre ya registrado sigue igual.
3. **Registrar entrega** (menú **Pedidos** → **+ Registrar entrega**), para administración y operador. Se elige un cliente o restaurante, o se escribe el nombre de un cliente nuevo; la fecha, los productos y la forma de pago. Queda como pedido entregado y suma al impacto de quien lo recibió.
   - El pedido guarda la fecha de entrega (`entregado_en`) y quién lo cargó. El impacto por mes se cuenta por la fecha de entrega.
4. **Un error que encontró la prueba en el navegador:** al contar los bultos, la lista de retiros perdía el orden y mostraba primero los más viejos.

**Quedó afuera:** la clasificación con foto, la granja por período con varios lotes y los Eggos en pantalla.

## Cómo correrlo

```bash
python manage.py migrate        # captura/0005 y 0006, tienda/0002 y 0003
python manage.py cargar_demo --password "<contraseña de prueba>"
python manage.py runserver
```

- **Retiro:** entrar como `chofer` u `operador` → **Nuevo retiro**.
- **Entrega:** entrar como `admin` u `operador` → **Pedidos** → **+ Registrar entrega**.

## Tests

`python manage.py test`: **112 tests, todos pasan**, en SQLite y en PostgreSQL 16. `makemigrations --check` no encuentra cambios pendientes.

- Las migraciones de datos se probaron en PostgreSQL sobre el esquema anterior, con retiros como los reales: el de 25 kg con 1 + 14 + 3 quedó con 8 kg de impropios, marcado como estimación; el que sumaba justo y el que no estaba clasificado no cambiaron.
- El flujo completo se probó en Chromium con tamaño de celular: tres bultos (18,4 + 17,6 + 13,7 = 49,7 kg), terminar, clasificar con diferencia y registrar una entrega a una clienta nueva. Sin errores. No se probó en un iPhone.

## SUPUESTOS

1. **Foto obligatoria en cada bulto.**
2. **Un retiro abierto por persona a la vez.**
3. **Mismo día, mismo retiro,** mientras no esté clasificado. Si ya se clasificó, el bulto abre un retiro nuevo.
4. **La fecha del retiro es la del momento de la carga.** No se puede cargar un retiro con fecha de otro día.
5. **Cliente nuevo en una entrega:** se le crea la cuenta sin que nadie sepa la contraseña. Si dejó el email, entra con "Olvidé mi contraseña".
6. **La entrega no pide dirección:** usa la que tenga cargada el cliente o el restaurante.

## Puntos para Marcel

- `captura/models.py`: `Bulto`, `Retiro.en_carga` y `Retiro.impropios_estimados`. `kg_levantados` se sigue guardando en el retiro (suma de bultos) para no tocar el resto de las cuentas.
- `captura/migrations/0006` y `tienda/migrations/0003` cambian datos. Conviene mirarlas antes de publicar.
- `captura/views.py`, `retiros()`: con `annotate(Count(...))` Django no aplica el `ordering` del modelo; por eso el `order_by` explícito.
- `tienda/forms.py`, `EntregaForm`: hereda de `PedidoForm` y saca dirección y teléfono.

## Preguntas

1. **Residuos que se procesaron sin pesar.** ¿Se cargan como estimación (cantidad de cajones × el promedio de los cajones pesados), marcados aparte, o no se cargan?
2. **Carga con fecha de otro día.** Para poner al día retiros de días anteriores, ¿habilitamos elegir la fecha (solo operador y administración)?
3. **Lotes y granja:** ver la propuesta en el resumen del checkpoint.
