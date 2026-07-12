"""리뷰 데이터 로딩. 지금은 아디다스 데모 큐레이션 셋을 같은 스키마로 읽는다."""
from __future__ import annotations

import json
from pathlib import Path

from . import config

REQUIRED = {"review_id", "product_id", "product_name", "rating", "date", "text"}


def load_reviews(path: str | Path | None = None) -> list[dict]:
    path = Path(path) if path else config.DEMO_REVIEWS
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    for r in rows:
        missing = REQUIRED - r.keys()
        if missing:
            raise ValueError(f"리뷰 {r.get('review_id', '?')} 필드 누락: {missing}")
    return rows


def products(rows: list[dict]) -> list[tuple[str, str]]:
    """(product_id, product_name) 유니크 목록, 등장 순서 유지."""
    seen: dict[str, str] = {}
    for r in rows:
        seen.setdefault(r["product_id"], r["product_name"])
    return list(seen.items())
