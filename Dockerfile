FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# El editable -e ./SQL-Connection-Module debe existir ANTES del sync.
COPY requirements.txt ./
COPY SQL-Connection-Module/ ./SQL-Connection-Module/
RUN uv pip sync --system requirements.txt

COPY . .

# La BD vive dentro del submódulo; fijar la ruta evita depender de get_db_path por defecto.
ENV DB_PATH=/app/SQL-Connection-Module/examples/toys_and_models.sqlite

ENTRYPOINT ["gunicorn", "app:app", "--workers", "4", "--bind", "0.0.0.0:7860"]
