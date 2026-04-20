from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

from app.agent import LabAgent
from app.llm import ApiLLM
from app.rag import retrieve, tool_search_price


def _mask(value: str) -> str:
    if not value:
        return "<empty>"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def run_llm_check(require_real_llm: bool) -> None:
    llm = ApiLLM()
    response = llm.generate("Tu van mua mot cay vot pickleball tam gia 2 trieu.")
    print("[LLM] model:", response.model)
    print("[LLM] answer_preview:", response.text[:140])
    print("[LLM] usage:", {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens})

    if require_real_llm and response.model.startswith("fallback-"):
        raise RuntimeError("LLM dang chay fallback, chua goi API that. Kiem tra NVIDIA_API_KEY/NVIDIA_BASE_URL.")


def run_rag_check() -> None:
    docs = retrieve("Cho toi bang gia vot va bong pickleball")
    prices = tool_search_price("gia vot pickleball")
    print("[RAG] docs_count:", len(docs))
    print("[RAG] price_hits:", len(prices))
    if not docs:
        raise RuntimeError("RAG khong tra ve tai lieu nao")
    if not prices:
        raise RuntimeError("Tool search gia khong tra ve ket qua")


def run_agent_check() -> None:
    agent = LabAgent()
    result = agent.run(
        user_id="u_demo",
        feature="qa",
        session_id="s_demo",
        message="Gia vot carbon pickleball nao duoi 3 trieu?",
    )
    print("[AGENT] latency_ms:", result.latency_ms)
    print("[AGENT] answer_preview:", result.answer[:140])
    print(
        "[AGENT] telemetry:",
        {
            "tokens_in": result.tokens_in,
            "tokens_out": result.tokens_out,
            "cost_usd": result.cost_usd,
            "quality_score": result.quality_score,
        },
    )


def run_api_check(base_url: str) -> None:
    health = requests.get(f"{base_url}/health", timeout=10)
    health.raise_for_status()
    print("[API] /health:", health.json())

    payload = {
        "user_id": "u_api",
        "session_id": "s_api",
        "feature": "qa",
        "message": "Cho toi gia vot pickleball va chinh sach doi tra",
    }
    chat = requests.post(f"{base_url}/chat", json=payload, timeout=20)
    chat.raise_for_status()
    body = chat.json()
    print("[API] /chat response keys:", sorted(body.keys()))
    print("[API] /chat answer_preview:", body.get("answer", "")[:140])



def check_logs(log_path: Path) -> None:
    if not log_path.exists():
        raise RuntimeError(f"Khong tim thay log file: {log_path}")
    lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("Log file rong")

    last = json.loads(lines[-1])
    required = ["ts", "level", "event"]
    missing = [key for key in required if key not in last]
    if missing:
        raise RuntimeError(f"Ban ghi log cuoi thieu truong: {missing}")
    print("[LOG] last_event:", {"event": last.get("event"), "service": last.get("service")})


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="End-to-end test for pickleball chatbot with real LLM API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL for running API")
    parser.add_argument("--log-path", default="data/logs.jsonl", help="Path to logs file")
    parser.add_argument(
        "--require-real-llm",
        action="store_true",
        help="Fail if ApiLLM is in fallback mode",
    )
    args = parser.parse_args()

    llm = ApiLLM()
    print("[CONFIG] api_url:", llm.api_url)
    print("[CONFIG] api_key:", _mask(llm.api_key))
    print("[CONFIG] model:", llm.model)

    run_llm_check(require_real_llm=args.require_real_llm)
    run_rag_check()
    run_agent_check()
    run_api_check(args.base_url)
    check_logs(Path(args.log_path))

    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
