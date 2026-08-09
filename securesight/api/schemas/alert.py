from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AlertRuleCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    metric_name: str = Field(..., max_length=255)
    condition: str = "greater_than"
    threshold: float
    threshold_high: float | None = None
    severity: str = "medium"
    evaluation_window_seconds: int = 300
    cooldown_seconds: int = 600
    enabled: bool = True
    config: dict | None = None
    escalation_policy: dict | None = None
    host_id: int | None = None


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    condition: str | None = None
    threshold: float | None = None
    threshold_high: float | None = None
    severity: str | None = None
    evaluation_window_seconds: int | None = None
    cooldown_seconds: int | None = None
    enabled: bool | None = None
    config: dict | None = None
    escalation_policy: dict | None = None
    host_id: int | None = None


class AlertRulePublic(BaseModel):
    id: int
    name: str
    description: str | None
    metric_name: str
    condition: str
    threshold: float
    threshold_high: float | None
    severity: str
    evaluation_window_seconds: int
    cooldown_seconds: int
    enabled: bool
    config: dict | None
    escalation_policy: dict | None
    host_id: int | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class AlertRuleInDB(AlertRulePublic):
    pass


class AlertCreate(BaseModel):
    alert_rule_id: int
    value: float
    message: str | None = None
    status: str = "firing"


class AlertHistoryPublic(BaseModel):
    id: int
    value: float
    message: str | None
    status: str
    fired_at: datetime
    resolved_at: datetime | None
    alert_rule_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
