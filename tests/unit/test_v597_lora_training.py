"""
V597 — LoRA Training Config + Job Runner 단위 테스트 (9 TC)

TC-A1~A3: LoRATrainingConfig 하이퍼파라미터 검증
TC-B1~B4: LoRAJobRunner GPUAdapter 연동 + SLO 집행
TC-C1~C2: BiweeklyScheduler 격주/주간 due 판단
"""
from __future__ import annotations

import json
import time
import tempfile
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pytest

from literary_system.finetune.lora_training_config import (
    DEFAULT_BASE_MODEL,
    DEFAULT_LORA_RANK,
    DEFAULT_TARGET_MODULES,
    MONTHLY_SLO_USD,
    LoRAQuantizationType,
    LoRAScheduleType,
    LoRATrainingConfig,
)
from literary_system.finetune.lora_job_runner import (
    BIWEEKLY_INTERVAL_DAYS,
    WEEKLY_INTERVAL_DAYS,
    BiweeklyScheduler,
    JobRunRecord,
    LoRAJobRunner,
)
from literary_system.finetune.gpu_adapter import (
    CostSLO,
    GPUJobStatus,
    GPUProvider,
)


class TestLoRATrainingConfig:
    """TC-A1~A3: 하이퍼파라미터 설정 검증."""

    def test_a1_default_config(self):
        """TC-A1: 기본 설정값이 본안 B-M-05와 일치해야 한다."""
        cfg = LoRATrainingConfig()
        assert cfg.base_model == DEFAULT_BASE_MODEL
        assert cfg.lora_rank == 16
        assert cfg.lora_alpha == 32
        assert cfg.lora_dropout == 0.05
        assert set(cfg.target_modules) == set(DEFAULT_TARGET_MODULES)
        assert cfg.bf16 is True
        assert cfg.seed == 42
        assert cfg.effective_batch_size == 16
        assert cfg.scaling_factor == 2.0

    def test_a2_validation_errors(self):
        """TC-A2: 잘못된 하이퍼파라미터는 ValueError를 발생시켜야 한다."""
        with pytest.raises(ValueError, match="lora_rank"):
            LoRATrainingConfig(lora_rank=0)
        with pytest.raises(ValueError, match="lora_dropout"):
            LoRATrainingConfig(lora_dropout=1.0)
        with pytest.raises(ValueError, match="target_modules"):
            LoRATrainingConfig(target_modules=[])
        with pytest.raises(ValueError, match="learning_rate"):
            LoRATrainingConfig(learning_rate=-0.001)

    def test_a3_roundtrip_serialization(self):
        """TC-A3: to_dict() -> from_dict() 라운드트립이 무손실이어야 한다."""
        cfg = LoRATrainingConfig(
            lora_rank=8,
            lora_alpha=16,
            num_epochs=5,
            quantization=LoRAQuantizationType.INT8,
            schedule_type=LoRAScheduleType.FINE_WEEKLY,
        )
        d = cfg.to_dict()
        restored = LoRATrainingConfig.from_dict(d)
        assert restored.lora_rank == 8
        assert restored.lora_alpha == 16
        assert restored.num_epochs == 5
        assert restored.quantization == LoRAQuantizationType.INT8
        assert restored.schedule_type == LoRAScheduleType.FINE_WEEKLY
        assert restored.effective_batch_size == cfg.effective_batch_size
        assert restored.scaling_factor == cfg.scaling_factor


