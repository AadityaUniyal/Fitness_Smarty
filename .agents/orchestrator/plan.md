# Validation & Sweep Plan: Fitness Smarty Recommender

## Architecture
- **Frontend**: React (Vite) + TS, including App.tsx, Dashboard.tsx, and 30+ dashboard routes/components. Supports dynamic theme switching based on profile gender (emerald/green for general, pink/female-theme for female/FemmeCare profiles) and language locale (EN/HI).
- **Backend**: FastAPI (Python) web server with SQLAlchemy ORM, exposing endpoints for auth, recommendation engine, meal scanning (YOLOv8 + Gemini), time-series forecasting (LSTM), FemmeCare tracking, etc.
- **Database**: Dual storage capability: local SQLite for local dev, Neon Serverless PostgreSQL for production (specified in backend/.env).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Setup & Environment Verification | Verify backend & frontend dependencies, check configuration (e.g. .env, database URLs) | None | DONE |
| 2 | Backend API Endpoint Verification | Run pytest suite to verify login, registration, workouts, foods, and cycle-phase tracking routes | M1 | IN_PROGRESS |
| 3 | Database State Sync Verification | Verify direct writes and data sync to the Neon PostgreSQL database for active user sessions | M1, M2 | PLANNED |
| 4 | Frontend & Theme Walkthrough | Run vitest suite and execute walkthrough checklist for 30+ dashboard shell routes, dynamic theme switching for female profiles, and viewport simulation | M1, M2 | PLANNED |
| 5 | Synthesis & Final Sweep Report | Compile aggregated sweep findings, run Forensic Audit validation, and report to Sentinel | M1, M2, M3, M4 | PLANNED |

## Validation & Checklists

### Milestone 1: Setup & Environment Verification
- [ ] Backend dependencies are installed (pip packages).
- [ ] Frontend dependencies are installed (npm packages).
- [ ] Database credentials (Neon and local) are verified.
- [ ] Environment variables (.env) are valid and loaded.

### Milestone 2: Backend API Endpoint Verification
- [ ] Run backend tests (e.g., `pytest tests/`) to check all major endpoints.
- [ ] Specifically verify routes for:
  - Auth (`/api/auth/register`, `/api/auth/login`, `/api/auth/me`)
  - Workouts (`/api/workouts`)
  - Foods/Nutrition (`/api/foods`, `/api/meals`)
  - FemmeCare/Cycle-phase tracking (`/api/femmecare`)
- [ ] Verify mock vs production model fallback behavior.

### Milestone 3: Database State Sync Verification
- [ ] Confirm backend correctly performs writes and updates to the Neon PostgreSQL database.
- [ ] Verify database states after registering a new user, updating onboarding profiles, and setting goals.
- [ ] Confirm no data loss or schema mismatches exist on Neon PostgreSQL.

### Milestone 4: Frontend & Theme Walkthrough
- [ ] Verify Vitest suite passes for React components.
- [ ] Ensure all 30+ navigation sidebar tabs in `App.tsx` resolve to valid components.
- [ ] Verify theme switches to `female-theme` (pink accent) when a female profile is active or registered.
- [ ] Verify desktop and mobile viewport behavior (layout adaptability, mobile menu sidebar toggle).

### Milestone 5: Synthesis & Final Sweep Report
- [ ] Run Forensic Auditor check to verify implementation authenticity and lack of cheat hacks.
- [ ] Synthesize all test outputs and findings.
- [ ] Create E2E Validation Sweep Report.
- [ ] Notify Sentinel and submit handoff.
