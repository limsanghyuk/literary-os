"""
V590 SP-A.3 — GPUAdapterContract + CostSLO + GPUCostLedger 단위 테스트

TC01~TC25 (목표: 20+ PASS)

그룹:
  TestGPUJobRequest    (TC01~TC04)  — 요청 유효성
  TestCostSLO          (TC05~TC08)  — SLO 경계 평가
  TestRunPodAdapter    (TC09~TC12)  — RunPod 어댑터
  TestLambdaLabsAdapter(TC13~TC16)  — Lambda Labs 어댑터
  TestHFAutoTrainAdapter(TC17~TC19) — HF AutoTrain 어댑터
  TestGPUCostLedger    (TC20~TC23)  — 비용 원장
  TestFactory          (TC24~TC25)  — Factory / list_providers
"""
from __future__ import annotations

import pytest

from literary_system.finetune.gpu_adapter import (
    CostSLO,
    DEFAULT_COST_SLO,
    GPUAdapterContract,
    GPUJobRequest,
    GPUJobResult,
    GPUProvider,
    HFAutoTrainAdapter,
    GPUJobStatus,
    LambdaLabsAdapter,
    RunPodAdapter,
    get_adapter,
    list_providers,
)
from literary_system.llm_bridge.cost_ledger import GPUCostLedger, GPUCostRecord


# ─────────────────────────────────────────────────────────────────────────────
# 픽스처
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def basic_request() -> GPUJobRequest:
    return GPUJobRequest(
        model_name     = "llama3-8b",
        dataset_path   = "/data/kdrama_scenes",
        hours_estimate = 2.0,
        dry_run        = True,
    )


@pytest.fixture
def runpod() -> RunPodAdapter:
    return RunPodAdapter()


@pytest.fixture
def lambda_labs() -> LambdaLabsAdapter:
    return LambdaLabsAdapter()


@pytest.fixture
def hf_autotrain() -> HFAutoTrainAdapter:
    return HFAutoTrainAdapter()


# ─────────────────────────────────────────────────────────────────────────────
# TC01~TC04 — GPUJobRequest 유효성
# ─────────────────────────────────────────────────────────────────────────────

class TestGPUJobRequest:
    def test_tc01_basic_creation(self):
        """TC01: 기본 요청 생성 성공."""
        req = GPUJobRequest(
            model_name="llama3", dataset_path="/data", hours_estimate=1.0
        )
        assert req.model_name == "llama3"
        assert req.hours_estimate == 1.0
        assert req.dry_run is True  # 기본값

    def test_tc02_job_id_auto_generated(self):
        """TC02: job_id 자동 생성."""
        req1 = GPUJobRequest(model_name="m", dataset_path="/d", hours_estimate=1.0)
        req2 = GPUJobRequest(model_name="m", dataset_path="/d", hours_estimate=1.0)
        assert req1.job_id != req2.job_id
        assert len(req1.job_id) == 8  # uuid[:8]

    def test_tc03_custom_job_id(self):
        """TC03: job_id 직접 지정."""
        req = GPUJobRequest(model_name="m", dataset_path="/d", hours_estimate=1.0, job_id="custom-id")
        assert req.job_id == "custom-id"

    def test_tc04_invalid_hours_raises(self):
        """TC04: hours_estimate <= 0 이면 ValueError."""
        with pytest.raises(ValueError, match="hours_estimate"):
            GPUJobRequest(model_name="m", dataset_path="/d", hours_estimate=0.0)


# ─────────────────────────────────────────────────────────────────────────────
# TC05~TC08 — CostSLO 경계 평가
# ─────────────────────────────────────────────────────────────────────────────

class TestCostSLO:
    def test_tc05_default_values(self):
        """TC05: DEFAULT_COST_SLO 기본값 검증."""
        slo = DEFAULT_COST_SLO
        assert slo.soft      == 90.0
        assert slo.hard      == 120.0
        assert slo.emergency == 150.0

    def test_tc06_assess_ok(self):
        """TC06: $89 → OK."""
        assert DEFAULT_COST_SLO.assess(89.0) == "OK"

    def test_tc07_assess_warn_block_halt(self):
        """TC07: 각 임계값 경계 평가."""
        slo = CostSLO(soft=90.0, hard=120.0, emergency=150.0)
        assert slo.assess(90.0)  == "WARN"
        assert slo.assess(100.0) == "WARN"
        assert slo.assess(120.0) == "BLOCK"
        assert slo.assess(130.0) == "BLOCK"
        assert slo.assess(150.0) == "HALT"
        assert slo.assess(200.0) == "HALT"

    def test_tc08_to_dict(self):
        """TC08: CostSLO.to_dict() 포함 키 검증."""
        d = DEFAULT_COST_SLO.to_dict()
        assert "soft_usd" in d
        assert "hard_usd" in d
        assert "emergency_usd" in d


# ─────────────────────────────────────────────────────────────────────────────
# TC09~TC12 — RunPodAdapter
# ─────────────────────────────────────────────────────────────────────────────

