from __future__ import annotations

from typing import Any

try:
    from prophet import Prophet

    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

    class Prophet:  # type: ignore[no-redef]
        def __init__(self, **kwargs: Any) -> None:
            pass

import pandas as pd

from securesight.api.core.logging import get_logger
from securesight.api.models.anomaly_event import AnomalySeverity

logger = get_logger(__name__)


class ProphetDetector:
    def __init__(
        self,
        changepoint_prior_scale: float = 0.05,
        seasonality_mode: str = "additive",
        uncertainty_interval: float = 0.95,
    ) -> None:
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_mode = seasonality_mode
        self.uncertainty_interval = uncertainty_interval
        self.model: Any = None
        self._fitted = False
        self._last_forecast: pd.DataFrame | None = None

    def fit(self, values: list[float], timestamps: list[str | None] | None = None) -> None:
        if not PROPHET_AVAILABLE:
            logger.warning("prophet.not_available")
            self._fitted = False
            return
        if len(values) < 10:
            logger.warning("prophet.insufficient_data", count=len(values))
            self._fitted = False
            return

        try:
            if timestamps and len(timestamps) == len(values) and timestamps[0]:
                ds = pd.to_datetime([t for t in timestamps if t is not None])
            else:
                ds = pd.date_range(end=pd.Timestamp.now(), periods=len(values), freq="5min")

            df = pd.DataFrame({"ds": ds[: len(values)], "y": values})
            self.model = Prophet(
                changepoint_prior_scale=self.changepoint_prior_scale,
                seasonality_mode=self.seasonality_mode,
                interval_width=self.uncertainty_interval,
            )
            self.model.fit(df)
            self._fitted = True
            logger.info("prophet.fitted", samples=len(values))
        except Exception as exc:
            logger.error("prophet.fit_failed", error=str(exc))
            self._fitted = False

    def predict(self, value: float) -> dict[str, Any]:
        if not self._fitted or self.model is None:
            return {"is_anomaly": False, "anomaly_score": 0.0, "predicted_value": None}

        try:
            future = self.model.make_future_dataframe(periods=1, include_history=False)
            forecast = self.model.predict(future)
            predicted = float(forecast["yhat"].iloc[-1])
            yhat_lower = float(forecast["yhat_lower"].iloc[-1])
            yhat_upper = float(forecast["yhat_upper"].iloc[-1])

            is_anomaly = value < yhat_lower or value > yhat_upper
            range_width = max(yhat_upper - yhat_lower, 1e-10)
            distance = min(abs(value - yhat_upper), abs(value - yhat_lower)) if is_anomaly else 0.0
            anomaly_score = min(1.0, distance / range_width)

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
                "predicted_value": round(predicted, 4),
            }
        except Exception as exc:
            logger.error("prophet.predict_failed", error=str(exc))
            return {"is_anomaly": False, "anomaly_score": 0.0, "predicted_value": None}
