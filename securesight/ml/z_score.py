from __future__ import annotations

from statistics import mean, stdev
from typing import Any

from securesight.api.core.logging import get_logger
from securesight.api.models.anomaly_event import AnomalySeverity

logger = get_logger(__name__)


class ZScoreDetector:
    def __init__(self, threshold: float = 3.0, use_mad: bool = False) -> None:
        self.threshold = threshold
        self.use_mad = use_mad
        self._mean: float = 0.0
        self._std: float = 0.0
        self._mad: float = 0.0
        self._median: float = 0.0
        self._fitted = False

    def fit(self, values: list[float]) -> None:
        if len(values) < 5:
            logger.warning("z_score.insufficient_data", count=len(values))
            self._fitted = False
            return

        self._mean = float(mean(values))
        self._median = float(sorted(values)[len(values) // 2])

        if self.use_mad:
            deviations = sorted(abs(v - self._median) for v in values)
            self._mad = float(stdev(deviations)) if len(deviations) > 1 else 0.0
        else:
            self._std = float(stdev(values)) if len(values) > 1 else 0.0

        self._fitted = True
        logger.info("z_score.fitted", samples=len(values), threshold=self.threshold, use_mad=self.use_mad)

    def predict(self, value: float) -> dict[str, Any]:
        if not self._fitted:
            return {"is_anomaly": False, "anomaly_score": 0.0, "z_score": 0.0}

        if self.use_mad:
            if self._mad == 0:
                z = 0.0
            else:
                z = abs(value - self._median) / self._mad
        else:
            if self._std == 0:
                z = 0.0
            else:
                z = abs(value - self._mean) / self._std

        is_anomaly = z > self.threshold
        anomaly_score = min(1.0, z / (self.threshold * 2))

        severity = AnomalySeverity.LOW
        if is_anomaly:
            if z > self.threshold * 3:
                severity = AnomalySeverity.CRITICAL
            elif z > self.threshold * 2:
                severity = AnomalySeverity.HIGH
            elif z > self.threshold * 1.5:
                severity = AnomalySeverity.MEDIUM

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(anomaly_score, 4),
            "severity": severity,
            "z_score": round(z, 4),
        }
