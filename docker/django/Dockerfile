FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DATABASE=postgres
ENV SQL_HOST=db
ENV SQL_PORT=5432

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        netcat-traditional \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements /app/requirements/
RUN pip install --no-cache-dir -r requirements/local.txt \
    && pip install --no-cache-dir watchdog[watchmedo]

COPY docker/django/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY backend /app/

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"] 