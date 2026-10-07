# Guía de revisión para Marcel

Esta guía junta lo que hay que mirar de las etapas 1 a 4. El detalle de cada etapa (qué se construyó, SUPUESTOS, tests) está en su doc: [etapa 1](etapa-1.md), [etapa 2](etapa-2.md), [etapa 3](etapa-3.md) y [etapa 4](etapa-4.md). La propuesta aprobada es la [etapa 0](etapa-0-propuesta.md), y el estudio de la policy está en [guardian/analisis-policy-flw.md](guardian/analisis-policy-flw.md).

## Qué es

Una app Django convencional (vistas como funciones, HTML desde el servidor, pocas dependencias). Registra el circuito residuo de restaurantes → larva BSF → gallinas → huevos, vende huevos y le informa a Hedera **solo a través de Guardian** (MGS, policy FLW del hackathon, testnet). La app nunca escribe a Hedera directo.

| App | Qué hace |
| --- | --- |
| `cuentas/` | Usuarios con rol, restaurantes con código público (`R-001`), clientes; permisos por rol: chofer, planta y granja ven solo su tarea (`cuentas/models.py`, `cuentas/permisos.py`) |
| `captura/` | Retiros (kg, foto, GPS; la planta clasifica después), lotes BSF, granja, panel, CSV para CarboSur e informe del circuito |
| `tienda/` | Productos y pedidos (pago contra entrega o transferencia) |
| `impacto/` | "Mi impacto" de clientes y restaurantes; **todas las fórmulas** en `impacto/calculos.py` |
| `guardian/` | Cliente de la API de MGS, reporte mensual por restaurante y sus comandos |

## Cómo correrlo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # completar DJANGO_SECRET_KEY
python manage.py migrate
python manage.py cargar_demo --password "<contraseña de prueba>"
python manage.py test           # 76 tests, sin red (Guardian simulado)
python manage.py runserver
```

`cargar_demo` crea los usuarios `admin`, `operador`, `carbosur`, `cliente` y `restaurante`, con cuatro meses de datos ficticios. Para hablar con Guardian hacen falta las variables `GUARDIAN_*` (ver `.env.example`). `guardian_estado` solo lee; **`guardian_enviar` y el botón "Enviar al registro" escriben en el Guardian real**.

## Orden de lectura sugerido

1. `captura/models.py`: el modelo de datos y sus validaciones.
2. `cuentas/models.py` y `cuentas/permisos.py`: roles y control de acceso.
3. `impacto/calculos.py`: de dónde sale cada número (impacto por huevo, niveles, CO2e provisorio, informe).
4. `guardian/cliente.py`: sesión con MGS (login por email, token de acceso, bloques por tag).
5. `guardian/reportes.py`: el reporte mensual, qué se publica (`documento()`) y el envío idempotente (`enviar()`).
6. `captura/almacen.py`: las fotos guardadas en la base.
7. `eggologic/settings.py` y `render.yaml`: configuración y hosting.

## Integración con Guardian

- **Roles:** cada restaurante es una entidad participante (rol PPE) con su propio usuario de Guardian, custodiado por Eggologic. Eggologic es el Proponente; CarboSur, el VVB.
- **Reporte mensual:** una persona de Eggologic lo verifica en **Reportes**. Después la app lo envía como el restaurante (`add_entity_report_btn`, vinculado al proyecto validado) y lo aprueba como Proponente (`approve_ppe_report_btn`), lo que mintea FGET a la cuenta del restaurante.
- **Idempotencia:** antes de cada paso, `enviar()` busca el reporte en la grilla de Guardian por el nombre de la actividad (código + mes).
- **Comportamientos de MGS que se aprendieron en testnet:**
  - Guardian procesa los envíos en segundo plano: la aprobación queda para la vuelta siguiente.
  - La policy deja el reporte original en "Waiting for Verification" aun aprobado. La app se fija en la copia `approved_entity_report`. **Nadie debería aprobar reportes desde la interfaz de MGS**, porque se mintearía dos veces.
- **Probado de punta a punta** el 06/10 con un reporte de prueba: quedó registrado en HCS y se mintearon 0,21 FGET (ver la etapa 3).

## Privacidad y seguridad (para mirar con lupa)

- **Lo que va a Guardian es público** (IPFS + HCS). `documento()` manda solo el código del restaurante, kg, tCO2e y el período. Hay un test que verifica que el nombre no aparece.
- El informe del circuito lleva código y nombre de cada restaurante (decisión de Ramón); no va a Guardian.
- **Secretos solo en variables de entorno.** El repo es público: las credenciales de Guardian van en el entorno de Render. Los errores de Guardian nunca repiten lo que se mandó (en el login va la contraseña).
- Las fotos no tienen URL pública: se sirven por `captura.views.retiro_foto` con login y permiso.
- **Producción:** `DEBUG=False`, https detrás del proxy de Render (`SECURE_PROXY_SSL_HEADER`), cookies seguras, WhiteNoise para los estáticos. `cargar_demo` se niega a correr sin `DEBUG`.
- **Excepción conocida:** el alta de R-001 en Guardian quedó con el nombre comercial del restaurante (ya es público y no se puede borrar). Ramón decidió dejarla así; las altas nuevas van solo con el código.

## Riesgos y limitaciones conocidos

- **La policy es la del hackathon sin cambios.** No calcula nada: las tCO2e las pone la app con un **factor provisorio** (`emisiones_evitadas()`), y FGET queda medido en tCO2e. Lo correcto, según el análisis, es adaptar la policy (`customLogicBlock`, mint por kg) cuando CarboSur dé sus factores.
- **FGET frente a Eggos:** si FGET va a ser Eggos, Eggos queda medido en carbono (H2 del análisis). Sin decidir.
- **Render gratis:**
  - la base vence a los 30 días;
  - la web se duerme sin uso;
  - no hay cron (se usa el botón "Enviar al registro").

  `render.yaml` explica cómo pasar a pago.
- **Credenciales por restaurante en variables de entorno:** alcanza para el piloto, pero no escala.
- Un retiro de un mes ya verificado se puede seguir editando. El reporte guarda los números verificados, pero la app no avisa la diferencia.
- **Caso borde del envío:** si hay un corte justo después de enviar y antes de guardar el estado, la vuelta siguiente podría enviar dos veces.
- El enlace a HashScan por timestamp de consenso no se pudo probar desde el entorno de desarrollo.

## Decisiones de diseño tomadas (no hace falta revisarlas, pero conviene saberlas)

- Solo FLW Standard (sin EWD-RB), sin Groups, sin gemelo digital, solo testnet.
- Un usuario de Guardian por fuente, custodiado por Eggologic.
- Un reporte por restaurante por mes, verificado por una persona.
- Fotos en la base mientras Render sea gratis.
- Nivel D afuera: incentivos a escala, emisión del CIN y modelo no custodial.
