FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

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

COPY docker/celery/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY backend /app/

ENTRYPOINT ["/entrypoint.sh"] 