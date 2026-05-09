# Job Scraper — Python + FastAPI (Playwright disabled — stub mode)
FROM python:3.12-slim AS base
WORKDIR /app
RUN adduser --system --uid 1001 appuser

FROM base AS production
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi==0.111.0 "uvicorn[standard]==0.30.1" pydantic==2.7.4
COPY --chown=appuser src ./src
USER appuser
EXPOSE 8003
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
