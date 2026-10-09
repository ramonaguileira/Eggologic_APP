#!/usr/bin/env bash
# Corre la app en el puerto 8321 (decision de usuario, 07/10/2026).

source .venv/bin/activate
python manage.py runserver 0.0.0.0:8321
