"""
learning/rlaif_orchestrator.py — E.4 RLAIF 오케스트레이션 브리지 (V764, ADR-224)

loop-C 선호쌍 → DPO 데이터셋 + LoRA 학습 스펙 준비 → finetune.LoRAJobRunner(GPU, Phase F)로 결선.
"선호쌍 → 보상 → 생성기 학습" 사슬을 코드로 닫는다(실 GPU 학습은 개발자 환경·GPU SLO).
LLM-0: 본 모듈은 외부 LLM 미호출(데이터·스펙 준비만).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from literary_system.learning.loop_c import (
    PreferencePair, write_dpo_jsonl, generation_win_rate,
)


@dataclass(frozen=True)
class RLAIFTrainingSpec:
    dpo_dataset_path: str
    n_pairs: int
    baseline_win_rate: float     # 현 loop-C 격차(학습으로 ↑ 목표)
    base_model: str
    lora_rank: int
    objective: str               # "dpo"
    status: str                  # "prepared" | "blocked"
    note: str = ""

    @property
    def summary(self) -> str:
        return (f"RLAIF[{self.status}] obj={self.objective} pairs={self.n_pairs} "
                f"baseline승률={self.baseline_win_rate} base={self.base_model} rank={self.lora_rank}")


class RLAIFOrchestrator:
    """loop-C 선호쌍 → DPO 데이터셋·학습 스펙 준비. 실 GPU 학습은 finetune.LoRAJobRunner(Phase F)."""
    def __init__(self, base_model: Optional[str] = None, lora_rank: Optional[int] = None,
                 min_pairs: int = 8) -> None:
        from literary_system.finetune.lora_training_config import (
            DEFAULT_BASE_MODEL, DEFAULT_LORA_RANK,
        )
        self.base_model = base_model or DEFAULT_BASE_MODEL
        self.lora_rank = lora_rank or DEFAULT_LORA_RANK
        self.min_pairs = min_pairs

    def prepare(self, pairs: List[PreferencePair], out_path: str) -> RLAIFTrainingSpec:
        """DPO 데이터셋 작성 + 학습 스펙 반환(GPU 미실행)."""
        n = len(pairs)
        if n < self.min_pairs:
            return RLAIFTrainingSpec(out_path, n, generation_win_rate(pairs),
                                     self.base_model, self.lora_rank, "dpo", "blocked",
                                     f"선호쌍 {n} < 최소 {self.min_pairs} — 학습 보류(수집 확대 필요)")
        write_dpo_jsonl(pairs, out_path)
        wr = generation_win_rate(pairs)
        return RLAIFTrainingSpec(out_path, n, wr, self.base_model, self.lora_rank, "dpo", "prepared",
                                 f"GPU 학습 finetune.LoRAJobRunner로 실행(GPU SLO 준수). 목표: 승률 {wr}↑")

    def job_request(self, spec: RLAIFTrainingSpec) -> dict:
        """LoRAJobRunner 제출용 요청 사양(실 제출은 개발자 GPU 환경)."""
        return {"objective": spec.objective, "dataset": spec.dpo_dataset_path,
                "base_model": spec.base_model, "lora_rank": spec.lora_rank,
                "n_pairs": spec.n_pairs, "ready": spec.status == "prepared",
                "note": "GPU SLO(월 한도·최소 7일 간격) 준수 — finetune.LoRAJobRunner가 집행"}
