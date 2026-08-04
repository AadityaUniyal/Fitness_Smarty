# SMARTY AI — Project Documentation

> Internal technical reference for development and maintenance.
> Last updated: August 2026

---

## Current Product Focus

- AI-powered daily workout and meal planning with explainable coaching
- Real-time daily progress tracking (calories, macros, hydration, workouts)
- Computer vision food scanning (YOLOv8 + Gemini hybrid pipeline)
- FemmeCare-aware cycle-based workout and nutrition adjustments
- Gamification engine with XP, badges, achievements, and streaks
- Social feed, wearable integrations, and billing/subscription system
- PWA-ready frontend with dark/light theme and i18n (English + Hindi)

---

## Repository Layout

```
Smarty-reco/
├── backend/          # FastAPI app, 87 modules in app/, 39 API routers
│   ├── main.py       # Entry point, router registration, lifespan events
│   ├── app/          # Core application package
│   │   ├── api/      # 39 API router modules (auth, meals, coach, etc.)
│   │   ├── models.py # 50+ SQLAlchemy ORM models
│   │   ├── database.py # Engine, sessions, seed functions
│   │   └── ...       # Services, ML, utilities
│   ├── tests/        # 41 pytest test files
│   └── migrations/   # Alembic database migrations
├── frontend/         # React 18 + TypeScript + Vite + Tailwind v4
│   ├── src/
│   │   ├── pages/    # 30+ page components
│   │   ├── components/ # 23 reusable components
│   │   ├── services/ # 10 service modules (API, AI, vision, export)
│   │   ├── contexts/ # AuthContext
│   │   ├── hooks/    # useAPI, useToast, useUserProfile, useCurrentUserId
│   │   └── types/    # TypeScript interfaces
│   └── public/       # PWA manifest, service worker, legal pages
├── docker/           # docker-compose.yml, Dockerfiles, nginx.conf
├── .github/workflows/ # ci.yml, pytest.yml, python-tests.yml
├── vercel.json       # Vercel deployment config with security headers
└── .env.example      # Environment variable template
```

---

## Backend Architecture

### Request Flow

1. Requests hit `main.py` → CORS middleware → rate limiter → JWT auth
2. Routed to one of **39 API routers** under `app/api/`
3. Routers call **service modules** for business logic
4. Services interact with **SQLAlchemy models** for data persistence
5. AI-powered endpoints call **Gemini API** or **YOLOv8** for inference
6. Responses are validated through **Pydantic schemas**

### Key Service Modules

| Module | Purpose |
|--------|---------|
| `unified_coach_service.py` | Daily coach, explainable coach, coach history |
| `recommendation_engine.py` | Multi-armed bandit recommendation system |
| `food_detection_model.py` | YOLOv8 food detection pipeline |
| `gemini_meal_scanner.py` | Gemini vision-based meal analysis |
| `meal_analysis_service.py` | Comprehensive meal nutrition analysis |
| `gamification_service.py` | XP, badges, achievements, streaks |
| `gender_specific_service.py` | FemmeCare cycle-aware planning |
| `hydration_service.py` | Water intake monitoring and goals |
| `calorie_tracker_service.py` | Calorie & macro calculation engine |
| `workout_recommendation_service.py` | Personalized workout generation |
| `nutrition_calculator.py` | TDEE, BMR, macro split calculations |
| `progressive_overload.py` | Training progression logic |
| `image_processor.py` | Image preprocessing pipeline |
| `email_service.py` | SMTP email notifications |
| `error_handler.py` | Centralized error handling with logging |
| `logging_config.py` | Structured JSON logging |
| `limiter.py` | Token-bucket rate limiter (Redis + local fallback) |
| `config.py` | Pydantic Settings with production fail-fast guards |
| `neon_config.py` | Neon PostgreSQL configuration |

### Database Models (50+)

**Core:** `EnhancedUser`, `UserProfile`, `UserGoal`
**Fitness:** `ExerciseCategory`, `ExerciseItem`, `WorkoutLog`, `WorkoutSchedule`, `FemaleExerciseItem`
**Nutrition:** `FoodCategory`, `FoodItem`, `MealLog`, `FoodDetection`, `FoodTrainingSample`, `MealPlan`, `MealPlanEntry`
**Progress:** `DailyProgress`, `DailyTask`, `SmartNextMove`, `ProgressSnapshot`, `BiometricReading`, `BiometricRecord`
**FemmeCare:** `MenstrualCycleLog`, `FemaleCycleEntry`
**Social:** `SocialPost`, `SocialComment`, `SocialLike`, `SocialFollow`, `SocialActivity`
**Gamification:** `Achievement`, `UserAchievement`, `Badge`, `UserBadge`, `UserPoints`, `UserStreak`, `StreakState`, `UserBanditState`
**Activity:** `ActivitySession`, `ActivityRoutePoint`, `ActivityEvent`
**Integrations:** `WearableConnection`, `WearableMetric`, `FormCoachSession`, `FormFeedbackLog`
**Billing:** `SubscriptionPlan`, `UserSubscription`, `PaymentTransaction`, `Invoice`
**Notifications:** `Reminder`, `NotificationLog`
**Feedback:** `UserFeedback`

