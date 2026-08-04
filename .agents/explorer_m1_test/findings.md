# Audit Findings: Test Suite & Documentation (Milestone 1)

**Audit Date**: 2026-08-02  
**Auditor**: Explorer 3 (Test Suite & Docs Audit)  
**Target Repository**: `c:/Users/HP/OneDrive/Desktop/Smarty-reco`

---

## Executive Summary

This audit evaluated the existing test suite and technical documentation in the `Smarty-reco` repository for Milestone 1 of the Pure-ML Transformation Plan.

Key Findings:
1. **Test Baseline**: Standard pytest execution against `backend/tests` yields **144 Passed, 2 Skipped, 0 Failed** out of 146 collected tests (execution time ~84s).
2. **Missing Unit Tests**: `hybrid_ranker.py` (`HybridRanker`) has **0 unit tests**. Duplicate Mifflin-St Jeor calculator implementations in `gender_specific_service.py`, `user_profile_service.py`, and `analytics_api.py` lack unit tests (only `nutrition_analytics.py` is tested).
3. **Flawed Model Loading Assertions**: Smoke test files `test_phase1_all_models.py`, `test_phase2_nlp.py`, and `test_phase3_forecast.py` use `assert response.status_code in {200, 400, 500}`, which treats server crashes (500 errors) as passing tests.
4. **Obsolete Gemini References**: `README.md`, `PROJECT_DOCUMENTATION.md`, and `PROJECT_STRUCTURE_AND_WORKING.md` contain 20+ obsolete references to Google Gemini Pro/Flash LLM orchestration and Gemini Vision API.
5. **Undocumented Visual Fallback Heuristics**: `PROJECT_STRUCTURE_AND_WORKING.md` mentions visual fallback heuristics without defining the bounding-box, density scaling, and confidence threshold logic present in `food_detection_model.py`.
6. **Model Status Ambiguity**: The model status table in `PROJECT_STRUCTURE_AND_WORKING.md` lacks status labels for **ResNet50** (confused with ResNet18 vs health classifier) and **DQN** (currently 100% mock-mode in runtime).

---

## 1. Test Suite Audit

### 1.1 Baseline Test Execution Summary
- **Command**: `pytest` (executed in `backend/`)
- **Config**: `backend/pytest.ini` (`testpaths = tests`, `pythonpath = .`)
- **Total Test Files Collected**: 34 files in `backend/tests/`
- **Total Test Cases Collected**: 146 items
- **Passed**: 144
- **Skipped**: 2
  1. `backend/tests/test_neon_connection.py::test_neon_connection` — Skipped (Requires live internet connection to Neon PostgreSQL DB, unreachable in CODE_ONLY environment).
  2. `backend/tests/test_phase1_complete.py::test_phase1_complete` — Skipped (Requires live FastAPI backend server running on `http://localhost:8000`).
- **Failed**: 0

### 1.2 Inventory of Test Files (`backend/tests/`)

