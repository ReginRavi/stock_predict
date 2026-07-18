from __future__ import annotations

from typing import Iterable, List

from models import ToolExecutionResult


async def kb_search(keywords: Iterable[str]) -> ToolExecutionResult:
    terms: List[str] = [t for t in keywords if t]
    return ToolExecutionResult(
        status="ok",
        data={
            "results": [],
            "summary": "Knowledge base search stubbed; no documents returned.",
            "keywords": terms,
        },
        warnings=["Knowledge base adapter is stubbed; integrate a vector DB to enable results."],
    )