class TestLoRAJobRunner:
    """TC-B1~B4: GPUAdapter 연동 + SLO 집행."""

    def test_b1_dry_run_success(self):
        """TC-B1: dry_run=True에서 실제 GPU 호출 없이 JobRunRecord를 반환해야 한다."""
        cfg = LoRATrainingConfig()
        runner = LoRAJobRunner(provider=GPUProvider.RUNPOD, dry_run=True)
        record = runner.run(cfg, dataset_path="tests/fixtures/dummy_train.jsonl")
        assert record.dry_run is True
        assert record.status == GPUJobStatus.DRY_RUN
        assert record.cost_usd >= 0.0
        assert record.hours > 0.0
        assert record.schedule_type == LoRAScheduleType.FULL_BIWEEKLY
        assert record.run_id

    def test_b2_history_persistence(self, tmp_path):
        """TC-B2: 실행 이력이 JSONL 파일에 올바르게 영속화되어야 한다."""
        history_file = tmp_path / "job_history.jsonl"
        cfg = LoRATrainingConfig()
        runner = LoRAJobRunner(
            provider=GPUProvider.RUNPOD,
            dry_run=True,
            history_path=str(history_file),
        )
        record = runner.run(cfg, dataset_path="data/train.jsonl")
        assert history_file.exists()
        lines = history_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        loaded = json.loads(lines[0])
        assert loaded["run_id"] == record.run_id
        assert loaded["dry_run"] is True

    def test_b3_slo_block(self):
        """TC-B3: 월 누적 비용이 hard SLO 초과 시 RuntimeError가 발생해야 한다."""
        tight_slo = CostSLO(soft=1.0, hard=10.0, emergency=50.0)
        runner = LoRAJobRunner(
            provider=GPUProvider.RUNPOD,
            dry_run=True,
            cost_slo=tight_slo,
        )
        fake_record = JobRunRecord(
            run_id="fake01",
            schedule_type=LoRAScheduleType.FULL_BIWEEKLY,
            provider=GPUProvider.RUNPOD,
            job_id="j-fake",
            status=GPUJobStatus.DRY_RUN,
            cost_usd=10.5,
            hours=2.0,
            artifact_path="",
            dataset_path="data/train.jsonl",
            config_snapshot={},
            started_at=datetime.now(timezone.utc).isoformat(),
            finished_at=datetime.now(timezone.utc).isoformat(),
            dry_run=True,
        )
        runner._history.append(fake_record)
        cfg = LoRATrainingConfig()
        with pytest.raises(RuntimeError, match="BLOCK"):
            runner.run(cfg, dataset_path="data/train.jsonl")

    def test_b4_monthly_spend(self):
        """TC-B4: monthly_spend()가 현재 월의 비용만 집계해야 한다."""
        runner = LoRAJobRunner(provider=GPUProvider.RUNPOD, dry_run=True)
        cfg = LoRATrainingConfig()
        runner.run(cfg, dataset_path="data/train.jsonl")
        runner.run(cfg, dataset_path="data/train.jsonl")
        spend = runner.monthly_spend()
        assert spend > 0.0
        assert len(runner.history()) == 2


class TestBiweeklyScheduler:
    """TC-C1~C2: 격주/주간 due 판단."""

    def test_c1_full_training_due(self):
        """TC-C1: 14일 경과 시 풀 학습이 due여야 한다; 13일이면 아직이다."""
        scheduler = BiweeklyScheduler()
        now = time.time()
        assert scheduler.is_full_training_due(None, now) is True
        last_14_days_ago = now - (BIWEEKLY_INTERVAL_DAYS * 86400)
        assert scheduler.is_full_training_due(last_14_days_ago, now) is True
        last_13_days_ago = now - (13 * 86400)
        assert scheduler.is_full_training_due(last_13_days_ago, now) is False

    def test_c2_next_schedule_priority(self):
        """TC-C2: 풀 학습과 미세조정이 동시에 due이면 풀 학습이 우선이어야 한다."""
        scheduler = BiweeklyScheduler()
        now = time.time()
        result = scheduler.next_schedule_type(
            last_full_ts=None,
            last_fine_ts=None,
            now=now,
        )
        assert result == LoRAScheduleType.FULL_BIWEEKLY
        result2 = scheduler.next_schedule_type(
            last_full_ts=now - 86400,
            last_fine_ts=now - 7 * 86400,
            now=now,
        )
        assert result2 == LoRAScheduleType.FINE_WEEKLY
        result3 = scheduler.next_schedule_type(
            last_full_ts=now - 86400,
            last_fine_ts=now - 86400,
            now=now,
        )
        assert result3 is None
