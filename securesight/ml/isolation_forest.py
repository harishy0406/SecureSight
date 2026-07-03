from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

from securesight.api.core.logging import get_logger
from securesight.api.models.anomaly_event import AnomalySeverity

logger = get_logger(__name__)


class IsolationForestDetector:
    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 100,
        random_state: int = 42,
    ) -> None:
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model: IsolationForest | None = None
        self._fitted = False

    def fit(self, values: list[float]) -> None:
        if len(values) < 10:
            logger.warning("isolation_forest.insufficient_data", count=len(values))
            self._fitted = False
            return

        X = np.array(values).reshape(-1, 1)
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
        )
        self.model.fit(X)
        self._fitted = True
        logger.info("isolation_forest.fitted", samples=len(values))

    def predict(self, value: float) -> dict[str, Any]:
        if not self._fitted or self.model is None:
            return {"is_anomaly": False, "anomaly_score": 0.0, "confidence": 0.0}

        X = np.array([[value]])
        pred = self.model.predict(X)
        scores = self.model.score_samples(X)

        anomaly_score = float(1.0 - (scores[0] + 0.5))
        anomaly_score = max(0.0, min(1.0, anomaly_score))

        is_anomaly = pred[0] == -1

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
            "confidence": round(abs(scores[0]), 4),
        }
