from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException

from agent import Agent, build_agent
from models import ChatRequest, ChatResponse, ErrorResponse

logger = logging.getLogger("observability_app")

app = FastAPI(
    title="K8s Observability AI Agent",
    version="0.1.0",
    description="Observability chat API for Kubernetes workloads.",
)

agent: Agent = build_agent()


@app.on_event("startup")
async def _startup() -> None:
    await agent.startup()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await agent.shutdown()


@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await agent.handle_chat(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unhandled error")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}
