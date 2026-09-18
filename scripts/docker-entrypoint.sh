#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    if [ -n "${DATABASE_URL_UNPOOLED:-}" ]; then
        DATABASE_URL="$DATABASE_URL_UNPOOLED" python manage.py migrate --noinput
    else
        python manage.py migrate --noinput
    fi
fi

exec "$@"
