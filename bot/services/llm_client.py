import json
import os
from typing import Any, Dict, List

import httpx


LLM_API_BASE_URL = os.environ.get("LLM_API_BASE_URL", "http://localhost:42005/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_API_MODEL = os.environ.get("LLM_API_MODEL", "qwen2.5-coder-32b-instruct")


def _llm_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }


def call_llm_with_tools(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
) -> Dict[str, Any]:
    body = {
        "model": LLM_API_MODEL,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }
    resp = httpx.post(
        f"{LLM_API_BASE_URL}/chat/completions",
        headers=_llm_headers(),
        content=json.dumps(body),
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]
