# Run sync/data scripts with deps installed at build time.
# Build from repo root: docker build -f scripts/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

# Install deps (includes httpx, etc.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy script and ingestion code
COPY scripts ./scripts
COPY data_ingestion ./data_ingestion

WORKDIR /app
# Default: show help. Override to run sync, e.g.:
#   docker compose run --rm sync python scripts/sync_substances_to_core_api.py --from-psychonautwiki
CMD ["python", "scripts/sync_substances_to_core_api.py", "--help"]
