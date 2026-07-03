from __future__ import annotations

from typing import Any

from securesight.api.core.config import get_settings
from securesight.api.core.logging import get_logger
from securesight.ml.arima import ARIMADetector
from securesight.ml.exponential_moving_average import EMADetector
from securesight.ml.feature_engineering import FeatureEngineer
from securesight.ml.isolation_forest import IsolationForestDetector
from securesight.ml.prophet_model import ProphetDetector
from securesight.ml.z_score import ZScoreDetector

logger = get_logger(__name__)


class AnomalyDetectorPipeline:
    def __init__(self) -> None:
        settings = get_settings()

        self.detectors: dict[str, Any] = {
            "isolation_forest": IsolationForestDetector(
                contamination=settings.ISOLATION_FOREST_CONTAMINATION,
                n_estimators=settings.ISOLATION_FOREST_ESTIMATORS,
            ),
            "arima": ARIMADetector(
                threshold_std=settings.ARIMA_THRESHOLD_STD,
            ),
            "prophet": ProphetDetector(),
            "z_score": ZScoreDetector(
                threshold=settings.Z_SCORE_THRESHOLD,
            ),
            "ema": EMADetector(
                alpha=settings.EMA_ALPHA,
                threshold_std=settings.EMA_THRESHOLD_STD,
            ),
        }

        self.weights: dict[str, float] = {
            "isolation_forest": settings.WEIGHT_ISOLATION_FOREST,
            "arima": settings.WEIGHT_ARIMA,
            "prophet": settings.WEIGHT_PROPHET,
            "z_score": settings.WEIGHT_Z_SCORE,
            "ema": settings.WEIGHT_EMA,
        }

        self.feature_engineer = FeatureEngineer(window_size=10)

    def run(self, records: list[dict]) -> list[dict]:
        series = self.feature_engineer.prepare_series(records)
        detections: list[dict] = []

        for metric_name, data in series.items():
            values = data["values"]
            timestamps = data.get("timestamps", [])

            for detector_name, detector in self.detectors.items():
                try:
                    if hasattr(detector, "fit") and callable(detector.fit):
                        if detector_name == "prophet":
                            detector.fit(values, timestamps)
                        else:
                            detector.fit(values)

                    last_value = values[-1]
                    result = detector.predict(last_value)

                    if result.get("is_anomaly", False):
                        detection = {
                            "metric_name": metric_name,
                            "observed_value": last_value,
                            "predicted_value": result.get("predicted_value"),
                            "anomaly_score": result.get("anomaly_score", 0.0),
                            "severity": result.get("severity", "medium"),
                            "detector": detector_name,
                            "explanation": self._build_explanation(detector_name, result),
                            "context": {
                                "detector": detector_name,
                                "score": result.get("anomaly_score"),
                                "values_snapshot": values[-5:],
                                "weight": self.weights.get(detector_name, 1.0),
                            },
                            "host_id": records[0].get("host_id") if records else None,
                        }
                        detections.append(detection)
                except Exception as exc:
                    logger.error(
                        "detector.run_failed",
                        detector=detector_name,
                        metric=metric_name,
                        error=str(exc),
                    )

        return self._deduplicate(detections)

    def _build_explanation(self, detector_name: str, result: dict) -> str:
        score = result.get("anomaly_score", 0.0)
        severity = result.get("severity", "medium")
        parts = {
            "isolation_forest": f"Isolation Forest flagged outlier (score={score})",
            "arima": f"ARIMA time-series deviation detected (score={score})",
            "prophet": f"Prophet forecast outside confidence interval (score={score})",
            "z_score": f"Statistical z-score anomaly (score={score})",
            "ema": f"Exponential moving average deviation (score={score})",
        }
        return f"[{severity.upper()}] {parts.get(detector_name, 'Unknown detector')}"

    def _deduplicate(self, detections: list[dict]) -> list[dict]:
        seen: dict[str, dict] = {}
        for det in detections:
            key = f"{det.get('metric_name')}:{det.get('host_id')}"
            if key not in seen or det.get("anomaly_score", 0) > seen[key].get("anomaly_score", 0):
                seen[key] = det
        return list(seen.values())


pipeline = AnomalyDetectorPipeline()


def run_anomaly_detection(records: list[dict]) -> list[dict]:
    return pipeline.run(records)
