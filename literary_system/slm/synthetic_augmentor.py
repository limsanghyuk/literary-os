"""
V446: SyntheticAugmentor
DRSE 점수 기반 고품질 씬 선별 후 LLM 자기-비평 방식으로 증강.

원칙:
  - DRSE L_total <= threshold인 씬만 증강 대상
  - LLM 직접 호출 없음 — MockAugmentor 또는 주입된 augment_fn 사용
  - 증강 결과는 TraceRecord를 새로 생성해 별도 관리 (원본 불변)
  - 증강 이력(AugmentLog)은 append-only

LLM 0회 (augment_fn 주입으로 실 LLM 연결 가능, 기본은 mock).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Dataclasses

@dataclass(frozen=True)
class AugmentLog:
    """단일 증강 작업 기록 (불변)."""
    aug_id:          str
    source_trace_id: str
    strategy:        str
    quality_before:  float
    quality_after:   float
    success:         bool
    timestamp:       str
    notes:           str = ""

    def to_dict(self) -> dict:
        return {
            "aug_id":          self.aug_id,
            "source_trace_id": self.source_trace_id,
            "strategy":        self.strategy,
            "quality_before":  self.quality_before,
            "quality_after":   self.quality_after,
            "success":         self.success,
            "timestamp":       self.timestamp,
            "notes":           self.notes,
        }


@dataclass
class AugmentResult:
    """SyntheticAugmentor.augment() 반환값."""
    augmented_records: list
    logs:              list
    source_count:      int
    augmented_count:   int
    failed_count:      int
    threshold:         float
    strategy:          str

    @property
    def success_rate(self) -> float:
        total = self.augmented_count + self.failed_count
        return round(self.augmented_count / max(total, 1), 4)

    def summary(self) -> dict:
        return {
            "source_count":    self.source_count,
            "augmented_count": self.augmented_count,
            "failed_count":    self.failed_count,
            "success_rate":    self.success_rate,
            "strategy":        self.strategy,
            "threshold":       self.threshold,
        }


# Mock strategies

def _mock_self_critique(text: str) -> str:
    replacements = [
        ("슬펐다", "손이 떨렸다"),
        ("기뻤다", "입꼬리가 올라갔다"),
        ("화가 났다", "주먹을 쥐었다"),
        ("두려웠다", "발이 굳었다"),
        ("외로웠다", "창문을 바라보았다"),
    ]
    result = text
    for src, tgt in replacements:
        result = result.replace(src, tgt)
    return result + " [증강됨]"


def _mock_paraphrase(text: str) -> str:
    return text.replace("그는", "남자는").replace("그녀는", "여자는") + " [패러프레이즈]"


def _mock_style_transfer(text: str) -> str:
    return "【" + text + "】"


_MOCK_STRATEGIES: dict = {
    "self_critique":  _mock_self_critique,
    "paraphrase":     _mock_paraphrase,
    "style_transfer": _mock_style_transfer,
}


# SyntheticAugmentor

class SyntheticAugmentor:
    """
    DRSE 기반 고품질 씬 선별 + 자기-비평 증강기.

    전략:
      - "self_critique"  : 감정 직설 -> 행동/오브제 변환 (기본)
      - "paraphrase"     : 표현 다양화
      - "style_transfer" : 스타일 전환
    """

    DEFAULT_THRESHOLD    = 0.12
    DEFAULT_STRATEGY     = "self_critique"
    SUPPORTED_STRATEGIES = {"self_critique", "paraphrase", "style_transfer"}

    def __init__(
        self,
        threshold:      float = DEFAULT_THRESHOLD,
        strategy:       str   = DEFAULT_STRATEGY,
        augment_fn:     Callable = None,
        max_per_record: int   = 1,
    ):
        if strategy not in self.SUPPORTED_STRATEGIES:
            raise ValueError(
                f"지원하지 않는 전략: {strategy}. "
                f"지원 목록: {sorted(self.SUPPORTED_STRATEGIES)}"
            )
        self.threshold      = threshold
        self.strategy       = strategy
        # augment_fn이 명시적으로 주입되면 우선 사용, 없으면 strategy 기본 mock 사용
        self.augment_fn     = augment_fn if augment_fn is not None else _MOCK_STRATEGIES[strategy]
        self.max_per_record = max_per_record
        self._logs: list    = []

    def select_candidates(self, records: list) -> list:
        """L_total <= threshold인 레코드만 선별."""
        return [
            r for r in records
            if r.loss_report.get("L_total", 1.0) <= self.threshold
        ]

    def augment(self, records: list, strategy: str = None) -> AugmentResult:
        """
        레코드 목록을 받아 증강된 TraceRecord 목록을 반환.
        원본 레코드는 불변으로 유지.
        """
        from literary_system.trace.trace_dataset_store import PromotionTier
        import dataclasses

        strat = strategy or self.strategy
        # 명시적 strategy 오버라이드가 있으면 해당 mock 사용,
        # 없으면 생성자에서 설정된 augment_fn 우선 (커스텀 fn 주입 지원)
        if strategy and strategy in _MOCK_STRATEGIES:
            fn = _MOCK_STRATEGIES[strategy]
        else:
            fn = self.augment_fn

        candidates     = self.select_candidates(records)
        augmented_out: list = []
        logs:          list = []
        failed         = 0

        for rec in candidates:
            for _ in range(self.max_per_record):
                aug_id = str(uuid.uuid4())
                try:
                    new_output: dict = {}
                    for k, v in rec.render_output.items():
                        new_output[k] = fn(v)

                    aug_rec = dataclasses.replace(
                        rec,
                        trace_id=f"aug_{aug_id[:8]}",
                        render_output=new_output,
                        promotion=PromotionTier.CANDIDATE,
                        promotion_reason=f"synthetic_aug:{strat}",
                        loss_report={
                            **rec.loss_report,
                            "L_total": max(0.0, rec.loss_report.get("L_total", 0) - 0.01),
                        },
                    )
                    augmented_out.append(aug_rec)

                    log = AugmentLog(
                        aug_id=aug_id,
                        source_trace_id=rec.trace_id,
                        strategy=strat,
                        quality_before=rec.loss_report.get("L_total", 1.0),
                        quality_after=aug_rec.loss_report.get("L_total", 1.0),
                        success=True,
                        timestamp=_now_iso(),
                    )
                    logs.append(log)
                    self._logs.append(log)

                except Exception as e:
                    failed += 1
                    log = AugmentLog(
                        aug_id=aug_id,
                        source_trace_id=rec.trace_id,
                        strategy=strat,
                        quality_before=rec.loss_report.get("L_total", 1.0),
                        quality_after=1.0,
                        success=False,
                        timestamp=_now_iso(),
                        notes=str(e),
                    )
                    logs.append(log)
                    self._logs.append(log)

        return AugmentResult(
            augmented_records=augmented_out,
            logs=logs,
            source_count=len(candidates),
            augmented_count=len(augmented_out),
            failed_count=failed,
            threshold=self.threshold,
            strategy=strat,
        )

    def all_logs(self) -> list:
        """누적 증강 로그 (불변 복사본)."""
        return list(self._logs)

    def stats(self) -> dict:
        logs = self._logs
        succeeded = [l for l in logs if l.success]
        return {
            "total_augmented": len(succeeded),
            "total_failed":    sum(1 for l in logs if not l.success),
            "strategies_used": list({l.strategy for l in logs}),
            "avg_quality_improvement": round(
                sum(l.quality_before - l.quality_after for l in succeeded)
                / max(len(succeeded), 1),
                4,
            ),
        }
