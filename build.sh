#!/usr/bin/env bash
# Lo que corre Render en cada deploy: dependencias, archivos estáticos y migraciones.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
