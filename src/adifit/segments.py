"""리뷰 세그먼트와 VOC 트렌드 분석.

석사 연구 배경을 보여주는 레이어다. LLM이 구조화한 태그와 리뷰 임베딩을 결합해
고객 사용 맥락별 클러스터를 만들고, 월별 VOC 이슈 변화를 추적한다.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from .schema import (
    AnalyzedReview,
    COMFORT_TAG_KO,
    CUSTOMER_TAG_KO,
    DESIGN_COLOR_TAG_KO,
    SIZE_SIGNAL_KO,
    USE_CASE_KO,
    VOC_ISSUE_TAG_KO,
    ComfortTag,
    CustomerTag,
    DesignColorTag,
    SizeSignal,
    UseCase,
    VocIssueTag,
)


@dataclass(frozen=True)
class SegmentSummary:
    cluster_id: int
    label: str
    n_reviews: int
    avg_rating: float
    product_names: list[str]
    top_use_cases: list[tuple[str, int]]
    top_comfort_tags: list[tuple[str, int]]
    top_design_color_tags: list[tuple[str, int]]
    top_customer_tags: list[tuple[str, int]]
    top_issue_tags: list[tuple[str, int]]
    size_mix: list[tuple[str, int]]
    representative_reviews: list[AnalyzedReview]
    action: str


@dataclass(frozen=True)
class SegmentAnalysis:
    summaries: list[SegmentSummary]
    points: list[dict]
    trend_rows: list[dict]


def _ko_counts(counter: Counter, ko_map: dict, enum_cls, n: int = 3) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for key, count in counter.most_common(n):
        out.append((ko_map[enum_cls(key)], count))
    return out


def _tag_values(review: AnalyzedReview) -> dict[str, list[str]]:
    e = review.extraction
    return {
        "use_cases": [x.value for x in e.use_cases],
        "comfort_tags": [x.value for x in e.comfort_tags],
        "design_color_tags": [x.value for x in e.design_color_tags],
        "customer_tags": [x.value for x in e.customer_tags],
        "issue_tags": [x.value for x in e.voc_issue_tags],
    }


def _label_segment(
    use_cases: Counter,
    comfort: Counter,
    design: Counter,
    customers: Counter,
    issues: Counter,
    size_mix: Counter,
    avg_rating: float = 5.0,
) -> str:
    n_reviews = sum(size_mix.values())
    performance_signal = use_cases.get(UseCase.race.value, 0) + customers.get(
        CustomerTag.performance_runner.value, 0
    )
    positive_comfort = (
        comfort.get(ComfortTag.cushioned.value, 0)
        + comfort.get(ComfortTag.responsive.value, 0)
        + comfort.get(ComfortTag.lightweight.value, 0)
        + comfort.get(ComfortTag.breathable.value, 0)
        + comfort.get(ComfortTag.long_wear_comfort.value, 0)
    )
    daily_signal = use_cases.get(UseCase.commute.value, 0) + use_cases.get(UseCase.walking.value, 0)
    style_signal = (
        use_cases.get(UseCase.daily.value, 0)
        + design.get(DesignColorTag.easy_to_style.value, 0)
        + design.get(DesignColorTag.stylish.value, 0)
        + design.get(DesignColorTag.photo_match.value, 0)
    )
    fit_risk = issues.get(VocIssueTag.fit_risk.value, 0)
    wide_feet = customers.get(CustomerTag.wide_feet.value, 0)
    small_share = size_mix.get(SizeSignal.runs_small.value, 0) / n_reviews if n_reviews else 0

    if performance_signal >= 1 or use_cases.get(UseCase.race.value, 0) >= 2:
        return "Performance Runners"
    if positive_comfort >= 4 and fit_risk <= 3:
        return "Comfort-driven Buyers"
    if daily_signal >= 2 or comfort.get(ComfortTag.long_wear_comfort.value, 0) >= 2:
        return "Daily Comfort Seekers"
    if style_signal >= 3 and fit_risk <= 2:
        return "Style-first Casual Users"
    if n_reviews >= 2 and avg_rating < 3.0 and (
        issues.get(VocIssueTag.comfort_complaint.value)
        or issues.get(VocIssueTag.durability.value)
        or issues.get(VocIssueTag.delivery_packaging.value)
        or issues.get(VocIssueTag.price_resistance.value)
    ):
        return "Post-purchase VOC Risk"
    if wide_feet >= 2 or fit_risk >= 3 or (n_reviews >= 2 and small_share >= 0.7):
        return "Wide-foot Fit Risk"
    if issues.get(VocIssueTag.durability.value) or issues.get(VocIssueTag.price_resistance.value):
        return "Post-purchase VOC Risk"
    if positive_comfort:
        return "Comfort-driven Buyers"
    return "Mixed Review Segment"


def _action_for(label: str, issues: Counter, size_mix: Counter, comfort: Counter, design: Counter) -> str:
    if label == "Wide-foot Fit Risk":
        return "PDP에 발볼/사이즈업 가이드를 선명하게 노출하고, 발볼 넓은 고객에게 대체 모델을 함께 추천"
    if label == "Performance Runners":
        return "반발력·경량성·대회용 근거 리뷰를 PDP 상단에 배치하고, 발볼 리스크 caveat를 함께 표시"
    if label == "Daily Comfort Seekers":
        return "장시간 착용·출퇴근 편안함 리뷰를 구매 전환 메시지로 활용"
    if label == "Style-first Casual Users":
        return "코디/색상/디자인 긍정 리뷰를 룩북·PDP 이미지 영역과 연결"
    if label == "Comfort-driven Buyers":
        return "쿠션·반발력·장시간 착용 리뷰를 핵심 USP로 묶어 PDP 카피와 추천 문구에 반영"
    if issues.get(VocIssueTag.durability.value):
        return "내구성 불만이 누적되는 세그먼트로 분리해 소재/보증/사용 조건 안내를 보강"
    if issues.get(VocIssueTag.delivery_packaging.value):
        return "배송·포장 이슈를 운영 VOC로 분리하고 물류/패키징 프로세스를 점검"
    if comfort.get(ComfortTag.foot_pain.value) or comfort.get(ComfortTag.thin_cushion.value):
        return "착용감 불만 고객군에 사용 목적별 대체 상품과 기대치 안내를 제공"
    if design.get(DesignColorTag.gets_dirty.value):
        return "오염/관리 이슈를 관리 팁 콘텐츠와 연결"
    return "긍정 키워드를 PDP 카피와 추천 로직의 세그먼트 메시지로 활용"


def build_segments(reviews: list[AnalyzedReview], vectors: np.ndarray, n_clusters: int = 5) -> SegmentAnalysis:
    if not reviews:
        return SegmentAnalysis([], [], [])

    n_clusters = max(1, min(n_clusters, len(reviews)))
    if n_clusters == 1:
        labels = np.zeros(len(reviews), dtype=int)
    else:
        labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=20).fit_predict(vectors)

    if len(reviews) >= 2:
        coords = PCA(n_components=2, random_state=42).fit_transform(vectors)
    else:
        coords = np.zeros((len(reviews), 2))

    groups: dict[int, list[int]] = defaultdict(list)
    for idx, label in enumerate(labels):
        groups[int(label)].append(idx)

    summaries: list[SegmentSummary] = []
    points: list[dict] = []
    for cluster_id, idxs in sorted(groups.items()):
        cluster_reviews = [reviews[i] for i in idxs]
        use_cases: Counter = Counter()
        comfort: Counter = Counter()
        design: Counter = Counter()
        customers: Counter = Counter()
        issues: Counter = Counter()
        size_mix: Counter = Counter()
        products: Counter = Counter()
        for r in cluster_reviews:
            tags = _tag_values(r)
            use_cases.update(tags["use_cases"])
            comfort.update(tags["comfort_tags"])
            design.update(tags["design_color_tags"])
            customers.update(tags["customer_tags"])
            issues.update(tags["issue_tags"])
            size_mix.update([r.extraction.size_signal.value])
            products.update([r.product_name])

        centroid = vectors[idxs].mean(axis=0)
        distances = [(i, float(np.linalg.norm(vectors[i] - centroid))) for i in idxs]
        representative = [reviews[i] for i, _ in sorted(distances, key=lambda x: x[1])[:3]]
        avg_rating = round(sum(r.rating for r in cluster_reviews) / len(cluster_reviews), 2)
        label = _label_segment(use_cases, comfort, design, customers, issues, size_mix, avg_rating)

        summaries.append(
            SegmentSummary(
                cluster_id=cluster_id,
                label=label,
                n_reviews=len(cluster_reviews),
                avg_rating=avg_rating,
                product_names=[name for name, _ in products.most_common()],
                top_use_cases=_ko_counts(use_cases, USE_CASE_KO, UseCase),
                top_comfort_tags=_ko_counts(comfort, COMFORT_TAG_KO, ComfortTag),
                top_design_color_tags=_ko_counts(design, DESIGN_COLOR_TAG_KO, DesignColorTag),
                top_customer_tags=_ko_counts(customers, CUSTOMER_TAG_KO, CustomerTag),
                top_issue_tags=_ko_counts(issues, VOC_ISSUE_TAG_KO, VocIssueTag),
                size_mix=_ko_counts(size_mix, SIZE_SIGNAL_KO, SizeSignal),
                representative_reviews=representative,
                action=_action_for(label, issues, size_mix, comfort, design),
            )
        )

        for i in idxs:
            r = reviews[i]
            tags = _tag_values(r)
            points.append(
                {
                    "cluster_id": cluster_id,
                    "segment": label,
                    "review_id": r.review_id,
                    "product": r.product_name,
                    "rating": r.rating,
                    "x": float(coords[i, 0]),
                    "y": float(coords[i, 1]),
                    "use_cases": ", ".join(USE_CASE_KO[UseCase(x)] for x in tags["use_cases"]) or "-",
                    "comfort": ", ".join(COMFORT_TAG_KO[ComfortTag(x)] for x in tags["comfort_tags"]) or "-",
                    "issues": ", ".join(VOC_ISSUE_TAG_KO[VocIssueTag(x)] for x in tags["issue_tags"]) or "-",
                    "text": r.text,
                }
            )

    return SegmentAnalysis(
        summaries=sorted(summaries, key=lambda s: (-s.n_reviews, s.label)),
        points=points,
        trend_rows=build_trend_rows(reviews),
    )


def build_trend_rows(reviews: list[AnalyzedReview]) -> list[dict]:
    grouped: dict[tuple[str, str], list[AnalyzedReview]] = defaultdict(list)
    for r in reviews:
        month = date.fromisoformat(r.date).strftime("%Y-%m")
        grouped[(month, r.product_name)].append(r)

    rows: list[dict] = []
    for (month, product), rows_for_key in sorted(grouped.items()):
        issues: Counter = Counter()
        use_cases: Counter = Counter()
        comfort: Counter = Counter()
        for r in rows_for_key:
            tags = _tag_values(r)
            issues.update(tags["issue_tags"])
            use_cases.update(tags["use_cases"])
            comfort.update(tags["comfort_tags"])

        rows.append(
            {
                "month": month,
                "product": product,
                "reviews": len(rows_for_key),
                "avg_rating": round(sum(r.rating for r in rows_for_key) / len(rows_for_key), 2),
                "fit_risk": issues.get(VocIssueTag.fit_risk.value, 0),
                "durability": issues.get(VocIssueTag.durability.value, 0),
                "delivery_packaging": issues.get(VocIssueTag.delivery_packaging.value, 0),
                "price_resistance": issues.get(VocIssueTag.price_resistance.value, 0),
                "comfort_complaint": issues.get(VocIssueTag.comfort_complaint.value, 0),
                "running": use_cases.get(UseCase.running.value, 0),
                "daily": use_cases.get(UseCase.daily.value, 0),
                "commute": use_cases.get(UseCase.commute.value, 0),
                "race": use_cases.get(UseCase.race.value, 0),
                "long_wear_comfort": comfort.get(ComfortTag.long_wear_comfort.value, 0),
            }
        )
    return rows
