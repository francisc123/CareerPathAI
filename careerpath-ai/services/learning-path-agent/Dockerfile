# Learning Path Agent — Python + Gemini
FROM python:3.12-slim AS production
WORKDIR /app
RUN adduser --system --uid 1001 appuser

# Copy dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the application's code
COPY --chown=appuser:appuser ./src ./src

USER appuser
EXPOSE 8007
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8007"]
