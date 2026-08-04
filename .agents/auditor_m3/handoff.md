# Forensic Audit Report — Milestone 3 (ML Model Training, Fallbacks & Integration)

**Work Product**: Milestone 3 ML Models, Training Pipelines, Fallback Mechanisms, Hybrid Ranker & Integration Tests
**Profile**: General Project
**Verdict**: CLEAN

---

## 1. Observation

Direct empirical observations from source code inspection and test execution:

1. **PyTorch LSTM Weight Predictor (`backend/app/ml_models/lstm_predictor.py`, `backend/app/ml_models/train_lstm.py`)**:
   - `LSTMModel` is a genuine PyTorch `nn.Module` with 2-layer LSTM and linear output layer (`nn.Linear(64, 1)`).
   - `train_lstm.py` generates synthetic trajectories, scales features, creates PyTorch `DataLoader` instances, performs backpropagation (`loss.backward()`, `optimizer.step()`), calculates holdout MAE and RMSE dynamically, and exports `lstm_metrics.json` and `lstm_weights.pth`.
   - Trajectories with fewer than 14 entries trigger moving-average fallback `_moving_average_predict()` returning model tag `"moving_average_fallback"`.

2. **Collaborative Filtering (`backend/app/ml_models/collaborative_filtering.py`)**:
   - Computes cosine similarity matrices for user-user and item-item interactions via scikit-learn (`sklearn.metrics.pairwise.cosine_similarity`).
   - `predict_score()` handles unknown/cold-start user or meal IDs by falling back cleanly to `fallback_rule_score` (default `0.50`), and blends `0.50 * cf_norm_score + 0.50 * fallback_rule_score` for known entities.
   - Dynamic metrics export produces `cf_metrics.json` recording sparsity and user/meal counts.

3. **PyTorch Recommendation MLP & Neural Trainer (`backend/app/ml_models/recommendation_mlp.py`, `backend/app/training/train_neural_model.py`)**:
   - `MealRecommendationNN` is a 4-layer PyTorch MLP (128 -> 64 -> 32 -> 1) with ReLU, Dropout, and Sigmoid activations.
   - `NeuralModelTrainer.train()` executes a full PyTorch training loop over `DataLoader`, computes test accuracy, precision, recall, and F1 score dynamically, exporting results to `mlp_metrics.json`.
   - `RecommendationMLP.predict_score()` falls back to `_rule_fallback_score()` based on nutritional goals when model is uninitialized.

4. **K-Means User Clustering (`backend/app/training/user_clustering.py`)**:
   - Uses `sklearn.cluster.KMeans` (or `GaussianMixture`) to cluster 9-dimensional user profiles, evaluating optimal K with silhouette analysis (`sklearn.metrics.silhouette_score`).
   - Generates human-readable archetype labels and typical user profiles, persisting artifacts (`kmeans.joblib`, `scaler.joblib`, `cluster_info.json`).

5. **Hybrid Ranker Integration (`backend/app/hybrid_ranker.py`)**:
   - Integrates exercise and meal candidate ranking.
   - Actively invokes `UserClusterEngine.predict(profile)` for cluster preference boosts, `CollaborativeFilteringRecommender.predict_score()` for user interaction scoring, and `RecommendationMLP.predict_score()` for deep learning score blending.

6. **Re-export Module Shims (`backend/ml/`)**:
   - `collaborative_filtering.py`, `hybrid_ranker.py`, `lstm_predictor.py`, `recommendation_mlp.py`, `train_neural_model.py`, `user_clustering.py` in `backend/ml/` cleanly re-export target classes from `app.ml_models` and `app.training`.

7. **Test Suite Execution (`backend/tests/test_m3_ml_integration.py`)**:
   - Command: `python -m pytest backend/tests/test_m3_ml_integration.py -v`
   - Results: **6 passed in 53.87s**
     - `test_lstm_moving_average_fallback` PASSED
     - `test_lstm_training_metrics_export` PASSED
     - `test_collaborative_filtering_fallback_and_predict` PASSED
     - `test_recommendation_mlp_metrics_and_scoring` PASSED
     - `test_user_clustering_engine` PASSED
     - `test_hybrid_ranker_integration` PASSED

---

## 2. Logic Chain

1. **Check 1 — Hardcoded Metrics Detection**:
   - Inspected metric exporter routines in `train_lstm.py`, `train_neural_model.py`, `collaborative_filtering.py`, `user_clustering.py`.
   - Metric values (`mae`, `rmse`, `accuracy`, `precision`, `recall`, `f1_score`, `sparsity`, `silhouette_score`) are computed dynamically from actual PyTorch tensor loss and scikit-learn evaluation metrics during run time.
   - Result: PASS — No hardcoded model metrics or static result stubs.

2. **Check 2 — Facade Training Loop Detection**:
   - Inspected PyTorch training procedures in `train_lstm.py` (lines 146–156) and `train_neural_model.py` (lines 319–335).
   - Both loops iterate over `DataLoader` batches, compute loss (`MSELoss`, `BCELoss`), zero gradients, execute `loss.backward()`, and step optimizer.
   - Result: PASS — Authentic deep learning training loops.

3. **Check 3 — Fake/Stubbed Fallback Routines**:
   - Inspected fallbacks in `lstm_predictor.py` (`_moving_average_predict`), `collaborative_filtering.py` (`predict_score` cold-start branch), and `recommendation_mlp.py` (`_rule_fallback_score`).
   - Fallbacks calculate real mathematical moving averages over available historical points or apply goal-specific nutrition heuristic rules. They are non-facade, functional, and explicitly tagged.
   - Result: PASS — Valid fallback implementations.

4. **Check 4 — Test Assertion Authenticity**:
   - Inspected assertions in `test_m3_ml_integration.py`.
   - Tests execute real training iterations, create dynamic model instances, invoke real predictions, verify generated JSON metrics on disk, and evaluate blended rank output from `HybridRanker`.
   - Result: PASS — Genuine test assertions without self-certifying or dummy mocks.

5. **Check 5 — Behavioral & Integration Verification**:
   - Executed full pytest suite on `backend/tests/test_m3_ml_integration.py`.
   - All 6 tests completed successfully with zero errors or failures.
   - Result: PASS — Behavioral verification complete.

---

## 3. Caveats

- **Network Mode**: Audit executed in `CODE_ONLY` offline mode. External dataset downloads (e.g., full Food-101 5GB tarball) use local synthetic generation fallbacks provided by the codebase.
- **Environment**: Tested on Windows OS with Python 3.13.3, PyTorch, and scikit-learn.

---

## 4. Conclusion

Milestone 3 (ML Model Training, Fallbacks & Integration) exhibits **zero integrity violations**. All model training pipelines perform genuine gradient descent / clustering, fallbacks operate correctly under boundary conditions (<14 entries, cold-start users), metrics are dynamically computed and exported, and all integration tests pass cleanly.

**Final Integrity Verdict**: **CLEAN**

---

## 5. Verification Method

To independently verify this audit:

```bash
cd c:\Users\HP\OneDrive\Desktop\Smarty-reco
pytest backend/tests/test_m3_ml_integration.py -v
```

Expected result: 6 passed tests in ~50–60s.
