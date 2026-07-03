/**
 * Deep Tech Service
 * Communications with Advanced ML/DL APIs (SHAP, LSTM, RL, Status)
 */

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('smarty_access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
}

export interface ModelStatus {
  available: boolean;
  status: string;
  description: string;
}

export interface ModelGroupStatus {
  models: Record<string, ModelStatus>;
  available_count: number;
  total_count: number;
}

export interface SHAPExplanation {
  recommendation: string;
  shap_values: Record<string, number>;
  explanation: string;
  confidence: number;
  model: string;
}

export interface FeatureImportance {
  model: string;
  features: Record<string, number>;
  top_features: Array<[string, number]>;
}

export interface DecisionStep {
  step: number;
  condition: string;
  action: string;
  result: string;
}

export interface DecisionPath {
  decision_path: DecisionStep[];
  final_prediction: any;
  confidence: number;
}

export interface WeightForecastPoint {
  date: string;
  predicted_weight: number;
  confidence: number;
}

export interface WeightForecastResult {
  predictions: WeightForecastPoint[];
  trend: 'stable' | 'decreasing' | 'increasing';
  avg_change_per_week: number;
  model: string;
  confidence_score: number;
}

export class DeepTechService {
  /**
   * Fetch health and availability status of all ML models in the system
   */
  static async getNeuralNetworkHealth(): Promise<Record<string, any>> {
    const endpoints = {
      vision: `${API_BASE}/api/vision/models/status`,
      rl: `${API_BASE}/api/rl/models/status`,
      forecast: `${API_BASE}/api/forecast/models/status`,
      explainability: `${API_BASE}/api/explain/models/status`
    };

    const results: Record<string, any> = {};

    for (const [key, url] of Object.entries(endpoints)) {
      try {
        const res = await fetch(url, { headers: getAuthHeaders() });
        if (res.ok) {
          results[key] = await res.json();
        } else {
          results[key] = { error: `HTTP Error ${res.status}` };
        }
      } catch (e) {
        results[key] = { error: 'Offline / Could not reach node' };
      }
    }

    return results;
  }

  /**
   * Explain a specific recommendation using SHAP values
   */
  static async explainRecommendation(
    mealId: number,
    name: string,
    score: number,
    proteinTarget = 150,
    calorieTarget = 2000,
    preferredIngredients: string[] = []
  ): Promise<SHAPExplanation> {
    try {
      const res = await fetch(`${API_BASE}/api/explain/recommendation`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          recommendation: { meal_id: mealId, name, score },
          user_features: {
            protein_target: proteinTarget,
            calorie_target: calorieTarget,
            preferred_ingredients: preferredIngredients
          }
        })
      });
      if (!res.ok) throw new Error(`SHAP explanation failed: ${res.statusText}`);
      return await res.json();
    } catch { throw new Error('SHAP explanation failed'); }
  }

  static async getFeatureImportance(modelName: string): Promise<FeatureImportance> {
    try {
      const res = await fetch(`${API_BASE}/api/explain/feature-importance/${modelName}`, {
        headers: getAuthHeaders()
      });
      if (!res.ok) throw new Error(`Failed to fetch feature importance for ${modelName}`);
      return await res.json();
    } catch { throw new Error(`Failed to fetch feature importance for ${modelName}`); }
  }

  static async getDecisionPath(mealName: string, calories: number): Promise<DecisionPath> {
    try {
      const res = await fetch(`${API_BASE}/api/explain/decision-path`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ name: mealName, calories })
      });
      if (!res.ok) throw new Error('Failed to fetch decision path');
      return await res.json();
    } catch { throw new Error('Failed to fetch decision path'); }
  }

  static async forecastWeight(
    historicalData: Array<{ date: string; weight: number; calories?: number; activity_minutes?: number }>,
    daysAhead = 7
  ): Promise<WeightForecastResult> {
    const formattedData = historicalData.map(d => ({
      date: d.date,
      weight: d.weight,
      calories: d.calories ?? 2000,
      activity_minutes: d.activity_minutes ?? 30
    }));
    try {
      const res = await fetch(`${API_BASE}/api/forecast/predict-weight?days_ahead=${daysAhead}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(formattedData)
      });
      if (!res.ok) throw new Error('Weight forecasting failed');
      return await res.json();
    } catch { throw new Error('Weight forecasting failed'); }
  }
}

export default DeepTechService;