| # | Test File | Primary Focus | Status / Notes |
|---|---|---|---|
| 1 | `test_admin_api.py` | Admin metrics, user management, system health | Passed (4 tests) |
| 2 | `test_aim_foods.py` | AI food detection mapping | Passed (1 test) |
| 3 | `test_analytics.py` | Analytics summary endpoints | Passed (1 test) |
| 4 | `test_anomaly_detector.py` | Calorie, macro & hydration Z-score anomaly detector | Passed (6 tests) |
| 5 | `test_async_jobs.py` | Async task execution endpoints | Passed (1 test) |
| 6 | `test_auth_flow.py` | Auth registration, login, JWT flow | Passed (10 tests) |
| 7 | `test_backend_extensions.py` | Extended backend API routes | Passed (11 tests) |
| 8 | `test_caching_limiter.py` | Rate limiter and caching middleware | Passed (2 tests) |
| 9 | `test_calorie_calculator.py` | BMR (Mifflin-St Jeor) & TDEE calculation logic | Passed (12 tests) |
| 10 | `test_db_training.py` | Database training data ingestion | Passed (1 test) |
| 11 | `test_env_vars.py` | Environment variable parsing | Passed (1 test) |
| 12 | `test_explainability.py` | Explainability API endpoints | Passed (1 test) |
| 13 | `test_femmecare_advanced.py` | FemmeCare cycle sync logic | Passed (4 tests) |
| 14 | `test_gamification_service.py` | XP, level calculation, badge unlocks, streaks | Passed (1 test) |
| 15 | `test_grounded_assistant.py` | Grounded assistant advice | Passed (1 test) |
| 16 | `test_idempotency_locking.py` | Idempotency middleware & locking | Passed (2 tests) |
| 17 | `test_image_validation.py` | Image preprocessing & validation | Passed (7 tests) |
| 18 | `test_lstm_predictor.py` | LSTM weight predictor model | Passed (3 tests) |
| 19 | `test_meal_scanner.py` | Meal scanner macro evaluation | Passed (1 test) |
| 20 | `test_neon_connection.py` | Neon DB live connection | **Skipped** (Network dependent) |
| 21 | `test_new_api.py` | Endpoints across workouts, meals, exercises | Passed (30 tests) |
| 22 | `test_phase1_all_models.py` | Vision model endpoints smoke test | Passed (4 tests) — *Weak assertion* |
| 23 | `test_phase1_complete.py` | Live HTTP server smoke test | **Skipped** (Requires localhost:8000) |
| 24 | `test_phase2_nlp.py` | NLP recipe & CLIP endpoints smoke test | Passed (5 tests) — *Weak assertion* |
| 25 | `test_phase3_forecast.py` | LSTM & Prophet forecasting smoke test | Passed (4 tests) — *Weak assertion* |
| 26 | `test_portion_optimizer.py` | Serving weight portion optimization | Passed (1 test) |
| 27 | `test_progressive_overload.py` | Progressive overload rep/weight scaling | Passed (6 tests) |
| 28 | `test_recovery_engine.py` | Mission Readiness Score (MRS) & recovery | Passed (2 tests) |
| 29 | `test_safety_validator.py` | Nutrition & workout safety checks | Passed (14 tests) |
| 30 | `test_search.py` | Database search functionality | Passed (1 test) |
| 31 | `test_unified_coach.py` | Unified Coach orchestrator service | Passed (3 tests) |
| 32 | `test_vision_api.py` | YOLO & Hybrid vision endpoints | Passed (4 tests) |

*Note on orphaned test file*: `backend/test_gamification.py` is located in `backend/` root rather than `backend/tests/`. Because `pytest.ini` configures `testpaths = tests`, this file is omitted from default `pytest` runs.

### 1.3 Audit of Specific Components

#### A. Hybrid Ranker (`backend/app/hybrid_ranker.py`)
- **Status**: **UNTESTED (0 Unit Tests)**.
- **Findings**: `HybridRanker` is imported and used in `ai_coach.py`, `meal_planner.py`, and `unified_coach_service.py`, but has **zero** unit test cases in `backend/tests/`.
- **Gap**: Missing unit tests for item filtering, weight scoring, profile matching, and cold-start fallback scoring.

#### B. Mifflin-St Jeor Calculators
- **Tested Implementation**: `backend/app/nutrition_analytics.py` (`NutritionAnalytics.calculate_bmr` and `calculate_tdee`) is thoroughly tested in `backend/tests/test_calorie_calculator.py` (12 test cases covering male/female, light/heavy weight, age variations, and activity multipliers).
- **Untested Duplicate Implementations**:
  1. `backend/app/gender_specific_service.py` (`GenderSpecificService.calculate_bmr`) — No unit test.
  2. `backend/app/user_profile_service.py` (`UserProfileService.calculate_bmr`) — No unit test.
  3. `backend/app/analytics_api.py` (`calculate_bmr`) — No unit test.
  4. `backend/app/api/gender_health.py` — No unit test.
- **Gap**: Duplicate Mifflin-St Jeor calculation routines exist across services without centralized unit tests or single-source delegation.

#### C. Startup Model Loading Integration Smoke Tests
- **Files**:
  - `backend/tests/test_phase1_all_models.py`
  - `backend/tests/test_phase2_nlp.py`
  - `backend/tests/test_phase3_forecast.py`
  - `backend/tests/test_phase1_complete.py`
