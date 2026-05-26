"""
data_augmentation_controller.py — DataAugmentationController V639 (ADR-081)

SP-C.1 Self-Learning Loop 훈련 데이터 증강 컨트롤러.

증강 전략 5종:
  - SYNONYM_SWAP    : 동의어 교체 (어휘 다양성)
  - BACK_TRANSLATE  : 역번역 시뮬레이션 (문장 구조 변형)
  - RANDOM_DELETION : 단어 무작위 삭제 (노이즈 강건성)
  - SENTENCE_SHUFFLE: 문장 순서 섞기 (순서 불변성)
  - TOKEN_INSERT    : 토큰 삽입 (밀도 증강)

설계 원칙:
  - LOSDB JSONL append-only 영속화 (':memory:' 모드 지원)
  - LLM-0 원칙 완전 준수 (외부 LLM 호출 없음)
  - 모든 연산은 순수 Python 표준 라이브러리만 사용
  - 재현성: random.seed() 지원
"""
from __future__ import annotations

import json
import random
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# -------------------------------------------------
# 증강 전략 상수
# -------------------------------------------------
AUGMENTATION_STRATEGIES: List[str] = [
    "SYNONYM_SWAP",
    "BACK_TRANSLATE",
    "RANDOM_DELETION",
    "SENTENCE_SHUFFLE",
    "TOKEN_INSERT",
]

# 기본 증강 파라미터
DEFAULT_AUGMENT_RATIO: float = 0.15   # 증강 대상 토큰/문장 비율
DEFAULT_AUGMENT_COUNT: int = 3        # 원본 1개당 생성할 증강 샘플 수
MAX_AUGMENT_COUNT: int = 10           # 최대 증강 배수

# 동의어 매핑 (한국어 드라마 도메인 예시 — LLM 없이 규칙 기반)
_SYNONYM_MAP: Dict[str, str] = {
    "훌륭한": "뛰어난", "뛰어난": "탁월한", "탁월한": "우수한",
    "슬픈": "애잔한", "애잔한": "비통한", "비통한": "슬픈",
    "기쁜": "즐거운", "즐거운": "행복한", "행복한": "기쁜",
    "아름다운": "고운", "고운": "예쁜", "예쁜": "아름다운",
    "말했다": "이야기했다", "이야기했다": "전했다", "전했다": "말했다",
    "보았다": "살펴봤다", "살펴봤다": "확인했다", "확인했다": "보았다",
}

# 삽입용 필러 토큰 (한국어 드라마 도메인)
_FILLER_TOKENS: List[str] = [
    "그리고", "하지만", "그래서", "또한", "결국", "사실",
]

