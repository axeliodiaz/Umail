#!/usr/bin/env bash
# Build step for Render (free web service + free Postgres).
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py loaddata \
  auth/fixtures/grupos.json auth/fixtures/preguntas.json \
  django_messages/fixtures/EstadoMemos.json \
  manual_usuario/fixtures/*.json noticias/fixtures/noticias.json \
  sedes/fixtures/paises.json sedes/fixtures/estados.json sedes/fixtures/municipios.json \
  sedes/fixtures/parroquias.json sedes/fixtures/niveles.json sedes/fixtures/tipo_sede.json \
  sedes/fixtures/dependencias.json \
  personas/fixtures/tipo_personal.json personas/fixtures/personal.json personas/fixtures/personas.json
# Demo admin: the first fixture person becomes a superuser with a password from the environment.
if [ -n "${DEMO_ADMIN_PASSWORD:-}" ]; then
python manage.py shell -c "
import os
from django.contrib.auth.models import User
u = User.objects.get(username='correo@correo.com')
u.is_superuser = True
u.set_password(os.environ['DEMO_ADMIN_PASSWORD'])
u.save()
"
fi
