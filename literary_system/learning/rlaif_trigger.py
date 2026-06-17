"""
learning/rlaif_trigger.py — RLAIF GPU 학습 트리거 (V765, ADR-225)

RLAIFTrainingSpec(DPO 데이터셋 준비됨) → finetune.LoRAJobRunner 제출.
이 로컬(GPU 없음·torch 미설치) = **dry_run 전용**(비용 추정만).
실 GPU LoRA 학습 = 클라우드(RunPod 주력 / Lambda H100 폴백)·GPU SLO(월 hard $120)·biweekly_train.yml. LLM-0(외부 LLM 미호출).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

from literary_system.learning.rlaif_orchestrator import RLAIFTrainingSpec


@dataclass(frozen=True)
class TriggerResult:
    status: str            # "dry_run" | "submitted" | "blocked_slo" | "not_ready"
    job: Dict[str, Any]
    note: str

    @property
    def summary(self) -> str:
        cost = self.job.get("cost_usd") or self.job.get("estimated_cost_usd")
        return f"RLAIF-Trigger[{self.status}] job={self.job.get('job_id', '-')} 비용≈${cost} | {self.note}"


class RLAIFTrigger:
    """RLAIFTrainingSpec → LoRAJobRunner. 이 환경=dry_run, 실 GPU=클라우드(Phase F)."""
    def __init__(self, provider=None, dry_run: bool = True, hours_estimate: float = 2.0, adapter=None) -> None:
        from literary_system.finetune.gpu_adapter import GPUProvider
        from literary_system.finetune.lora_job_runner import LoRAJobRunner
        self._provider = provider or GPUProvider.RUNPOD
        self._dry_run = dry_run
        self._hours = hours_estimate
        self._runner = LoRAJobRunner(provider=self._provider, dry_run=dry_run, adapter=adapter)

    def _config(self, spec: RLAIFTrainingSpec):
        from literary_system.finetune.lora_training_config import (
            LoRATrainingConfig, DEFAULT_TARGET_MODULES,
        )
        return LoRATrainingConfig(base_model=spec.base_model, lora_rank=spec.lora_rank,
                                  target_modules=list(DEFAULT_TARGET_MODULES),
                                  extra={"objective": spec.objective, "rlaif": True})

    def trigger(self, spec: RLAIFTrainingSpec) -> TriggerResult:
        if spec.status != "prepared":
            return TriggerResult("not_ready", {}, f"스펙 미준비({spec.status}) — 선호쌍 확대 필요")
        try:
            rec = self._runner.run(self._config(spec), spec.dpo_dataset_path, self._hours)
        except Exception as exc:                     # SLO BLOCK 등
            return TriggerResult("blocked_slo", {}, f"GPU SLO/실행 차단: {str(exc)[:120]}")
        job = rec.to_dict() if hasattr(rec, "to_dict") else dict(rec.__dict__)
        status = "dry_run" if self._dry_run else "submitted"
        return TriggerResult(status, job,
                             f"provider={self._provider.value} dry_run={self._dry_run}. "
                             f"실 GPU 학습=클라우드(RunPod/Lambda)·GPU SLO·biweekly_train. "
                             f"baseline 승률 {spec.baseline_win_rate}↑ 목표.")
