from __future__ import annotations

import time
from collections import Counter
from statistics import mean

START_TIME = time.time()

REQUEST_LATENCIES: list[int] = []
REQUEST_COSTS: list[float] = []
REQUEST_TOKENS_IN: list[int] = []
REQUEST_TOKENS_OUT: list[int] = []
ERRORS: Counter[str] = Counter()
TRAFFIC: int = 0
QUALITY_SCORES: list[float] = []


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    global TRAFFIC
    TRAFFIC += 1
    REQUEST_LATENCIES.append(latency_ms)
    REQUEST_COSTS.append(cost_usd)
    REQUEST_TOKENS_IN.append(tokens_in)
    REQUEST_TOKENS_OUT.append(tokens_out)
    QUALITY_SCORES.append(quality_score)



def record_error(error_type: str) -> None:
    ERRORS[error_type] += 1



def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])



def snapshot() -> dict:
    total_errors = sum(ERRORS.values())
    error_rate = total_errors / TRAFFIC if TRAFFIC > 0 else 0.0
    error_rate_pct = error_rate * 100
    uptime = time.time() - START_TIME
    qps_estimate = TRAFFIC / uptime if uptime > 0 else 0.0

    return {
        "latency": {
            "p50": percentile(REQUEST_LATENCIES, 50),
            "p95": percentile(REQUEST_LATENCIES, 95),
            "p99": percentile(REQUEST_LATENCIES, 99),
        },
        "traffic": TRAFFIC,
        "qps_estimate": round(qps_estimate, 2),
        "errors": {
            "total_errors": total_errors,
            "rate": round(error_rate, 4),
            "error_rate_pct": round(error_rate_pct, 2),
            "breakdown": dict(ERRORS),
        },
        "cost": {
            "avg_usd": round(mean(REQUEST_COSTS), 4) if REQUEST_COSTS else 0.0,
            "total_usd": round(sum(REQUEST_COSTS), 4),
        },
        "tokens": {
            "in_total": sum(REQUEST_TOKENS_IN),
            "out_total": sum(REQUEST_TOKENS_OUT),
        },
        "quality": {
            "proxy_score_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
        }
    }
