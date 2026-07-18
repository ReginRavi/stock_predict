from __future__ import annotations

from datetime import datetime
from typing import Optional

import httpx

from models import ToolExecutionResult


async def metrics_query(
    client: httpx.AsyncClient,
    base_url: Optional[str],
    query: str,
    start: datetime,
    end: datetime,
    step_seconds: int = 30,
) -> ToolExecutionResult:
    if not base_url:
        return ToolExecutionResult(status="skipped", error="PROMETHEUS_BASE_URL not set")

    params = {
        "query": query,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "step": max(step_seconds, 10),
    }
    try:
        response = await client.get(f"{base_url.rstrip('/')}/api/v1/query_range", params=params)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", {})
        result = data.get("result", [])
        summary = f"{len(result)} series returned for query '{query}'."
        return ToolExecutionResult(
            status="ok",
            data={
                "result_type": data.get("resultType"),
                "series": result,
                "summary": summary,
            },
        )
    except httpx.HTTPError as exc:
        return ToolExecutionResult(status="error", error=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        return ToolExecutionResult(status="error", error=str(exc))
