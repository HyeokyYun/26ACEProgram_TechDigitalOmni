"""환경설정 — .env 로드, 경로, 모델명. 한 곳에서만 관리."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# --- LLM backend (교체 가능) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = os.getenv("ADIFIT_LLM_MODEL", "gemini-2.5-flash")
EMBED_MODEL = os.getenv("ADIFIT_EMBED_MODEL", "gemini-embedding-001")

# --- 경로 ---
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
DEMO_REVIEWS = DATA_DIR / "adidas_demo_reviews.json"
GOLD_LABELS = DATA_DIR / "gold_labels.json"

CACHE_DIR.mkdir(parents=True, exist_ok=True)


def require_api_key() -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY가 없습니다. .env 파일에 키를 넣어주세요 "
            "(무료 발급: https://aistudio.google.com/apikey)."
        )
    return GEMINI_API_KEY
