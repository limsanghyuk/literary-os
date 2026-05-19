"""
literary_system/slm/synthetic_augmentor_sp3.py
V495: SyntheticAugmentor SP3 확장 레이어

소량 시드 데이터 → 합성 데이터 확장 (Mock LLM 기반).
실 LLM 어댑터를 주입하면 실제 합성 텍스트를 생성할 수 있으며,
주입하지 않으면 규칙 기반 Mock으로 동작한다.

3종 전략:
  1. paraphrase       — 동의어 치환 + 어순 변경
  2. back_translation — 다국어 역번역 시뮬레이션 (Mock)
  3. style_transfer   — 문체 변환 (격식체 ↔ 구어체)

ADR-008 준수: 합성 데이터에 synthetic=True 플래그 부착
"""
from __future__ import annotations

import copy
import random
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

# ── Mock 변환 함수 ────────────────────────────────────────────────────

# 한국어 동의어 간이 맵
_SYNONYMS: Dict[str, str] = {
    "주인공": "화자", "등장한다": "나타난다", "이야기": "서사", "갈등": "충돌",
    "사랑": "애정", "시작": "출발", "끝": "마무리", "마음": "심정",
    "생각": "고민", "결국": "마침내", "하지만": "그러나", "그래서": "따라서",
    "장면": "씬", "대화": "대사", "감정": "심리", "결말": "엔딩",
}

_FORMAL_TO_COLLOQUIAL: Dict[str, str] = {
    "하였다": "했다", "되었다": "됐다", "이었다": "였다",
    "합니다": "해요", "입니다": "이에요", "습니다": "어요",
    "하겠습니다": "할게요", "보겠습니다": "볼게요",
}

_COLLOQUIAL_TO_FORMAL: Dict[str, str] = {v: k for k, v in _FORMAL_TO_COLLOQUIAL.items()}


def _mock_paraphrase(text: str, rng: random.Random) -> str:
    """단어 수준 동의어 치환."""
    words = text.split()
    result = []
    for w in words:
        # 30% 확률로 동의어 치환
        if rng.random() < 0.3 and w in _SYNONYMS:
            result.append(_SYNONYMS[w])
        else:
            result.append(w)
    return " ".join(result)


def _mock_back_translation(text: str, rng: random.Random) -> str:
    """역번역 시뮬레이션 — 문장 순서 약간 변경 + 어미 변형."""
    sentences = re.split(r'(?<=[.!?。])\s+', text.strip())
    if len(sentences) > 1 and rng.random() < 0.4:
        # 인접 문장 2개 교환
        i = rng.randint(0, len(sentences) - 2)
        sentences[i], sentences[i+1] = sentences[i+1], sentences[i]
    # 어미 소폭 변형
    result = " ".join(sentences)
    for src, dst in list(_FORMAL_TO_COLLOQUIAL.items())[:3]:
        if src in result and rng.random() < 0.5:
            result = result.replace(src, dst, 1)
    return result


def _mock_style_transfer(text: str, rng: random.Random, to_formal: bool = True) -> str:
    """문체 변환 (격식체 ↔ 구어체)."""
    mapping = _COLLOQUIAL_TO_FORMAL if to_formal else _FORMAL_TO_COLLOQUIAL
    result = text
    for src, dst in mapping.items():
        result = result.replace(src, dst)
    return result


# ── 전략 레지스트리 ───────────────────────────────────────────────────
StrategyFn = Callable[[str, random.Random], str]

STRATEGY_REGISTRY: Dict[str, StrategyFn] = {
    "paraphrase":       _mock_paraphrase,
    "back_translation": _mock_back_translation,
    "style_transfer":   lambda text, rng: _mock_style_transfer(text, rng, to_formal=rng.random() < 0.5),
}

SUPPORTED_STRATEGIES = list(STRATEGY_REGISTRY.keys())


# ── 결과 타입 ─────────────────────────────────────────────────────────
@dataclass
class AugmentedRecord:
    """합성 생성된 단일 레코드."""
    id:           str
    text:         str
    source_id:    str          # 원본 레코드 ID
    strategy:     str          # 사용된 전략
    synthetic:    bool = True  # ADR-008: 합성 데이터 표시
    quality_score: float = 0.7  # 합성 데이터 기본 품질
    tier:         str = "B"    # 합성 데이터는 B 티어
    metadata:     Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "text": self.text, "source_id": self.source_id,
            "strategy": self.strategy, "synthetic": self.synthetic,
            "quality_score": self.quality_score, "tier": self.tier,
            **self.metadata,
        }


@dataclass
class AugmentResultSP3:
    """SP3 증강 결과."""
    original:    List[Dict[str, Any]]    # 원본 레코드
    augmented:   List[AugmentedRecord]   # 합성 레코드
    strategy_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def total_count(self) -> int:
        return len(self.original) + len(self.augmented)

    @property
    def success_rate(self) -> float:
        if not self.original:
            return 0.0
        return len(self.augmented) / max(len(self.original), 1)

    def all_records(self) -> List[Dict[str, Any]]:
        """원본 + 합성 전체 dict 리스트."""
        result = list(self.original)
        result.extend(r.to_dict() for r in self.augmented)
        return result

    def summary(self) -> str:
        cats = ", ".join(f"{k}:{v}" for k, v in self.strategy_counts.items())
        return (f"AugmentResultSP3: 원본={len(self.original)} 합성={len(self.augmented)} "
                f"총={self.total_count} | 전략별: [{cats}]")