class TestRunPodAdapter:
    def test_tc09_provider_id(self, runpod):
        """TC09: provider_id == RUNPOD."""
        assert runpod.provider_id == GPUProvider.RUNPOD

    def test_tc10_cost_per_hour(self, runpod):
        """TC10: cost_per_hour == $0.39."""
        assert runpod.cost_per_hour == 0.39

    def test_tc11_dry_run_returns_correct_result(self, runpod, basic_request):
        """TC11: dry_run() → GPUJobResult(status=DRY_RUN, dry_run=True, cost>=0)."""
        result = runpod.dry_run(basic_request)
        assert isinstance(result, GPUJobResult)
        assert result.status   == GPUJobStatus.DRY_RUN
        assert result.dry_run  is True
        assert result.cost_usd == pytest.approx(2.0 * 0.39, abs=0.0001)

    def test_tc12_launch_job_dry_run_flag(self, runpod, basic_request):
        """TC12: launch_job(dry_run=True) → DRY_RUN (api_key 없음)."""
        result = runpod.launch_job(basic_request)
        assert result.status == GPUJobStatus.DRY_RUN


# ─────────────────────────────────────────────────────────────────────────────
# TC13~TC16 — LambdaLabsAdapter
# ─────────────────────────────────────────────────────────────────────────────

class TestLambdaLabsAdapter:
    def test_tc13_provider_id(self, lambda_labs):
        """TC13: provider_id == LAMBDA_LABS."""
        assert lambda_labs.provider_id == GPUProvider.LAMBDA_LABS

    def test_tc14_cost_per_hour(self, lambda_labs):
        """TC14: cost_per_hour == $1.49."""
        assert lambda_labs.cost_per_hour == 1.49

    def test_tc15_dry_run_cost(self, lambda_labs, basic_request):
        """TC15: 2h × $1.49 = $2.98 추정."""
        result = lambda_labs.dry_run(basic_request)
        assert result.cost_usd == pytest.approx(2.0 * 1.49, abs=0.0001)

    def test_tc16_is_abc_subclass(self, lambda_labs):
        """TC16: GPUAdapterContract 서브클래스 확인."""
        assert isinstance(lambda_labs, GPUAdapterContract)


# ─────────────────────────────────────────────────────────────────────────────
# TC17~TC19 — HFAutoTrainAdapter
# ─────────────────────────────────────────────────────────────────────────────

class TestHFAutoTrainAdapter:
    def test_tc17_provider_id(self, hf_autotrain):
        """TC17: provider_id == HF_AUTOTRAIN."""
        assert hf_autotrain.provider_id == GPUProvider.HF_AUTOTRAIN

    def test_tc18_cost_per_hour(self, hf_autotrain):
        """TC18: cost_per_hour == $4.00."""
        assert hf_autotrain.cost_per_hour == 4.00

    def test_tc19_dry_run_metadata(self, hf_autotrain, basic_request):
        """TC19: dry_run() 메타데이터에 space_name 포함."""
        result = hf_autotrain.dry_run(basic_request)
        assert "space_name" in result.metadata


# ─────────────────────────────────────────────────────────────────────────────
# TC20~TC23 — GPUCostLedger
# ─────────────────────────────────────────────────────────────────────────────

class TestGPUCostLedger:
    def test_tc20_gpu_track_basic(self):
        """TC20: gpu_track() 기본 호출."""
        ledger = GPUCostLedger()
        result = ledger.gpu_track(provider="runpod", hours=1.0, cost_per_hour=0.39)
        assert result["cost_usd"]      == pytest.approx(0.39, abs=0.0001)
        assert result["monthly_total"] == pytest.approx(0.39, abs=0.0001)
        assert result["slo_status"]    == "OK"

    def test_tc21_monthly_total_accumulates(self):
        """TC21: 여러 작업 누적 합계."""
        ledger = GPUCostLedger()
        ledger.gpu_track(provider="runpod",      hours=10.0, cost_per_hour=0.39)  # $3.90
        ledger.gpu_track(provider="lambda_labs", hours=5.0,  cost_per_hour=1.49)  # $7.45
        total = ledger.monthly_total_gpu()
        assert total == pytest.approx(3.90 + 7.45, abs=0.001)

    def test_tc22_slo_warn_at_90(self):
        """TC22: $90 이상 → SLO WARN."""
        ledger = GPUCostLedger()
        ledger.gpu_track(provider="runpod", hours=100.0, cost_per_hour=0.90)  # $90
        result = ledger.gpu_track(provider="runpod", hours=0.1, cost_per_hour=0.01)
        assert result["slo_status"] == "WARN"

    def test_tc23_to_dict_structure(self):
        """TC23: to_dict() 구조 검증."""
        ledger = GPUCostLedger()
        ledger.gpu_track(provider="hf", hours=1.0, cost_per_hour=4.0)
        d = ledger.to_dict()
        assert "month_key"     in d
        assert "monthly_total" in d
        assert "slo_status"    in d
        assert "record_count"  in d
        assert "records"       in d
        assert d["record_count"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# TC24~TC25 — Factory
# ─────────────────────────────────────────────────────────────────────────────

class TestFactory:
    def test_tc24_get_adapter_all_providers(self):
        """TC24: get_adapter() 3종 프로바이더 모두 성공."""
        for provider in [GPUProvider.RUNPOD, GPUProvider.LAMBDA_LABS, GPUProvider.HF_AUTOTRAIN]:
            adapter = get_adapter(provider)
            assert isinstance(adapter, GPUAdapterContract)
            assert adapter.provider_id == provider

    def test_tc25_list_providers(self):
        """TC25: list_providers() — 4개 항목 반환(V767 LocalGPUAdapter 포함)."""
        providers = list_providers()
        assert len(providers) == 4
        provider_names = {p["provider"] for p in providers}
        assert "runpod"       in provider_names
        assert "lambda_labs"  in provider_names
        assert "hf_autotrain" in provider_names
        assert "local"        in provider_names
