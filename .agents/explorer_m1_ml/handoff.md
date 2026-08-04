# Handoff Report — Explorer 2 (ML Models & Hybrid Ranker Audit)

## 1. Observation
Direct evidence gathered from inspecting the codebase:

1. **LSTM Weight Predictor**:
   - `backend/app/ml_models/lstm_predictor.py` line 102:
     ```python
     if self.mock_mode or len(historical_data) < 7:
         return self._mock_predict(historical_data, days_ahead)
     ```
     `_mock_predict` (line 186): `pred_weight = current_weight - (day * 0.08)`. No moving-average fallback exists.
   - `backend/app/ml_models/train_lstm.py` line 121: `seq_length = 30`. Saves `lstm_weights.pth` and `lstm_config.json`.
   - `backend/app/training/train_lstm.py` line 80: `seq_length = 14`. Saves `lstm_weight.pth` and `scaler.joblib`.
   - Searching for `lstm_metrics.json` across `backend/`: 0 files found.

2. **Collaborative Filtering**:
   - `backend/app/recommendation_api_v2.py` lines 35-87: `get_real_user_meal_ratings(db)` queries `MealLog` table (`log.user_feedback` True -> 5.0, False -> 1.0, None -> 3.0).
   - Lines 109-116: If `<2` users or `<3` ratings, sets `is_mock_fallback = True` and hardcodes `{1: {1: 5.0, 2: 4.0...}}`.
   - `backend/app/hybrid_ranker.py`: Contains ZERO references to `collaborative_filtering` or CF scores.

3. **Recommendation MLP**:
   - `backend/app/training/train_neural_model.py` lines 286-288: `X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)`.
   - Searching for `mlp_metrics.json` across `backend/`: 0 files found. Model saved as `model.pth` and `scaler.joblib` in `app/training/models/neural_model/`.
   - No alignment or interaction hierarchy connecting MLP (20 tabular features) to CF or ranker.

4. **K-Means User Clustering**:
   - `backend/app/training/user_clustering.py` implements `UserClusterEngine` with KMeans and GMM.
   - `backend/app/hybrid_ranker.py`: ZERO references to cluster assignments or `UserClusterEngine`.
   - `backend/app/recommendation_engine.py` line 737: Calls `engine.assign_cluster(profile_dict)` to interpolate string labels (`cluster_label`) into recommendation text. Not consumed for ranking.
   - Frontend dashboards: Admin `TrainingDashboard.tsx` line 73 lists `User Clusters` card to trigger training. User-facing dashboards do not render cluster assignments.

5. **ResNet50 & DQN**:
   - `backend/app/ml_models/resnet_classifier.py` line 28: Uses `ResNet18` (`models.resnet18`) fine-tuned on Food-101 (101 classes).
   - `backend/app/training/train_health_classifier.py` line 44: Uses `ResNet50` (`models.resnet50`) for binary healthy/unhealthy classification.
   - Docs (`PROJECT_STRUCTURE_AND_WORKING.md` line 124) & frontend (`TrainingDashboard.tsx` line 67) refer to "ResNet50".
   - `backend/app/ml_models/reinforcement_learning.py` lines 2-8: `[SCAFFOLD / MOCK IMPLEMENTATION ONLY]`. `rl_api.py` line 122 returns `'status': 'mock'`. `train_dqn.py` trains offline PyTorch model (`dqn_meal.pth`), but runtime API never loads it.

6. **Hybrid Ranker & Mifflin-St Jeor**:
   - `backend/app/hybrid_ranker.py` lines 19-25, 52-80, 105-127: Pure rule-based scoring (`goal_match`, `difficulty_match`, `recovery_clear`, `cycle_match`, `calorie_efficiency`, `protein_fit`, `cal_fit`). 0 ML models integrated.
   - `backend/app/user_profile_service.py` line 427: `_calculate_bmr` computes `(bmr_male + bmr_female) / 2`. Lines 514-516: Uses 1919 Harris-Benedict equation (`88.362 + 13.397*W + ...`) instead of Mifflin-St Jeor.
   - `backend/app/nutrition_analytics.py` & `gender_specific_service.py`: Use correct Mifflin-St Jeor equation (`10*W + 6.25*H - 5*A + (5 if male else -161)`).

