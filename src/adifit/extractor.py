"""속성기반 추출 — 리뷰 1건 → 구조화(사이즈/발볼/사용맥락/VOC).

LLM 호출은 결정적이지 않지만 temperature=0 + 캐시로 재현성과 비용을 관리한다.
캐시 키 = 스키마 버전 + review_id + 원문 해시 → 스키마/원문이 바뀌면 자동 재추출.
"""
from __future__ import annotations

import hashlib
import json

from . import config
from .llm import LLMClient
from .schema import AnalyzedReview, ReviewExtraction

_SCHEMA_VERSION = "v2-context-tags"

_SYSTEM = """너는 신발·의류 이커머스 리뷰를 분석하는 시스템이다.
주어진 리뷰 1건에서 아래를 구조화 추출하라.

[size_signal] 이 리뷰가 시사하는 사이즈 경향
- runs_small: 작게 나옴 / 사이즈 업(반 치수↑)을 했거나 권장 / 평소보다 크게 신음
- true_to_size: 정사이즈로 잘 맞음
- runs_large: 크게 나옴 / 사이즈 다운 권장
- not_mentioned: 사이즈 언급 없음

[width_signal] 발볼(볼 너비): narrow(좁음) / normal(보통) / wide(넓음) / not_mentioned

[aspects] 리뷰에 실제로 언급된 속성만. 각 항목에 evidence는 리뷰 원문에서 짧게 인용.
- fit_size(핏·사이즈), comfort(착용감·쿠션), quality(품질·마감),
  durability(내구성), delivery(배송·포장), design(디자인), value(가격 대비 가치)

[use_cases] 리뷰에 명시된 사용 맥락만 배열로 선택. 없으면 [].
- running(러닝/조깅), walking(걷기/산책), commute(출퇴근/이동),
  daily(일상/코디), gym(헬스장/운동), race(대회/기록 목적)

[comfort_tags] 착용감·성능 관련 세부 신호만 배열로 선택. 없으면 [].
- cushioned(쿠션 좋음), responsive(반발력/추진력), lightweight(가벼움),
  breathable(통기성), long_wear_comfort(장시간 착용 편함),
  stiff(뻣뻣함), thin_cushion(쿠션 얇음), foot_pain(발 통증/눌림),
  heel_slip(뒤꿈치 헐거움)

[design_color_tags] 디자인·색상·코디 관련 신호만 배열로 선택. 없으면 [].
- photo_match(사진/상세페이지와 유사), easy_to_style(코디 쉬움), stylish(디자인 긍정),
  color_mismatch(색상 차이), gets_dirty(오염/관리 이슈), low_height(굽/키높이 기대 미달)

[customer_tags] 사용자 맥락이 명시된 경우만 배열로 선택. 없으면 [].
- wide_feet(발볼 넓음), narrow_feet(발볼 좁음), high_instep(발등 높음),
  performance_runner(기록 목적 러너), casual_user(일상 착용자), value_sensitive(가격 민감)

[voc_issue_tags] 개선/운영 관점의 이슈만 배열로 선택. 없으면 [].
- fit_risk(핏/사이즈 리스크), durability(내구성), delivery_packaging(배송/포장),
  price_resistance(가격 저항), quality_finish(품질/마감), comfort_complaint(착용감 불만)

[overall_sentiment] 리뷰 전체 톤: positive / neutral / negative

규칙:
- evidence는 반드시 리뷰 원문 인용. 지어내지 말 것.
- 언급되지 않은 속성은 넣지 말 것.
- 태그도 리뷰에 명시된 내용만 선택하고, 추론이 약하면 넣지 말 것.
- "반 올렸다 / 사이즈 업 했다"는 곧 작게 나온다는 신호(runs_small)로 판단.
"""


def _cache_key(review_id: str, text: str) -> str:
    h = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"{_SCHEMA_VERSION}:{review_id}:{h}"


def _load_cache() -> dict:
    p = config.CACHE_DIR / "extractions.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict) -> None:
    p = config.CACHE_DIR / "extractions.json"
    p.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_one(client: LLMClient, review: dict) -> ReviewExtraction:
    return client.generate_structured(review["text"], ReviewExtraction, system=_SYSTEM, temperature=0.0)


def extract_all(
    client: LLMClient, reviews: list[dict], use_cache: bool = True, progress=None
) -> list[AnalyzedReview]:
    cache = _load_cache() if use_cache else {}
    out: list[AnalyzedReview] = []
    n_calls = 0
    for i, r in enumerate(reviews):
        key = _cache_key(r["review_id"], r["text"])
        if use_cache and key in cache:
            ext = ReviewExtraction.model_validate(cache[key])
        else:
            ext = extract_one(client, r)
            cache[key] = ext.model_dump()
            n_calls += 1
        out.append(
            AnalyzedReview(
                review_id=r["review_id"],
                product_id=r["product_id"],
                product_name=r["product_name"],
                rating=int(r["rating"]),
                date=r["date"],
                text=r["text"],
                extraction=ext,
            )
        )
        if progress:
            progress(i + 1, len(reviews))
    if use_cache and n_calls:
        _save_cache(cache)
    return out
