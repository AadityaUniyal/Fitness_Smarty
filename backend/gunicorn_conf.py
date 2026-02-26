# Gunicorn configuration
import multiprocessing

# Bind to 0.0.0.0 to be accessible from outside container
bind = "0.0.0.0:8000"

# Use Uvicorn workers for FastAPI
worker_class = "uvicorn.workers.UvicornWorker"

# Adjust worker count based on CPU resources
workers = multiprocessing.cpu_count() * 2 + 1

# Timeout for long inference requests (Vision API can be slow)
timeout = 120

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
