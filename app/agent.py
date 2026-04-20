from __future__ import annotations

import os
import time
from dataclasses import dataclass

from . import metrics
from .mock_llm import FakeLLM
from .nvidia_llm import NvidiaLLM
from .pii import hash_user_id, summarize_text
from .rag import retrieve
from .tracing import langfuse_context, observe


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LabAgent:
    def __init__(self, model: str | None = None) -> None:
        use_mock = os.getenv("USE_MOCK_LLM", "false").lower() in {"1", "true", "yes"}

        if use_mock:
            selected_model = model or "mock-llm"
            self.llm = FakeLLM(model=selected_model)
            self.model = selected_model
        else:
            self.llm = NvidiaLLM(model=model)
            self.model = self.llm.model

        self.system_prompt = (
            "You are a Vietnamese shopping assistant for a pickleball store. "
            "Give practical recommendations with short bullet points. "
            "Use only the retrieved catalog context when naming products and prices. "
            "When user budget or level is missing, ask one concise follow-up question."
        )

    @observe()
    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()
        docs = retrieve(message, top_k=4)
        doc_block = "\n".join(f"- {doc}" for doc in docs)
        prompt = (
            f"Feature: {feature}\n"
            f"Retrieved Catalog Context:\n{doc_block}\n\n"
            f"User Question: {message}\n\n"
            "Response format:\n"
            "1) Nhu cau nguoi dung (1 dong)\n"
            "2) De xuat san pham (2-4 goi y cu the, kem ly do va gia)\n"
            "3) Combo phu kien nen mua kem\n"
            "4) Luu y su dung bao quan ngan gon"
        )
        response = self.llm.generate(prompt, system_prompt=self.system_prompt)
        quality_score = self._heuristic_quality(message, response.text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)

        langfuse_context.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=["lab", feature, self.model],
        )
        langfuse_context.update_current_observation(
            metadata={"doc_count": len(docs), "query_preview": summarize_text(message)},
            usage_details={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
        )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
