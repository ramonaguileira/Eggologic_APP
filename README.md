# Eggologic App

App piloto de Eggologic: registra el circuito residuo → larva BSF → gallinas → huevos, y lo informa a Hedera a través de Guardian con la policy FLW Standard. La construimos por etapas (Ramón con Claude Code); Marcel revisa el conjunto al final.

El diseño vive en el [Plano de arquitectura: app/dapp Eggologic en Hedera](https://claude.ai/artifact/Fg1DT7HeNYqL5CmuaAiVad). La regla central: la app **no escribe a Hedera directo**. Envía los reportes a Guardian vía API, y Guardian registra en HCS y mintea en HTS.

## Estado

| Etapa | Contenido | Estado |
| --- | --- | --- |
| 0 | [Propuesta aprobada](docs/etapa-0-propuesta.md) y [análisis de la policy FLW](docs/guardian/analisis-policy-flw.md) | Aprobada |
| 1 | [Captura: retiros, lotes BSF, granja y exportación para CarboSur](docs/etapa-1.md) | Aprobada |
| 2 | [Tienda de huevos e impacto con gráficas; foto y GPS en los retiros](docs/etapa-2.md) | Lista, para revisar |
| 3 | Guardian: policy FLW, reportes por restaurante, tokens en testnet | Pendiente |
| 4 | Entregables ANDE (demostrable 19/10/2026) | Pendiente |

## Correr la app en tu computadora

Hace falta Python 3.11 o más nuevo.

```bash
# 1. Entorno virtual e instalación
python -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configuración: copiar el ejemplo y completar DJANGO_SECRET_KEY
cp .env.example .env               # en Windows: copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"   # pegar el resultado en DJANGO_SECRET_KEY

# 3. Base de datos y datos de ejemplo
python manage.py migrate
python manage.py cargar_demo --password "una-contraseña-para-probar"

# 4. Levantar la app
python manage.py runserver
```

Después abrí <http://127.0.0.1:8000> y entrá con alguno de los usuarios que crea `cargar_demo`. Todos usan la contraseña que elegiste:

- `operador`: carga retiros, lotes y granja;
- `carbosur`: solo ve y exporta;
- `cliente`: compra huevos y ve su impacto;
- `restaurante`: lo mismo, más lo que entregó (La Huerta);
- `admin`: todo, más la administración en `/admin/` (pedidos, productos, usuarios).

Los clientes nuevos se registran solos en `/registrarse/`.

Sin datos de ejemplo, el primer usuario se crea con `python manage.py createsuperuser`.

## Tests

```bash
python manage.py test
```