---

## 2. Logic Chain
1. **Observation**: `hybrid_ranker.py` contains hardcoded weights (`EXERCISE_WEIGHTS`) and rule-based macro matching formulas, with zero imports from `ml_models/` or `training/`.
   **Inference**: `hybrid_ranker.py` is currently a pseudo-ranker operating entirely on heuristic rules rather than machine learning signals.

2. **Observation**: `collaborative_filtering.py`, `train_neural_model.py`, and `user_clustering.py` exist and train standalone models (or fallback to mock data), but their output scores are never passed into `hybrid_ranker.py`.
   **Inference**: ML models exist as isolated micro-services/endpoints without being integrated into the core recommendation decision path.

3. **Observation**: Neither `ml_models/train_lstm.py` nor `training/train_neural_model.py` writes `lstm_metrics.json` or `mlp_metrics.json`.
   **Inference**: Metric tracking is ephemeral (printed to console during training runs) rather than structured for automated evaluation or CI monitoring.

4. **Observation**: `lstm_predictor.py` uses linear weight reduction for <7 entries and edge-padding for 7-29 entries, while `training/train_lstm.py` uses `seq_length=14` and `ml_models/train_lstm.py` uses `seq_length=30`.
   **Inference**: There is a mismatch between offline training sequence lengths and online inference expectations, and moving-average fallback for <14 entries is missing.

5. **Observation**: `user_profile_service.py` calculates BMR using an ungendered average in one method and the 1919 Harris-Benedict equation in another, while `nutrition_analytics.py` and `gender_specific_service.py` use Mifflin-St Jeor.
   **Inference**: Profile calculations are duplicated and inconsistent across backend services.

---

## 3. Caveats
- Did not execute full model training scripts (e.g. running 500 episodes of DQN or training ResNet50 on GPU) as this was a read-only investigation.
- Synthetic dataset generation scripts (`generate_synthetic_user_data`, `SyntheticWeightGenerator`) were inspected statically for sequence logic and distribution parameters.

---

## 4. Conclusion
Milestone 1 audit reveals that while individual ML model training scripts and prediction classes exist (LSTM, CF, MLP, K-Means, ResNet18/50, DQN), they function as isolated standalone components. The system's core ranking engine (`hybrid_ranker.py`) is entirely rule-based. Key missing items include `lstm_metrics.json`, `mlp_metrics.json`, moving-average fallback for short weight histories, ML score blending in the ranker, and unified Mifflin-St Jeor metabolic calculations.

---

## 5. Verification Method

To independently verify these findings:

1. **Verify Missing Metrics Files**:
   Run search for `lstm_metrics.json` and `mlp_metrics.json`:
   ```powershell
   Get-ChildItem -Path "backend" -Recurse -Filter "*metrics.json"
   ```
   *Expected Result*: No `lstm_metrics.json` or `mlp_metrics.json` files found.

2. **Verify Hybrid Ranker Disconnection**:
   Inspect `backend/app/hybrid_ranker.py`:
   - Search for `import` statements at top of file.
   *Expected Result*: Only imports `sqlalchemy.orm.Session` and models (`ExerciseItem`, `FemaleExerciseItem`, `FoodItem`). No ML imports.

3. **Verify LSTM Fallback Logic**:
   Inspect `backend/app/ml_models/lstm_predictor.py` around line 102 and 181.
   *Expected Result*: `< 7` entries triggers `_mock_predict` (linear decrease), not moving average.

4. **Verify BMR Formula Inconsistency**:
   Inspect `backend/app/user_profile_service.py` lines 427 & 514-516.
   *Expected Result*: Line 427 averages male & female BMR; line 514 uses `88.362 + 13.397 * weight` (Harris-Benedict).
