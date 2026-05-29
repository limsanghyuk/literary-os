"""
SP-A.3 (V590) — GPUAdapterContract + 3종 Provider Adapter

GPU fine-tuning 작업을 외부 GPU 클라우드에 위임하는 계약 인터페이스.
LLM-0 원칙: 이 모듈은 외부 LLM API를 직접 호출하지 않음.
실제 GPU API 호출은 dry_run=True 시 전면 Mock 처리.

ADR-051 참조.
"""
from __future__ import annotations

import abc
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GPUProvider(str, Enum):
    """지원하는 GPU 클라우드 프로바이더."""
    RUNPOD       = "runpod"
    LAMBDA_LABS  = "lambda_labs"
    HF_AUTOTRAIN = "hf_autotrain"


class GPUJobStatus(str, Enum):
    """GPU 작업 상태."""
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    DRY_RUN   = "dry_run"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Cost SLO
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CostSLO:
    """
    월간 GPU 비용 SLO 경계 (USD).

    soft:       $90  — 경보 발령 (alert), 계속 허용
    hard:       $120 — 신규 작업 차단 (block_new_jobs)
    emergency:  $150 — 즉시 중단 (halt_all)
    """
    soft:      float = 90.0
    hard:      float = 120.0
    emergency: float = 150.0

    def assess(self, monthly_spend: float) -> str:
        """
        현재 지출 수준 평가.
        Returns: "OK" | "WARN" | "BLOCK" | "HALT"
        """
        if monthly_spend >= self.emergency:
            return "HALT"
        if monthly_spend >= self.hard:
            return "BLOCK"
        if monthly_spend >= self.soft:
            return "WARN"
        return "OK"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "soft_usd":      self.soft,
            "hard_usd":      self.hard,
            "emergency_usd": self.emergency,
        }


# 기본 SLO 인스턴스 (ADR-051 §4)
DEFAULT_COST_SLO = CostSLO(soft=90.0, hard=120.0, emergency=150.0)


# ---------------------------------------------------------------------------
# Request / Result
# ---------------------------------------------------------------------------

@dataclass
class GPUJobRequest:
    """
    GPU fine-tuning 작업 요청.

    Attributes:
        model_name:       기반 모델 식별자 (e.g. "llama3-8b")
        dataset_path:     훈련 데이터셋 경로 또는 HF Hub 경로
        hours_estimate:   예상 학습 소요 시간 (시간 단위)
        job_id:           고유 작업 ID (미지정 시 자동 생성)
        dry_run:          True이면 실제 GPU 기동 없이 비용 추정만 수행
        extra:            프로바이더별 추가 파라미터
    """
    model_name:     str
    dataset_path:   str
    hours_estimate: float
    job_id:         str              = field(default_factory=lambda: str(uuid.uuid4())[:8])
    dry_run:        bool             = True
    extra:          Dict[str, Any]   = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.hours_estimate <= 0:
            raise ValueError(f"hours_estimate must be > 0, got {self.hours_estimate}")


@dataclass
class GPUJobResult:
    """
    GPU fine-tuning 작업 결과.

    Attributes:
        job_id:        요청 job_id
        provider:      실행 프로바이더
        status:        GPUJobStatus
        actual_hours:  실제 사용 시간 (dry_run이면 예상값)
        cost_usd:      발생 비용 USD (dry_run이면 추정값)
        dry_run:       dry_run 여부
        artifact_path: 학습된 모델 저장 경로 (dry_run이면 "")
        error:         오류 메시지 (없으면 "")
        metadata:      부가 정보
    """
    job_id:        str
    provider:      GPUProvider
    status:        GPUJobStatus
    actual_hours:  float
    cost_usd:      float
    dry_run:       bool
    artifact_path: str              = ""
    error:         str              = ""
    metadata:      Dict[str, Any]   = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id":        self.job_id,
            "provider":      self.provider.value,
            "status":        self.status.value,
            "actual_hours":  self.actual_hours,
            "cost_usd":      round(self.cost_usd, 4),
            "dry_run":       self.dry_run,
            "artifact_path": self.artifact_path,
            "error":         self.error,
            "metadata":      self.metadata,
        }


# ---------------------------------------------------------------------------
# ABC — GPUAdapterContract
# ---------------------------------------------------------------------------

