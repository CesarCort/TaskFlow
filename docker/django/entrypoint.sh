#!/bin/bash

if [ "$DATABASE" = "postgres" ]
then
    echo "Esperando a PostgreSQL..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL iniciado"
fi

python manage.py migrate
python manage.py collectstatic --no-input

exec "$@" 