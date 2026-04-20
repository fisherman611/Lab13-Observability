from __future__ import annotations

import json
import re
import time
import unicodedata
from functools import lru_cache
from pathlib import Path

from .incidents import STATE

CATALOG_PATH = Path("data/pickleball_catalog.json")
STOPWORDS = {
    "toi",
    "muon",
    "mua",
    "cho",
    "la",
    "va",
    "de",
    "giup",
    "tu",
    "van",
    "vot",
    "pickleball",
    "co",
    "khong",
    "can",
    "duoc",
    "voi",
    "nhu",
    "nao",
    "the",
    "la",
    "help",
    "for",
    "the",
    "and",
    "with",
}


def _tokenize(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFD", text.lower())
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    raw = re.findall(r"[a-z0-9]+", normalized)
    return {tok for tok in raw if len(tok) > 1 and tok not in STOPWORDS}


@lru_cache(maxsize=1)
def _load_catalog() -> list[dict]:
    if not CATALOG_PATH.exists():
        raise RuntimeError(f"Catalog file is missing: {CATALOG_PATH}")
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _render_doc(item: dict) -> str:
    tags = ", ".join(item.get("tags", []))
    return (
        f"SKU: {item.get('sku')} | Product: {item.get('name')} | Category: {item.get('category')} | "
        f"Level: {item.get('level')} | Price(VND): {item.get('price_vnd')} | "
        f"Tags: {tags} | Description: {item.get('description')}"
    )


def _score_item(query_tokens: set[str], item: dict) -> int:
    haystack = " ".join(
        [
            str(item.get("name", "")),
            str(item.get("category", "")),
            str(item.get("level", "")),
            str(item.get("description", "")),
            " ".join(item.get("tags", [])),
        ]
    ).lower()

    score = 0
    for token in query_tokens:
        if token in haystack:
            score += 2
    if item.get("category", "") in {"paddle", "grip", "ball", "shoes", "bag", "accessory"}:
        score += 1
    return score


def retrieve(message: str, top_k: int = 4) -> list[str]:
    if STATE["tool_fail"]:
        raise RuntimeError("Vector store timeout")
    if STATE["rag_slow"]:
        time.sleep(2.5)

    catalog = _load_catalog()
    query_tokens = _tokenize(message)

    if not query_tokens:
        picks = catalog[:top_k]
        return [_render_doc(item) for item in picks]

    scored: list[tuple[int, dict]] = []
    for item in catalog:
        scored.append((_score_item(query_tokens, item), item))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = [item for score, item in scored if score > 0][:top_k]

    if not best:
        best = catalog[:top_k]

    return [_render_doc(item) for item in best]
