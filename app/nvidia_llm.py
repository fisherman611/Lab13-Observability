from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv

from .incidents import STATE


@dataclass
class LLMUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class LLMResponse:
    text: str
    usage: LLMUsage
    model: str


class NvidiaLLM:
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_s: float = 45.0,
    ) -> None:
        load_dotenv()
        self.api_key = (api_key or os.getenv("NVIDIA_API_KEY", "")).strip()
        self.base_url = (base_url or os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")).rstrip("/")
        self.model = model or os.getenv("NVIDIA_MODEL", "nvidia/gpt-oss-20b")
        self.timeout_s = timeout_s

        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is missing. Set it in environment before starting the app.")

    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                    or "You are a helpful retail assistant for a pickleball store."
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": float(os.getenv("NVIDIA_TEMPERATURE", "0.2")),
            "top_p": float(os.getenv("NVIDIA_TOP_P", "0.9")),
            "max_tokens": int(os.getenv("NVIDIA_MAX_TOKENS", "450")),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout_s,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise RuntimeError(f"NVIDIA API HTTP {exc.response.status_code}: {detail}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"NVIDIA API request failed: {exc}") from exc

        body = response.json()
        answer = self._extract_answer(body)
        usage = body.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or max(1, len(prompt) // 4))
        output_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or max(1, len(answer) // 4))

        if STATE["cost_spike"]:
            output_tokens *= 4

        return LLMResponse(
            text=answer,
            usage=LLMUsage(input_tokens=input_tokens, output_tokens=output_tokens),
            model=str(body.get("model") or self.model),
        )

    def _extract_answer(self, body: dict[str, Any]) -> str:
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("NVIDIA API returned no choices")

        message = choices[0].get("message", {})
        content = message.get("content", "")

        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text")
                    if isinstance(text, str):
                        chunks.append(text)
            joined = "\n".join(chunks).strip()
            if joined:
                return joined

        raise RuntimeError("NVIDIA API returned an unsupported response content format")
