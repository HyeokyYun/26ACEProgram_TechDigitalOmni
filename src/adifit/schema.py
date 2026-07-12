"""데이터 스키마 — 리뷰 추출·집계·어드바이저 결과의 구조 정의.

이 스키마가 파이프라인의 계약(contract)이다. LLM 구조화 출력, 집계, UI가
모두 이 타입에 의존한다.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ---------- 열거형 ----------
class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class SizeSignal(str, Enum):
    runs_small = "runs_small"      # 작게 나옴 → 사이즈 업 권장
    true_to_size = "true_to_size"  # 정사이즈
    runs_large = "runs_large"      # 크게 나옴 → 사이즈 다운
    not_mentioned = "not_mentioned"


class WidthSignal(str, Enum):
    narrow = "narrow"    # 발볼 좁음
    normal = "normal"
    wide = "wide"        # 발볼 넓음
    not_mentioned = "not_mentioned"


class Aspect(str, Enum):
    fit_size = "fit_size"        # 핏/사이즈
    comfort = "comfort"          # 착용감/쿠션
    quality = "quality"          # 품질/마감
    durability = "durability"    # 내구성
    delivery = "delivery"        # 배송/포장
    design = "design"            # 디자인
    value = "value"              # 가격 대비 가치


class UseCase(str, Enum):
    running = "running"          # 러닝/조깅
    walking = "walking"          # 걷기/산책
    commute = "commute"          # 출퇴근/이동
    daily = "daily"              # 일상/코디
    gym = "gym"                  # 헬스장/운동
    race = "race"                # 대회/기록 목적


class ComfortTag(str, Enum):
    cushioned = "cushioned"                  # 쿠션감 좋음
    responsive = "responsive"                # 반발력/추진력
    lightweight = "lightweight"              # 가벼움
    breathable = "breathable"                # 통기성
    long_wear_comfort = "long_wear_comfort"  # 장시간 착용 편함
    stiff = "stiff"                          # 뻣뻣함
    thin_cushion = "thin_cushion"            # 쿠션 얇음
    foot_pain = "foot_pain"                  # 발 통증/눌림
    heel_slip = "heel_slip"                  # 뒤꿈치 헐거움


class DesignColorTag(str, Enum):
    photo_match = "photo_match"          # 사진/상세페이지와 유사
    easy_to_style = "easy_to_style"      # 코디 쉬움
    stylish = "stylish"                  # 디자인 긍정
    color_mismatch = "color_mismatch"    # 색상 차이
    gets_dirty = "gets_dirty"            # 오염/관리 이슈
    low_height = "low_height"            # 굽/키높이 기대 미달


class CustomerTag(str, Enum):
    wide_feet = "wide_feet"
    narrow_feet = "narrow_feet"
    high_instep = "high_instep"
    performance_runner = "performance_runner"
    casual_user = "casual_user"
    value_sensitive = "value_sensitive"


class VocIssueTag(str, Enum):
    fit_risk = "fit_risk"
    durability = "durability"
    delivery_packaging = "delivery_packaging"
    price_resistance = "price_resistance"
    quality_finish = "quality_finish"
    comfort_complaint = "comfort_complaint"


ASPECT_KO = {
    Aspect.fit_size: "핏·사이즈",
    Aspect.comfort: "착용감·쿠션",
    Aspect.quality: "품질·마감",
    Aspect.durability: "내구성",
    Aspect.delivery: "배송·포장",
    Aspect.design: "디자인",
    Aspect.value: "가격 대비 가치",
}

USE_CASE_KO = {
    UseCase.running: "러닝",
    UseCase.walking: "걷기",
    UseCase.commute: "출퇴근",
    UseCase.daily: "일상",
    UseCase.gym: "헬스장",
    UseCase.race: "대회",
}

COMFORT_TAG_KO = {
    ComfortTag.cushioned: "쿠션 좋음",
    ComfortTag.responsive: "반발력",
    ComfortTag.lightweight: "가벼움",
    ComfortTag.breathable: "통기성",
    ComfortTag.long_wear_comfort: "장시간 편함",
    ComfortTag.stiff: "뻣뻣함",
    ComfortTag.thin_cushion: "쿠션 얇음",
    ComfortTag.foot_pain: "발 통증",
    ComfortTag.heel_slip: "뒤꿈치 헐거움",
}

DESIGN_COLOR_TAG_KO = {
    DesignColorTag.photo_match: "사진과 유사",
    DesignColorTag.easy_to_style: "코디 쉬움",
    DesignColorTag.stylish: "디자인 긍정",
    DesignColorTag.color_mismatch: "색상 차이",
    DesignColorTag.gets_dirty: "오염/관리",
    DesignColorTag.low_height: "굽 낮음",
}

CUSTOMER_TAG_KO = {
    CustomerTag.wide_feet: "발볼 넓음",
    CustomerTag.narrow_feet: "발볼 좁음",
    CustomerTag.high_instep: "발등 높음",
    CustomerTag.performance_runner: "기록 목적 러너",
    CustomerTag.casual_user: "일상 착용자",
    CustomerTag.value_sensitive: "가격 민감",
}

VOC_ISSUE_TAG_KO = {
    VocIssueTag.fit_risk: "핏/사이즈 리스크",
    VocIssueTag.durability: "내구성",
    VocIssueTag.delivery_packaging: "배송/포장",
    VocIssueTag.price_resistance: "가격 저항",
    VocIssueTag.quality_finish: "품질/마감",
    VocIssueTag.comfort_complaint: "착용감 불만",
}

SIZE_SIGNAL_KO = {
    SizeSignal.runs_small: "작게 나옴",
    SizeSignal.true_to_size: "정사이즈",
    SizeSignal.runs_large: "크게 나옴",
    SizeSignal.not_mentioned: "언급 없음",
}

WIDTH_SIGNAL_KO = {
    WidthSignal.narrow: "좁음",
    WidthSignal.normal: "보통",
    WidthSignal.wide: "넓음",
    WidthSignal.not_mentioned: "언급 없음",
}


# ---------- LLM 추출 결과 (리뷰 1건) ----------
class AspectMention(BaseModel):
    aspect: Aspect
    sentiment: Sentiment
    evidence: str = Field(description="해당 판단의 근거가 된 리뷰 원문 일부(짧게 인용)")


class ReviewExtraction(BaseModel):
    """LLM이 리뷰 1건에서 뽑아내는 구조화 정보 (review_id는 코드가 부여)."""
    size_signal: SizeSignal
    width_signal: WidthSignal
    aspects: list[AspectMention]
    overall_sentiment: Sentiment
    use_cases: list[UseCase] = Field(
        default_factory=list,
        description="리뷰에 명시된 사용 맥락. 언급이 없으면 빈 배열.",
    )
    comfort_tags: list[ComfortTag] = Field(
        default_factory=list,
        description="착용감/성능 관련 세부 태그. 언급이 없으면 빈 배열.",
    )
    design_color_tags: list[DesignColorTag] = Field(
        default_factory=list,
        description="디자인/색상/코디 관련 세부 태그. 언급이 없으면 빈 배열.",
    )
    customer_tags: list[CustomerTag] = Field(
        default_factory=list,
        description="리뷰 작성자 또는 사용자의 맥락 태그. 언급이 없으면 빈 배열.",
    )
    voc_issue_tags: list[VocIssueTag] = Field(
        default_factory=list,
        description="운영/상품 개선 관점의 VOC 이슈 태그. 언급이 없으면 빈 배열.",
    )


class AnalyzedReview(BaseModel):
    """원본 리뷰 + 추출 결과 결합."""
    review_id: str
    product_id: str
    product_name: str
    rating: int
    date: str
    text: str
    extraction: ReviewExtraction


# ---------- 집계 결과 (상품 1개) ----------
class AspectSentimentBreakdown(BaseModel):
    aspect: Aspect
    positive: int = 0
    neutral: int = 0
    negative: int = 0

    @property
    def total(self) -> int:
        return self.positive + self.neutral + self.negative

    @property
    def net_score(self) -> float:
        """(긍정-부정)/전체, -1~1. 이슈 랭킹에 사용."""
        return (self.positive - self.negative) / self.total if self.total else 0.0


class ProductInsight(BaseModel):
    product_id: str
    product_name: str
    n_reviews: int
    avg_rating: float
    aspect_breakdown: list[AspectSentimentBreakdown]
    size_distribution: dict[str, int]   # SizeSignal.value -> count
    width_distribution: dict[str, int]  # WidthSignal.value -> count
    size_verdict: str                   # 사람이 읽는 사이즈 결론
    width_verdict: str
    top_issues: list[str]               # 부정 비중 높은 속성 요약
    action_recommendations: list[str]   # 비즈니스 실행 제안


# ---------- 어드바이저 결과 ----------
class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class CitedEvidence(BaseModel):
    review_id: str
    quote: str


class FitAdvice(BaseModel):
    recommended_size: str = Field(description="예: '정사이즈', '반 사이즈 업(270)'")
    confidence: Confidence
    rationale: str = Field(description="검색된 리뷰 근거에 기반한 설명")
    citations: list[CitedEvidence] = Field(description="근거가 된 리뷰 id와 인용문")
    caveats: str = Field(description="주의사항 또는 근거가 부족한 부분")
