from __future__ import annotations

from typing import Optional

from models import ResolvedTimeWindow, ToolExecutionResult


async def logs_query(
    base_url: Optional[str],
    query: str,
    time_window: ResolvedTimeWindow,
) -> ToolExecutionResult:
    if not base_url:
        return ToolExecutionResult(status="skipped", error="LOKI_BASE_URL not set")
    return ToolExecutionResult(
        status="ok",
        data={
            "entries": [],
            "summary": (
                f"Logs stub executed for query '{query}' between "
                f"{time_window.start.isoformat()} and {time_window.end.isoformat()}."
            ),
        },
        warnings=["Logs adapter is stubbed; connect Loki or Elastic to enable results."],
    )
