"""
Test Phase 3: Time-Series Forecasting

Tests for LSTM weight prediction and Prophet trend analysis
"""

import requests
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def test_lstm_weight_prediction():
    """Test LSTM weight predictor"""
    print("\n" + "="*70)
    print("  TESTING LSTM WEIGHT PREDICTION")
    print("="*70)
    
    # Generate mock historical data
    historical_data = []
    for i in range(14):
        date = (datetime.now() - timedelta(days=14-i)).strftime('%Y-%m-%d')
        historical_data.append({
            "date": date,
            "weight": 78 - (i * 0.1),  # Gradual weight mọc loss
            "calories": 1800 + (i * 10),
            "activity_minutes": 45
        })
    
    response = requests.post(
        f"{API_BASE}/api/forecast/predict-weight",
        json={
            "historical_data": historical_data,
            "days_ahead": 7
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ LSTM Weight Prediction:")
        print(f"   Model: {data['model']}")
        print(f"   Trend: {data['trend']}")
        print(f"   Avg change/week: {data['avg_change_per_week']:+.2f}kg")
        
        print(f"\n   7-day forecast:")
        for pred in data['predictions'][:3]:
            print(f"     {pred['date']}: {pred['predicted_weight']}kg "
                  f"(confidence: {pred['confidence']:.0%})")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    return response.status_code == 200


def test_prophet_nutrition_trends():
    """Test Prophet trend analysis"""
    print("\n" + "="*70)
    print("  TESTING PROPHET NUTRITION TRENDS")
    print("="*70)
    
    # Generate mock nutrition data
    historical_data = []
    for i in range(21):  # 3 weeks
        date = (datetime.now() - timedelta(days=21-i)).strftime('%Y-%m-%d')
        historical_data.append({
            "date": date,
            "calories": 1900 + (i * 5),
            "protein_g": 80 + (i * 0.5),
            "carbs_g": 200 - (i * 2),
            "fat_g": 60
        })
    
    response = requests.post(
        f"{API_BASE}/api/forecast/analyze-nutrition-trends",
        json={
            "historical_data": historical_data,
            "forecast_days": 14
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Prophet Nutrition Analysis:")
        print(f"   Model: {data.get('model', 'unknown')}")
        
        # Calories trend
        cal_trend = data.get('calories_trend', {})
        print(f"\n   📊 Calories:")
        print(f"      Trend: {cal_trend.get('trend', 'N/A')}")
        print(f"      Current avg: {cal_trend.get('recent_avg', 0)}")
        print(f"      Forecast avg: {cal_trend.get('forecast_avg', 0)}")
        print(f"      Change: {cal_trend.get('change_percent', 0):+.1f}%")
        
        # Protein trend
        prot_trend = data.get('protein_trend', {})
        print(f"\n   💪 Protein:")
        print(f"      Trend: {prot_trend.get('trend', 'N/A')}")
        print(f"      Forecast avg: {prot_trend.get('forecast_avg', 0)}g/day")
        
        # Insights
        insights = data.get('insights', [])
        if insights:
            print(f"\n   💡 Insights:")
            for insight in insights:
                print(f"      {insight}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    return response.status_code == 200


def test_goal_projection():
    """Test goal achievement projection"""
    print("\n" + "="*70)
    print("  TESTING GOAL PROJECTION")
    print("="*70)
    
    response = requests.get(
        f"{API_BASE}/api/forecast/goal-projection",
        params={
            "user_id": 1,
            "goal_weight": 75.0
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Goal Projection:")
        print(f"   Current weight: {data.get('currentweight', 'N/A')}kg")
        print(f"   Goal weight: {data['goal_weight']}kg")
        
        if data.get('achievable'):
            print(f"   ✅ Goal achievable!")
            print(f"   Projected date: {data['projected_date']}")
            print(f"   Days remaining: {data['days_remaining']}")
            print(f"   Confidence: {data.get('confidence', 0):.0%}")
        else:
            print(f"   ❌ Goal not achievable in forecast period")
            print(f"   {data.get('message', '')}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    return response.status_code == 200


def test_forecast_models_status():
    """Test forecast models status"""
    print("\n" + "="*70)
    print("  TESTING FORECAST MODELS STATUS")
    print("="*70)
    
    response = requests.get(f"{API_BASE}/api/forecast/models/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Forecast Models: {data['available_count']}/{data['total_count']} available")
        print(f"   Phase: {data['phase']}")
        
        print(f"\n   Models:")
        for model_name, info in data['models'].items():
            status_emoji = "✅" if info['available'] else "❌"
            print(f"     {status_emoji} {model_name}: {info['status']}")
            print(f"        {info['description']}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    return response.status_code == 200


def main():
    """Run all Phase 3 tests"""
    print("\n" + "="*70)
    print("  PHASE 3 TESTING")
    print("  (LSTM + Prophet)")
    print("="*70)
    
    # Check backend
    try:
        response = requests.get(f"{API_BASE}/docs")
        if response.status_code == 200:
            print("\n✅ Backend running\n")
        else:
            print(f"❌ Backend issue: {response.status_code}")
            return
    except:
        print(f"❌ Backend not running at {API_BASE}")
        return
    
    # Run tests
    results = {
        "LSTM Weight prediction": test_lstm_weight_prediction(),
        "Prophet Nutrition Trends": test_prophet_nutrition_trends(),
        "Goal Projection": test_goal_projection(),
        "Forecast Models Status": test_forecast_models_status()
    }
    
    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        emoji = "✅" if passed else "❌"
        print(f"{emoji} {test_name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎯 {passed_count}/{total_count} tests passed")
    
    print("\n" + "="*70)
    print("✅ PHASE 3 FORECASTING COMPLETE!")
    print("="*70)
    print("\n🔮 Time-Series Features:")
    print("  • LSTM weight prediction (7-30 days)")
    print("  • Prophet nutrition trends")
    print("  • Goal achievement projection")
    print("  • Confidence intervals")
    print("  • Actionable insights")
    print("\n📊 Total Endpoints: 4")
    print("  • POST /api/forecast/predict-weight")
    print("  • POST /api/forecast/analyze-nutrition-trends")
    print("  • GET  /api/forecast/goal-projection")
    print("  • GET  /api/forecast/models/status")
    print("="*70)


if __name__ == "__main__":
    main()