### API Route Groups (39 routers)

| Prefix | Module | Description |
|--------|--------|-------------|
| `/api/auth` | `auth.py` | Register, login, JWT refresh, password reset |
| `/api/auth/oauth` | `oauth.py` | Google OAuth 2.0 flow |
| `/api/users` | `users.py` | User profile and goal management |
| `/api/admin` | `admin.py` | Admin dashboard and user management |
| `/api/ai` | `ai_coach.py` | Gemini AI chat, workout plans, meal analysis |
| `/api/coach` | `coach.py` | Unified daily coaching with explanations |
| `/api/meals` | `meals.py` | Meal logging and scan results |
| `/api/exercises` | `exercises.py` | Exercise library CRUD |
| `/api/calorie-tracking` | `calorie_tracking.py` | Macro & calorie tracking |
| `/api/daily-progress` | `daily_progress.py` | Live daily progress |
| `/api/hydration` | `hydration.py` | Water intake tracking |
| `/api/meal-plans` | `meal_planner.py` | Weekly meal plan generation |
| `/api/meal-planning` | `enhanced_meal_planning.py` | AI-enhanced meal planning |
| `/api/smart-meals` | `smart_meals.py` | AI meal recommendations |
| `/api/food` | `food.py` | Food database search |
| `/api/food-swaps` | `food_swaps.py` | Healthier food alternatives |
| `/api/recommendations` | `recommendations.py` | Smart recommendations |
| `/api/workout-recommendations` | `workout_recommendations.py` | Workout suggestions |
| `/api/progress` | `progress_tracking.py` | Progress charts and trends |
| `/api/goals` | `goal_validation.py` | Goal CRUD and validation |
| `/api/gamification` | `gamification.py` | XP, badges, achievements |
| `/api/activities` | `activities.py` | Activity session tracking |
| `/api/social` | `social.py` | Social feed (posts, comments, likes) |
| `/api/form-coach` | `form_coach.py` | Exercise form analysis |
| `/api/wearables` | `wearables.py` | Wearable device integration |
| `/api/reminders` | `reminders.py` | Reminder scheduling |
| `/api/notifications` | `smart_notifications.py` | Push notifications |
| `/api/billing` | `billing.py` | Stripe subscriptions |
| `/api/feedback` | `feedback.py` | User feedback |
| `/api/tasks` | `tasks.py` | Daily checklist tasks |
| `/api/nextmove` | `nextmove.py` | Smart next actions |
| `/api/analytics` | `analytics.py` + `advanced_analytics.py` | Analytics |
| `/api/female` | `female.py` | FemmeCare endpoints |
| `/api/gender-health` | `gender_health.py` | Cycle-aware health |
| `/api/extensions` | `extensions.py` | Backend extensions |
| `/api/neural` | `neural.py` | Neural infrastructure |
| `/health` | `main.py` | Health check probe |
| `/ready` | `main.py` | Readiness probe (DB + services) |

### Legacy Routers (dynamically loaded)

These are loaded via `importlib` in `main.py` and won't crash the app if missing:
- `app.meal_scanning_api`
- `app.recommendation_api` / `app.recommendation_api_v2`
- `app.vision_api`
- `app.nlp_api`
- `app.forecast_api`
- `app.rl_api`
- `app.explainability_api`
- `app.mobile_api`
- `app.infrastructure_api`

---

## Frontend Architecture

### Tech Stack
- **React 18** with functional components and hooks
- **TypeScript** for type safety
- **Vite** for fast dev server and optimized production builds
- **Tailwind CSS v4** for utility-first styling
- **React Router v7** for SPA routing
- **Recharts** for data visualization
- **Lucide React** for icons
- **TensorFlow.js** (loaded via CDN) for client-side pose estimation

### Page Components (30+)

