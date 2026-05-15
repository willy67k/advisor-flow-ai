"""Sync LangSmith / LangChain tracing env before LangChain graphs run — Step 8.1."""

from __future__ import annotations

import os

from app.config.env import get_env


def configure_langsmith_envvars() -> None:
    """When an API key is configured, enable LangChain tracing for LangGraph / Chat models."""
    env = get_env()
    key = (env.langsmith_api_key or "").strip()
    if not key:
        return
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if env.langsmith_tracing_v2 else "false"
    os.environ["LANGCHAIN_API_KEY"] = key
    proj = (env.langsmith_project or "").strip()
    if proj:
        os.environ["LANGCHAIN_PROJECT"] = proj
    endpoint = (env.langsmith_endpoint or "").strip()
    if endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = endpoint.rstrip("/")


__all__ = ["configure_langsmith_envvars"]
