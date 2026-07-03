from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean, stdev

import numpy as np


class FeatureEngineer:
    def __init__(self, window_size: int = 10) -> None:
        self.window_size = window_size

    def extract_features(self, values: list[float]) -> dict[str, float]:
        if not values:
            return {}

        arr = np.array(values)
        features: dict[str, float] = {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "median": float(np.median(arr)),
            "range": float(np.max(arr) - np.min(arr)),
            "q1": float(np.percentile(arr, 25)),
            "q3": float(np.percentile(arr, 75)),
            "iqr": float(np.percentile(arr, 75) - np.percentile(arr, 25)),
            "skewness": float(self._skewness(arr)),
            "kurtosis": float(self._kurtosis(arr)),
            "cv": float(self._cv(arr)),
            "rate_of_change": float(self._rate_of_change(values)),
        }
        return features

    def extract_rolling_features(self, window: list[float]) -> dict[str, float]:
        if len(window) < 2:
            return {"rolling_mean": 0.0, "rolling_std": 0.0, "rolling_min": 0.0, "rolling_max": 0.0}

        return {
            "rolling_mean": float(mean(window)),
            "rolling_std": float(stdev(window)) if len(window) > 1 else 0.0,
            "rolling_min": float(min(window)),
            "rolling_max": float(max(window)),
            "rolling_median": float(sorted(window)[len(window) // 2]),
        }

    def prepare_series(self, records: list[dict], metric_name: str | None = None) -> dict[str, list]:
        grouped: dict[str, list[float]] = defaultdict(list)
        timestamps: dict[str, list[str]] = defaultdict(list)

        for record in records:
            name = record.get("name", metric_name or "unknown")
            value = record.get("value")
            ts = record.get("recorded_at", "")
            if value is not None:
                grouped[name].append(float(value))
                timestamps[name].append(str(ts))

        result = {}
        for name, vals in grouped.items():
            if len(vals) >= self.window_size:
                result[name] = {
                    "values": vals,
                    "timestamps": timestamps.get(name, []),
                    "features": self.extract_features(vals),
                }
        return result

    def _skewness(self, arr: np.ndarray) -> float:
        if len(arr) < 3 or np.std(arr) == 0:
            return 0.0
        return float(np.mean((arr - np.mean(arr)) ** 3) / (np.std(arr) ** 3))

    def _kurtosis(self, arr: np.ndarray) -> float:
        if len(arr) < 4 or np.std(arr) == 0:
            return 0.0
        return float(np.mean((arr - np.mean(arr)) ** 4) / (np.std(arr) ** 4) - 3)

    def _cv(self, arr: np.ndarray) -> float:
        m = float(np.mean(arr))
        if m == 0:
            return 0.0
        return float(np.std(arr) / m)

    def _rate_of_change(self, values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        changes = [abs(values[i] - values[i - 1]) / max(abs(values[i - 1]), 1e-10) for i in range(1, len(values))]
        return float(mean(changes)) if changes else 0.0
