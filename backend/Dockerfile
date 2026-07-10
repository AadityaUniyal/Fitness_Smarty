FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2, bcrypt, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer caching)
COPY requirements-base.txt requirements-ml.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for production security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Production: use gunicorn with uvicorn workers
CMD ["gunicorn", "main:app", \
     "--bind", "0.0.0.0:8000", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-"]