# ── 핵심 클래스 ───────────────────────────────────────────────────────
class SyntheticAugmentorSP3:
    """
    SP3 SLM 수출용 합성 데이터 증강기.

    기존 SyntheticAugmentor 대비 추가사항:
      - target_count 파라미터 (목표 레코드 수)
      - 명시적 3종 전략 (paraphrase / back_translation / style_transfer)
      - ADR-008 synthetic=True 플래그 의무 부착
      - 실 LLM 어댑터 주입 지원 (선택)
    """

    DEFAULT_STRATEGY = "paraphrase"
    DEFAULT_QUALITY  = 0.7

    def __init__(
        self,
        strategies: Optional[List[str]] = None,
        quality_score: float = DEFAULT_QUALITY,
        seed: int = 42,
        llm_adapter: Optional[Any] = None,   # 실 LLM 어댑터 (선택)
    ) -> None:
        if strategies is None:
            self._strategies = SUPPORTED_STRATEGIES
        else:
            unknown = set(strategies) - set(STRATEGY_REGISTRY)
            if unknown:
                raise ValueError(f"지원하지 않는 전략: {unknown}")
            self._strategies = strategies
        self._quality  = quality_score
        self._rng      = random.Random(seed)
        self._llm      = llm_adapter      # 주입된 어댑터 (None이면 Mock 사용)

    @property
    def supported_strategies(self) -> List[str]:
        return SUPPORTED_STRATEGIES

    def _apply_strategy(self, text: str, strategy: str) -> str:
        """전략 적용 — 실 LLM 또는 Mock."""
        if self._llm is not None:
            # 실 LLM 어댑터 주입 시 호출 (인터페이스: llm.call(prompt) → str)
            prompt = f"[{strategy}] 다음 텍스트를 변형하라:\n{text}"
            try:
                resp = self._llm.call(prompt)
                return getattr(resp, "text", str(resp))
            except Exception:
                pass  # 실패 시 Mock으로 폴백
        fn = STRATEGY_REGISTRY[strategy]
        return fn(text, self._rng)

    def augment(
        self,
        records: List[Dict[str, Any]],
        strategy: Optional[str] = None,
        target_count: Optional[int] = None,
    ) -> AugmentResultSP3:
        """
        records를 증강하여 AugmentResultSP3 반환.

        Args:
            records:      원본 dict 레코드 리스트
            strategy:     단일 전략 지정 (None이면 라운드로빈)
            target_count: 목표 총 레코드 수 (None이면 원본 × 전략 수)
        """
        if not records:
            return AugmentResultSP3(original=[], augmented=[], strategy_counts={})

        strategies = [strategy] if strategy else self._strategies
        augmented: List[AugmentedRecord] = []
        strategy_counts: Dict[str, int] = {s: 0 for s in strategies}

        # target_count가 있으면 순환 생성, 없으면 각 전략 1회씩 적용
        if target_count is not None:
            needed = max(0, target_count - len(records))
            pool = list(records)
            strat_cycle = strategies * (needed // len(strategies) + 1)
            for i in range(needed):
                src = pool[i % len(pool)]
                strat = strat_cycle[i % len(strat_cycle)]
                new_text = self._apply_strategy(str(src.get("text", "")), strat)
                aug = AugmentedRecord(
                    id=f"aug_{uuid.uuid4().hex[:8]}",
                    text=new_text,
                    source_id=str(src.get("id", "")),
                    strategy=strat,
                    quality_score=self._quality,
                )
                augmented.append(aug)
                strategy_counts[strat] = strategy_counts.get(strat, 0) + 1
        else:
            for rec in records:
                for strat in strategies:
                    new_text = self._apply_strategy(str(rec.get("text", "")), strat)
                    aug = AugmentedRecord(
                        id=f"aug_{uuid.uuid4().hex[:8]}",
                        text=new_text,
                        source_id=str(rec.get("id", "")),
                        strategy=strat,
                        quality_score=self._quality,
                    )
                    augmented.append(aug)
                    strategy_counts[strat] = strategy_counts.get(strat, 0) + 1

        return AugmentResultSP3(
            original=records,
            augmented=augmented,
            strategy_counts=strategy_counts,
        )

    def select_candidates(
        self,
        records: List[Dict[str, Any]],
        min_quality: float = 0.6,
        max_count: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """품질 임계값 이상인 레코드를 증강 후보로 선택."""
        candidates = [r for r in records if float(r.get("quality_score", 1.0)) >= min_quality]
        if max_count is not None:
            candidates = candidates[:max_count]
        return candidates