- **Flaw Identified**: In `test_phase1_all_models.py` (lines 7, 16, 25), `test_phase2_nlp.py` (lines 17, 25, 34, 43), and `test_phase3_forecast.py` (lines 21, 43, 54), the assertions read:
  ```python
  assert response.status_code in {200, 400, 500}
  ```
- **Risk**: Any unhandled exception or crash during model loading (returning HTTP 500 Internal Server Error) is counted as a **PASSING** test. These assertions must be tightened to `assert response.status_code in {200, 400}` or `assert response.status_code == 200`.

---

## 2. Documentation & References Audit

### 2.1 Obsolete Gemini Service References

The codebase was transitioned to 100% deterministic Pure-ML logic, but documentation files still refer to Google Gemini LLM orchestration and Gemini Vision API.

#### A. `README.md`
- **Line 3**: `"combines local machine learning models, rule-based expert engines, and LLM orchestration (Google Gemini)..."`
- **Line 36**: `"- LLM Orchestration: Google Gemini Pro processes these structured data inputs..."`
- **Line 37**: `"- Computer Vision: Food detection utilizes YOLOv8 combined with Gemini Vision API..."`
- **Line 45**: `"- AI Meal Scanner: YOLOv8 + Gemini Vision API pipeline..."`
- **Lines 96-97**: Mermaid Diagram nodes `P[YOLOv8 + Gemini Vision]` and `Q[Google Gemini API]`.
- **Line 128**: Tech Stack: `"Google Gemini Pro & Flash (NLG & Vision)"`.
- **Line 137**: `unified_coach_service.py` description: `"...formats the contextual prompt for Google Gemini..."`.

#### B. `PROJECT_DOCUMENTATION.md`
- **Line 25**: `"Combines local expert systems... with Large Language Models (LLM) orchestration (Google Gemini)..."`
- **Lines 39-40**: Mermaid diagram nodes `Chat[Gemini Chat & Voice Coach]`, `Scanner[YOLOv8 + Gemini Meal Scanner]`.
- **Lines 64 & 82**: Mermaid nodes `Gemini[Google Gemini API Pro/Flash]`, `Orch --> Gemini`.
- **Line 172**: `"4. Requests Google Gemini to generate a cohesive Daily Briefing..."`
- **Line 220**: `GET /api/coach/daily` - `"generate the Gemini Daily Coach report."`
- **Line 235**: `geminiService.ts`: `"Integrates local chat interactions with LLM models."`
- **Lines 248-269**: `"A. YOLOv8 & Gemini Vision Meal Scanning Pipeline"` section and diagram.

#### C. `PROJECT_STRUCTURE_AND_WORKING.md`
- **Line 53**: `geminiService.ts           # Route connectors for backend AI coach endpoints`.

---

### 2.2 Documentation of Visual Fallback Heuristics

`PROJECT_STRUCTURE_AND_WORKING.md` (Line 110) states:
> *"The backend decodes the file and runs the local FoodDetectionModel (wrapping YOLOv8 or falling back to local visual matching heuristics)."*

**Audit of Code Implementation (`backend/app/food_detection_model.py`)**:
The visual fallback heuristic operates as follows:
1. **Model Fallback**: If `ultralytics` (YOLOv8) is not installed or model weight loading fails, `FoodDetectionModel` falls back to `_mock_detection` and heuristic portion sizing.
2. **Bounding Box Area Scaling**: Calculates fraction of image area `area_fraction = bbox_width * bbox_height`. Portion grams are estimated as `round(area_fraction * 400.0, 1)`, bounded between `[30.0g, 500.0g]`.
3. **Density Adjustments**:
   - **Dense Foods** (chicken, beef, pork, fish, cheese, steak): Multiplied by `1.3x`.
   - **Light Foods** (salad, lettuce, spinach, broccoli, cauliflower): Multiplied by `0.7x`.
   - **Default lookup table**: Standard portion defaults (e.g., chicken=150g, rice=200g, salad=100g).
