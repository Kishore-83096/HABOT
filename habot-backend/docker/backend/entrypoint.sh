#!/bin/sh
set -eu

# Give the container network a moment to initialize before contacting Neon.
sleep "${STARTUP_DELAY:-2}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
