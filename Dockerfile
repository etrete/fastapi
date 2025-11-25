FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry

COPY scripts/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

COPY pyproject.toml poetry.lock* ./
COPY src/app ./src/app
COPY frontend ./frontend

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

RUN mkdir -p /app/static

EXPOSE 8000

CMD ["/wait-for-it.sh", "db", "3306", "--", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]