class GPUAdapterContract(abc.ABC):
    """
    GPU 클라우드 프로바이더 추상 계약.

    구현체는 반드시 다음을 제공해야 함:
      - provider_id()       → GPUProvider
      - cost_per_hour()     → float (USD/h)
      - launch_job()        → GPUJobResult
      - dry_run()           → GPUJobResult (실제 기동 없음)
      - estimate_cost()     → float (USD 추정)

    LLM-0: 이 인터페이스를 구현하는 어떤 클래스도
            외부 LLM API(OpenAI, Anthropic 등)를 호출해서는 안 됨.
    """

    @property
    @abc.abstractmethod
    def provider_id(self) -> GPUProvider:
        """프로바이더 식별자."""

    @property
    @abc.abstractmethod
    def cost_per_hour(self) -> float:
        """시간당 비용 (USD)."""

    @abc.abstractmethod
    def estimate_cost(self, hours: float) -> float:
        """예상 비용 계산 (USD)."""

    @abc.abstractmethod
    def launch_job(self, request: GPUJobRequest) -> GPUJobResult:
        """
        실제 GPU 작업 기동.
        dry_run=True인 request가 전달되면 dry_run()과 동일하게 동작해야 함.
        """

    @abc.abstractmethod
    def dry_run(self, request: GPUJobRequest) -> GPUJobResult:
        """
        비용 추정 전용 — 실제 GPU 기동 없이 GPUJobResult 반환.
        status=GPUJobStatus.DRY_RUN, dry_run=True.
        """

    def check_slo(
        self,
        request: GPUJobRequest,
        monthly_spend: float,
        slo: CostSLO = DEFAULT_COST_SLO,
    ) -> str:
        """
        SLO 위반 여부 사전 점검.
        monthly_spend + 예상 비용 합산으로 평가.
        Returns: "OK" | "WARN" | "BLOCK" | "HALT"
        """
        projected = monthly_spend + self.estimate_cost(request.hours_estimate)
        return slo.assess(projected)


# ---------------------------------------------------------------------------
# RunPodAdapter — RTX 4090 $0.39/h
# ---------------------------------------------------------------------------

class RunPodAdapter(GPUAdapterContract):
    """
    RunPod GPU 클라우드 어댑터.
    기본 인스턴스: RTX 4090 ($0.39/h)
    """

    _PROVIDER_ID    = GPUProvider.RUNPOD
    _COST_PER_HOUR  = 0.39          # USD / h, RTX 4090

    def __init__(
        self,
        api_key: str = "",
        instance_type: str = "RTX4090",
        cost_override: Optional[float] = None,
    ) -> None:
        self._api_key       = api_key
        self._instance_type = instance_type
        self._cost_ph       = cost_override if cost_override is not None else self._COST_PER_HOUR

    @property
    def provider_id(self) -> GPUProvider:
        return self._PROVIDER_ID

    @property
    def cost_per_hour(self) -> float:
        return self._cost_ph

    def estimate_cost(self, hours: float) -> float:
        return round(hours * self._cost_ph, 4)

    def dry_run(self, request: GPUJobRequest) -> GPUJobResult:
        """비용 추정만 수행 — RunPod API 호출 없음."""
        estimated_cost = self.estimate_cost(request.hours_estimate)
        return GPUJobResult(
            job_id        = request.job_id,
            provider      = self._PROVIDER_ID,
            status        = GPUJobStatus.DRY_RUN,
            actual_hours  = request.hours_estimate,
            cost_usd      = estimated_cost,
            dry_run       = True,
            artifact_path = "",
            metadata      = {
                "instance_type": self._instance_type,
                "model_name":    request.model_name,
                "dataset_path":  request.dataset_path,
            },
        )

    def launch_job(self, request: GPUJobRequest) -> GPUJobResult:
        """
        GPU 작업 기동.
        dry_run=True인 경우 dry_run()으로 위임.
        실제 RunPod API 연동은 api_key 제공 시 활성화 (현재 Mock).
        """
        if request.dry_run or not self._api_key:
            return self.dry_run(request)

        # ── 실제 API 호출 자리 (Mock 구현) ──────────────────────
        # 실제 환경: requests.post("https://api.runpod.io/graphql", ...)
        # LLM-0 준수: GPU 훈련 API이지 LLM 추론 API가 아님
        simulated_hours = request.hours_estimate * 1.05   # 5% 오버헤드 가정
        simulated_cost  = self.estimate_cost(simulated_hours)
        return GPUJobResult(
            job_id        = request.job_id,
            provider      = self._PROVIDER_ID,
            status        = GPUJobStatus.COMPLETED,
            actual_hours  = simulated_hours,
            cost_usd      = simulated_cost,
            dry_run       = False,
            artifact_path = f"runpod://jobs/{request.job_id}/checkpoint",
            metadata      = {"instance_type": self._instance_type},
        )


# ---------------------------------------------------------------------------
# LambdaLabsAdapter — H100 $1.49/h
# ---------------------------------------------------------------------------

