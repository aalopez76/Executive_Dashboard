FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY requirements.txt .
RUN uv pip sync --system requirements.txt
COPY . .

ENTRYPOINT ["gunicorn", "app:app", "--workers", "4", "--bind", "0.0.0.0:7860"]
