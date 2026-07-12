"""전체 파이프라인 오케스트레이터 — 로드 → 추출 → 색인 → 집계.

extractor/retriever가 각자 디스크 캐시를 하므로, 최초 1회만 LLM을 호출하고
이후에는 즉시 로드된다. Streamlit은 이 함수를 세션 캐시로 감싼다.
"""
from __future__ import annotations

from .aggregator import aggregate_product
from .data_loader import load_reviews, products
from .llm import LLMClient
from .retriever import Retriever
from .schema import AnalyzedReview, ProductInsight
from .segments import SegmentAnalysis, build_segments


class Analysis:
    def __init__(
        self,
        analyzed: list[AnalyzedReview],
        insights: dict[str, ProductInsight],
        retriever: Retriever,
        product_list: list[tuple[str, str]],
        segments: SegmentAnalysis,
    ):
        self.analyzed = analyzed
        self.insights = insights
        self.retriever = retriever
        self.products = product_list  # [(product_id, product_name), ...]
        self.segments = segments


def build_analysis(client: LLMClient, path=None, progress=None) -> Analysis:
    from .extractor import extract_all

    rows = load_reviews(path)
    analyzed = extract_all(client, rows, progress=progress)
    retriever = Retriever.build(client, analyzed)
    plist = products(rows)
    insights = {pid: aggregate_product(pid, pname, analyzed) for pid, pname in plist}
    segments = build_segments(analyzed, retriever.vectors)
    return Analysis(analyzed, insights, retriever, plist, segments)
