import pytest
from app.anomaly_detector import (
    calculate_mean_and_std,
    calculate_percentile,
    detect_outliers_zscore,
    detect_outliers_iqr,
    check_single_log_anomaly
)


def test_calculate_mean_and_std():
    mean, std = calculate_mean_and_std([10, 10, 10])
    assert mean == 10.0
    assert std == 0.0
    
    mean2, std2 = calculate_mean_and_std([10, 20])
    assert mean2 == 15.0
    # std deviation of [10, 20] is sqrt(((10-15)^2 + (20-15)^2)/2) = sqrt((25 + 25)/2) = 5.0
    assert std2 == 5.0


def test_calculate_percentile():
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    p25 = calculate_percentile(values, 0.25)
    p75 = calculate_percentile(values, 0.75)
    assert abs(p25 - 3.25) < 0.1
    assert abs(p75 - 7.75) < 0.1


def test_detect_outliers_zscore():
    values = [10.0, 10.2, 9.8, 10.1, 10.3, 9.9, 100.0]  # 100 is a clear outlier
    outliers = detect_outliers_zscore(values, threshold=2.0)
    assert outliers[-1] is True
    assert all(outliers[i] is False for i in range(len(values) - 1))


def test_detect_outliers_iqr():
    values = [10, 11, 12, 10, 11, 12, 10, 11, 12, 100]
    outliers = detect_outliers_iqr(values, factor=1.5)
    assert outliers[-1] is True
    assert all(outliers[i] is False for i in range(len(values) - 1))


def test_check_single_log_anomaly_weight():
    history = [75.0, 75.2, 75.1, 75.3, 75.0, 75.2]
    # Weight change of 10% (75.2 -> 83.0)
    res = check_single_log_anomaly(history, 83.0, metric_type="weight")
    assert res["is_anomaly"]
    assert "physically implausible" in res["reason"]

    # normal weight
    res_normal = check_single_log_anomaly(history, 75.4, metric_type="weight")
    assert not res_normal["is_anomaly"]


def test_check_single_log_anomaly_calories():
    history = [2000.0, 2200.0, 1900.0, 2100.0, 2050.0, 2150.0]
    # Extremely large log (5000 kcal)
    res = check_single_log_anomaly(history, 5000.0, metric_type="calories")
    assert res["is_anomaly"]
    assert "exceeds the statistical upper threshold" in res["reason"]

    # normal calories
    res_normal = check_single_log_anomaly(history, 2100.0, metric_type="calories")
    assert not res_normal["is_anomaly"]
