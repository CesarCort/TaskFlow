#!/bin/bash

# Esperar a que Redis esté disponible
until nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
    echo "Esperando a Redis..."
    sleep 1
done

echo "Redis está disponible"

exec "$@" 