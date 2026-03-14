# Build from repo root: docker build -f backend/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend

# Default env; override NEO4J_* when running
ENV NEO4J_URI="" NEO4J_USERNAME="" NEO4J_PASSWORD=""
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
