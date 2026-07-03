# Backend Startup Guide

## Prerequisites
- Python 3.9+
- pip (Python package manager)

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note:** If you encounter issues with `google-genai`:
- The package may not be available yet, in which case the code falls back to `google-generativeai`
- Both packages are supported through conditional imports

## Step 2: Set Up Environment Variables

Copy `.env.example` to `.env` and update with your values:

```bash
# Linux/Mac
cp .env.example .env

# Windows
copy .env.example .env
```

**Important variables:**
- `GEMINI_API_KEY`: Get from https://aistudio.google.com/apikeys
- `DATABASE_URL`: PostgreSQL (Neon) URL or SQLite path
- `SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`

## Step 3: Initialize Database

```bash
# Create database tables
python -c "from app.database import engine; from app import models; models.Base.metadata.create_all(bind=engine)"
```

## Step 4: Start the Backend Server

```bash
python main.py
```

Or use uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Verification

1. **Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "Smarty Neural Backend",
     "version": "2.0.0",
     "infrastructure": "Neural Core v5"
   }
   ```

2. **API Documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Common Issues

### Issue: `ModuleNotFoundError`
**Solution:** Ensure all packages are installed: `pip install -r requirements.txt`

### Issue: `google.genai` not found
**Solution:** This is okay! The code supports both `google-genai` and `google-generativeai`

### Issue: `psycopg2` compilation error
**Solution:** Install pre-compiled binary: `pip install psycopg2-binary`

### Issue: Database connection refused
**Solution:** 
- For SQLite (default): No action needed
- For PostgreSQL: Verify `DATABASE_URL` in `.env` is correct

## Database Choice

**Development:** SQLite (default)
- Set `DATABASE_URL=sqlite:///./smarty_neural_core.db` in `.env`
- No additional setup required

**Production:** PostgreSQL (Neon)
- Set `DATABASE_URL=postgresql://...` in `.env`
- Ensure psycopg2-binary is installed

## Next Steps

After the backend is running:
1. Start the frontend (see `frontend/README.md`)
2. Test API endpoints at http://localhost:8000/docs
3. Create test users and start using the app!
