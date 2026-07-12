"""RAG 검색기 — 리뷰 임베딩 색인 + 코사인 top-k 검색.

수백 건 규모라 FAISS 없이 numpy 코사인으로 충분(경량·의존성 최소). 임베딩은
review_id+원문 해시로 디스크 캐시하여 재실행 비용을 없앤다.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

from . import config
from .llm import LLMClient
from .schema import AnalyzedReview


def _key(review_id: str, text: str) -> str:
    return f"{review_id}:{hashlib.md5(text.encode()).hexdigest()[:8]}"


def _load_emb_cache() -> dict:
    p = config.CACHE_DIR / "embeddings.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _save_emb_cache(cache: dict) -> None:
    (config.CACHE_DIR / "embeddings.json").write_text(
        json.dumps(cache, ensure_ascii=False), encoding="utf-8"
    )


def _normalize(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.clip(norms, 1e-9, None)


class Retriever:
    def __init__(self, reviews: list[AnalyzedReview], vectors: np.ndarray):
        self.reviews = reviews
        self.vectors = vectors  # (N, d) L2 정규화됨

    @classmethod
    def build(cls, client: LLMClient, reviews: list[AnalyzedReview], use_cache: bool = True) -> "Retriever":
        cache = _load_emb_cache() if use_cache else {}
        need_idx, need_texts = [], []
        vecs: list[list[float] | None] = [None] * len(reviews)
        for i, r in enumerate(reviews):
            k = _key(r.review_id, r.text)
            if use_cache and k in cache:
                vecs[i] = cache[k]
            else:
                need_idx.append(i)
                need_texts.append(r.text)
        if need_texts:
            fresh = client.embed(need_texts, task_type="RETRIEVAL_DOCUMENT")
            for j, i in enumerate(need_idx):
                vecs[i] = fresh[j]
                cache[_key(reviews[i].review_id, reviews[i].text)] = fresh[j]
            if use_cache:
                _save_emb_cache(cache)
        mat = _normalize(np.array(vecs, dtype=np.float32))
        return cls(reviews, mat)

    def search(
        self, client: LLMClient, query: str, product_id: str | None = None, k: int = 6
    ) -> list[tuple[AnalyzedReview, float]]:
        qv = np.array(client.embed([query], task_type="RETRIEVAL_QUERY")[0], dtype=np.float32)
        qv = qv / max(np.linalg.norm(qv), 1e-9)
        sims = self.vectors @ qv
        order = np.argsort(-sims)
        results: list[tuple[AnalyzedReview, float]] = []
        for i in order:
            r = self.reviews[int(i)]
            if product_id and r.product_id != product_id:
                continue
            results.append((r, float(sims[int(i)])))
            if len(results) >= k:
                break
        return results
