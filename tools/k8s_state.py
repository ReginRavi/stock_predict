from __future__ import annotations

import asyncio
from typing import Optional

from models import ToolExecutionResult

try:
    from kubernetes.client import CoreV1Api
except ImportError:  # pragma: no cover - only hit when dependency missing
    CoreV1Api = None  # type: ignore


async def k8s_state_query_pods(
    api: Optional["CoreV1Api"],
    namespace: Optional[str],
    service: Optional[str],
) -> ToolExecutionResult:
    if api is None:
        return ToolExecutionResult(status="skipped", error="Kubernetes client not initialized")

    ns = namespace or "default"
    label_selector = f"app={service}" if service else None

    loop = asyncio.get_event_loop()

    def _list_pods():
        return api.list_namespaced_pod(namespace=ns, label_selector=label_selector)

    try:
        pods = await loop.run_in_executor(None, _list_pods)
        items = pods.items or []
        pod_summaries = []
        for pod in items:
            metadata = getattr(pod, "metadata", None)
            status = getattr(pod, "status", None)
            container_statuses = getattr(status, "container_statuses", []) or []
            restarts = sum(cs.restart_count or 0 for cs in container_statuses)
            ready_states = [cs.ready for cs in container_statuses if hasattr(cs, "ready")]
            ready = all(ready_states) if ready_states else False
            pod_summaries.append(
                {
                    "name": getattr(metadata, "name", ""),
                    "phase": getattr(status, "phase", "Unknown"),
                    "ready": ready,
                    "restarts": restarts,
                    "node": getattr(status, "node_name", None),
                }
            )
        summary = f"{len(pod_summaries)} pods listed in namespace '{ns}'."
        unhealthy = [p for p in pod_summaries if not p["ready"] or p["restarts"] > 0]
        if unhealthy:
            summary += f" {len(unhealthy)} pods not fully healthy."
        return ToolExecutionResult(
            status="ok",
            data={
                "pods": pod_summaries,
                "unhealthy": unhealthy,
                "summary": summary,
            },
        )
    except Exception as exc:
        return ToolExecutionResult(status="error", error=str(exc))
