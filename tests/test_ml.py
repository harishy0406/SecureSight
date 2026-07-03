from __future__ import annotations

import pytest

from securesight.ml.isolation_forest import IsolationForestDetector
from securesight.ml.z_score import ZScoreDetector
from securesight.ml.exponential_moving_average import EMADetector
from securesight.ml.feature_engineering import FeatureEngineer


class TestIsolationForest:
    def test_normal_values(self):
        detector = IsolationForestDetector()
        values = [10.0 + (i % 5) * 0.1 for i in range(100)]
        detector.fit(values)
        result = detector.predict(10.1)
        assert "is_anomaly" in result
        assert "anomaly_score" in result

    def test_insufficient_data(self):
        detector = IsolationForestDetector()
        values = [1.0, 2.0]
        detector.fit(values)
        result = detector.predict(1.5)
        assert not result["is_anomaly"]


class TestZScoreDetector:
    def test_normal_values(self):
        detector = ZScoreDetector()
        values = [100 + i for i in range(50)]
        detector.fit(values)
        result = detector.predict(100)
        assert not result["is_anomaly"]

    def test_outlier_detection(self):
        detector = ZScoreDetector(threshold=2.0)
        values = [100.0] * 20
        detector.fit(values)
        result = detector.predict(500.0)
        assert result["is_anomaly"]
        assert result["z_score"] > 2.0

    def test_insufficient_data(self):
        detector = ZScoreDetector()
        detector.fit([1.0, 2.0])
        result = detector.predict(100.0)
        assert not result["is_anomaly"]


class TestEMADetector:
    def test_normal_values(self):
        detector = EMADetector(alpha=0.3)
        values = [50.0 + (i % 3) for i in range(30)]
        detector.fit(values)
        result = detector.predict(50.5)
        assert "is_anomaly" in result

    def test_insufficient_data(self):
        detector = EMADetector()
        detector.fit([1.0, 2.0])
        result = detector.predict(3.0)
        assert not result["is_anomaly"]


class TestFeatureEngineer:
    def test_extract_features(self):
        engineer = FeatureEngineer()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        features = engineer.extract_features(values)
        assert features["mean"] == 3.0
        assert features["min"] == 1.0
        assert features["max"] == 5.0

    def test_empty_values(self):
        engineer = FeatureEngineer()
        features = engineer.extract_features([])
        assert features == {}
