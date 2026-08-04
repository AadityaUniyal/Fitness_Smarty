# Pure-ML Transformation Plan: Smarty AI Fitness Recommender

## Architecture
- **Backend Framework**: FastAPI (Python) web server with SQLAlchemy ORM.
- **ML Models**:
  - LSTM Weight Predictor (moving-average fallback for <14 entries, saves `lstm_metrics.json`).
  - Collaborative Filtering Re-ranker (blended into `hybrid_ranker.py`, cold-start rule-based fallback).
  - Recommendation MLP (PyTorch, train/val split, saves `mlp_metrics.json`, aligned hierarchy with CF).
  - K-Means User Clustering (cluster assignment active in ranker/dashboard).
  - ResNet50 & DQN (labeled explicitly as "Planned" or "In Progress" in codebase & docs).
- **Admin Dashboard**: FastAPI backend endpoints for asynchronous retraining with `is_admin=true` auth and concurrency locking.
- **Testing**: Pytest unit & integration test suite.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration & Architecture Assessment | Codebase audit for security, ML models, admin endpoints, tests & docs | None | DONE |
| 2 | Security Verification & Credentials Hardening | Remove plaintext credentials; dynamic `DATABASE_URL` & `ADMIN_PASSWORD` loading with secure fallback | M1 | DONE |
| 3 | ML Model Training, Fallbacks & Integration | LSTM, CF, MLP, K-Means models + fallbacks + metrics JSON + ResNet50/DQN doc labeling | M1, M2 | DONE |
| 4 | Hardened Admin Training Dashboard | Admin auth check (`is_admin=true`), async retraining jobs, model concurrency locking | M1, M3 | IN_PROGRESS |
| 5 | Test Suite & Documentation Alignment | Unit tests (hybrid ranker, Mifflin-St Jeor), model load smoke test, doc update (`PROJECT_STRUCTURE_AND_WORKING.md`), full clean pytest pass | M1, M3, M4 | PLANNED |

## Checklists

### Milestone 1: Exploration & Architecture Assessment
- [x] Audit DB connection string handling and admin credentials across tracked code.
- [x] Audit existing model files (`lstm_predictor.py`, `collaborative_filtering.py`, `train_neural_model.py`, `user_clustering.py`, `hybrid_ranker.py`, etc.).
- [x] Audit admin endpoints and background task support in FastAPI backend.
- [x] Audit test suite and `PROJECT_STRUCTURE_AND_WORKING.md`.

### Milestone 2: Security Verification & Credentials Hardening
- [x] Ensure no plaintext DB / admin credentials exist in tracked code.
- [x] Dynamically load `DATABASE_URL` and `ADMIN_PASSWORD`.
- [x] Implement secure random password generation fallback at seed/init time when `ADMIN_PASSWORD` is unset.

### Milestone 3: ML Model Training, Fallbacks & Integration
- [x] LSTM Weight Predictor: train on trajectories, save `lstm_metrics.json`, moving-average fallback (<14 entries), align sequence length.
- [x] Collaborative Filtering: train on feedback data, blend into `hybrid_ranker.py`, cold-start rule-based fallback.
- [x] PyTorch Recommendation MLP: train/val split, save `mlp_metrics.json`, align hierarchy with CF.
- [x] K-Means Clustering: verify cluster assignment consumption in ranker or dashboard.
- [x] ResNet50 & DQN: label as "Planned" or "In Progress" in codebase, README, and doc tables.

### Milestone 4: Hardened Admin Training Dashboard
- [ ] Mount `training_api.py` in `backend/main.py`.
- [ ] Secure retraining endpoints with server-side `is_admin=true` checks.
- [ ] Implement async retraining jobs (FastAPI BackgroundTasks).
- [ ] Implement concurrency locking to block duplicate concurrent retraining runs for the same model.

### Milestone 5: Test Suite & Documentation Alignment
- [ ] Create unit tests for `hybrid_ranker.py` scoring logic and Mifflin-St Jeor calculators.
- [ ] Create integration smoke test verifying all model files load on startup; fix flawed 500 error assertions.
- [ ] Update `PROJECT_STRUCTURE_AND_WORKING.md`, `README.md`, `PROJECT_DOCUMENTATION.md` to remove Gemini references and define visual fallback heuristic.
- [ ] Run full `pytest` suite and confirm all tests pass cleanly.
- [ ] Pass Forensic Integrity Audit.
