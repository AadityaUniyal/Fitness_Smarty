# ML Models & Hybrid Ranker Audit Findings — Milestone 1

## Executive Summary
This document provides a comprehensive audit of all Machine Learning (ML) model components, the hybrid ranker scoring logic, and metabolic calculators (Mifflin-St Jeor equation) across the Smarty-reco codebase.

---

## 1. Audit of ML Model Components

### 1.1 LSTM Weight Predictor
- **Files Inspected**:
  - `backend/app/ml_models/lstm_predictor.py` (lines 1-209)
  - `backend/app/ml_models/train_lstm.py` (lines 1-188)
  - `backend/app/training/train_lstm.py` (lines 1-227)
  - `backend/app/forecast_api.py` (lines 1-181)
- **Trajectory Training Analysis**:
  - Two distinct, un-unified training scripts exist:
    - `backend/app/ml_models/train_lstm.py`: Trains a 2-layer PyTorch LSTM model on 60 synthetic users x 90 days. Expects `seq_length = 30`. Saves `lstm_weights.pth` and `lstm_config.json` containing normalization statistics (`means`, `stds`).
    - `backend/app/training/train_lstm.py`: Trains `LSTMTrainer` on 50 synthetic users x 90 days. Expects `seq_length = 14`. Saves model to `app/training/models/lstm/lstm_weight.pth` and `scaler.joblib`.
  - **Sequence Length Discrepancy**: Runtime predictor (`lstm_predictor.py` line 120) takes `current_seq = np.array(sequence[-30:])` assuming 30-day history, whereas `training/train_lstm.py` trains on `seq_length = 14`.
- **Metrics Saving (`lstm_metrics.json`)**:
  - **GAP / FINDING**: `lstm_metrics.json` IS NOT CREATED OR SAVED ANYWHERE IN THE CODEBASE.
  - `ml_models/train_lstm.py` outputs `lstm_config.json` with keys `means`, `stds`, `seq_length`, and `mae`.
  - `training/train_lstm.py` returns a metrics dictionary to stdout but does not persist a JSON metrics artifact.
- **Moving-Average Fallback (< 14 entries)**:
  - **GAP / FINDING**: No moving-average fallback is implemented.
  - In `lstm_predictor.py` (line 102):
    ```python
    if self.mock_mode or len(historical_data) < 7:
        return self._mock_predict(historical_data, days_ahead)
    ```
  - When `len(historical_data) < 7`, it invokes `_mock_predict` (line 181), which calculates a linear decrease: `pred_weight = current_weight - (day * 0.08)`.
  - When historical entries are between 7 and 29, `predict_weight` edge-pads the array up to 30: `np.pad(current_seq, ((pad_width, 0), (0, 0)), mode='edge')`.

---

### 1.2 Collaborative Filtering
- **Files Inspected**:
  - `backend/app/ml_models/collaborative_filtering.py` (lines 1-209)
  - `backend/app/recommendation_api_v2.py` (lines 1-377)
  - `backend/app/hybrid_ranker.py` (lines 1-152)
- **Feedback Training**:
  - In `recommendation_api_v2.py` (lines 35-87), `get_real_user_meal_ratings(db)` extracts feedback from `MealLog` table entries:
    - `log.user_feedback is True` -> rating 5.0 (Like)
    - `log.user_feedback is False` -> rating 1.0 (Dislike)
    - `log.user_feedback is None` -> rating 3.0 (Logged)
  - In `collaborative_filtering.py` (lines 42-80), `fit()` constructs a user-item rating matrix and computes cosine similarity matrices (`user_similarity` and `item_similarity`).
- **Blending into `hybrid_ranker.py`**:
  - **CRITICAL GAP**: ZERO INTEGRATION. `hybrid_ranker.py` does not import, reference, or blend scores from `CollaborativeFilteringRecommender`. The recommendation endpoint `/api/recommend/collaborative/user-based` operates as an isolated API.
- **Cold-Start Rule-Based Fallback**:
  - In `recommendation_api_v2.py` (lines 109-116): If `len(user_meal_ratings) < 2` or total ratings `< 3`, it falls back to hardcoded mock ratings:
    `{1: {1: 5.0, 2: 4.0, 3: 3.0}, 2: {1: 4.0, 4: 5.0, 5: 4.0}, ...}` with flag `is_mock_fallback = True`.
  - In `collaborative_filtering.py` (lines 98, 188), if user is not in matrix or in `mock_mode`, returns mock recommendations `_mock_recommendations(top_k)` with meal IDs 100, 101, etc.

---

### 1.3 Recommendation MLP
- **Files Inspected**:
  - `backend/app/training/train_neural_model.py` (lines 1-454)
  - `backend/app/api/neural.py` (lines 1-120)
  - `frontend/src/pages/TrainingDashboard.tsx` (lines 43-51)
