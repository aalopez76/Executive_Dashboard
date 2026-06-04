FROM python:3.11-slim

# Variables que hacen funcionar el código del repo SIN cambios dentro del bundle:
#   QUERIES_DIR -> queries/ locales (en vez del submódulo SQL-Queries)
#   DB_PATH     -> data/ local (en vez del submódulo SQL-Connection-Module)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    QUERIES_DIR=/app/queries \
    DB_PATH=/app/data/toys_and_models.sqlite

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hugging Face inyecta $PORT; Vizro/Dash es WSGI -> gunicorn sobre app:server.
CMD ["bash", "-lc", "gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120"]
