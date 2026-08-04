"""
Empirical Stress Test Harness for Milestone 3 (ML Model Training, Fallbacks & Integration)
Written by Challenger 2 (.agents/challenger_m3_2)
"""

import os
import sys
import json
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))

def run_empirical_verification():
    print("=" * 70)
    print(" EMPIRICAL VERIFICATION HARNESS - CHALLENGER 2 (MILESTONE 3)")
    print("=" * 70)
    
    findings = []
    
    # ---------------------------------------------------------
    # TEST 1: MLP Metrics File Verification & Math Consistency
    # ---------------------------------------------------------
    print("\n[TEST 1] Verifying mlp_metrics.json files and metric math...")
    mlp_json_paths = [
        backend_dir / "ml" / "mlp_metrics.json",
        backend_dir / "app" / "training" / "models" / "neural_model" / "mlp_metrics.json"
    ]
    
    for p in mlp_json_paths:
        if not p.exists():
            findings.append(f"CRITICAL: Metrics file missing at {p}")
            continue
            
        with open(p, "r") as f:
            data = json.load(f)
            
        print(f"  Inspecting {p.relative_to(root_dir)}:")
        print(f"    - Accuracy: {data.get('accuracy')}%")
        print(f"    - Precision: {data.get('precision')}")
        print(f"    - Recall: {data.get('recall')}")
        print(f"    - F1 Score: {data.get('f1_score')}")
        print(f"    - Train Loss: {data.get('train_loss')}")
        print(f"    - Val Loss: {data.get('val_loss')}")
        print(f"    - Input Size: {data.get('input_size')}")
        
        # Verify F1 math
        prec = data.get('precision', 0)
        rec = data.get('recall', 0)
        expected_f1 = round(2 * prec * rec / (prec + rec), 4) if (prec + rec) > 0 else 0.0
        actual_f1 = data.get('f1_score', 0)
        
        if abs(expected_f1 - actual_f1) > 0.001:
            findings.append(f"F1 Score Mismatch in {p}: expected {expected_f1}, found {actual_f1}")
        else:
            print(f"    [PASS] F1 math verified (2 * {prec} * {rec} / ({prec} + {rec}) = {expected_f1})")
            
        # Verify input_size
        if data.get('input_size') != 20:
            findings.append(f"Input size mismatch in {p}: expected 20, got {data.get('input_size')}")
        else:
            print("    [PASS] Input size 20 matches feature vector count")

    # ---------------------------------------------------------
    # TEST 2: Candidate Item Alignment & Goal Encoding Stress Test
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing Candidate Item Alignment and User Profile Key Handling...")
    try:
        from app.ml_models.recommendation_mlp import RecommendationMLP
        mlp = RecommendationMLP()
        
        # Test A: Standardized meal conversion
        raw_meal = {"id": 42, "name": "Grilled Salmon", "calories": 450, "protein": 35, "carbs": 10, "fats": 20}
        std_meal = mlp._standardize_meal(raw_meal)
        assert std_meal["nutrition"]["calories"] == 450.0
        assert std_meal["nutrition"]["protein_g"] == 35.0
        assert std_meal["nutrition"]["carbs_g"] == 10.0
        assert std_meal["nutrition"]["fat_g"] == 20.0
        print("  [PASS] RecommendationMLP._standardize_meal maps flat candidate dict to nested nutrition schema")
        
        # Test B: Profile with 'goal' vs 'primary_goal'
        profile_with_goal = {"age": 30, "weight_kg": 70, "height_cm": 175, "bmi": 22.9, "gender": "male", "goal": "muscle_gain", "activity_level": "active"}
        profile_with_primary_goal = {"age": 30, "weight_kg": 70, "height_cm": 175, "bmi": 22.9, "gender": "male", "primary_goal": "muscle_gain", "activity_level": "active"}
        
        try:
            score1 = mlp.predict_score(profile_with_goal, raw_meal)
            print(f"  Predict score with 'goal': {score1}")
        except Exception as e:
            findings.append(f"MLP predict_score failed for profile_with_goal: {e}")

        try:
            from app.training.train_neural_model import NeuralModelTrainer
            trainer = NeuralModelTrainer()
            rec1 = {"user_profile": profile_with_goal, "meal": std_meal, "label": 1}
            feats1 = trainer.extract_features(rec1)
            assert len(feats1) == 20
            print("  [PASS] NeuralModelTrainer.extract_features produces 20 features for 'goal' key")
            
            # Check what happens with 'primary_goal'
            rec2 = {"user_profile": profile_with_primary_goal, "meal": std_meal, "label": 1}
            try:
                feats2 = trainer.extract_features(rec2)
            except KeyError as ke:
                print(f"  [EDGE CASE FOUND] extract_features raises KeyError: {ke} when profile lacks 'goal' key (only has 'primary_goal')!")
                findings.append("EDGE CASE: NeuralModelTrainer.extract_features expects 'goal' key in user profile dict. If profile uses 'primary_goal', KeyError is raised, falling back to rule score.")

        except Exception as e:
            findings.append(f"Feature extraction test error: {e}")

    except Exception as e:
        findings.append(f"RecommendationMLP test exception: {e}")

    # ---------------------------------------------------------
    # TEST 3: User Cluster Engine Encoding & Key Resilience
    # ---------------------------------------------------------
    print("\n[TEST 3] Testing UserClusterEngine encoding and assignment...")
    try:
        from app.training.user_clustering import UserClusterEngine
        engine = UserClusterEngine()
        
        prof1 = {"age": 28, "gender": "male", "weight_kg": 80, "height_cm": 180, "bmi": 24.7, "goal": "weight_loss", "activity_level": "sedentary"}
        prof2 = {"age": 28, "gender": "male", "weight_kg": 80, "height_cm": 180, "bmi": 24.7, "primary_goal": "weight_loss", "activity_level": "sedentary"}
        
        vec1 = engine._encode_profile(prof1)
        vec2 = engine._encode_profile(prof2)
        
        print(f"  Vector with 'goal': {vec1}")
        print(f"  Vector with 'primary_goal': {vec2}")
        
        if vec1[5] != vec2[5]:
            print(f"  [EDGE CASE FOUND] _encode_profile goal index mismatch: vec1[5]={vec1[5]} (weight_loss=0) vs vec2[5]={vec2[5]} (default general=1)")
            findings.append("EDGE CASE: UserClusterEngine._encode_profile only reads profile.get('goal'), ignoring profile.get('primary_goal'). Profiles with 'primary_goal' default to goal=1 ('maintenance'/'general').")
        else:
            print("  [PASS] Goal encoding matches across profile keys")
            
    except Exception as e:
        findings.append(f"UserClusterEngine test exception: {e}")

    # ---------------------------------------------------------
    # TEST 4: ResNet50 and DQN Status Label Verification
    # ---------------------------------------------------------
    print("\n[TEST 4] Verifying ResNet50 & DQN status labels...")
    resnet_path = backend_dir / "app" / "ml_models" / "resnet_classifier.py"
    dqn_path = backend_dir / "app" / "ml_models" / "reinforcement_learning.py"
    doc_path = root_dir / "PROJECT_STRUCTURE_AND_WORKING.md"
    
    with open(resnet_path, "r", encoding="utf-8") as f:
        resnet_text = f.read()
    with open(dqn_path, "r", encoding="utf-8") as f:
        dqn_text = f.read()
    with open(doc_path, "r", encoding="utf-8") as f:
        doc_text = f.read()
        
    labels_checked = 0
    if "Status: Planned / In Progress" in resnet_text:
        labels_checked += 1
        print("  [PASS] resnet_classifier.py contains explicit '[Status: Planned / In Progress]' label")
    else:
        findings.append("resnet_classifier.py missing '[Status: Planned / In Progress]' label")
        
    if "Status: Planned / In Progress" in dqn_text:
        labels_checked += 1
        print("  [PASS] reinforcement_learning.py contains explicit '[Status: Planned / In Progress]' label")
    else:
        findings.append("reinforcement_learning.py missing '[Status: Planned / In Progress]' label")
        
    if "| **Health Classifier** | ResNet50" in doc_text and "Planned / In Progress" in doc_text:
        labels_checked += 1
        print("  [PASS] PROJECT_STRUCTURE_AND_WORKING.md model table labels ResNet50 as 'Planned / In Progress'")
        
    if "| **DQN Meal Sequencer**" in doc_text and "Planned / In Progress" in doc_text:
        labels_checked += 1
        print("  [PASS] PROJECT_STRUCTURE_AND_WORKING.md model table labels DQN as 'Planned / In Progress'")

    print("\n" + "=" * 70)
    print(" VERIFICATION SUMMARY")
    print("=" * 70)
    if findings:
        print(f"Total findings/edge-cases surfaced: {len(findings)}")
        for i, f in enumerate(findings, 1):
            print(f"  {i}. {f}")
    else:
        print("All empirical checks passed with zero findings!")

if __name__ == "__main__":
    run_empirical_verification()
