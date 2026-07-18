from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class TimeWindow(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    lookback_minutes: Optional[int] = Field(default=60, ge=1, le=1440)

    model_config = ConfigDict(extra="ignore", frozen=False)

    @field_validator("end")
    @classmethod
    def _end_requires_start(cls, v: Optional[datetime], info: Any) -> Optional[datetime]:
        if v and not info.data.get("start") and not info.data.get("lookback_minutes"):
            raise ValueError("end supplied without start or lookback")
        return v

    def resolve(self, now: Optional[datetime] = None) -> "ResolvedTimeWindow":
        now = _ensure_timezone(now or datetime.now(timezone.utc))
        if self.start and self.end:
            start = _ensure_timezone(self.start)
            end = _ensure_timezone(self.end)
        else:
            lookback = self.lookback_minutes or 60
            end = now
            start = now - timedelta(minutes=lookback)
        if start >= end:
            raise ValueError("time window start must be before end")
        return ResolvedTimeWindow(start=start, end=end)


class ResolvedTimeWindow(BaseModel):
    start: datetime
    end: datetime

    model_config = ConfigDict(extra="ignore")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    service: Optional[str] = None
    namespace: Optional[str] = None
    severity_hint: Optional[str] = None
    time_window: Optional[TimeWindow] = None
    max_results: int = Field(default=3, ge=1, le=20)

    model_config = ConfigDict(extra="ignore")

    def resolved_time_window(self) -> ResolvedTimeWindow:
        window = self.time_window or TimeWindow()
        return window.resolve()


class ToolExecutionResult(BaseModel):
    status: Literal["ok", "error", "skipped"]
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class RequestMetadata(BaseModel):
    latency_ms: int
    time_window: Optional[ResolvedTimeWindow] = None
    trace_id: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class ChatResponse(BaseModel):
    answer: str
    findings: List[str] = Field(default_factory=list)
    tool_results: Dict[str, ToolExecutionResult] = Field(default_factory=dict)
    metadata: Optional[RequestMetadata] = None

    model_config = ConfigDict(extra="ignore")


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: Optional[str] = None

    model_config = ConfigDict(extra="ignore")
