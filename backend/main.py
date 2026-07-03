import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app import models, database

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT in {"production", "prod"}

app = FastAPI(title="Smarty AI Neural Infrastructure", version="2.0.0")

from app.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
_cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173")
CORS_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()]

# Enforce secure CORS policy and secret keys in production
if IS_PRODUCTION:
    if "*" in CORS_ORIGINS or len(CORS_ORIGINS) == 0:
        logger.critical("FATAL: Wildcard (*) or empty CORS_ORIGINS is not allowed in production!")
        raise RuntimeError("Secure CORS configuration required for production environment. Specify explicit CORS_ORIGINS.")
    
    secret_key = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
    if not secret_key:
        logger.critical("FATAL: JWT_SECRET_KEY or SECRET_KEY must be set in production environments!")
        raise RuntimeError("JWT_SECRET_KEY or SECRET_KEY env var is required in production environment.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Modular Routers with error handling
try:
    from app.api import auth, meals, exercises, users, recommendations, social, analytics as analytics_v2
    from app.api import feedback as feedback_router, food as food_router, tasks as tasks_router, billing as billing_router
    from app.api import nextmove as nextmove_router, female as female_router, oauth, activities, meal_planner
    from app.api import form_coach, wearables, reminders, ai_coach, vision_ws, extensions
    
    app.include_router(auth.router)
    app.include_router(oauth.router)
    app.include_router(meals.router)
    app.include_router(exercises.router)
    app.include_router(users.router)
    app.include_router(recommendations.router)
    app.include_router(social.router)
    app.include_router(analytics_v2.router)
    app.include_router(feedback_router.router)
    app.include_router(food_router.router)
    app.include_router(tasks_router.router)
    app.include_router(nextmove_router.router)
    app.include_router(female_router.router)
    app.include_router(activities.router)
    app.include_router(meal_planner.router)
    app.include_router(form_coach.router)
    app.include_router(wearables.router)
    app.include_router(reminders.router)
    app.include_router(billing_router.router)
    app.include_router(ai_coach.router)
    app.include_router(vision_ws.router)
    app.include_router(extensions.router)
except Exception as e:
    logger.warning(f"Could not import some API modules: {e}")
    if IS_PRODUCTION:
        raise

# Include Legacy/Phase-specific Routers (keeping them for compatibility)
legacy_routers = [
    ('app.meal_scanning_api', 'meal_scanner_router'),
    ('app.recommendation_api', 'router'),
    # ('app.analytics_api', 'analytics_router'),  # REMOVED: duplicates app/api/analytics.py routes; v2 is the maintained version
    ('app.vision_api', 'vision_router'),
    ('app.nlp_api', 'nlp_router'),
    ('app.forecast_api', 'forecast_router'),
    ('app.recommendation_api_v2', 'recommendation_v2_router'),
    ('app.rl_api', 'rl_router'),
    ('app.explainability_api', 'explainability_router'),
    ('app.mobile_api', 'mobile_router'),
    ('app.infrastructure_api', 'infrastructure_router'),
    ('app.training_api', 'training_router'),
]

for module_name, router_var_name in legacy_routers:
    try:
        module = __import__(module_name, fromlist=['router'])
        router = getattr(module, 'router')
        app.include_router(router)
    except Exception as e:
        logger.warning(f"Could not import router from {module_name}: {e}")
        if IS_PRODUCTION:
            raise

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Smarty Neural Backend",
        "version": "2.0.0",
        "infrastructure": "Neural Core v5",
        "environment": ENVIRONMENT,
        "routes": len(app.routes),
    }

# Serve built frontend in production (must be AFTER all routes)
static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if static_dir.exists():
    from fastapi.responses import FileResponse
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        fp = static_dir / full_path
        if fp.exists() and fp.is_file():
            return FileResponse(str(fp))
        index = static_dir / "index.html"
        return FileResponse(str(index))

@app.on_event("startup")
def startup_event():
    # Production security checks
    if IS_PRODUCTION:
        secret_key = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
        if not secret_key:
            logger.critical("FATAL: JWT_SECRET_KEY or SECRET_KEY must be set in production environment!")
            raise RuntimeError("JWT_SECRET_KEY or SECRET_KEY environment variable is required in production mode.")

    # Initialize DB and Seed Data Libraries
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Database schema initialized")
    
    # Auto-download YOLOv8 weights if missing
    try:
        from ultralytics import YOLO
        logger.info("Initializing YOLOv8 weights auto-downloader...")
        # This will download yolov8n.pt if not present locally
        YOLO('yolov8n.pt')
        logger.info("YOLOv8 weights verified/downloaded successfully.")
    except Exception as e:
        logger.warning(f"Could not download/verify YOLOv8 weights: {e}")
    
    # Optional: Seed data if needed
    try:
        database.seed_nutrition_database()
        database.seed_exercise_database()
        logger.info("Database seeded successfully")
    except Exception as e:
        logger.warning(f"Seeding skipped or failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