- **PyTorch Train/Val Split**:
  - Architecture: `MealRecommendationNN` is a 4-layer PyTorch MLP (input 20 -> 128 -> 64 -> 32 -> 1 sigmoid).
  - Train/Val split logic in `train_neural_model.py` (lines 286-288):
    ```python
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    ```
- **Metrics Saving (`mlp_metrics.json`)**:
  - **GAP / FINDING**: `mlp_metrics.json` IS NOT SAVED ANYWHERE IN THE CODEBASE.
  - `train_neural_model.py` (lines 367-376) saves model state dict `model.pth` and `scaler.joblib` under `app/training/models/neural_model/`, but does not create `mlp_metrics.json`.
- **Interaction Hierarchy Documentation / Alignment with CF**:
  - **GAP / FINDING**: NO ALIGNMENT OR DOCUMENTATION. The MLP operates strictly as a binary classifier predicting `is_good_for_you` based on 20 tabular features (7 user demographic/goal features, 5 meal nutrition features, 8 derived macro ratios). It does not use user IDs or item IDs, nor does it share embeddings or feature spaces with Collaborative Filtering.

---

### 1.4 K-Means User Clustering
- **Files Inspected**:
  - `backend/app/training/user_clustering.py` (lines 1-444)
  - `backend/app/recommendation_engine.py` (lines 653-744)
  - `backend/app/hybrid_ranker.py` (lines 1-152)
  - `frontend/src/pages/TrainingDashboard.tsx` (lines 72-81)
- **Consumption Audit**:
  - **`hybrid_ranker.py` Consumption**: ZERO. `hybrid_ranker.py` does not reference user clusters or `UserClusterEngine`.
  - **Frontend Dashboards Consumption**: Admin `TrainingDashboard.tsx` includes a button to trigger cluster model training (`/api/training/cluster-users`). No end-user frontend dashboards render user cluster assignments or archetypes.
  - **Backend Consumption**: In `recommendation_engine.py` (line 737), `engine.assign_cluster(profile_dict)` is called to retrieve `cluster_label` (e.g. "Male / Muscle Gain / Active"), which is inserted into generic text strings (e.g. `"Your cluster ({cluster_label}) indicates..."`). The cluster assignment is not used for numeric scoring, ranking, or candidate filtering.

---

### 1.5 ResNet50 & DQN Status
- **Files Inspected**:
  - `backend/app/ml_models/resnet_classifier.py` (lines 1-231)
  - `backend/app/training/train_health_classifier.py` (lines 1-361)
  - `backend/app/ml_models/reinforcement_learning.py` (lines 1-232)
  - `backend/app/training/train_dqn.py` (lines 1-229)
  - `backend/app/rl_api.py` (lines 1-139)
  - `PROJECT_STRUCTURE_AND_WORKING.md` (lines 124, 127)
- **ResNet Audit**:
  - Model Discrepancy:
    - `resnet_classifier.py` implements a `ResNet18` model for 101 food classes (Food-101 dataset). Falls back to `_mock_classify` when `weights/resnet18_food101.pth` is missing.
    - `train_health_classifier.py` fine-tunes `ResNet50` for binary food classification (healthy vs unhealthy).
    - `PROJECT_STRUCTURE_AND_WORKING.md` and `TrainingDashboard.tsx` label the image classifier as "ResNet50", causing naming confusion between ResNet18 and ResNet50 implementations.
- **DQN Audit**:
  - Runtime Implementation: `reinforcement_learning.py` has an explicit top-level banner:
    ```
    [SCAFFOLD / MOCK IMPLEMENTATION ONLY]
    WARNING: This module is currently 100% mock-mode.
    ```
  - `rl_api.py` endpoint `/api/rl/models/status` explicitly returns `'status': 'mock'`.
  - Offline Training Script: `train_dqn.py` in `backend/app/training` trains a PyTorch DQN agent on a simulated 8-meal `MealEnvironment` and saves `dqn_meal.pth`. However, `reinforcement_learning.py` and `rl_api.py` never load `dqn_meal.pth` and remain 100% mock in production.

---

## 2. Hybrid Ranker & Mifflin-St Jeor Audit

