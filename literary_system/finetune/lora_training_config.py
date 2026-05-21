"""
SP-B.1 (V597) — LoRATrainingConfig: LoRA 학습 하이퍼파라미터 + GPU SLO 정책

Phase B 본안 보강 D3 / B-M-05:
- 베이스 모델: Llama-3.1-8B (128K 컨텍스트, rank=16)
- Target modules: q_proj / k_proj / v_proj / o_proj
- 격주 풀 학습($48) + 주간 미세조정($48) → 월 SLO ~$96

ADR-057 참조.

LLM-0 원칙: 이 모듈은 외부 LLM API를 직접 호출하지 않음.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


# ---------------------------------------------------------------------------
# 상수 — 본안 보강 D3 / B-M-04 / B-M-05
# ---------------------------------------------------------------------------

DEFAULT_BASE_MODEL: str = "meta-llama/Llama-3.1-8B"
EXAONE_CANDIDATE_MODEL: str = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct"

DEFAULT_LORA_RANK: int = 16
DEFAULT_LORA_ALPHA: int = 32          # alpha = 2 × rank (통상 관행)
DEFAULT_LORA_DROPOUT: float = 0.05
DEFAULT_TARGET_MODULES: List[str] = ["q_proj", "k_proj", "v_proj", "o_proj"]

DEFAULT_LEARNING_RATE: float = 2e-4
DEFAULT_BATCH_SIZE: int = 4
DEFAULT_GRAD_ACCUM_STEPS: int = 4     # effective batch = 16
DEFAULT_NUM_EPOCHS: int = 3
DEFAULT_MAX_SEQ_LEN: int = 2048
DEFAULT_WARMUP_RATIO: float = 0.03
DEFAULT_WEIGHT_DECAY: float = 0.01
DEFAULT_LR_SCHEDULER: str = "cosine"
DEFAULT_BF16: bool = True             # Llama-3.1 BF16 권장

# 월 GPU SLO — 본안 보강 B-M-06
MONTHLY_FULL_TRAINING_USD: float = 48.0    # 격주 풀 학습
MONTHLY_FINE_TUNING_USD: float = 48.0      # 주간 미세조정
MONTHLY_SLO_USD: float = MONTHLY_FULL_TRAINING_USD + MONTHLY_FINE_TUNING_USD  # $96


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class LoRAScheduleType(str, Enum):
    """학습 스케줄 유형."""
    FULL_BIWEEKLY = "full_biweekly"          # 격주 풀 학습
    FINE_WEEKLY = "fine_weekly"              # 주간 미세조정
    MANUAL = "manual"                        # 수동 트리거


class LoRAQuantizationType(str, Enum):
    """양자화 유형 (선택적)."""
    NONE = "none"
    INT8 = "int8"
    INT4 = "int4"
    NF4 = "nf4"


# ---------------------------------------------------------------------------
# LoRATrainingConfig
# ---------------------------------------------------------------------------

@dataclass
class LoRATrainingConfig:
    """
    LoRA 학습 하이퍼파라미터 설정.

    Attributes:
        base_model:         기반 모델 HuggingFace Hub 경로 또는 로컬 경로
        lora_rank:          LoRA 행렬 분해 rank (default: 16)
        lora_alpha:         LoRA 스케일 팩터 (default: 32)
        lora_dropout:       LoRA dropout 확률 (default: 0.05)
        target_modules:     LoRA 적용 대상 레이어 (default: q/k/v/o_proj)
        learning_rate:      초기 학습률 (default: 2e-4)
        batch_size:         미니배치 크기 (default: 4)
        grad_accum_steps:   그래디언트 누적 스텝 (default: 4 → effective batch 16)
        num_epochs:         에포크 수 (default: 3)
        max_seq_len:        최대 시퀀스 길이 (default: 2048)
        warmup_ratio:       웜업 비율 (default: 0.03)
        weight_decay:       가중치 감쇠 (default: 0.01)
        lr_scheduler:       학습률 스케줄러 유형 (default: cosine)
        bf16:               BF16 혼합 정밀도 활성화 (default: True)
        quantization:       QLoRA 양자화 (default: NONE)
        schedule_type:      학습 스케줄 유형 (default: FULL_BIWEEKLY)
        output_dir:         체크포인트 저장 경로
        seed:               재현성 시드 (default: 42)
        extra:              프로바이더별 추가 파라미터
    """
    base_model: str = DEFAULT_BASE_MODEL
    lora_rank: int = DEFAULT_LORA_RANK
    lora_alpha: int = DEFAULT_LORA_ALPHA
    lora_dropout: float = DEFAULT_LORA_DROPOUT
    target_modules: List[str] = field(default_factory=lambda: list(DEFAULT_TARGET_MODULES))
    learning_rate: float = DEFAULT_LEARNING_RATE
    batch_size: int = DEFAULT_BATCH_SIZE
    grad_accum_steps: int = DEFAULT_GRAD_ACCUM_STEPS
    num_epochs: int = DEFAULT_NUM_EPOCHS
    max_seq_len: int = DEFAULT_MAX_SEQ_LEN
    warmup_ratio: float = DEFAULT_WARMUP_RATIO
    weight_decay: float = DEFAULT_WEIGHT_DECAY
    lr_scheduler: str = DEFAULT_LR_SCHEDULER
    bf16: bool = DEFAULT_BF16
    quantization: LoRAQuantizationType = LoRAQuantizationType.NONE
    schedule_type: LoRAScheduleType = LoRAScheduleType.FULL_BIWEEKLY
    output_dir: str = "outputs/lora"
    seed: int = 42
    extra: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # 검증
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        """하이퍼파라미터 유효성 검사."""
        errors: List[str] = []

        if self.lora_rank <= 0:
            errors.append(f"lora_rank must be > 0, got {self.lora_rank}")
        if self.lora_alpha <= 0:
            errors.append(f"lora_alpha must be > 0, got {self.lora_alpha}")
        if not (0.0 <= self.lora_dropout < 1.0):
            errors.append(f"lora_dropout must be in [0, 1), got {self.lora_dropout}")
        if not self.target_modules:
            errors.append("target_modules must not be empty")
        if self.learning_rate <= 0:
            errors.append(f"learning_rate must be > 0, got {self.learning_rate}")
        if self.batch_size <= 0:
            errors.append(f"batch_size must be > 0, got {self.batch_size}")
        if self.num_epochs <= 0:
            errors.append(f"num_epochs must be > 0, got {self.num_epochs}")
        if self.max_seq_len <= 0:
            errors.append(f"max_seq_len must be > 0, got {self.max_seq_len}")

        if errors:
            raise ValueError(
                f"LoRATrainingConfig validation failed ({len(errors)} error(s)):\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

        # lora_alpha != 2 * lora_rank 이면 경고
        if self.lora_alpha != 2 * self.lora_rank:
            warnings.warn(
                f"lora_alpha={self.lora_alpha} is not 2×lora_rank={self.lora_rank}. "
                "Conventional setting is alpha=2×rank.",
                UserWarning,
                stacklevel=2,
            )

    # ------------------------------------------------------------------
    # 유틸리티
    # ------------------------------------------------------------------

    @property
    def effective_batch_size(self) -> int:
        """실질 배치 크기 (batch_size × grad_accum_steps)."""
        return self.batch_size * self.grad_accum_steps

    @property
    def scaling_factor(self) -> float:
        """LoRA 스케일 팩터 = alpha / rank."""
        return self.lora_alpha / self.lora_rank

    def estimated_cost_usd(self, hours_estimate: float, cost_per_hour: float) -> float:
        """
        예상 학습 비용 계산 (USD).

        Args:
            hours_estimate: 예상 학습 시간
            cost_per_hour:  GPU 프로바이더 시간당 비용

        Returns:
            예상 비용 (USD)
        """
        return round(hours_estimate * cost_per_hour, 4)

    def to_dict(self) -> Dict[str, Any]:
        """직렬화 (JSON 호환)."""
        return {
            "base_model": self.base_model,
            "lora_rank": self.lora_rank,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "target_modules": list(self.target_modules),
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "grad_accum_steps": self.grad_accum_steps,
            "effective_batch_size": self.effective_batch_size,
            "num_epochs": self.num_epochs,
            "max_seq_len": self.max_seq_len,
            "warmup_ratio": self.warmup_ratio,
            "weight_decay": self.weight_decay,
            "lr_scheduler": self.lr_scheduler,
            "bf16": self.bf16,
            "quantization": self.quantization.value,
            "schedule_type": self.schedule_type.value,
            "output_dir": self.output_dir,
            "seed": self.seed,
            "scaling_factor": self.scaling_factor,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LoRATrainingConfig":
        """역직렬화."""
        d = dict(d)
        if "quantization" in d and isinstance(d["quantization"], str):
            d["quantization"] = LoRAQuantizationType(d["quantization"])
        if "schedule_type" in d and isinstance(d["schedule_type"], str):
            d["schedule_type"] = LoRAScheduleType(d["schedule_type"])
        # 직렬화 전용 계산 필드 제거
        d.pop("effective_batch_size", None)
        d.pop("scaling_factor", None)
        return cls(**d)

    @classmethod
    def default_full(cls) -> "LoRATrainingConfig":
        """격주 풀 학습용 기본 설정 (B-M-05)."""
        return cls(
            schedule_type=LoRAScheduleType.FULL_BIWEEKLY,
            num_epochs=3,
        )

    @classmethod
    def default_fine(cls) -> "LoRATrainingConfig":
        """주간 미세조정용 기본 설정 — 에포크 1로 축소."""
        return cls(
            schedule_type=LoRAScheduleType.FINE_WEEKLY,
            num_epochs=1,
            learning_rate=5e-5,      # 미세조정은 낮은 LR
        )

    @classmethod
    def exaone_candidate(cls) -> "LoRATrainingConfig":
        """EXAONE A/B 후보 설정 (B-M-04)."""
        return cls(
            base_model=EXAONE_CANDIDATE_MODEL,
            schedule_type=LoRAScheduleType.MANUAL,
        )
