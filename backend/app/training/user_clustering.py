"""
User Clustering & Segmentation

Clusters users into archetypes based on profile data (demographics, goals, activity).
Uses K-means and GMM for unsupervised segmentation.
Serves cluster assignments for personalized recommendations.
"""

import json, pickle, warnings
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass, field, asdict

import numpy as np

try:
    from sklearn.cluster import KMeans
    from sklearn.mixture import GaussianMixture
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[!] scikit-learn not available. Install with: pip install scikit-learn")

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    PLOT_AVAILABLE = True
except ImportError:
    PLOT_AVAILABLE = False


@dataclass
class UserProfile:
    age: float
    weight_kg: float
    height_cm: float
    bmi: float
    gender: int  # 0=female, 1=male
    goal: int  # encoded
    activity_level: int  # encoded
    bmr: float = 0.0
    tdee: float = 0.0


@dataclass
class ClusterInfo:
    cluster_id: int
    size: int
    centroid: List[float]
    feature_importance: Dict[str, float]
    label: str
    description: str
    typical_user: Dict[str, Any] = field(default_factory=dict)


GOAL_MAP = {'weight_loss': 0, 'maintenance': 1, 'muscle_gain': 2, 'athletic': 3, 'general': 1}
ACTIVITY_MAP = {'sedentary': 0, 'light': 1, 'moderate': 2, 'active': 3, 'very_active': 4}
GOAL_REVERSE = {0: 'weight_loss', 1: 'maintenance', 2: 'muscle_gain', 3: 'athletic'}
ACTIVITY_REVERSE = {0: 'sedentary', 1: 'light', 2: 'moderate', 3: 'active', 4: 'very_active'}


