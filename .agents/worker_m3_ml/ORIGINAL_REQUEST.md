## 2026-08-02T20:35:48Z

<USER_REQUEST>
You are Worker 3 (ML Models & Integration Worker).
Working directory: c:\Users\HP\OneDrive\Desktop\Smarty-reco\.agents\worker_m3_ml

Task: Milestone 3 — ML Model Training, Fallbacks & Integration for Smarty AI fitness recommender.

Scope & Detailed Requirements:
1. **LSTM Weight Predictor** (`backend/ml/lstm_predictor.py`):
   - Ensure training routine trains on weight trajectory data and saves metrics to `backend/ml/lstm_metrics.json`.
   - Implement moving-average fallback when user trajectory has fewer than 14 entries.
   - Align input sequence length cleanly between training and inference functions.

2. **Collaborative Filtering Re-ranker** (`backend/ml/collaborative_filtering.py` & `backend/ml/hybrid_ranker.py`):
   - Train CF model on user feedback / rating data.
   - Integrate/blend CF predictions directly into `hybrid_ranker.py` scoring logic.
   - Implement a robust rule-based fallback for cold-start users or missing interaction data.

3. **PyTorch Recommendation MLP** (`backend/ml/train_neural_model.py` & `backend/ml/recommendation_mlp.py`):
   - Add proper train/val split during model training.
   - Export evaluation metrics to `backend/ml/mlp_metrics.json`.
   - Ensure target output indices align cleanly with CF and item catalog indices.

4. **K-Means User Clustering** (`backend/ml/user_clustering.py`):
   - Verify K-Means model training and cluster assignment logic.
   - Ensure user cluster assignment is actively consumed in `hybrid_ranker.py` or recommendation pipeline.

5. **ResNet50 & DQN Status Labeling**:
   - Locate references to ResNet50 or DQN across `backend/ml/`, code comments, and doc files.
   - Explicitly label them as "Planned" or "In Progress" (visual/advanced ML features reserved for future vision integration) so status is completely accurate across code and docs.

6. **Validation & Tests**:
   - Run existing and updated tests with pytest.
   - Confirm all model fallbacks, metrics saving, and hybrid ranker execute cleanly without errors.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

When completed, write a comprehensive `handoff.md` and report your results.
</USER_REQUEST>
