from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AnomalyCreate(BaseModel):
    metric_name: str = Field(..., max_length=255)
    observed_value: float
    predicted_value: float | None = None
    anomaly_score: float = Field(..., ge=0)
    severity: str = "medium"
    detector: str = Field(..., max_length=100)
    explanation: str | None = None
    context: dict | None = None
    host_id: int


class AnomalyEventPublic(BaseModel):
    id: int
    metric_name: str
    observed_value: float
    predicted_value: float | None
    anomaly_score: float
    severity: str
    status: str
    detector: str
    explanation: str | None
    context: dict | None
    host_id: int
    detected_at: datetime
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class AnomalyFeedbackCreate(BaseModel):
    status: str = Field(..., pattern="^(confirmed|false_positive)$")
    comment: str | None = None
