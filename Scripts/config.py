from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from kubernetes import client as k8s_client
    from kubernetes import config as k8s_config
except ImportError:  # pragma: no cover - only hit when dependency missing
    k8s_client = None
    k8s_config = None

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    prometheus_base_url: Optional[str] = Field(default=None, alias="PROMETHEUS_BASE_URL")
    loki_base_url: Optional[str] = Field(default=None, alias="LOKI_BASE_URL")
    alertmanager_url: Optional[str] = Field(default=None, alias="ALERTMANAGER_URL")
    gemini_model: str = Field(default="gemini-2.0-flash-exp", alias="GEMINI_MODEL")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    kube_context: Optional[str] = Field(default=None, alias="KUBE_CONTEXT")
    request_timeout_seconds: float = Field(default=10.0, alias="REQUEST_TIMEOUT_SECONDS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    configure_logging(settings.log_level)
    return settings


def init_kubernetes_client(settings: Settings):
    if k8s_client is None or k8s_config is None:
        logger.info("kubernetes package not available; skipping client init")
        return None
    try:
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            k8s_config.load_incluster_config()
        else:
            k8s_config.load_kube_config(context=settings.kube_context)
        return k8s_client.CoreV1Api()
    except Exception as exc:
        logger.warning("could not initialize kubernetes client: %s", exc)
        return None
