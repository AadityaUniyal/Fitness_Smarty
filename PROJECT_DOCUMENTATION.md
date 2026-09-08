# SMARTY AI — Project Documentation

> Comprehensive technical reference, architecture guide, and maintenance manual.
> Last updated: September 2026

---

## 🎯 Product Overview & Architecture Summary

SMARTY AI is an athletic, enterprise-grade AI fitness, nutrition, and biometric tracking platform. It features an immersive 3D-enhanced dark-mode glassmorphic user interface paired with a multi-provider AI decision engine (Google Gemini 2.0, YOLOv8 computer vision, LSTM weight forecasting, SHAP explainable AI, and multi-armed bandit recommendation logic).

### Key System Capabilities
- **Immersive 3D Athletic Design System**: Glassmorphism (`backdrop-blur-md bg-neutral-900/80 border-white/10`), dynamic tilt hook (`use3DTilt`), neon accent gradients (Emerald, Electric Cyan, Aura Pink, Amber), and scanline micro-interactions.
- **Explainable Daily Coaching**: Multi-provider AI recommendations detailing precise reasoning behind training, recovery, and nutrition adjustments.
- **Computer Vision Food Scanner**: Hybrid pipeline utilizing YOLOv8 object detection combined with Gemini 2.0 multimodal vision analysis.
- **FemmeCare Cycle Support**: Menstrual cycle tracking, hormonal phase-aware training limits, and micro-nutrient recommendations (iron, magnesium).
- **Gamification Engine**: XP progression, level milestones, streaks, badge unlocks, and live achievements tracking.
- **Predictive Deep Tech Suite**: Weight trend forecasting via LSTM, target weight goal projection dates, and SHAP feature importance analysis.
- **Zero-Error Quality**: 100% type-checked React 18 / TypeScript frontend with 34 passing Vitest unit tests across 14 test suites and clean production Vite bundle compilation.

---

## 📁 Repository Layout

```
Smarty-reco/
├── backend/                  # FastAPI Application & AI Core
│   ├── main.py               # Entry point, router registration, lifespan events
│   ├── app/                  # Application core package
│   │   ├── api/              # 39 API router modules (auth, meals, coach, etc.)
│   │   ├── models.py         # 50+ SQLAlchemy ORM models
│   │   ├── database.py       # Engine, DB sessions, seed utilities
│   │   ├── config.py         # Pydantic Settings with production fail-fast guards
│   │   ├── auth.py           # JWT authentication & password hashing (bcrypt)
│   │   ├── unified_coach_service.py # Central coaching & explanation engine
│   │   ├── gamification_service.py  # XP, badges, achievements, streaks
│   │   ├── gender_specific_service.py # FemmeCare cycle-aware logic
│   │   └── deep_tech/        # Forecasting, SHAP, & ML models
│   ├── tests/                # Pytest unit & integration test suites
│   ├── migrations/           # Alembic database migrations
│   └── seed_neon_database.py # Database seeder script
├── frontend/                 # React 18 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── pages/            # 30+ dashboard page components
│   │   ├── components/       # 25+ reusable UI components (PageFrame, DailyChecklist, etc.)
│   │   ├── services/         # 10 service clients (apiService, geminiService, deepTechService)
│   │   ├── hooks/            # Custom hooks (use3DTilt, useCurrentUserId, useUserProfile)
│   │   ├── contexts/         # AuthContext with JWT & local state persistence
│   │   ├── styles/           # Global styles & animation patterns
│   │   └── types/            # Strict TypeScript interfaces
│   └── public/               # Static assets, web manifest, service worker
├── docker/                   # Docker Compose, Dockerfile, Nginx configs
├── .github/workflows/        # CI/CD pipeline definitions
├── vercel.json               # Vercel deployment configuration
├── verify_all.bat            # Automated build & test execution script
└── README.md                 # Product overview & quickstart guide
```

---

## ⚙️ Backend Architecture

### Request Processing Lifecycle
1. Request arrives at `main.py` → CORS headers & Security Middleware.
2. Token-bucket rate limiter (`limiter.py`) evaluates client quota.
3. Auth middleware validates JWT bearer token header.
4. Route handler processes request via service modules.
5. AI requests route to Gemini API or YOLOv8 inference engines.
6. SQL transactions commit via SQLAlchemy ORM to PostgreSQL (Neon) or SQLite.
7. Pydantic schemas serialize and validate response payload.

