"""핏 어드바이저 — 검색된 리뷰 근거만으로 사이즈를 조언(RAG + 근거 통제).

핵심 차별점: 가드레일. 제공 근거 밖 주장 금지, 근거 부족 시 confidence=low,
모든 판단에 실제 review_id 인용. 환각을 구조적으로 억제한다.
"""
from __future__ import annotations

from .llm import LLMClient
from .retriever import Retriever
from .schema import (
    AnalyzedReview,
    FitAdvice,
    SIZE_SIGNAL_KO,
    WIDTH_SIGNAL_KO,
)

_SYSTEM = """너는 아디다스 상품의 '핏 어드바이저'다.
오직 아래 [검색된 리뷰 근거] 안의 내용만으로 사이즈를 조언한다.

규칙:
- 제공된 리뷰에 없는 내용은 추측·생성 금지.
- 근거가 부족하거나 상충하면 confidence를 low/medium으로 낮추고 caveats에 명시.
- 모든 핵심 판단은 실제 review_id와 원문 인용을 citations에 담는다.
- 사용자가 평소 사이즈/발볼을 밝히면 반영한다. 특히 발볼이 넓은 사용자에게는
  '발볼 좁음' 리뷰를 비중 있게 반영해 사이즈 업을 더 적극 고려한다.
- 한국어로, 간결하고 실용적으로 답한다.
"""


def _format_reviews(results: list[tuple[AnalyzedReview, float]]) -> str:
    lines = []
    for r, sim in results:
        e = r.extraction
        lines.append(
            f"[{r.review_id}] (평점 {r.rating}, 사이즈신호={SIZE_SIGNAL_KO[e.size_signal]}, "
            f"발볼={WIDTH_SIGNAL_KO[e.width_signal]})\n  \"{r.text}\""
        )
    return "\n".join(lines)


def advise(
    client: LLMClient,
    retriever: Retriever,
    query: str,
    product_id: str,
    user_ctx: str | None = None,
    k: int = 6,
) -> tuple[FitAdvice, list[tuple[AnalyzedReview, float]]]:
    results = retriever.search(client, query, product_id=product_id, k=k)
    ctx = f"사용자 추가정보: {user_ctx}\n\n" if user_ctx else ""
    prompt = (
        f"{ctx}사용자 질문: {query}\n\n"
        f"[검색된 리뷰 근거] (반드시 이 안에서만 판단)\n{_format_reviews(results)}\n"
    )
    advice = client.generate_structured(prompt, FitAdvice, system=_SYSTEM, temperature=0.1)
    return advice, results


def groundedness(advice: FitAdvice, results: list[tuple[AnalyzedReview, float]]) -> dict:
    """인용된 review_id가 실제 검색 근거에 존재하는지 검증(환각 방지 지표)."""
    retrieved_ids = {r.review_id for r, _ in results}
    cited = [c.review_id for c in advice.citations]
    valid = [cid for cid in cited if cid in retrieved_ids]
    return {
        "n_citations": len(cited),
        "n_valid": len(valid),
        "grounded_ratio": (len(valid) / len(cited)) if cited else 0.0,
        "invalid_ids": [cid for cid in cited if cid not in retrieved_ids],
    }
