"""상품 단위 집계 — 리뷰 추출 결과 → 대시보드용 인사이트 + 비즈니스 액션.

여기서 '분석'이 '의사결정'으로 번역된다: 사이즈 편향 → PDP 가이드/반품 액션 등.
"""
from __future__ import annotations

from collections import defaultdict

from .schema import (
    AnalyzedReview,
    Aspect,
    AspectSentimentBreakdown,
    ProductInsight,
    Sentiment,
    SizeSignal,
    WidthSignal,
    ASPECT_KO,
)


def _size_verdict(dist: dict[str, int]) -> str:
    mentioned = {k: v for k, v in dist.items() if k != SizeSignal.not_mentioned.value and v > 0}
    total = sum(mentioned.values())
    if total == 0:
        return "사이즈 관련 언급이 충분하지 않음"
    dom = max(mentioned, key=mentioned.get)
    share = round(100 * mentioned[dom] / total)
    label = {
        SizeSignal.runs_small.value: f"작게 나옴 — 사이즈 언급 {total}건 중 {share}%가 업 권장",
        SizeSignal.true_to_size.value: f"정사이즈 — 사이즈 언급 {total}건 중 {share}%가 만족",
        SizeSignal.runs_large.value: f"크게 나옴 — 사이즈 언급 {total}건 중 {share}%가 다운 권장",
    }
    return label.get(dom, "판단 보류")


def _width_verdict(dist: dict[str, int]) -> str:
    mentioned = {k: v for k, v in dist.items() if k != WidthSignal.not_mentioned.value and v > 0}
    total = sum(mentioned.values())
    if total == 0:
        return "발볼 관련 언급 적음"
    dom = max(mentioned, key=mentioned.get)
    share = round(100 * mentioned[dom] / total)
    label = {
        WidthSignal.narrow.value: f"발볼 좁은 편 — 발볼 언급 {total}건 중 {share}%가 좁다고 응답",
        WidthSignal.normal.value: f"발볼 보통 — 발볼 언급 {total}건 중 {share}%",
        WidthSignal.wide.value: f"발볼 넓은 편 — 발볼 언급 {total}건 중 {share}%가 넓다고 응답",
    }
    return label.get(dom, "판단 보류")


def _actions(insight_ctx: dict) -> list[str]:
    """분포/속성 기반 규칙형 비즈니스 액션 제안."""
    acts: list[str] = []
    size_dist = insight_ctx["size_dist"]
    width_dist = insight_ctx["width_dist"]
    breakdown: dict[Aspect, AspectSentimentBreakdown] = insight_ctx["breakdown"]

    size_mentioned = sum(v for k, v in size_dist.items() if k != SizeSignal.not_mentioned.value)
    small = size_dist.get(SizeSignal.runs_small.value, 0)
    large = size_dist.get(SizeSignal.runs_large.value, 0)
    if size_mentioned and small / size_mentioned >= 0.5:
        pct = round(100 * small / size_mentioned)
        acts.append(
            f"PDP 사이즈 영역에 '정사이즈보다 반 치수 크게' 안내 노출 "
            f"(리뷰 {pct}%가 작다고 응답) → 사이즈 미스매치 교환·반품 감소"
        )
    if size_mentioned and large / size_mentioned >= 0.5:
        acts.append("PDP에 '한 치수 작게' 안내 노출 → 큰 사이즈 반품 감소")

    width_mentioned = sum(v for k, v in width_dist.items() if k != WidthSignal.not_mentioned.value)
    narrow = width_dist.get(WidthSignal.narrow.value, 0)
    if width_mentioned and narrow / width_mentioned >= 0.5:
        acts.append("발볼 좁음 안내 + 발볼 넓은 고객 대상 대체 모델 추천 → 핏 불만 CS 감소")

    dur = breakdown.get(Aspect.durability)
    if dur and dur.total and dur.negative / dur.total >= 0.4:
        acts.append("내구성 부정 리뷰 다수 → 소재/보증 정책 상세페이지 보강, 품질 CS 선제 대응")

    deliv = breakdown.get(Aspect.delivery)
    if deliv and deliv.negative >= 1:
        acts.append("배송·포장 불만 발생 → 물류/포장 프로세스 점검")

    val = breakdown.get(Aspect.value)
    if val and val.total and val.negative / val.total >= 0.5:
        acts.append("가격 저항 신호 → 프로모션/가치 소구 메시지(내구·성능) 강화")

    if not acts:
        acts.append("주요 부정 신호 없음 — 현재 상품 경험 유지, 긍정 키워드를 마케팅에 활용")
    return acts


def aggregate_product(product_id: str, product_name: str, reviews: list[AnalyzedReview]) -> ProductInsight:
    reviews = [r for r in reviews if r.product_id == product_id]
    n = len(reviews)
    avg = round(sum(r.rating for r in reviews) / n, 2) if n else 0.0

    # 속성별 감성 카운트
    counts: dict[Aspect, dict[Sentiment, int]] = defaultdict(lambda: defaultdict(int))
    for r in reviews:
        for a in r.extraction.aspects:
            counts[a.aspect][a.sentiment] += 1
    breakdown_map: dict[Aspect, AspectSentimentBreakdown] = {}
    for aspect in Aspect:
        c = counts.get(aspect, {})
        breakdown_map[aspect] = AspectSentimentBreakdown(
            aspect=aspect,
            positive=c.get(Sentiment.positive, 0),
            neutral=c.get(Sentiment.neutral, 0),
            negative=c.get(Sentiment.negative, 0),
        )
    breakdown = [b for b in breakdown_map.values() if b.total > 0]

    # 사이즈/발볼 분포
    size_dist: dict[str, int] = defaultdict(int)
    width_dist: dict[str, int] = defaultdict(int)
    for r in reviews:
        size_dist[r.extraction.size_signal.value] += 1
        width_dist[r.extraction.width_signal.value] += 1
    size_dist = dict(size_dist)
    width_dist = dict(width_dist)

    # 상위 이슈: 부정 비중 높은 속성
    issues = sorted(
        [b for b in breakdown if b.negative > 0],
        key=lambda b: (b.net_score, -b.negative),
    )
    top_issues = [
        f"{ASPECT_KO[b.aspect]}: 부정 {b.negative}건 (순점수 {b.net_score:+.2f})" for b in issues[:3]
    ]

    actions = _actions({"size_dist": size_dist, "width_dist": width_dist, "breakdown": breakdown_map})

    return ProductInsight(
        product_id=product_id,
        product_name=product_name,
        n_reviews=n,
        avg_rating=avg,
        aspect_breakdown=breakdown,
        size_distribution=size_dist,
        width_distribution=width_dist,
        size_verdict=_size_verdict(size_dist),
        width_verdict=_width_verdict(width_dist),
        top_issues=top_issues,
        action_recommendations=actions,
    )