| Page | Route | Description |
|------|-------|-------------|
| `LoginPage` | `/` | Auth with Google OAuth + guest mode |
| `OnboardingPage` | `/onboarding` | Profile setup wizard |
| `Dashboard` | `/dashboard` | Main home with live progress cards |
| `MealScanner` | `/dashboard/food-scanner` | Camera food scanning + AI analysis |
| `WorkoutAssistant` | `/dashboard/workout` | AI workout builder + timer |
| `ExerciseBrowser` | `/dashboard/exercises` | Exercise library with search/filter |
| `NutritionHub` | `/dashboard/nutrition` | Nutrition tracking + analytics |
| `MealPlanner` | `/dashboard/meal-planner` | Weekly AI meal plans |
| `LiveCoach` | `/dashboard/coach` | Voice + text AI coaching |
| `FemmeCare` | `/dashboard/femmecare` | Menstrual cycle wellness |
| `FemaleDashboard` | `/dashboard/female` | Female-specific health hub |
| `Achievements` | `/dashboard/achievements` | Gamification badges |
| `ProgressTracking` | `/dashboard/progress` | Charts and trends |
| `BodyMeasurements` | `/dashboard/body` | Body composition |
| `SleepTracker` | `/dashboard/sleep` | Sleep quality tracking |
| `MoodTracker` | `/dashboard/mood` | Mood & energy logging |
| `ActivityTracker` | `/dashboard/activity` | Steps, distance, calories |
| `HydrationHub` | `/dashboard/hydration` | Water intake tracker |
| `SocialFeed` | `/dashboard/social` | Community feed |
| `FormCorrector` | `/dashboard/form-coach` | AI form analysis |
| `QuickWorkout` | `/dashboard/quick` | Express workouts |
| `WorkoutHistory` | `/dashboard/history` | Training log |
| `TrainingDashboard` | `/dashboard/training` | Training overview |
| `WeeklyReview` | `/dashboard/weekly` | Weekly progress review |
| `ProgressPhotos` | `/dashboard/photos` | Body transformation photos |
| `Reminders` | `/dashboard/reminders` | Notification management |
| `ExportPage` | `/dashboard/export` | Data export (PDF/CSV/JSON) |
| `WearableIntegrations` | `/dashboard/wearables` | Device connections |
| `BioLink` | `/dashboard/bio` | User profile |
| `AiInterpreter` | `/dashboard/interpreter` | AI text interpreter |
| `AdminWorkspace` | `/admin` | Admin panel (admin-only) |
| `ContactPage` | `/contact` | Contact information |
| `FeedbackPage` | `/dashboard/feedback` | Feedback submission |

### Service Layer

| Service | Description |
|---------|-------------|
| `apiService.ts` | REST client with JWT auto-refresh on 401 |
| `geminiService.ts` | Gemini AI integration (chat, meal analysis, plans) |
| `visionService.ts` | YOLOv8 + hybrid food detection client |
| `exportService.ts` | Data export to PDF, CSV, JSON |
| `storageService.ts` | LocalStorage management |
| `syncQueue.ts` | Offline sync queue for network resilience |
| `notificationService.ts` | Browser notification management |
| `deepTechService.ts` | Deep tech feature integration |
| `n8nService.ts` | n8n workflow automation hooks |

### UX Features
- **Dark/Light theme** toggle with persistent preference
- **FemmeCare theme** — pink accent when enabled
- **Animated background orbs** and glassmorphism panels
- **PWA** — installable with service worker for offline
- **i18n** — English + Hindi (extensible)
- **Responsive** — mobile-first with sidebar collapse

---

## CI/CD Pipeline

### GitHub Actions (`ci.yml`)

```
Push/PR to main → Backend Tests → Frontend Build → Docker Build
                      ↓                  ↓              ↓
                Python 3.10/3.11   TypeScript Check   Image Build
                pytest + coverage   Vitest + Build     Backend + Frontend
                Ruff linting       Output verify
```

### Deployment Targets
- **Frontend:** Vercel (configured via `vercel.json`)
- **Backend:** Render, Railway, or any Docker host
- **Full Stack:** Docker Compose with health checks

---

## Security Measures

| Layer | Implementation |
|-------|----------------|
| **Authentication** | JWT with access + refresh token rotation |
| **Password Storage** | bcrypt with cost factor 12 |
| **Rate Limiting** | Token-bucket: AI 10/min, Write 30/min, Read 120/min |
| **CORS** | Strict origin enforcement (no wildcards in production) |
| **Production Guards** | App fails fast on missing secrets via `config.py` |
| **FemmeCare Privacy** | Sensitive health data encrypted at rest |
| **Input Validation** | Pydantic schemas on all endpoints |
| **SQL Injection** | SQLAlchemy ORM with parameterized queries |
| **Optimistic Locking** | Version column on EnhancedUser model |
| **Headers** | X-Content-Type-Options, X-Frame-Options, Referrer-Policy |
| **Docs Gating** | Swagger UI disabled in production |

---

## Maintenance Guidance

- Update this document whenever a new API router, database model, or page component is added.
- Keep the README (`README.md`) user-facing and visually rich; keep this file technical and structural.
- Remove references to deleted or abandoned features promptly.
- All new features should have at least one test in `backend/tests/` or `frontend/src/**/*.test.tsx`.
- Run `python -m pytest -q` and `npm test` before merging to main.
