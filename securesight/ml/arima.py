from __future__ import annotations

from typing import Any

import numpy as np

try:
    from statsmodels.tsa.arima.model import ARIMA as ARIMAModel

    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

from securesight.api.core.logging import get_logger
from securesight.api.models.anomaly_event import AnomalySeverity

logger = get_logger(__name__)


class ARIMADetector:
    def __init__(self, order: tuple[int, int, int] = (5, 1, 2), threshold_std: float = 2.5) -> None:
        self.order = order
        self.threshold_std = threshold_std
        self.model: ARIMAModel | None = None
        self.residuals: list[float] = []
        self._fitted = False

    def fit(self, values: list[float]) -> None:
        if not STATSMODELS_AVAILABLE:
            logger.warning("arima.statsmodels_not_available")
            self._fitted = False
            return
        if len(values) < max(self.order[0] + self.order[1] + 1, 20):
            logger.warning("arima.insufficient_data", count=len(values))
            self._fitted = False
            return

        try:
            self.model = ARIMAModel(values, order=self.order)
            fitted = self.model.fit()
            pred = fitted.predict(start=0, end=len(values) - 1)
            self.residuals = [float(values[i] - pred[i]) for i in range(len(values))]
            self._fitted = True
            logger.info("arima.fitted", samples=len(values))
        except Exception as exc:
            logger.error("arima.fit_failed", error=str(exc))
            self._fitted = False

    def predict(self, value: float) -> dict[str, Any]:
        if not self._fitted or not self.residuals:
            return {"is_anomaly": False, "anomaly_score": 0.0, "predicted_value": None}

        residual_std = float(np.std(self.residuals)) if len(self.residuals) > 1 else 0.0
        residual_mean = float(np.mean(self.residuals))

        if residual_std == 0:
            return {"is_anomaly": False, "anomaly_score": 0.0, "predicted_value": None}

        z_score = abs(value - residual_mean) / residual_std
        is_anomaly = z_score > self.threshold_std

        anomaly_score = min(1.0, z_score / (self.threshold_std * 2))

        severity = AnomalySeverity.LOW
        if is_anomaly:
            if anomaly_score > 0.8:
                severity = AnomalySeverity.CRITICAL
            elif anomaly_score > 0.6:
                severity = AnomalySeverity.HIGH
            elif anomaly_score > 0.4:
                severity = AnomalySeverity.MEDIUM

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(anomaly_score, 4),
            "severity": severity,
            "predicted_value": round(residual_mean, 4),
        }
