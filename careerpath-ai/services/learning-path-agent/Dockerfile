# Learning Path Agent (AI Professor) — Python + Claude
FROM python:3.12-slim AS production
WORKDIR /app
RUN adduser --system --uid 1001 appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser . .
USER appuser
EXPOSE 8007
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8007"]
