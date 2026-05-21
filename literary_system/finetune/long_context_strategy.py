"""
SP-B.1 (V599) — LongContextStrategy: 장문 맥락 청킹 전략

Phase B 본안 보강 B-M-11:
  - 청크 크기: 100K 토큰 (≈ 400K 문자)
  - 오버랩:    16K 토큰  (≈  64K 문자)
  - NKG RAG 컨텍스트 주입 (선택적)
  - 청크별 독립 처리 후 결과 병합

목적: Llama-3.1-8B 128K 컨텍스트 윈도우 내에서
     드라마 원고 전체를 청크 단위로 파인튜닝 데이터로 변환.

LLM-0 원칙: 외부 LLM API 호출 없음.
ADR-059 참조.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


# ---------------------------------------------------------------------------
# 상수 (B-M-11)
# ---------------------------------------------------------------------------

# 토큰 근사: 1 토큰 ≈ 4 문자 (한국어 기준 보수적 추정)
CHARS_PER_TOKEN: int = 4

CHUNK_SIZE_TOKENS:   int = 100_000        # 100K 토큰
OVERLAP_TOKENS:      int =  16_000        #  16K 토큰

CHUNK_SIZE_CHARS:    int = CHUNK_SIZE_TOKENS  * CHARS_PER_TOKEN   # 400_000
OVERLAP_CHARS:       int = OVERLAP_TOKENS     * CHARS_PER_TOKEN   #  64_000


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class TextChunk:
    """단일 텍스트 청크."""
    chunk_id:    int
    text:        str
    start_char:  int
    end_char:    int
    token_count: int          # 근사 토큰 수
    nkg_context: Optional[str] = None   # NKG RAG 주입 컨텍스트

    @property
    def prompt_text(self) -> str:
        """NKG 컨텍스트 포함 최종 프롬프트 텍스트."""
        if self.nkg_context:
            return f"[NKG_CONTEXT]\n{self.nkg_context}\n[/NKG_CONTEXT]\n\n{self.text}"
        return self.text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id":    self.chunk_id,
            "start_char":  self.start_char,
            "end_char":    self.end_char,
            "token_count": self.token_count,
            "text_len":    len(self.text),
            "has_nkg":     self.nkg_context is not None,
        }


@dataclass
class ChunkingResult:
    """청킹 결과 전체."""
    chunks:       List[TextChunk]
    total_chars:  int
    total_tokens: int

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_count":  self.chunk_count,
            "total_chars":  self.total_chars,
            "total_tokens": self.total_tokens,
            "chunks":       [c.to_dict() for c in self.chunks],
        }


# ---------------------------------------------------------------------------
# LongContextStrategy — 메인 클래스
# ---------------------------------------------------------------------------

class LongContextStrategy:
    """
    장문 텍스트를 100K 토큰 청크로 분할하는 전략 클래스.

    B-M-11:
      chunk_size_tokens = 100K
      overlap_tokens    = 16K
      nkg_rag 컨텍스트 선택 주입

    청크 경계는 단락(\\n\\n) 또는 문장(。!?) 단위에서 정렬.

    Usage:
        strategy = LongContextStrategy()
        result = strategy.chunk("드라마 전체 원고 텍스트…")
        for chunk in result.chunks:
            # chunk.prompt_text → NKG 컨텍스트 포함 완전 텍스트
            train_sample(chunk.prompt_text)
    """

    def __init__(
        self,
        chunk_size_tokens: int = CHUNK_SIZE_TOKENS,
        overlap_tokens:    int = OVERLAP_TOKENS,
        chars_per_token:   int = CHARS_PER_TOKEN,
    ) -> None:
        """
        Args:
            chunk_size_tokens: 청크 크기 (토큰 수)
            overlap_tokens:    오버랩 크기 (토큰 수)
            chars_per_token:   토큰당 문자 수 추정
        """
        if overlap_tokens >= chunk_size_tokens:
            raise ValueError(
                f"overlap_tokens({overlap_tokens}) must be < chunk_size_tokens({chunk_size_tokens})"
            )
        self.chunk_size_chars = chunk_size_tokens * chars_per_token
        self.overlap_chars    = overlap_tokens    * chars_per_token
        self.chars_per_token  = chars_per_token

    def _find_boundary(self, text: str, target: int) -> int:
        """
        target 위치 근처에서 자연스러운 청크 경계(단락/문장 끝) 탐색.

        최대 500자 범위 안에서 \\n\\n, \\n, 문장 부호 순으로 탐색.
        못 찾으면 target 그대로 반환.
        """
        search_start = max(0, target - 500)
        search_end   = min(len(text), target + 500)
        region       = text[search_start:search_end]

        # 1순위: 단락 경계
        para_pos = region.rfind("\n\n", 0, target - search_start + 1)
        if para_pos != -1:
            return search_start + para_pos + 2

        # 2순위: 개행
        nl_pos = region.rfind("\n", 0, target - search_start + 1)
        if nl_pos != -1:
            return search_start + nl_pos + 1

        # 3순위: 문장 부호
        for punct in ("。", "！", "？", ".", "!", "?"):
            p_pos = region.rfind(punct, 0, target - search_start + 1)
            if p_pos != -1:
                return search_start + p_pos + 1

        return target

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // self.chars_per_token)

    def chunk(
        self,
        text: str,
        nkg_contexts: Optional[List[str]] = None,
    ) -> ChunkingResult:
        """
        텍스트를 청크로 분할.

        Args:
            text:         분할할 전체 텍스트
            nkg_contexts: 청크별 NKG RAG 컨텍스트 리스트 (선택).
                          길이가 chunks 수보다 짧으면 순환(cycle) 사용.

        Returns:
            ChunkingResult
        """
        total_len = len(text)
        chunks: List[TextChunk] = []
        start = 0
        chunk_id = 0

        while start < total_len:
            # 청크 끝 위치 계산
            raw_end = min(start + self.chunk_size_chars, total_len)

            # 자연 경계 탐색 (마지막 청크면 그냥 끝까지)
            if raw_end < total_len:
                end = self._find_boundary(text, raw_end)
            else:
                end = total_len

            chunk_text = text[start:end]

            # NKG 컨텍스트 할당
            nkg_ctx: Optional[str] = None
            if nkg_contexts:
                nkg_ctx = nkg_contexts[chunk_id % len(nkg_contexts)]

            chunks.append(TextChunk(
                chunk_id    = chunk_id,
                text        = chunk_text,
                start_char  = start,
                end_char    = end,
                token_count = self._estimate_tokens(chunk_text),
                nkg_context = nkg_ctx,
            ))

            chunk_id += 1

            # 다음 청크 시작 위치 (오버랩 적용)
            next_start = end - self.overlap_chars
            if next_start <= start:
                # 진행이 없는 경우 강제 전진
                next_start = start + max(1, self.chunk_size_chars - self.overlap_chars)
            start = next_start

            if start >= total_len:
                break

        return ChunkingResult(
            chunks       = chunks,
            total_chars  = total_len,
            total_tokens = self._estimate_tokens(text),
        )

    def iter_chunks(
        self,
        text: str,
        nkg_contexts: Optional[List[str]] = None,
    ) -> Iterator[TextChunk]:
        """chunk()의 제너레이터 버전."""
        result = self.chunk(text, nkg_contexts)
        yield from result.chunks

    def summary(self, result: ChunkingResult) -> Dict[str, Any]:
        """청킹 결과 요약 통계."""
        if not result.chunks:
            return {"chunk_count": 0, "total_chars": 0, "avg_chunk_chars": 0}

        lens = [len(c.text) for c in result.chunks]
        return {
            "chunk_count":      result.chunk_count,
            "total_chars":      result.total_chars,
            "total_tokens_est": result.total_tokens,
            "avg_chunk_chars":  round(sum(lens) / len(lens)),
            "min_chunk_chars":  min(lens),
            "max_chunk_chars":  max(lens),
            "chunk_size_tokens_config": self.chunk_size_chars // self.chars_per_token,
            "overlap_tokens_config":    self.overlap_chars    // self.chars_per_token,
        }