### Primary API Router Groups (39 Routers)

| Endpoint Group | Router File | Description |
|----------------|-------------|-------------|
| `/api/auth` | `api/auth.py` | JWT login, registration, token refresh |
| `/api/auth/oauth` | `api/oauth.py` | Google OAuth 2.0 integration |
| `/api/users` | `api/users.py` | User profile & goal settings |
| `/api/coach` | `api/coach.py` | Unified daily coach & SHAP explanations |
| `/api/ai` | `api/ai_coach.py` | Gemini chat & interactive workout/meal AI |
| `/api/meals` | `api/meals.py` | Meal logging, image scans, nutrition breakdown |
| `/api/exercises` | `api/exercises.py` | Exercise library search & filtering |
| `/api/hydration` | `api/hydration.py` | Water intake logging & goals |
| `/api/female` | `api/female.py` | FemmeCare cycle tracking & guidance |
| `/api/gamification` | `api/gamification.py` | User XP, streaks, level progression |
| `/api/forecast` | `api/forecast_api.py` | Weight forecasting & goal date projections |
| `/api/admin` | `api/admin.py` | Admin workspace & user governance |

---

## 🎨 Frontend Architecture & Design System

### 3D Dark-Mode Brand System
- **Background**: Deep obsidian slate (`bg-slate-950` / `bg-neutral-950`).
- **Containers**: Glassmorphic panels with subtle borders (`backdrop-blur-md bg-neutral-900/80 border-white/10`).
- **Accent Tones**:
  - **Emerald**: Core athletic progress, health stats, success states.
  - **Electric Cyan**: Neural AI indicators, telemetry, active metrics.
  - **Aura Pink**: FemmeCare cycle guidance & health mode.
  - **Amber/Orange**: Streaks, alerts, energy levels.
- **Interactions**:
  - **Tilt Effect**: `use3DTilt` hook provides dynamic 3D perspective tilt on hover.
  - **Animations**: CSS keyframe glows, pulse indicators, smooth accordion transitions.

### Page Component Architecture (30+ Screens)
- `Dashboard.tsx`: Hero status hub, daily coach card, quick telemetry, telemetry charts.
- `MealScanner.tsx`: Real-time food image scanning with multi-item nutritional estimation.
- `WorkoutAssistant.tsx`: Interactive AI workout builder with set/rep timers.
- `FemmeCare.tsx`: Cycle tracking, phase guidance, and symptom logging.
- `MealPlanner.tsx`: AI weekly meal schedule generator with fallback offline support.
- `Analytics.tsx`: Biometric trend charts (steps, weight, heart rate) with LSTM forecasting.
- `Achievements.tsx`: Visual trophy case for unlocked badges and streak milestones.

---

## 🧪 Testing & Verification

### Vitest Unit Test Suite (`frontend/`)
- **Total Test Files**: `14 passed (14)`
- **Total Unit Tests**: `34 passed (34)`
- **Coverage Highlights**:
  - `AuthContext.test.tsx`: Login, register, token handling.
  - `Dashboard.test.tsx`: Telemetry rendering, async coach card loading.
  - `DailyChecklist.test.tsx`: Array safety, task toggling, task deletion.
  - `FemmeCare.test.tsx`: Cycle advice loading, period log submission, setting sync.
  - `MealPlanner.test.tsx`: AI meal plan generation & backend fallback logic.
  - `LoginPage.test.tsx`: Form mode toggles, guest login flow, input validation.

### Production Build Verification
- **Command**: `npm run build`
- **Output**: 2,269 modules transformed in 10.66s with `0 errors`.

---

## 🔒 Security & Performance Guidelines

1. **Authentication**: JWT access token rotation with short expiry and secure localStorage / HTTP-only cookie strategy.
2. **Input Validation**: Strict typing across Pydantic backend models and TypeScript frontend interfaces.
3. **Optimistic UI Updates**: State mutations update locally with graceful rollback on API errors.
4. **Offline Resilience**: Essential features degrade gracefully to cached localStorage state when network is unavailable.
