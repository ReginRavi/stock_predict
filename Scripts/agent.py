from __future__ import annotations

import asyncio
import logging
import time
import sys
import os
from typing import Dict
import json

import httpx
from google import genai

# Add parent directory to path for tools import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings, get_settings, init_kubernetes_client
from models import (
    ChatRequest,
    ChatResponse,
    RequestMetadata,
    ResolvedTimeWindow,
    ToolExecutionResult,
)
from tools.alerts import alerts_list
from tools.k8s_state import k8s_state_query_pods
from tools.kb import kb_search
from tools.logs import logs_query
from tools.prometheus import metrics_query


class Agent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger("observability_agent")
        self.http_client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)
        self.kube_client = init_kubernetes_client(settings)
        self.system_prompt = (
            "You are a Kubernetes-focused observability assistant. "
            "Use only the provided tool outputs to explain system health. "
            "Never mutate resources; only describe findings and safe next steps."
        )
        
        # Initialize Gemini API client
        if settings.gemini_api_key:
            self.gemini_client = genai.Client(api_key=settings.gemini_api_key)
            self.gemini_model_name = settings.gemini_model
            self.logger.info("Gemini API configured with model %s", settings.gemini_model)
        else:
            self.gemini_client = None
            self.gemini_model_name = None
            self.logger.warning("GEMINI_API_KEY not set; using fallback response generation")

    async def startup(self) -> None:
        self.logger.info("Agent ready with model %s", self.settings.gemini_model)

    async def shutdown(self) -> None:
        await self.http_client.aclose()

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        time_window = request.resolved_time_window()
        started = time.perf_counter()
        tool_results = await self._run_tools(request, time_window)
        answer_text = await self._call_llm(request, tool_results, time_window)
        latency_ms = int((time.perf_counter() - started) * 1000)
        findings = self._extract_findings(tool_results)
        metadata = RequestMetadata(latency_ms=latency_ms, time_window=time_window)
        return ChatResponse(
            answer=answer_text,
            findings=findings,
            tool_results=tool_results,
            metadata=metadata,
        )

    async def _run_tools(
        self, request: ChatRequest, time_window: ResolvedTimeWindow
    ) -> Dict[str, ToolExecutionResult]:
        tasks = {
            "prometheus": metrics_query(
                client=self.http_client,
                base_url=self.settings.prometheus_base_url,
                query="up",
                start=time_window.start,
                end=time_window.end,
            ),
            "k8s_state": k8s_state_query_pods(
                api=self.kube_client,
                namespace=request.namespace,
                service=request.service,
            ),
            "logs": logs_query(
                base_url=self.settings.loki_base_url,
                query=request.service or request.question,
                time_window=time_window,
            ),
            "alerts": alerts_list(base_url=self.settings.alertmanager_url),
            "kb": kb_search(keywords=[request.service or "", request.question]),
        }

        results: Dict[str, ToolExecutionResult] = {}

        async def _wrap(name: str, coro) -> None:
            try:
                result = await coro
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.exception("Tool %s failed", name)
                result = ToolExecutionResult(status="error", error=str(exc))
            results[name] = result

        await asyncio.gather(*[_wrap(name, coro) for name, coro in tasks.items()])
        return results

    async def _call_llm(
        self,
        request: ChatRequest,
        tool_results: Dict[str, ToolExecutionResult],
        time_window: ResolvedTimeWindow,
    ) -> str:
        # Build context from tool results
        tool_context = self._build_tool_context(tool_results, time_window)
        
        # If Gemini API is configured, use it
        if self.gemini_client:
            try:
                return await self._call_gemini_api(request, tool_context, time_window)
            except Exception as exc:
                self.logger.error("Gemini API call failed: %s", exc)
                self.logger.info("Falling back to template-based response")
        
        # Fallback to template-based response
        return self._generate_fallback_response(request, tool_results, time_window)
    
    def _build_tool_context(
        self,
        tool_results: Dict[str, ToolExecutionResult],
        time_window: ResolvedTimeWindow,
    ) -> str:
        """Build a structured context string from tool results"""
        context_parts = []
        
        context_parts.append(f"Time Window: {time_window.start.isoformat()} to {time_window.end.isoformat()}")
        context_parts.append("\nTool Results:")
        
        for tool_name, result in tool_results.items():
            context_parts.append(f"\n{tool_name.upper()}:")
            context_parts.append(f"  Status: {result.status}")
            
            if result.data:
                context_parts.append(f"  Data: {json.dumps(result.data, indent=2)}")
            
            if result.error:
                context_parts.append(f"  Error: {result.error}")
            
            if result.warnings:
                context_parts.append(f"  Warnings: {', '.join(result.warnings)}")
        
        return "\n".join(context_parts)
    
    async def _call_gemini_api(
        self,
        request: ChatRequest,
        tool_context: str,
        time_window: ResolvedTimeWindow,
    ) -> str:
        """Call Gemini API with the observability context"""
        prompt = f"""{self.system_prompt}

User Question: {request.question}
Namespace: {request.namespace or 'default'}
Service: {request.service or 'N/A'}
Severity Hint: {request.severity_hint or 'N/A'}

{tool_context}

Based on the above observability data, provide a comprehensive analysis that includes:
1. Summary of the current state
2. Key observations from the tool outputs
3. Potential root causes or hypotheses
4. Recommended next steps for investigation or remediation

Keep your response focused on the data provided. Do not make assumptions beyond what the tools have reported."""

        # Run Gemini API call in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        def _generate():
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model_name,
                contents=prompt
            )
            return response.text
        
        response_text = await loop.run_in_executor(None, _generate)
        return response_text
    
    def _generate_fallback_response(
        self,
        request: ChatRequest,
        tool_results: Dict[str, ToolExecutionResult],
        time_window: ResolvedTimeWindow,
    ) -> str:
        """Generate a template-based response when Gemini API is unavailable"""
        checks = [
            f"Prometheus ({tool_results.get('prometheus', ToolExecutionResult(status='skipped')).status})",
            f"Kubernetes state ({tool_results.get('k8s_state', ToolExecutionResult(status='skipped')).status})",
            f"Logs ({tool_results.get('logs', ToolExecutionResult(status='skipped')).status})",
            f"Alerts ({tool_results.get('alerts', ToolExecutionResult(status='skipped')).status})",
            f"Knowledge base ({tool_results.get('kb', ToolExecutionResult(status='skipped')).status})",
        ]
        observations = []
        prom_data = tool_results.get("prometheus")
        if prom_data and prom_data.data:
            observations.append(prom_data.data.get("summary", "Prometheus queried."))
        k8s_data = tool_results.get("k8s_state")
        if k8s_data and k8s_data.data:
            observations.append(k8s_data.data.get("summary", "Kubernetes state checked."))
        alert_data = tool_results.get("alerts")
        if alert_data and alert_data.data:
            observations.append(alert_data.data.get("summary", "Alerts inspected."))

        if not observations:
            observations.append("No concrete observations available from tools.")

        next_steps = [
            "Review the summarized observations above.",
            "Drill into the service logs for recent errors.",
            "Inspect pods with high restarts or failing readiness probes.",
        ]

        return (
            f"Summary: Investigated '{request.question}' for namespace '{request.namespace or 'default'}' "
            f"between {time_window.start.isoformat()} and {time_window.end.isoformat()}.\n"
            f"Checks Run:\n- " + "\n- ".join(checks) + "\n"
            f"Observations:\n- " + "\n- ".join(observations) + "\n"
            f"Hypotheses:\n- Potential service-level issue or transient node problems.\n"
            f"Next Steps:\n- " + "\n- ".join(next_steps) + "\n\n"
            f"Note: This is a template-based response. Configure GEMINI_API_KEY for AI-powered analysis."
        )

    def _extract_findings(self, tool_results: Dict[str, ToolExecutionResult]) -> list[str]:
        findings: list[str] = []
        prom = tool_results.get("prometheus")
        if prom and prom.data and prom.data.get("summary"):
            findings.append(prom.data["summary"])
        k8s = tool_results.get("k8s_state")
        if k8s and k8s.data and k8s.data.get("summary"):
            findings.append(k8s.data["summary"])
        alerts = tool_results.get("alerts")
        if alerts and alerts.data and alerts.data.get("summary"):
            findings.append(alerts.data["summary"])
        return findings or ["No notable findings from tools."]


def build_agent() -> Agent:
    settings = get_settings()
    return Agent(settings=settings)
