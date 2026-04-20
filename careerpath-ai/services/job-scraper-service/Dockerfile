# Job Scraper — Python + Playwright (headless Chromium)
FROM python:3.12-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN adduser --system --uid 1001 appuser

FROM base AS production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps
COPY --chown=appuser . .
USER appuser
EXPOSE 8003
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
