"""
Prophet Trend Analyzer

Time-series trend analysis and forecasting using Facebook Prophet
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pandas as pd
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except Exception as e:
    pd = None
    PROPHET_AVAILABLE = False
    print(f"[!] Prophet/pandas not available: {e}. Using mock mode.")


class ProphetTrendAnalyzer:
    """
    Facebook Prophet for nutrition trend analysis
    
    Analyzes trends in calories, macros, and provides forecasts
    """
    
    def __init__(self):
        """Initialize Prophet analyzer"""
        self.mock_mode = not PROPHET_AVAILABLE
        
        if PROPHET_AVAILABLE:
            print("[OK] Prophet trend analyzer initialized")
        else:
            print("[!] Prophet not installed. Using mock mode.")
    
    def analyze_nutrition_trends(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_days: int = 14
    ) -> Dict[str, Any]:
        """
        Analyze and forecast nutrition trends
        
        Args:
            historical_data: List of {date, calories, protein_g, carbs_g, fat_g}
            forecast_days: Days to forecast
            
        Returns:
            {
                'calories_trend': {...},
                'protein_trend': {...},
                'forecast': [...],
                'insights': [...]
            }
        """
        if self.mock_mode or len(historical_data) < 14:
            return self._mock_analysis(historical_data, forecast_days)
        
        try:
            # Analyze each metric
            results = {
                'calories_trend': self._analyze_metric(historical_data, 'calories', forecast_days),
                'protein_trend': self._analyze_metric(historical_data, 'protein_g', forecast_days),
                'carbs_trend': self._analyze_metric(historical_data, 'carbs_g', forecast_days),
                'fat_trend': self._analyze_metric(historical_data, 'fat_g', forecast_days)
            }
            
            # Generate insights
            insights = self._generate_insights(results)
            results['insights'] = insights
            results['model'] = 'prophet'
            
            return results
            
        except Exception as e:
            print(f"Error in Prophet analysis: {e}")
            return self._mock_analysis(historical_data, forecast_days)
    
    def _analyze_metric(
        self,
        data: List[Dict],
        metric: str,
        forecast_days: int
    ) -> Dict[str, Any]:
        """Analyze single metric with Prophet, with fallback for constant/zero-variance data or Stan failures"""
        try:
            # Prepare DataFrame
            df = pd.DataFrame([
                {
                    'ds': datetime.strptime(d['date'], '%Y-%m-%d') if isinstance(d['date'], str) else d['date'],
                    'y': float(d.get(metric, 0))
                }
                for d in data
            ])
            
            # Check if variance is near 0 or data length small
            if df['y'].std() < 1e-5:
                return self._fallback_metric_analysis(df, metric, forecast_days)

            # Fit Prophet model
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=False
            )
            model.fit(df)
            
            # Make forecast
            future = model.make_future_dataframe(periods=forecast_days)
            forecast = model.predict(future)
            
            # Extract key info
            recent_actual = float(df['y'].tail(7).mean())
            forecast_avg = float(forecast['yhat'].tail(forecast_days).mean())
            trend = 'increasing' if forecast_avg > recent_actual + 1e-3 else 'decreasing' if forecast_avg < recent_actual - 1e-3 else 'stable'
            
            # Get forecast values
            forecast_values = []
            for idx in range(-forecast_days, 0):
                forecast_values.append({
                    'date': str(forecast.iloc[idx]['ds'].strftime('%Y-%m-%d')),
                    'predicted': round(float(forecast.iloc[idx]['yhat']), 1),
                    'lower_bound': round(float(forecast.iloc[idx]['yhat_lower']), 1),
                    'upper_bound': round(float(forecast.iloc[idx]['yhat_upper']), 1)
                })
            
            change_pct = float((forecast_avg - recent_actual) / recent_actual * 100) if recent_actual != 0 else 0.0

            return {
                'metric': metric,
                'trend': trend,
                'recent_avg': round(recent_actual, 1),
                'forecast_avg': round(forecast_avg, 1),
                'change_percent': round(change_pct, 1),
                'forecast': forecast_values
            }
        except Exception as e:
            print(f"[!] Prophet _analyze_metric fallback for {metric}: {e}")
            df = pd.DataFrame([
                {
                    'ds': datetime.strptime(d['date'], '%Y-%m-%d') if isinstance(d['date'], str) else d['date'],
                    'y': float(d.get(metric, 0))
                }
                for d in data
            ])
            return self._fallback_metric_analysis(df, metric, forecast_days)

    def _fallback_metric_analysis(
        self,
        df: Any,
        metric: str,
        forecast_days: int
    ) -> Dict[str, Any]:
        """Fallback analysis for constant values or Prophet fitting failures"""
        recent_avg = float(df['y'].tail(7).mean()) if not df.empty else 0.0
        last_date = df['ds'].iloc[-1] if not df.empty else datetime.now()
        
        forecast_values = []
        for i in range(forecast_days):
            pred_date = last_date + timedelta(days=i+1)
            forecast_values.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'predicted': round(recent_avg, 1),
                'lower_bound': round(recent_avg * 0.95, 1),
                'upper_bound': round(recent_avg * 1.05, 1)
            })
            
        return {
            'metric': metric,
            'trend': 'stable',
            'recent_avg': round(recent_avg, 1),
            'forecast_avg': round(recent_avg, 1),
            'change_percent': 0.0,
            'forecast': forecast_values
        }
    
    def _generate_insights(self, results: Dict) -> List[str]:
        """Generate actionable insights from trends"""
        insights = []
        
        # Calorie insights
        cal_trend = results['calories_trend']
        if cal_trend['trend'] == 'increasing':
            insights.append(f"[UP] Calories trending up ({cal_trend['change_percent']:+.1f}%). Consider portion control.")
        elif cal_trend['trend'] == 'decreasing':
            insights.append(f"[DOWN] Calories trending down ({cal_trend['change_percent']:+.1f}%). Ensure adequate nutrition.")
        
        # Protein insights
        prot_trend = results['protein_trend']
        if prot_trend['forecast_avg'] < 50:
            insights.append("[FIT] Protein intake below recommended. Add lean meats, eggs, or legumes.")
        elif prot_trend['trend'] == 'increasing':
            insights.append("[FIT] Great job increasing protein! Supports muscle recovery.")
        
        # Macro balance
        carbs = results['carbs_trend']['forecast_avg']
        protein = results['protein_trend']['forecast_avg']
        fat = results['fat_trend']['forecast_avg']
        
        total = carbs * 4 + protein * 4 + fat * 9
        if total > 0:
            prot_pct = (protein * 4 / total) * 100
            if prot_pct < 15:
                insights.append("[BALANCE] Protein ratio low. Aim for 20-30% of calories from protein.")
        
        return insights
    
    def _mock_analysis(self, data: List[Dict], forecast_days: int) -> Dict[str, Any]:
        """Mock analysis for development"""
        def _get_avg(key: str, default: float) -> float:
            vals = [float(d.get(key, default)) for d in data[-7:]] if data else [default]
            if np is not None:
                return float(np.mean(vals))
            return float(sum(vals) / max(1, len(vals)))

        avg_calories = _get_avg('calories', 2000.0)
        avg_protein = _get_avg('protein_g', 80.0)
        avg_carbs = _get_avg('carbs_g', 200.0)
        avg_fat = _get_avg('fat_g', 60.0)
        
        forecast = []
        for day in range(forecast_days):
            pred_date = datetime.now() + timedelta(days=day+1)
            forecast.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'predicted': round(float(avg_calories + (day * 5)), 1),
                'lower_bound': round(float(avg_calories - 50), 1),
                'upper_bound': round(float(avg_calories + 50), 1)
            })
        
        return {
            'calories_trend': {
                'metric': 'calories',
                'trend': 'stable',
                'recent_avg': round(float(avg_calories), 1),
                'forecast_avg': round(float(avg_calories), 1),
                'change_percent': 0.5,
                'forecast': forecast
            },
            'protein_trend': {
                'metric': 'protein_g',
                'trend': 'stable',
                'recent_avg': round(float(avg_protein), 1),
                'forecast_avg': round(float(avg_protein), 1),
                'change_percent': -1.2
            },
            'carbs_trend': {
                'metric': 'carbs_g',
                'trend': 'stable',
                'recent_avg': round(float(avg_carbs), 1),
                'forecast_avg': round(float(avg_carbs), 1),
                'change_percent': 0.0
            },
            'fat_trend': {
                'metric': 'fat_g',
                'trend': 'stable',
                'recent_avg': round(float(avg_fat), 1),
                'forecast_avg': round(float(avg_fat), 1),
                'change_percent': 0.0
            },
            'insights': [
                "[CHART] Your nutrition is stable over the past week",
                "[FIT] Protein intake is adequate at {}g/day".format(int(avg_protein))
            ],
            'model': 'mock'
        }


# Singleton instance
_prophet_instance: Optional[ProphetTrendAnalyzer] = None

def get_trend_analyzer() -> ProphetTrendAnalyzer:
    """Get singleton Prophet instance"""
    global _prophet_instance
    if _prophet_instance is None:
        _prophet_instance = ProphetTrendAnalyzer()
    return _prophet_instance