_DEFAULT_STORE = "data/losdb/data_augmentation_controller.jsonl"
_MEMORY_SENTINEL = ":memory:"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _split_sentences(text: str) -> List[str]:
    """간단한 문장 분리 (마침표/느낌표/물음표 기준)."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def _tokenize(text: str) -> List[str]:
    """공백 기준 토크나이즈."""
    return text.split()


# -------------------------------------------------
# 데이터 클래스
# -------------------------------------------------
@dataclass
class AugmentedSample:
    """증강된 단일 샘플."""
    sample_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_text: str = ""
    augmented_text: str = ""
    strategy: str = ""
    augment_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "original_text": self.original_text,
            "augmented_text": self.augmented_text,
            "strategy": self.strategy,
            "augment_ratio": self.augment_ratio,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AugmentedSample":
        return cls(
            sample_id=d["sample_id"],
            original_text=d.get("original_text", ""),
            augmented_text=d.get("augmented_text", ""),
            strategy=d.get("strategy", ""),
            augment_ratio=float(d.get("augment_ratio", 0.0)),
        )


@dataclass
class AugmentationBatch:
    """증강 배치 결과."""
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=_now_iso)
    dataset_id: str = ""
    original_count: int = 0
    augmented_count: int = 0
    samples: List[AugmentedSample] = field(default_factory=list)
    strategies_used: List[str] = field(default_factory=list)
    controller_id: str = ""
    note: str = ""

    def summary(self) -> str:
        return (
            f"[BATCH] dataset={self.dataset_id} "
            f"original={self.original_count} "
            f"augmented={self.augmented_count} "
            f"strategies={self.strategies_used}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "created_at": self.created_at,
            "dataset_id": self.dataset_id,
            "original_count": self.original_count,
            "augmented_count": self.augmented_count,
            "samples": [s.to_dict() for s in self.samples],
            "strategies_used": self.strategies_used,
            "controller_id": self.controller_id,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AugmentationBatch":
        return cls(
            batch_id=d["batch_id"],
            created_at=d["created_at"],
            dataset_id=d.get("dataset_id", ""),
            original_count=d.get("original_count", 0),
            augmented_count=d.get("augmented_count", 0),
            samples=[AugmentedSample.from_dict(s) for s in d.get("samples", [])],
            strategies_used=d.get("strategies_used", []),
            controller_id=d.get("controller_id", ""),
            note=d.get("note", ""),
        )


# -------------------------------------------------
# DataAugmentationController 본체
# -------------------------------------------------
class DataAugmentationController:
    """
    훈련 데이터 증강 컨트롤러 -- SP-C.1 V639 (ADR-081).

    사용법::

        ctrl = DataAugmentationController()           # 메모리 모드
        ctrl = DataAugmentationController("path.jsonl")  # 파일 영속화

        batch = ctrl.augment(
            dataset_id="ds-2026-q2",
            texts=["드라마 장면 텍스트..."],
            strategies=["SYNONYM_SWAP", "RANDOM_DELETION"],
            augment_count=3,
            controller_id="human-1",
        )
    """

    def __init__(
        self,
        store_path: str = _MEMORY_SENTINEL,
        synonym_map: Optional[Dict[str, str]] = None,
        filler_tokens: Optional[List[str]] = None,
        seed: Optional[int] = None,
    ) -> None:
        self._store_path = store_path
        self._synonym_map = synonym_map or _SYNONYM_MAP
        self._filler_tokens = filler_tokens or _FILLER_TOKENS
        self._rng = random.Random(seed)
        self._memory: List[AugmentationBatch] = []
        if store_path != _MEMORY_SENTINEL:
            self._load_from_disk()

    # -- 증강 API ----------------------------
    def augment(
        self,
        dataset_id: str,
        texts: List[str],
        strategies: Optional[List[str]] = None,
        augment_count: int = DEFAULT_AUGMENT_COUNT,
        augment_ratio: float = DEFAULT_AUGMENT_RATIO,
        controller_id: str = "",
        note: str = "",
        now: Optional[str] = None,
    ) -> AugmentationBatch:
        """
        텍스트 목록을 증강하여 AugmentationBatch 반환.

        Args:
            dataset_id: 데이터셋 식별자
            texts: 증강 대상 원본 텍스트 목록
            strategies: 사용할 증강 전략 목록 (None이면 전체 5종)
            augment_count: 원본 1개당 생성할 증강 샘플 수 (최대 MAX_AUGMENT_COUNT)
            augment_ratio: 증강 강도 (0.0~1.0)
            controller_id: 제어자 ID
            note: 메모
            now: ISO8601 타임스탬프 (테스트용)
        """
        strategies = strategies or AUGMENTATION_STRATEGIES
        augment_count = min(max(augment_count, 1), MAX_AUGMENT_COUNT)

        samples: List[AugmentedSample] = []
        used_strategies: List[str] = []

        for text in texts:
            if not text.strip():
                continue
            for i in range(augment_count):
                strategy = strategies[i % len(strategies)]
                aug_text = self._apply_strategy(text, strategy, augment_ratio)
                samples.append(AugmentedSample(
                    original_text=text,
                    augmented_text=aug_text,
                    strategy=strategy,
                    augment_ratio=augment_ratio,
                ))
                if strategy not in used_strategies:
                    used_strategies.append(strategy)

        batch = AugmentationBatch(
            created_at=now or _now_iso(),
            dataset_id=dataset_id,
            original_count=len(texts),
            augmented_count=len(samples),
            samples=samples,
            strategies_used=used_strategies,
            controller_id=controller_id,
            note=note,
        )
        self._memory.append(batch)
        if self._store_path != _MEMORY_SENTINEL:
            self._append_to_disk(batch)
        return batch

    def augment_single(
        self,
        text: str,
        strategy: str,
        augment_ratio: float = DEFAULT_AUGMENT_RATIO,
    ) -> AugmentedSample:
        """단일 텍스트 단일 전략 증강 (유틸리티)."""
        aug_text = self._apply_strategy(text, strategy, augment_ratio)
        return AugmentedSample(
            original_text=text,
            augmented_text=aug_text,
            strategy=strategy,
            augment_ratio=augment_ratio,
        )

    # -- 증강 전략 구현 -----------------------
    def _apply_strategy(self, text: str, strategy: str, ratio: float) -> str:
        """전략 디스패처."""
        if strategy == "SYNONYM_SWAP":
            return self._synonym_swap(text, ratio)
        elif strategy == "BACK_TRANSLATE":
            return self._back_translate(text, ratio)
        elif strategy == "RANDOM_DELETION":
            return self._random_deletion(text, ratio)
        elif strategy == "SENTENCE_SHUFFLE":
            return self._sentence_shuffle(text)
        elif strategy == "TOKEN_INSERT":
            return self._token_insert(text, ratio)
        else:
            return text  # 알 수 없는 전략 → 원본 반환

    def _synonym_swap(self, text: str, ratio: float) -> str:
        """동의어 교체: 비율만큼의 단어를 동의어로 교체."""
        tokens = _tokenize(text)
        n_swap = max(1, int(len(tokens) * ratio))
        indices = self._rng.sample(range(len(tokens)), min(n_swap, len(tokens)))
        for idx in indices:
            word = tokens[idx]
            if word in self._synonym_map:
                tokens[idx] = self._synonym_map[word]
        return " ".join(tokens)

    def _back_translate(self, text: str, ratio: float) -> str:
        """
        역번역 시뮬레이션: LLM 없이 규칙 기반 어순 변형.
        비율만큼의 문장을 대상으로 어절 순서를 부분 변경.
        """
        sentences = _split_sentences(text)
        n_target = max(1, int(len(sentences) * ratio))
        indices = self._rng.sample(range(len(sentences)), min(n_target, len(sentences)))
        for idx in indices:
            tokens = _tokenize(sentences[idx])
            if len(tokens) >= 4:
                # 앞 2개 토큰과 나머지 교환 (간단한 어순 변형)
                mid = len(tokens) // 2
                tokens = tokens[mid:] + tokens[:mid]
                sentences[idx] = " ".join(tokens)
        return " ".join(sentences)

    def _random_deletion(self, text: str, ratio: float) -> str:
        """무작위 단어 삭제: 비율만큼 삭제. 단, 최소 1개 토큰 보존."""
        tokens = _tokenize(text)
        if len(tokens) <= 1:
            return text
        n_delete = max(1, int(len(tokens) * ratio))
        n_delete = min(n_delete, len(tokens) - 1)  # 최소 1개 보존
        indices_to_delete = set(self._rng.sample(range(len(tokens)), n_delete))
        return " ".join(t for i, t in enumerate(tokens) if i not in indices_to_delete)

    def _sentence_shuffle(self, text: str) -> str:
        """문장 순서 섞기."""
        sentences = _split_sentences(text)
        if len(sentences) <= 1:
            return text
        self._rng.shuffle(sentences)
        return " ".join(sentences)

    def _token_insert(self, text: str, ratio: float) -> str:
        """필러 토큰 삽입: 비율만큼의 위치에 삽입."""
        tokens = _tokenize(text)
        n_insert = max(1, int(len(tokens) * ratio))
        result = list(tokens)
        for _ in range(n_insert):
            pos = self._rng.randint(0, len(result))
            filler = self._rng.choice(self._filler_tokens)
            result.insert(pos, filler)
        return " ".join(result)

    # -- 조회 API ----------------------------
    def history(self) -> List[AugmentationBatch]:
        """모든 배치 반환 (시간순)."""
        return list(self._memory)

    def last_batch(self) -> Optional[AugmentationBatch]:
        """가장 최근 배치."""
        return self._memory[-1] if self._memory else None

    def total_augmented(self) -> int:
        """누적 증강 샘플 수."""
        return sum(b.augmented_count for b in self._memory)

    def batches_by_dataset(self, dataset_id: str) -> List[AugmentationBatch]:
        """특정 데이터셋 ID의 배치 목록."""
        return [b for b in self._memory if b.dataset_id == dataset_id]

    def count(self) -> int:
        """누적 배치 수."""
        return len(self._memory)

    def clear(self) -> None:
        """메모리 및 디스크 데이터 초기화."""
        self._memory.clear()
        if self._store_path != _MEMORY_SENTINEL:
            Path(self._store_path).write_text("", encoding="utf-8")

    # -- 영속화 ------------------------------
    def _append_to_disk(self, batch: AugmentationBatch) -> None:
        """JSONL append-only 영속화."""
        path = Path(self._store_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(batch.to_dict(), ensure_ascii=False) + "\n")

    def _load_from_disk(self) -> None:
        """디스크에서 JSONL 로드."""
        path = Path(self._store_path)
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                self._memory.append(
                    AugmentationBatch.from_dict(json.loads(line))
                )
            except (json.JSONDecodeError, KeyError):
                continue
