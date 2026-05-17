# Job Scraper — Python + FastAPI (Playwright disabled — stub mode)
FROM python:3.12-slim AS base
WORKDIR /app
RUN adduser --system --uid 1001 appuser

FROM base AS production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser src ./src
USER appuser
EXPOSE 8003
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
