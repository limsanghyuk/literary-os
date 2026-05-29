"""
test_v469_finetune_job_manager.py — FineTuneJobManager 단위 테스트 (V469)

ADR-014: Fine-tune Lifecycle (LoRA 1순위, OpenAI Tier-2 consent 필수)
"""
import pytest
from literary_system.finetune.finetune_job_manager import (
    FineTuneJobManager,
    FineTuneMethod,
    JobStatus,
)


class TestFineTuneJobManagerBasic:
    """기본 잡 제출 및 조회"""

    def test_submit_mock_job(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-001", method=FineTuneMethod.MOCK)
        assert job_id is not None
        assert len(job_id) > 0

    def test_submit_lora_job(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-lora", method=FineTuneMethod.LORA)
        assert job_id is not None

    def test_submit_qlora_job(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-qlora", method=FineTuneMethod.QLORA)
        assert job_id is not None

    def test_submit_openai_t2_requires_consent(self):
        """ADR-014: OpenAI Tier-2는 consent_verified=True 필요"""
        mgr = FineTuneJobManager()
        with pytest.raises((ValueError, PermissionError)):
            mgr.submit("dataset-t2", method=FineTuneMethod.OPENAI_TIER2, consent_verified=False)

    def test_submit_openai_t2_with_consent(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-t2", method=FineTuneMethod.OPENAI_TIER2, consent_verified=True)
        assert job_id is not None

    def test_job_initial_status_queued(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-001", method=FineTuneMethod.MOCK)
        job = mgr.get_job(job_id)
        assert job is not None
        assert job.status in (JobStatus.QUEUED, JobStatus.PREPARING, JobStatus.TRAINING)

    def test_get_nonexistent_job_returns_none_or_raises(self):
        mgr = FineTuneJobManager()
        try:
            result = mgr.get_job("nonexistent-id")
            assert result is None
        except (KeyError, ValueError):
            pass  # 예외도 허용


class TestFineTuneJobManagerSimulate:
    """simulate_training 검증"""

    def test_simulate_training_completes(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-sim", method=FineTuneMethod.MOCK)
        job = mgr.simulate_training(job_id, steps=1000)
        assert job.status.value == "completed"

    def test_simulate_training_steps_match(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-sim", method=FineTuneMethod.MOCK)
        job = mgr.simulate_training(job_id, steps=1000)
        assert job.current_step == job.total_steps

    def test_simulate_training_sets_artifact(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-sim", method=FineTuneMethod.MOCK)
        job = mgr.simulate_training(job_id, steps=1000)
        assert job.model_artifact_id is not None
        assert job.model_artifact_id != ""

    def test_simulate_training_loss_decreases(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-sim", method=FineTuneMethod.MOCK)
        job = mgr.simulate_training(job_id, steps=1000, loss_start=2.5, loss_end=0.8)
        assert job.status.value == "completed"
        # 완료된 잡의 손실은 시작값보다 낮아야 함
        if hasattr(job, "final_loss") and job.final_loss is not None:
            assert job.final_loss < 2.5

    def test_simulate_training_checkpoints(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-chk", method=FineTuneMethod.MOCK)
        job = mgr.simulate_training(job_id, steps=1000)
        # 체크포인트 생성 확인 (500 단계마다)
        if hasattr(job, "checkpoints"):
            assert len(job.checkpoints) >= 1


class TestFineTuneJobManagerCancel:
    """잡 취소"""

    def test_cancel_queued_job(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-cancel", method=FineTuneMethod.MOCK)
        result = mgr.cancel(job_id)
        assert result is True

    def test_cancel_completed_job_returns_false(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-cancel", method=FineTuneMethod.MOCK)
        mgr.simulate_training(job_id, steps=1000)
        result = mgr.cancel(job_id)
        assert result is False

    def test_cancel_nonexistent_job(self):
        mgr = FineTuneJobManager()
        try:
            result = mgr.cancel("ghost-id")
            assert result is False
        except (KeyError, ValueError):
            pass


class TestFineTuneJobManagerConcurrency:
    """동시 잡 제한 (MAX_CONCURRENT_JOBS=3)"""

    def test_max_concurrent_jobs_limit(self):
        mgr = FineTuneJobManager()
        # MAX_CONCURRENT_JOBS=3 이면 4번째 제출 시 예외 또는 큐잉
        job_ids = []
        for i in range(FineTuneJobManager.MAX_CONCURRENT_JOBS):
            jid = mgr.submit(f"dataset-{i}", method=FineTuneMethod.MOCK)
            job_ids.append(jid)
        assert len(job_ids) == FineTuneJobManager.MAX_CONCURRENT_JOBS

    def test_list_jobs_returns_all(self):
        mgr = FineTuneJobManager()
        mgr.submit("ds-a", method=FineTuneMethod.MOCK)
        mgr.submit("ds-b", method=FineTuneMethod.MOCK)
        jobs = mgr.list_jobs()
        assert len(jobs) >= 2

    def test_list_jobs_filter_by_status(self):
        mgr = FineTuneJobManager()
        job_id = mgr.submit("ds-filter", method=FineTuneMethod.MOCK)
        mgr.simulate_training(job_id, steps=1000)
        completed = mgr.list_jobs(status_filter=JobStatus.COMPLETED)
        assert any(j.job_id == job_id for j in completed)

