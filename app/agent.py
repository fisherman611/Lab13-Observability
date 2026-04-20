from __future__ import annotations
import time
import os
from dataclasses import dataclass
from . import metrics
from .nvidia_llm import NvidiaLLM
from .rag import retrieve
from .pii import hash_user_id, summarize_text
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
        # Ưu tiên Llama 3.1 8B vì độ ổn định cao nhất trên NVIDIA NIM
        self.model = model or os.getenv("NVIDIA_MODEL") or "meta/llama-3.1-8b-instruct"
        self.llm = NvidiaLLM(model=self.model)

    @observe()
    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()
        
        # 1. RAG Retrieval
        docs = retrieve(message)
        
        # 2. Sinh câu trả lời từ NVIDIA NIM
        # Gửi kèm hướng dẫn hệ thống để trả lời tốt hơn
        system_prompt = f"Ban la tro ly chuyen ve Pickleball. Feature: {feature}"
        response = self.llm.generate(message, system_prompt=system_prompt)
        
        answer = response.text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        quality_score = self._heuristic_quality(message, answer, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(input_tokens, output_tokens)

        # Tracing & Metrics
        langfuse_context.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=["nvidia", feature, self.model],
        )
        langfuse_context.update_current_observation(
            metadata={"doc_count": len(docs), "query_preview": summarize_text(message)},
            usage_details={"input": input_tokens, "output": output_tokens},
        )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=input_tokens,
            tokens_out=output_tokens,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=answer,
            latency_ms=latency_ms,
            tokens_in=input_tokens,
            tokens_out=output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        # Giá trung bình cho Llama 8B trên NIM
        input_cost = (tokens_in / 1_000_000) * 0.15
        output_cost = (tokens_out / 1_000_000) * 0.15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs: score += 0.2
        if answer and len(answer) > 50: score += 0.1
        if question.lower().split()[:2] and answer and any(t in answer.lower() for t in question.lower().split()[:3]):
            score += 0.1
        return round(max(0.0, min(1.0, score)), 2)