class LambdaLabsAdapter(GPUAdapterContract):
    """
    Lambda Labs GPU 클라우드 어댑터.
    기본 인스턴스: H100 SXM5 80GB ($1.49/h)
    """

    _PROVIDER_ID    = GPUProvider.LAMBDA_LABS
    _COST_PER_HOUR  = 1.49          # USD / h, H100 SXM5

    def __init__(
        self,
        api_key: str = "",
        instance_type: str = "gpu_1x_h100_sxm5",
        cost_override: Optional[float] = None,
    ) -> None:
        self._api_key       = api_key
        self._instance_type = instance_type
        self._cost_ph       = cost_override if cost_override is not None else self._COST_PER_HOUR

    @property
    def provider_id(self) -> GPUProvider:
        return self._PROVIDER_ID

    @property
    def cost_per_hour(self) -> float:
        return self._cost_ph

    def estimate_cost(self, hours: float) -> float:
        return round(hours * self._cost_ph, 4)

    def dry_run(self, request: GPUJobRequest) -> GPUJobResult:
        """비용 추정만 수행 — Lambda Labs API 호출 없음."""
        estimated_cost = self.estimate_cost(request.hours_estimate)
        return GPUJobResult(
            job_id        = request.job_id,
            provider      = self._PROVIDER_ID,
            status        = GPUJobStatus.DRY_RUN,
            actual_hours  = request.hours_estimate,
            cost_usd      = estimated_cost,
            dry_run       = True,
            artifact_path = "",
            metadata      = {
                "instance_type": self._instance_type,
                "model_name":    request.model_name,
                "dataset_path":  request.dataset_path,
            },
        )

    def launch_job(self, request: GPUJobRequest) -> GPUJobResult:
        if request.dry_run or not self._api_key:
            return self.dry_run(request)

        # ── 실제 Lambda Labs API 자리 (Mock) ──────────────────────
        simulated_hours = request.hours_estimate * 1.03
        simulated_cost  = self.estimate_cost(simulated_hours)
        return GPUJobResult(
            job_id        = request.job_id,
            provider      = self._PROVIDER_ID,
            status        = GPUJobStatus.COMPLETED,
            actual_hours  = simulated_hours,
            cost_usd      = simulated_cost,
            dry_run       = False,
            artifact_path = f"lambda://instances/{request.job_id}/model",
            metadata      = {"instance_type": self._instance_type},
        )


# ---------------------------------------------------------------------------
# HFAutoTrainAdapter — AutoTrain Advanced ~$4/h
# ---------------------------------------------------------------------------

class HFAutoTrainAdapter(GPUAdapterContract):
    """
    Hugging Face AutoTrain Advanced 어댑터.
    평균 비용: ~$4/h (A100 80GB 기준)
    """

    _PROVIDER_ID    = GPUProvider.HF_AUTOTRAIN
    _COST_PER_HOUR  = 4.00          # USD / h, AutoTrain A100

    def __init__(
        self,
        hf_token: str = "",
        space_name: str = "autotrain-ft",
        cost_override: Optional[float] = None,
    ) -> None:
        self._hf_token   = hf_token
        self._space_name = space_name
        self._cost_ph    = cost_override if cost_override is not None else self._COST_PER_HOUR

    @property
    def provider_id(self) -> GPUProvider:
        return self._PROVIDER_ID

    @property
    def cost_per_hour(self) -> float:
        return self._cost_ph

    def estimate_cost(self, hours: float) -> float:
        return round(hours * self._cost_ph, 4)

    def dry_run(self, request: GPUJobRequest) -> GPUJobResult:
        """비용 추정만 수행 — HF AutoTrain API 호출 없음."""
        estimated_cost = self.estimate_cost(request.hours_estimate)
        return GPUJobResult(
            job_id        = request.job_id,
            provider      = self._PROVIDER_ID,
            status        = GPUJobStatus.DRY_RUN,
            actual_hours  = request.hours_estimate,
            cost_usd      = estimated_cost,
            dry_run       = True,
            artifact_path = "",
            metadata      = {
                "space_name":   self._space_name,
                "model_name":   request.model_name,
                "dataset_path": request.dataset_path,
            },
        )

    def launch_job(self, request: GPUJobRequest) -> GPUJobResult:
        if request.dry_run or not self._hf_token:
            return self.dry_run(request)

        # ── 실제 HF AutoTrain API 자리 (Mock) ─────────────────────
        simulated_hours = request.hours_estimate * 1.08
        simulated_cost  = self.estimate_cost(simulated_hours)
        return GPUJobResult(
            job_id        = request.job_id,
            provider      = self._PROVIDER_ID,
            status        = GPUJobStatus.COMPLETED,
            actual_hours  = simulated_hours,
            cost_usd      = simulated_cost,
            dry_run       = False,
            artifact_path = f"hf://spaces/{self._space_name}/{request.job_id}",
            metadata      = {"space_name": self._space_name},
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_ADAPTER_REGISTRY: Dict[GPUProvider, type] = {
    GPUProvider.RUNPOD:       RunPodAdapter,
    GPUProvider.LAMBDA_LABS:  LambdaLabsAdapter,
    GPUProvider.HF_AUTOTRAIN: HFAutoTrainAdapter,
}


def get_adapter(provider: GPUProvider, **kwargs: Any) -> GPUAdapterContract:
    """
    GPUProvider 식별자로 어댑터 인스턴스 생성.

    Usage::

        adapter = get_adapter(GPUProvider.RUNPOD)
        result  = adapter.dry_run(GPUJobRequest(model_name="llama3", ...))
    """
    cls = _ADAPTER_REGISTRY.get(provider)
    if cls is None:
        raise ValueError(f"Unknown GPU provider: {provider!r}")
    return cls(**kwargs)


def list_providers() -> List[Dict[str, Any]]:
    """등록된 모든 프로바이더 목록 반환."""
    return [
        {
            "provider":       p.value,
            "adapter_class":  cls.__name__,
            "cost_per_hour":  cls._COST_PER_HOUR,  # type: ignore[attr-defined]
        }
        for p, cls in _ADAPTER_REGISTRY.items()
    ]
