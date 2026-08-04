import importlib
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Add backend directory to sys.path to ensure correct resolution of app
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import database, models, training_api
from app.api import (
    admin,
    activities,
    advanced_analytics,
    ai_coach,
    analytics as analytics_v2,
    auth,
    billing as billing_router,
    calorie_tracking,
    coach as coach_router,
    enhanced_meal_planning,
    exercises,
    extensions,
    feedback as feedback_router,
    female as female_router,
    food as food_router,
    food_swaps,
    form_coach,
    daily_progress,
    gamification,
    gender_health,
    goal_validation,
    hydration,
    meal_planner,
    meals,
    neural,
    nextmove as nextmove_router,
    oauth,
    progress_tracking,
    recommendations,
    reminders,
    smart_meals,
    smart_notifications,
    social,
    tasks as tasks_router,
    users,
    vision_ws,
    wearables,
    workout_recommendations,
)
from app.limiter import limiter

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT in {"production", "prod"}

# Gate interactive API docs behind non-production environment
_docs_url = "/docs" if not IS_PRODUCTION else None
_redoc_url = "/redoc" if not IS_PRODUCTION else None


# ─── Application Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events for the application."""
    # ── Startup ──
    # Production security checks
    if IS_PRODUCTION:
        secret_key = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
        if not secret_key:
            logger.critical(
                "FATAL: JWT_SECRET_KEY or SECRET_KEY must be set in "
                "production environment!"
            )
            raise RuntimeError(
                "JWT_SECRET_KEY or SECRET_KEY environment variable "
                "is required in production mode."
            )

    is_test_run = os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("CI")

    # Initialize DB
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Database schema initialized")

    # Avoid expensive network-bound model warmups during tests and CI.
    # The vision stack loads lazily when the endpoints are actually used.
    if os.getenv("PYTEST_CURRENT_TEST") is None and not os.getenv("CI"):
        try:
            from ultralytics import YOLO

            logger.info("Initializing YOLOv8 weights auto-downloader...")
            YOLO("yolov8n.pt")
            logger.info("YOLOv8 weights verified/downloaded successfully.")
        except Exception as e:
            logger.warning(f"Could not download/verify YOLOv8 weights: {e}")

    # Seed data if needed. Keep test startup lean.
    if not is_test_run:
        try:
            database.seed_nutrition_database()
            database.seed_exercise_database()
            logger.info("Database seeded successfully")
        except Exception as e:
            logger.warning(f"Seeding skipped or failed: {e}")

    yield  # Application runs

    # ── Shutdown ──
    logger.info("Application shutdown")


# ─── FastAPI Application ───────────────────────────────────────────────────
app = FastAPI(
    title="Smarty AI Neural Infrastructure",
    version="2.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
_cors_origins_default = (
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:5173,http://127.0.0.1:5173"
)
_cors_env = os.getenv("CORS_ORIGINS", _cors_origins_default)
CORS_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()]

# Enforce secure CORS policy in production
if IS_PRODUCTION:
    if "*" in CORS_ORIGINS or len(CORS_ORIGINS) == 0:
        logger.critical(
            "FATAL: Wildcard (*) or empty CORS_ORIGINS "
            "is not allowed in production!"
        )
        raise RuntimeError(
            "Secure CORS configuration required for production environment. "
            "Specify explicit CORS_ORIGINS."
        )

    secret_key = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
    if not secret_key:
        logger.critical(
            "FATAL: JWT_SECRET_KEY or SECRET_KEY must "
            "be set in production environments!"
        )
        raise RuntimeError(
            "JWT_SECRET_KEY or SECRET_KEY env var "
            "is required in production environment."
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include Modular Routers ───────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(training_api.router)
app.include_router(oauth.router)
app.include_router(meals.router)
app.include_router(exercises.router)
app.include_router(users.router)
app.include_router(recommendations.router)
app.include_router(social.router)
app.include_router(analytics_v2.router)
app.include_router(advanced_analytics.router)
app.include_router(feedback_router.router)
app.include_router(food_router.router)
app.include_router(tasks_router.router)
app.include_router(nextmove_router.router)
app.include_router(female_router.router)
app.include_router(activities.router)
app.include_router(meal_planner.router)
app.include_router(enhanced_meal_planning.router)
app.include_router(form_coach.router)
app.include_router(wearables.router)
app.include_router(reminders.router)
app.include_router(smart_notifications.router)
app.include_router(billing_router.router)
app.include_router(ai_coach.router)
app.include_router(vision_ws.router)
app.include_router(extensions.router)
app.include_router(coach_router.router)
app.include_router(calorie_tracking.router)
app.include_router(gender_health.router)
app.include_router(goal_validation.router)
app.include_router(smart_meals.router)
app.include_router(progress_tracking.router)
app.include_router(daily_progress.router)
app.include_router(workout_recommendations.router)
app.include_router(hydration.router)
app.include_router(food_swaps.router)
app.include_router(gamification.router)
app.include_router(neural.router)

# ─── Include Legacy/Phase-specific Routers ─────────────────────────────────
_legacy_modules = [
    'app.meal_scanning_api',
    'app.recommendation_api',
    'app.vision_api',
    'app.nlp_api',
    'app.forecast_api',
    'app.recommendation_api_v2',
    'app.rl_api',
    'app.explainability_api',
    'app.mobile_api',
    'app.infrastructure_api',
]

for module_path in _legacy_modules:
    try:
        mod = importlib.import_module(module_path)
        app.include_router(mod.router)
    except Exception as e:
        logger.warning(f"Could not import router from {module_path}: {e}")
        if IS_PRODUCTION:
            raise


# ─── Health & Readiness Probes ─────────────────────────────────────────────
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


@app.get("/ready")
def readiness_check():
    """Readiness probe — verifies DB connectivity and external service
    reachability.  Used by deploy platforms (Render, Railway, k8s) to
    decide when to route traffic to this instance."""
    checks = {"database": "unknown", "gemini_api": "unknown"}

    # 1. Database connectivity
    try:
        db_gen = database.get_db()
        db = next(db_gen)
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
        try:
            next(db_gen)
        except StopIteration:
            pass
    except Exception as e:
        checks["database"] = f"error: {e}"

    # 2. Gemini API key presence (don't call the API, just verify config)
    gemini_key = os.getenv("GEMINI_API_KEY")
    checks["gemini_api"] = "configured" if gemini_key else "not_configured"

    all_ok = checks["database"] == "ok"
    status_code = 200 if all_ok else 503

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_ok,
            "checks": checks,
            "environment": ENVIRONMENT,
        },
    )


# ─── Serve Built Frontend in Production ────────────────────────────────────
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
