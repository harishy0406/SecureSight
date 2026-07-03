from __future__ import annotations

from typing import Any

from securesight.api.core.logging import get_logger
from securesight.api.models.anomaly_event import AnomalySeverity

logger = get_logger(__name__)


class EMADetector:
    def __init__(self, alpha: float = 0.3, threshold_std: float = 2.5) -> None:
        self.alpha = alpha
        self.threshold_std = threshold_std
        self._ema: float = 0.0
        self._residuals: list[float] = []
        self._fitted = False
        self._history: list[float] = []

    def fit(self, values: list[float]) -> None:
        if len(values) < 5:
            logger.warning("ema.insufficient_data", count=len(values))
            self._fitted = False
            return

        self._history = list(values)
        self._ema = float(values[0])
        self._residuals = []

        for v in values[1:]:
            residual = v - self._ema
            self._residuals.append(abs(residual))
            self._ema = self.alpha * v + (1 - self.alpha) * self._ema

        self._fitted = True
        logger.info("ema.fitted", samples=len(values), alpha=self.alpha)

    def predict(self, value: float) -> dict[str, Any]:
        if not self._fitted or not self._residuals:
            return {"is_anomaly": False, "anomaly_score": 0.0, "predicted_value": None}

        residual_std = (
            __import__("statistics").stdev(self._residuals)
            if len(self._residuals) > 1
            else 0.0
        )
        residual_mean = __import__("statistics").mean(self._residuals)

        deviation = abs(value - self._ema)

        if residual_std > 0:
            z = (deviation - residual_mean) / residual_std
        else:
            z = 0.0

        is_anomaly = z > self.threshold_std
        anomaly_score = min(1.0, z / (self.threshold_std * 2))

        severity = AnomalySeverity.LOW
        if is_anomaly:
            if anomaly_score > 0.8:
                severity = AnomalySeverity.CRITICAL
            elif anomaly_score > 0.6:
                severity = AnomalySeverity.HIGH
            elif anomaly_score > 0.4:
                severity = AnomalySeverity.MEDIUM

        self._ema = self.alpha * value + (1 - self.alpha) * self._ema
        self._residuals.append(deviation)
        if len(self._residuals) > 1000:
            self._residuals = self._residuals[-500:]

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(anomaly_score, 4),
            "severity": severity,
            "predicted_value": round(self._ema, 4),
        }
