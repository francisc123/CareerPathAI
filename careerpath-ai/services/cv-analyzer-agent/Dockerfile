# CV Analyzer Agent — Python + Claude + Qdrant RAG
FROM python:3.12-slim AS production
WORKDIR /app
RUN adduser --system --uid 1001 appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser . .
USER appuser
EXPOSE 8006
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8006"]