4. **Manual Entry Fallback Trigger**: If overall confidence is `< 0.5` or no foods are detected, `should_request_manual_entry()` returns `True` and prompts user manual logging (`get_fallback_message()`).

**Documentation Deficit**: `PROJECT_STRUCTURE_AND_WORKING.md` does NOT explicitly document these bounding-box area calculations, density multipliers, and confidence threshold triggers.

---

### 2.3 Documentation Tables for Model Status (ResNet50 & DQN)

In `PROJECT_STRUCTURE_AND_WORKING.md` (Lines 120-127), the Local Training Pipeline table reads:

```markdown
| Model | Type | Dataset Source | Purpose |
| :--- | :--- | :--- | :--- |
| **Recommendation NN** | PyTorch Multi-layer Perceptron | `synthetic_meals.jsonl` + `meal_feedback.jsonl` | Predicts "good/bad" meal combinations for a profile. |
| **YOLO Food Detector** | Object Detection (CNN) | Ingested user camera logs | Identifies food bounds & ingredient types. |
| **Health Classifier** | ResNet50 | Image classes | Categorizes healthy vs. junk food from scanner pictures. |
| **User Clusters** | K-Means | DB user profiles | Groups profiles into fitness archetypes. |
| **LSTM Weight Predictor** | Recurrent Neural Net (RNN) | Time-series metrics | Forecasts user weight trends over 14-day windows. |
| **DQN Meal Sequencer** | Deep Reinforcement Learning | Simulated environment | Computes optimal meal rotation sequencing. |
```

#### Discrepancies Found:
1. **ResNet50 vs. ResNet18**:
   - `backend/app/ml_models/resnet_classifier.py` uses **ResNet18** (fine-tuned on Food-101 for 101 food classes, loaded from `weights/resnet18_food101.pth`).
   - `backend/app/training/train_health_classifier.py` trains **ResNet50** (binary healthy vs unhealthy classification, saved to `app/training/models/health_classifier/resnet50_food_health.pth`).
   - The table does not differentiate between ResNet18 (Active Food Classifier) and ResNet50 (Health Retraining Classifier).
2. **DQN Meal Sequencer Status**:
   - `backend/app/ml_models/reinforcement_learning.py` explicitly states: `WARNING: This module is currently 100% mock-mode. The DQN and Q-Learning models are simulated`.
   - `backend/app/training/train_dqn.py` provides the PyTorch DQN trainer (`dqn_meal.pth`).
   - The table does not include explicit status labels (e.g. `[Mock-Mode / Retrainable]`) for DQN.

---

## 3. Recommended Remediation Plan (Milestone 2 & Beyond)

1. **Add HybridRanker Unit Tests**: Create `backend/tests/test_hybrid_ranker.py` to test score calculations, filtering, and cold-start fallback ranking.
2. **Consolidate Mifflin-St Jeor Calculators**: Refactor `GenderSpecificService`, `UserProfileService`, and `analytics_api.py` to delegate BMR calculations to `NutritionAnalytics` or a shared utility, with unified unit tests.
3. **Fix Smoke Test Assertions**: In `test_phase1_all_models.py`, `test_phase2_nlp.py`, and `test_phase3_forecast.py`, replace `assert response.status_code in {200, 400, 500}` with strict non-500 assertions.
4. **Relocate `test_gamification.py`**: Move `backend/test_gamification.py` into `backend/tests/` so it runs automatically in CI/pytest.
5. **Clean Gemini References in Docs**: Update `README.md`, `PROJECT_DOCUMENTATION.md`, and `PROJECT_STRUCTURE_AND_WORKING.md` to remove Gemini LLM / Vision references, replacing them with deterministic expert engine and local YOLO descriptions.
6. **Define Visual Fallback Heuristics**: Update `PROJECT_STRUCTURE_AND_WORKING.md` section on meal scanning to describe the bounding-box area scaling, density factors (1.3x dense / 0.7x light), and confidence threshold triggers.
7. **Update Model Status Tables**: Add explicit status labels (`[Active - ResNet18]`, `[Retrainable - ResNet50]`, `[Mock-Mode / Retrainable - DQN]`) to `PROJECT_STRUCTURE_AND_WORKING.md`.
