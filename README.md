# Eggologic App

App/dapp piloto de Eggologic sobre Hedera. La construimos en etapas (Ramón con Claude Code), con un checkpoint de Marcel al final de cada una.

El diseño vive en el [Plano de arquitectura: app/dapp Eggologic en Hedera](https://claude.ai/artifact/Fg1DT7HeNYqL5CmuaAiVad). Su regla central: la app **no escribe a Hedera directo**. Envía los reportes a Guardian vía API, y Guardian registra en HCS y mintea en HTS.

## Estado

| Etapa | Contenido | Estado |
| --- | --- | --- |
| Previa | [Análisis de la policy FLW Standard del hackathon](docs/guardian/analisis-policy-flw.md) | Hecho, pendiente de revisión |
| 1 | Esquema unificado de captura (Camino Verde, restaurantes, Planta BSF) | Pendiente |
| 2 | Integración con Guardian | Pendiente |
| 3 | Schema definitivo de CarboSur | Pendiente |
| 4 | Dashboard de entregables ANDE (demostrable 19/10/2026) | Pendiente |