### 2.1 `hybrid_ranker.py` Scoring Logic
- **File**: `backend/app/hybrid_ranker.py` (lines 1-152)
- **Scoring Formulas**:
  - **Exercise Ranking (`rank_exercises`)**:
    $$\text{Score} = w_{\text{goal}} \cdot \mathbb{I}_{\text{goal\_match}} + w_{\text{diff}} \cdot \mathbb{I}_{\text{diff\_match}} + w_{\text{rec}} \cdot \text{RecoveryScore} + w_{\text{cycle}} \cdot \mathbb{I}_{\text{cycle\_match}} + w_{\text{cal}} \cdot \min\left(\frac{\text{cal\_per\_min}}{10}, 1.0\right)$$
    Where $w_{\text{goal}}=3.0$, $w_{\text{diff}}=2.0$, $w_{\text{rec}}=2.5$ (or $-1.5$ if gated), $w_{\text{cycle}}=2.0$, $w_{\text{cal}}=0.5$.
  - **Food Ranking (`rank_meals_from_db`)**:
    $$\text{ProteinFit} = 1.0 - \min\left(\frac{|\text{protein} - \text{target\_protein}|}{40}, 1.0\right)$$
    $$\text{CalorieFit} = 1.0 - \min\left(\frac{|\text{calories} - \text{target\_calories}|}{500}, 1.0\right)$$
    $$\text{Score} = 2.0 \cdot \text{ProteinFit} + 1.5 \cdot \text{CalorieFit} + 0.2 \cdot \mathbb{I}_{\text{goal\_boost}} + 0.3 \cdot \mathbb{I}_{\text{elite}}$$
  - **Meal Template Scoring (`score_meal_template`)**:
    $$\text{Score} = -(2 \cdot |\text{protein\_diff}| + 0.5 \cdot |\text{cal\_diff}|)$$
- **Key Finding**: `hybrid_ranker.py` is **100% rule-based / heuristic**. Despite its name, it does NOT combine or blend machine learning model predictions (CF, MLP, LSTM, K-Means) into candidate ranking.

---

### 2.2 Mifflin-St Jeor Calculators Audit
- **Canonical Formula**:
  $$\text{BMR}_{\text{male}} = 10 \times \text{weight\_kg} + 6.25 \times \text{height\_cm} - 5 \times \text{age} + 5$$
  $$\text{BMR}_{\text{female}} = 10 \times \text{weight\_kg} + 6.25 \times \text{height\_cm} - 5 \times \text{age} - 161$$
- **Implementations & Inconsistencies**:
  1. `backend/app/nutrition_analytics.py` (`calculate_bmr`): Correct Mifflin-St Jeor (+5 male, -161 female).
  2. `backend/app/gender_specific_service.py` (`calculate_bmr_gender_specific`): Correct Mifflin-St Jeor (+5 male, -161 female, -78 other).
  3. `backend/app/user_profile_service.py`:
     - In `_calculate_bmr` (lines 423-427): Averages male and female formulas `(bmr_male + bmr_female) / 2` without inspecting user gender.
     - In `get_user_coach_profile` (lines 514-516): Uses the **1919 Harris-Benedict equation** (`88.362 + 13.397*W + 4.799*H - 5.677*A` for male, `447.593 + 9.247*W + 3.098*H - 4.330*A` for female) instead of Mifflin-St Jeor!
  4. `backend/app/training/user_clustering.py` (`generate_sample_profiles`): Correct Mifflin-St Jeor.
  5. `backend/app/ml_models/train_lstm.py` (`generate_synthetic_user_data`): Uses linear approximation `tdee = weight * 22.0 + 300.0`.

---

## Summary Gap Matrix

| Component | Status | Missing / Misaligned Features | Impact on Pure-ML Transformation |
| :--- | :--- | :--- | :--- |
| **LSTM Weight Predictor** | Partial (PyTorch) | Missing `lstm_metrics.json`, no moving average for <14 entries, seq_length mismatch (14 vs 30) | High — needs unified sequence length, JSON metric export, and fallback logic |
| **Collaborative Filtering** | Disconnected | Not blended into `hybrid_ranker.py`, falls back to hardcoded mock matrix | High — ranker needs CF score blending |
| **Recommendation MLP** | Disconnected | Missing `mlp_metrics.json`, no alignment with CF or ranker | High — ranker needs MLP inference integration & metric logging |
| **K-Means Clustering** | Unused in Ranker | Cluster assignments ignored by `hybrid_ranker.py` and user UI | Medium — requires ranker score weight adjustments based on user cluster |
| **ResNet / DQN** | Scaffold / Discrepant | ResNet18 vs ResNet50 mismatch; DQN is 100% mock scaffold in API | Medium — sync architecture names and hook trained models to API |
| **Hybrid Ranker** | Pure Heuristic | 0 ML model signals incorporated | Critical — ranker requires pure-ML transformation |
| **Metabolic Calculators** | Inconsistent | `user_profile_service.py` uses Harris-Benedict & average gender formulas | Low — standardize on `GenderSpecificService` Mifflin-St Jeor |
