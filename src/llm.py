"""Optional OpenAI-compatible model adapter.

The core proposal remains useful without an API key.  This module is only for
polishing an executive summary after the deterministic retrieval and citation
checks have completed; it never invents or modifies evidence references.
"""
from __future__ import annotations

import json
import os
from urllib import request


class LLMConfigurationError(RuntimeError):
    """Raised when optional model refinement is requested without configuration."""


class OpenAICompatibleRefiner:
    def __init__(self) -> None:
        self.api_key = os.getenv("PRESALES_LLM_API_KEY")
        self.base_url = os.getenv("PRESALES_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("PRESALES_LLM_MODEL")
        if not self.api_key or not self.model:
            raise LLMConfigurationError(
                "Set PRESALES_LLM_API_KEY and PRESALES_LLM_MODEL to enable optional refinement."
            )

    def executive_summary(self, facts: str) -> str:
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an enterprise presales consultant. Write a concise Chinese executive summary "
                        "using only the supplied facts. Do not promise pricing, SLA, compliance certification, "
                        "or capabilities not explicitly supplied. Return Markdown only."
                    ),
                },
                {"role": "user", "content": facts[:12000]},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=45) as response:  # nosec B310: configured trusted endpoint
            answer = json.loads(response.read().decode("utf-8"))
        return answer["choices"][0]["message"]["content"].strip()
