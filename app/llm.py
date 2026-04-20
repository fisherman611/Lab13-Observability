from __future__ import annotations

import os
import random
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class LLMResponse:
    text: str
    usage: LLMUsage
    model: str


class ApiLLM:
    """LLM client that calls a real chat completion API with safe fallback."""

    def __init__(self, model: str = "meta/llama-3.1-70b-instruct") -> None:
        self.model = os.getenv("LLM_MODEL", model)
        self.api_key = os.getenv("LLM_API_KEY") or os.getenv("NVIDIA_API_KEY", "")
        self.api_url = self._resolve_api_url()
        self.timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

    def _resolve_api_url(self) -> str:
        explicit_url = os.getenv("LLM_API_URL")
        if explicit_url:
            return explicit_url

        base = os.getenv("NVIDIA_BASE_URL")
        if base:
            normalized = base.rstrip("/")
            if normalized.endswith("/chat/completions"):
                return normalized
            if normalized.endswith("/v1"):
                return f"{normalized}/chat/completions"
            return f"{normalized}/v1/chat/completions"

        return "https://api.openai.com/v1/chat/completions"

    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        if not self.api_key:
            return self._fallback(prompt)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                    or "Bạn là trợ lý bán hàng pickleball, ưu tiên thông tin rõ ràng, đúng giá, và dễ hiểu.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json()
        except Exception:
            return self._fallback(prompt)

        text = self._extract_text(body)
        usage = body.get("usage", {}) if isinstance(body, dict) else {}
        in_tokens = int(usage.get("prompt_tokens", max(20, len(prompt) // 4)))
        out_tokens = int(usage.get("completion_tokens", max(60, len(text) // 4)))
        used_model = str(body.get("model") or self.model)
        return LLMResponse(text=text, usage=LLMUsage(in_tokens, out_tokens), model=used_model)

    def _extract_text(self, body: dict) -> str:
        choices = body.get("choices", []) if isinstance(body, dict) else []
        if choices:
            first = choices[0]
            message = first.get("message", {}) if isinstance(first, dict) else {}
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, str) and content.strip():
                return content.strip()
        return "Xin lỗi, tôi chưa nhận được nội dung phản hồi hợp lệ từ LLM."

    def _fallback(self, prompt: str) -> LLMResponse:
        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(90, 150)
        answer = (
            "Tôi đang ở chế độ dự phòng. Bạn có thể đặt câu hỏi về giá vợt, bóng, túi đựng, "
            "giày và phụ kiện pickleball để nhận tư vấn mua bán."
        )
        return LLMResponse(text=answer, usage=LLMUsage(input_tokens, output_tokens), model=f"fallback-{self.model}")
