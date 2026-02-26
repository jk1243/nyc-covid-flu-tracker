FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# On startup: initialise the DB schema, fetch the latest data, then serve.
# Railway injects $PORT at runtime; fall back to 8000 for local docker runs.
CMD ["sh", "-c", "python -m ingestion.ingest && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
