# CV Service — Python + FastAPI + OCR tools
FROM python:3.12-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-ron \
    libmagic1 \
 && rm -rf /var/lib/apt/lists/*
RUN adduser --system --uid 1001 appuser

FROM base AS production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser . .
USER appuser
EXPOSE 8002
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]
