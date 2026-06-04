FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git build-essential \
    && rm -rf /var/lib/apt/lists/*

# El conector editable (-e ./SQL-Connection-Module) debe existir ANTES del pip install.
COPY requirements.txt ./
COPY SQL-Connection-Module/ ./SQL-Connection-Module/
RUN pip install --no-cache-dir -r requirements.txt

# Resto del código (queries, utils, app, wsgi, assets).
COPY . .

# La BD vive dentro del submódulo; get_db_path() por defecto apunta fuera del repo.
ENV DB_PATH=/app/SQL-Connection-Module/examples/toys_and_models.sqlite
ENV PORT=8050

# Vizro/Dash es WSGI: se sirve con gunicorn, no uvicorn.
CMD ["sh", "-c", "gunicorn wsgi:server --bind 0.0.0.0:${PORT}"]
