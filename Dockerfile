FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    OJT_KNOWLEDGE_DIR=/app/knowledge \
    OJT_MIGRATIONS_DIR=/app/sql/postgres/migrations

WORKDIR /app

ARG PIP_VERSION=26.1.2

COPY pyproject.toml README.md constraints.txt ./
COPY src ./src
COPY knowledge ./knowledge
COPY sql ./sql

RUN python -m pip install --no-cache-dir "pip==${PIP_VERSION}" \
    && python -m pip install --no-cache-dir \
        --constraint /app/constraints.txt \
        --build-constraint /app/constraints.txt \
        ".[parsing]"

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "ojtflow.interfaces.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
