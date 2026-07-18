from __future__ import annotations

from typing import Optional

from models import ToolExecutionResult


async def alerts_list(base_url: Optional[str]) -> ToolExecutionResult:
    if not base_url:
        return ToolExecutionResult(status="skipped", error="ALERTMANAGER_URL not set")
    return ToolExecutionResult(
        status="ok",
        data={
            "alerts": [],
            "summary": "Alerts adapter stubbed; plug into Alertmanager or Grafana alerting to populate active alerts.",
        },
        warnings=["Alerts adapter is stubbed; no live data returned."],
    )
