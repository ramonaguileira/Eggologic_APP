# Eggologic · pack pixel art

Paleta de 16 colores y sprites para la app. Principal: Verde Eggologic `#1d583b`. Acento: Yema `#f5b921`. Contorno: Tinta `#0c2a1f` (nunca negro puro).

## Contenido
- `paleta.css`: variables CSS `--egg-*` y la clase `.pixel`.
- `paleta-y-sprites.json`: colores (nombre, hex, rampa) y tamaño de cada sprite.
- `png/`: sprites a 1×, fondo transparente.
- `png@4x/`: los mismos a 4× (vecino más cercano).
- `svg/`: vectoriales con `shape-rendering="crispEdges"`.

## Reglas de uso
- Escalar solo en múltiplos enteros (1×, 2×, 3×, 4×) y con `image-rendering: pixelated`.
- `eggo-chico` (13 × 16) es el ícono de interfaz para los Eggos; `eggo` (22 × 27) es la versión grande.
- `eggo-dorado` queda para premios y bonus; `eggo-linea` es de una sola tinta blanca, para fondos verdes.
- `cerco` se repite horizontalmente cada 12 px.
- Yema es acento: Eggos, premios y llamados a la acción. Fondos en Verde Eggologic o Bosque, texto en Blanco o Cáscara.

## Sprites
| Archivo | Tamaño (px) |
|---|---|
| `eggo` | 22 × 27 |
| `eggo-chico` | 13 × 16 |
| `eggo-dorado` | 22 × 27 |
| `eggo-dorado-chico` | 13 × 16 |
| `eggo-linea` | 22 × 27 |
| `gallina-blanca` | 16 × 16 |
| `gallina-colorada` | 16 × 16 |
| `pollito` | 10 × 10 |
| `larva` | 16 × 6 |
| `nido` | 18 × 8 |
| `cerco` | 12 × 13 |
| `casita` | 22 × 22 |
| `gallinero` | 22 × 18 |
| `granero` | 28 × 24 |
| `brote` | 16 × 16 |
| `escena-granja` | 127 × 36 |