class UserClusterEngine:
    """
    User segmentation via unsupervised clustering.

    Features:
    - K-means clustering with optimal K selection (elbow + silhouette)
    - GMM for soft clustering
    - PCA visualization
    - Cluster description generation
    - New user assignment to nearest cluster
    - Model persistence
    """

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = Path(model_dir or "app/training/models/user_clusters")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.scaler = StandardScaler()
        self.kmeans: Optional[KMeans] = None
        self.gmm: Optional[GaussianMixture] = None
        self.pca: Optional[PCA] = None
        self.cluster_info: List[ClusterInfo] = []
        self.feature_names = ['age', 'weight_kg', 'height_cm', 'bmi', 'gender', 'goal', 'activity_level', 'bmr', 'tdee']
        self.mock_mode = not SKLEARN_AVAILABLE

    def _encode_profile(self, profile: Dict) -> np.ndarray:
        """Encode a user profile dict into a numerical feature vector."""
        gender = 1 if str(profile.get('gender', 'male')).lower() == 'male' else 0
        goal = GOAL_MAP.get(str(profile.get('goal', 'general')).lower(), 1)
        activity = ACTIVITY_MAP.get(str(profile.get('activity_level', 'moderate')).lower(), 2)
        bmr = profile.get('bmr', 0) or 0
        tdee = profile.get('tdee', 0) or 0
        return np.array([
            float(profile.get('age', 30)),
            float(profile.get('weight_kg', 70)),
            float(profile.get('height_cm', 170)),
            float(profile.get('bmi', 22)),
            float(gender),
            float(goal),
            float(activity),
            float(bmr),
            float(tdee),
        ], dtype=np.float32)

    def _find_optimal_k(self, X: np.ndarray, max_k: int = 10) -> Tuple[int, float]:
        """Find optimal cluster count using elbow + silhouette."""
        inertias = []
        sil_scores = []
        K_range = range(2, min(max_k + 1, len(X)))

        for k in K_range:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            km.fit(X)
            inertias.append(km.inertia_)
            sil = silhouette_score(X, km.labels_)
            sil_scores.append(sil)

        best_k = K_range[np.argmax(sil_scores)]
        best_sil = max(sil_scores)

        if PLOT_AVAILABLE:
            fig, axes = plt.subplots(1, 2, figsize=(12, 4))
            axes[0].plot(list(K_range), inertias, 'bo-')
            axes[0].set_xlabel('K')
            axes[0].set_ylabel('Inertia')
            axes[0].set_title('Elbow Method')
            axes[0].grid(alpha=0.3)
            axes[1].plot(list(K_range), sil_scores, 'ro-')
            axes[1].axvline(best_k, color='green', linestyle='--', alpha=0.5)
            axes[1].set_xlabel('K')
            axes[1].set_ylabel('Silhouette Score')
            axes[1].set_title(f'Silhouette Analysis (best K={best_k})')
            axes[1].grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig(str(self.model_dir / "optimal_k.png"), dpi=150, bbox_inches='tight')
            plt.close()

        print(f"[OK] Optimal K={best_k} (silhouette: {best_sil:.4f})")
        return best_k, best_sil

    def _generate_cluster_labels(self, centers: np.ndarray) -> List[ClusterInfo]:
        """Generate human-readable labels and descriptions for each cluster."""
        scaled_centers = self.scaler.inverse_transform(centers)
        infos = []

        for i, center in enumerate(scaled_centers):
            traits = {}
            for j, name in enumerate(self.feature_names):
                traits[name] = float(round(center[j], 2))

            age, weight, height, bmi, gender, goal, activity = center[:7]

            keywords = []
            if gender > 0.5:
                keywords.append("Male")
            else:
                keywords.append("Female")

            goal_label = GOAL_REVERSE.get(int(round(goal)), 'general')
            keywords.append(goal_label.replace('_', ' ').title())

            activity_label = ACTIVITY_REVERSE.get(int(round(activity)), 'moderate')
            keywords.append(activity_label.title())

            if age < 25:
                keywords.append("Young Adult")
            elif age < 40:
                keywords.append("Adult")
            else:
                keywords.append("Mature")

            if bmi > 27:
                keywords.append("Overweight")
            elif bmi > 24:
                keywords.append("Overweight-Targeting")
            elif bmi < 20:
                keywords.append("Lean")

            label = " / ".join(keywords[:3])

            # Generate richer description based on cluster characteristics
            desc_parts = []
            desc_parts.append(f"Age ~{int(age)}, BMI {bmi:.1f}")
            desc_parts.append(f"Goal: {goal_label.replace('_', ' ')}")

            if goal < 0.5:
                desc_parts.append("Calorie-conscious, favors lighter meals")
            elif goal > 1.5:
                desc_parts.append("High-protein, calorie-surplus oriented")
            else:
                desc_parts.append("Balanced nutrition focus")

            if activity > 2.5:
                desc_parts.append("High activity — needs energy-dense foods")
            elif activity < 1:
                desc_parts.append("Sedentary — lower calorie requirements")

            typical = {
                "age": int(round(age)),
                "gender": "Male" if gender > 0.5 else "Female",
                "weight_kg": round(float(weight), 1),
                "height_cm": round(float(height), 1),
                "bmi": round(float(bmi), 1),
                "goal": goal_label,
                "activity": activity_label,
            }

            info = ClusterInfo(
                cluster_id=i,
                size=0,
                centroid=center.tolist(),
                feature_importance={},
                label=label,
                description=" | ".join(desc_parts),
                typical_user=typical,
            )
            infos.append(info)

        return infos

    def fit(self, profiles: List[Dict], n_clusters: Optional[int] = None, method: str = 'kmeans') -> Dict:
        """
        Fit clustering model on user profiles.

        Args:
            profiles: List of user profile dicts
            n_clusters: Number of clusters (auto-detect if None)
            method: 'kmeans' or 'gmm'

        Returns:
            Clustering results with assignments and metrics
        """
        if self.mock_mode:
            print("[MOCK] User clustering simulated")
            return self._mock_fit_result(profiles)

        if len(profiles) < 5:
            print(f"[!] Too few profiles ({len(profiles)}), need at least 5")
            return self._mock_fit_result(profiles)

        print("=" * 70)
        print(f"  USER CLUSTERING ({method.upper()})")
        print("=" * 70)
        print(f"  Profiles: {len(profiles)}")
        print()

        X = np.array([self._encode_profile(p) for p in profiles])
        X_scaled = self.scaler.fit_transform(X)

        if n_clusters is None or n_clusters < 2:
            n_clusters, sil = self._find_optimal_k(X_scaled)
        else:
            n_clusters = min(n_clusters, len(X_scaled) - 1)

        if method == 'gmm':
            model = GaussianMixture(n_components=n_clusters, random_state=42, covariance_type='full')
            labels = model.fit_predict(X_scaled)
            self.gmm = model
        else:
            model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = model.fit_predict(X_scaled)
            self.kmeans = model

        # PCA for visualization
        if X_scaled.shape[1] > 2:
            self.pca = PCA(n_components=2, random_state=42)
            X_2d = self.pca.fit_transform(X_scaled)
        else:
            self.pca = None
            X_2d = X_scaled

        if PLOT_AVAILABLE:
            plt.figure(figsize=(10, 7))
            scatter = plt.scatter(X_2d[:, 0], X_2d[:, 1], c=labels, cmap='viridis', alpha=0.7, s=50)
            centers_2d = self.pca.transform(model.cluster_centers_) if method == 'kmeans' and self.pca else (
                np.random.randn(n_clusters, 2) if method != 'kmeans' else X_2d[:n_clusters]
            )
            if method == 'kmeans':
                plt.scatter(centers_2d[:, 0], centers_2d[:, 1], c='red', marker='X', s=200, linewidths=2, edgecolors='white')
            plt.colorbar(scatter, label='Cluster')
            plt.xlabel('PC1' if self.pca else 'Feature 1')
            plt.ylabel('PC2' if self.pca else 'Feature 2')
            plt.title(f'User Clusters (K={n_clusters})')
            plt.tight_layout()
            plt.savefig(str(self.model_dir / "clusters.png"), dpi=150, bbox_inches='tight')
            plt.close()

        # Generate cluster info
        centers = model.cluster_centers_ if method == 'kmeans' else self.gmm.means_
        self.cluster_info = self._generate_cluster_labels(centers)
        for info in self.cluster_info:
            info.size = int(np.sum(labels == info.cluster_id))

        # Assignments
        assignments = []
        for i, profile in enumerate(profiles):
            assignments.append({
                "profile_index": i,
                "cluster_id": int(labels[i]),
                "cluster_label": self.cluster_info[int(labels[i])].label,
                "distance_to_center": float(np.linalg.norm(X_scaled[i] - centers[int(labels[i])])),
            })

        silhouette = float(silhouette_score(X_scaled, labels)) if n_clusters > 1 else 0.0

        result = {
            "status": "success",
            "method": method,
            "n_clusters": n_clusters,
            "n_profiles": len(profiles),
            "silhouette_score": silhouette,
            "clusters": [asdict(info) for info in self.cluster_info],
            "assignments": assignments,
            "explained_variance_ratio": list(self.pca.explained_variance_ratio_) if self.pca else None,
        }

        self._save_model()
        return result

    def predict(self, profile: Dict) -> Dict:
        """Assign a new user profile to the nearest cluster."""
        if self.kmeans is None:
            self._load_model()
            if self.kmeans is None:
                return {"error": "No trained model found. Run fit() first."}

        X = self._encode_profile(profile).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        cluster_id = int(self.kmeans.predict(X_scaled)[0])
        distances = self.kmeans.transform(X_scaled)[0]
        confidence = 1.0 - (distances[cluster_id] / (distances.sum() + 1e-8))

        info = self.cluster_info[cluster_id] if cluster_id < len(self.cluster_info) else None
        return {
            "cluster_id": cluster_id,
            "cluster_label": info.label if info else f"Cluster {cluster_id}",
            "cluster_description": info.description if info else "",
            "confidence": float(confidence),
            "distance_to_center": float(distances[cluster_id]),
        }

    def _save_model(self):
        """Save trained model to disk."""
        import joblib
        if self.kmeans:
            joblib.dump(self.kmeans, self.model_dir / "kmeans.joblib")
        if self.gmm:
            joblib.dump(self.gmm, self.model_dir / "gmm.joblib")
        if self.pca:
            joblib.dump(self.pca, self.model_dir / "pca.joblib")
        joblib.dump(self.scaler, self.model_dir / "scaler.joblib")
        with open(self.model_dir / "cluster_info.json", 'w') as f:
            json.dump([asdict(ci) for ci in self.cluster_info], f, indent=2)
        print(f"[OK] Model saved to {self.model_dir}")

    def _load_model(self):
        """Load trained model from disk."""
        import joblib
        kmeans_path = self.model_dir / "kmeans.joblib"
        scaler_path = self.model_dir / "scaler.joblib"
        info_path = self.model_dir / "cluster_info.json"

        if kmeans_path.exists():
            self.kmeans = joblib.load(kmeans_path)
        if scaler_path.exists():
            self.scaler = joblib.load(scaler_path)
        if info_path.exists():
            with open(info_path) as f:
                self.cluster_info = [ClusterInfo(**d) for d in json.load(f)]

        pca_path = self.model_dir / "pca.joblib"
        if pca_path.exists():
            self.pca = joblib.load(pca_path)

    def _mock_fit_result(self, profiles: List[Dict]) -> Dict:
        n = len(profiles)
        k = min(4, max(2, n // 3))
        labels = np.random.randint(0, k, size=n)

        self.cluster_info = [
            ClusterInfo(
                cluster_id=i, size=int(np.sum(labels == i)),
                centroid=[0] * len(self.feature_names),
                feature_importance={},
                label=["Weight Loss Focus", "Muscle Building", "Balanced Lifestyle", "Athletic Performance"][i % 4],
                description=f"Simulated cluster {i}",
                typical_user={"goal": ["weight_loss", "muscle_gain", "maintenance", "athletic"][i % 4]},
            ) for i in range(k)
        ]

        return {
            "status": "mock",
            "method": "kmeans",
            "n_clusters": k,
            "n_profiles": n,
            "silhouette_score": round(0.35 + 0.15 * np.random.random(), 4),
            "clusters": [asdict(ci) for ci in self.cluster_info],
            "assignments": [{"profile_index": i, "cluster_id": int(labels[i]), "cluster_label": self.cluster_info[int(labels[i])].label} for i in range(n)],
            "note": "Simulated clustering — install scikit-learn for real clustering",
        }


def generate_sample_profiles(n: int = 200) -> List[Dict]:
    """Generate synthetic user profiles for testing."""
    profiles = []
    for _ in range(n):
        age = np.random.randint(18, 65)
        gender = np.random.choice(['male', 'female'])
        height = int(np.random.normal(175 if gender == 'male' else 162, 7))
        weight = int(np.random.normal(78 if gender == 'male' else 65, 12))
        bmi = round(weight / ((height / 100) ** 2), 1)
        goal = np.random.choice(['weight_loss', 'maintenance', 'muscle_gain', 'athletic'])
        activity = np.random.choice(['sedentary', 'light', 'moderate', 'active', 'very_active'])
        bmr = 10 * weight + 6.25 * height - 5 * age + (5 if gender == 'male' else -161)
        tdee = bmr * [1.2, 1.375, 1.55, 1.725, 1.9][['sedentary', 'light', 'moderate', 'active', 'very_active'].index(activity)]
        profiles.append({
            "age": age, "gender": gender, "height_cm": height, "weight_kg": weight,
            "bmi": bmi, "goal": goal, "activity_level": activity, "bmr": round(bmr), "tdee": round(tdee),
        })
    return profiles


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="User Clustering Engine")
    parser.add_argument("--n-profiles", type=int, default=200, help="Number of synthetic profiles")
    parser.add_argument("--n-clusters", type=int, default=None, help="Number of clusters (auto if unset)")
    parser.add_argument("--method", choices=['kmeans', 'gmm'], default='kmeans', help="Clustering method")
    args = parser.parse_args()

    profiles = generate_sample_profiles(args.n_profiles)
    engine = UserClusterEngine()
    result = engine.fit(profiles, n_clusters=args.n_clusters, method=args.method)
    print(f"\n[RESULT] {json.dumps(result, indent=2)}")

    if result["status"] != "mock":
        test_profile = profiles[0]
        assignment = engine.predict(test_profile)
        print(f"\n[PREDICT] Test profile assigned to: {json.dumps(assignment, indent=2)}")
