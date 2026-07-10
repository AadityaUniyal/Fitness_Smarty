"""
Vercel Serverless Entry Point

Re-exports the FastAPI application for Vercel's Python runtime.
"""
import sys
from pathlib import Path

# Ensure the backend root is on sys.path so `app.*` imports resolve
backend_root = str(Path(__file__).resolve().parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from main import app  # noqa: E402 – must be after path setup

# Vercel looks for `app` by default
handler = app
