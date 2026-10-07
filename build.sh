#!/usr/bin/env bash
# Lo que corre Render en cada deploy: dependencias, archivos estáticos, migraciones, el primer
# usuario de administración y un diagnóstico de la conexión con Guardian.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py crear_admin
# Solo lee. En el plan gratis no hay consola: así el log del deploy muestra si Guardian responde.
python manage.py guardian_estado || echo "Revisar la conexión con Guardian (ver arriba). El deploy sigue."
