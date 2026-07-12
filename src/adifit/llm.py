"""LLM 백엔드 추상화.

파이프라인은 `LLMClient` 인터페이스에만 의존한다. 지금은 Gemini(무료 API)를
쓰지만, 같은 인터페이스로 Claude·Ollama 등으로 교체할 수 있다. 이 경계 덕분에
모델 교체가 파이프라인/UI에 영향을 주지 않는다.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel

from . import config

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    """모든 LLM 백엔드가 구현해야 하는 계약."""

    @abstractmethod
    def generate_structured(
        self, prompt: str, schema: Type[T], system: str | None = None, temperature: float = 0.0
    ) -> T:
        """스키마에 맞는 구조화 객체를 반환."""

    @abstractmethod
    def generate_text(self, prompt: str, system: str | None = None, temperature: float = 0.7) -> str:
        ...

    @abstractmethod
    def embed(self, texts: list[str], task_type: str | None = None) -> list[list[float]]:
        ...


class GeminiClient(LLMClient):
    """Google Gemini 구현 (google-genai SDK)."""

    def __init__(self, api_key: str | None = None, model: str | None = None, embed_model: str | None = None):
        from google import genai  # 지연 임포트: 백엔드 미사용 시 의존성 불필요

        self._genai = genai
        from google.genai import types

        self._types = types
        self.model = model or config.LLM_MODEL
        self.embed_model = embed_model or config.EMBED_MODEL
        self.client = genai.Client(api_key=api_key or config.require_api_key())

    def _retry(self, fn, tries: int = 4):
        last = None
        for i in range(tries):
            try:
                return fn()
            except Exception as e:  # noqa: BLE001 — 재시도 대상은 주로 rate limit/일시 오류
                last = e
                msg = str(e).lower()
                # 인증/모델 오류는 재시도 무의미
                if any(k in msg for k in ("api key", "not_found", "permission", "invalid")):
                    raise
                time.sleep(1.5 * (i + 1))
        raise last  # type: ignore[misc]

    def generate_structured(self, prompt, schema, system=None, temperature=0.0):
        cfg = self._types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            system_instruction=system,
            temperature=temperature,
        )
        r = self._retry(
            lambda: self.client.models.generate_content(model=self.model, contents=prompt, config=cfg)
        )
        if r.parsed is None:
            # 방어적: 스키마 파싱 실패 시 원문으로 재구성 시도
            return schema.model_validate_json(r.text)
        return r.parsed

    def generate_text(self, prompt, system=None, temperature=0.7):
        cfg = self._types.GenerateContentConfig(system_instruction=system, temperature=temperature)
        r = self._retry(
            lambda: self.client.models.generate_content(model=self.model, contents=prompt, config=cfg)
        )
        return r.text or ""

    def embed(self, texts, task_type=None):
        out: list[list[float]] = []
        # 임베딩 API 배치 한도를 고려해 청크 처리
        for i in range(0, len(texts), 100):
            chunk = texts[i : i + 100]
            cfg = self._types.EmbedContentConfig(task_type=task_type) if task_type else None
            r = self._retry(
                lambda c=chunk, cf=cfg: self.client.models.embed_content(
                    model=self.embed_model, contents=c, config=cf
                )
            )
            out.extend(list(e.values) for e in r.embeddings)
        return out


def get_client() -> LLMClient:
    """기본 백엔드 팩토리. 여기만 바꾸면 전체 백엔드 교체."""
    return GeminiClient()
