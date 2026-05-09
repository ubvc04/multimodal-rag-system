FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
	gcc \
	libpq-dev \
	tesseract-ocr \
	libtesseract-dev \
	poppler-utils \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --user -r /app/requirements.txt

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
	libpq5 \
	tesseract-ocr \
	poppler-utils \
	libmagic1 \
	curl \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

RUN useradd -m -u 1001 appuser \
	&& chown -R appuser:appuser /app /tmp

USER appuser
ENV PATH="/root/.local/bin:${PATH}"
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "httptools"]
