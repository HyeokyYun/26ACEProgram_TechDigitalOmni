"""검증 레이어 — '그럴듯함'이 아니라 '측정된 신뢰도'.

1) 추출 정확도: 직접 라벨링한 골드셋 대비 size_signal 일치율.
2) 근거성(groundedness): 어드바이저 답변의 인용이 실제 근거에 존재하는 비율.
"""
from __future__ import annotations

import json

from . import config
from .advisor import advise, groundedness
from .llm import LLMClient
from .retriever import Retriever
from .schema import AnalyzedReview


def load_gold() -> dict[str, str]:
    if config.GOLD_LABELS.exists():
        return json.loads(config.GOLD_LABELS.read_text(encoding="utf-8"))
    return {}


def eval_extraction(analyzed: list[AnalyzedReview], gold: dict[str, str] | None = None) -> dict:
    gold = gold if gold is not None else load_gold()
    rows, correct = [], 0
    for r in analyzed:
        if r.review_id not in gold:
            continue
        pred = r.extraction.size_signal.value
        g = gold[r.review_id]
        ok = pred == g
        correct += int(ok)
        rows.append({"review_id": r.review_id, "gold": g, "pred": pred, "correct": ok})
    n = len(rows)
    return {"n": n, "accuracy": round(correct / n, 3) if n else 0.0, "rows": rows}


def eval_groundedness(
    client: LLMClient, retriever: Retriever, cases: list[dict]
) -> dict:
    """cases: [{"query":..., "product_id":..., "user_ctx":...}]"""
    results = []
    total_ratio = 0.0
    for c in cases:
        advice, retrieved = advise(
            client, retriever, c["query"], c["product_id"], user_ctx=c.get("user_ctx")
        )
        g = groundedness(advice, retrieved)
        total_ratio += g["grounded_ratio"]
        results.append(
            {
                "query": c["query"],
                "recommended_size": advice.recommended_size,
                "confidence": advice.confidence.value,
                **g,
            }
        )
    n = len(cases)
    return {
        "n": n,
        "avg_grounded_ratio": round(total_ratio / n, 3) if n else 0.0,
        "rows": results,
    }
