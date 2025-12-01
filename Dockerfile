# ===== Build stage =====
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ===== Runtime stage =====
FROM python:3.12-slim

WORKDIR /app

# agregar dependencias instaladas
COPY --from=builder /install /usr/local

# copiar código fuente
COPY src ./src
COPY tests ./tests
COPY pyproject.toml .

# añadir src al path
ENV PYTHONPATH=/app/src

CMD ["python"]
