"""literary_system/serving/model_serving_endpoint_v2.py

ModelServingEndpoint v2.0 — Kubernetes HPA 지원 (ADR-122)

v1.0 대비 확장:
  - HPAConfig: Kubernetes HPA 파라미터 관리
  - HPAStatus: 실시간 레플리카 및 부하 상태
  - MetricsCollector: QPS / 큐 깊이 / CPU 사용률 집계
  - ModelServingEndpointV2: v1.0 슈퍼셋 + HPA 인터페이스
  - generate_hpa_manifest(): HPA YAML spec 생성
  - K8s 준비 프로브 (liveness / readiness) 응답 지원

LLM-0 원칙: 외부 LLM API 호출 없음.
DEV_MODE: 항상 False.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

__all__ = [
    "HPAConfig",
    "HPAStatus",
    "ServingMetricsSnapshot",
    "MetricsCollector",
    "ModelServingEndpointV2",
    "generate_hpa_manifest",
    "HPAConfigError",
    "EndpointV2Error",
]

# ── 상수 ──────────────────────────────────────────────────────────────
_MIN_REPLICAS_FLOOR: int = 1
_MAX_REPLICAS_CEILING: int = 100
_CPU_THRESHOLD_LOW: float = 10.0    # % — scale-down 경계
_CPU_THRESHOLD_HIGH: float = 90.0   # % — 위험 경계
_DEFAULT_SCALE_UP_COOLDOWN: int = 60   # seconds
_DEFAULT_SCALE_DOWN_COOLDOWN: int = 300  # seconds


# ── 예외 ─────────────────────────────────────────────────────────────

class HPAConfigError(ValueError):
    """HPA 설정 오류."""


class EndpointV2Error(RuntimeError):
    """ModelServingEndpointV2 런타임 오류."""


# ── 데이터 클래스 ─────────────────────────────────────────────────────

@dataclass
class HPAConfig:
    """Kubernetes HPA 파라미터.

    Args:
        min_replicas: 최소 레플리카 수 (≥1)
        max_replicas: 최대 레플리카 수 (≥ min_replicas)
        target_cpu_utilization_pct: 목표 CPU 사용률 (1~99 %)
        target_memory_utilization_pct: 목표 메모리 사용률 (1~99 %)
        target_rps: 레플리카당 목표 RPS (requests per second)
        scale_up_cooldown_sec: 스케일업 쿨다운 (초)
        scale_down_cooldown_sec: 스케일다운 쿨다운 (초)
        namespace: Kubernetes 네임스페이스
        deployment_name: 대상 Deployment 이름
    """
    min_replicas: int = 2
    max_replicas: int = 10
    target_cpu_utilization_pct: int = 70
    target_memory_utilization_pct: int = 80
    target_rps: float = 100.0           # RPS per replica
    scale_up_cooldown_sec: int = _DEFAULT_SCALE_UP_COOLDOWN
    scale_down_cooldown_sec: int = _DEFAULT_SCALE_DOWN_COOLDOWN
    namespace: str = "literary-os"
    deployment_name: str = "literary-os-server"

    def validate(self) -> None:
        """설정 유효성 검사. 오류 시 HPAConfigError."""
        if self.min_replicas < _MIN_REPLICAS_FLOOR:
            raise HPAConfigError(
                f"min_replicas={self.min_replicas} < {_MIN_REPLICAS_FLOOR}"
            )
        if self.max_replicas < self.min_replicas:
            raise HPAConfigError(
                f"max_replicas={self.max_replicas} < min_replicas={self.min_replicas}"
            )
        if self.max_replicas > _MAX_REPLICAS_CEILING:
            raise HPAConfigError(
                f"max_replicas={self.max_replicas} > ceiling {_MAX_REPLICAS_CEILING}"
            )
        if not (1 <= self.target_cpu_utilization_pct <= 99):
            raise HPAConfigError(
                f"target_cpu_utilization_pct={self.target_cpu_utilization_pct} not in [1,99]"
            )
        if not (1 <= self.target_memory_utilization_pct <= 99):
            raise HPAConfigError(
                f"target_memory_utilization_pct={self.target_memory_utilization_pct} not in [1,99]"
            )
        if self.target_rps <= 0:
            raise HPAConfigError(f"target_rps={self.target_rps} must be > 0")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HPAStatus:
    """현재 HPA 상태 스냅샷."""
    current_replicas: int
    desired_replicas: int
    min_replicas: int
    max_replicas: int
    last_scale_time: float = 0.0      # UNIX timestamp (0 = 미스케일)
    scale_direction: str = "none"     # "up" | "down" | "none"
    conditions: list[str] = field(default_factory=list)

    @property
    def is_at_max(self) -> bool:
        return self.current_replicas >= self.max_replicas

    @property
    def is_at_min(self) -> bool:
        return self.current_replicas <= self.min_replicas

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_replicas": self.current_replicas,
            "desired_replicas": self.desired_replicas,
            "min_replicas": self.min_replicas,
            "max_replicas": self.max_replicas,
            "last_scale_time": self.last_scale_time,
            "scale_direction": self.scale_direction,
            "is_at_max": self.is_at_max,
            "is_at_min": self.is_at_min,
            "conditions": self.conditions,
        }


@dataclass
class ServingMetricsSnapshot:
    """단일 시점 메트릭 스냅샷."""
    timestamp: float
    qps: float              # 초당 요청 수
    queue_depth: int        # 대기 중인 요청 수
    cpu_utilization_pct: float   # 0~100
    memory_utilization_pct: float  # 0~100
    active_replicas: int
    p95_latency_ms: float = 0.0
    error_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MetricsCollector:
    """서빙 메트릭 수집기 — 슬라이딩 윈도우 집계."""

    def __init__(self, window_sec: float = 60.0) -> None:
        self._window = window_sec
        self._samples: list[ServingMetricsSnapshot] = []

    def record(self, snapshot: ServingMetricsSnapshot) -> None:
        self._samples.append(snapshot)
        self._evict_old()

    def _evict_old(self) -> None:
        now = time.monotonic()
        cutoff = now - self._window
        self._samples = [s for s in self._samples if s.timestamp >= cutoff]

    def avg_qps(self) -> float:
        if not self._samples:
            return 0.0
        return sum(s.qps for s in self._samples) / len(self._samples)

    def avg_cpu(self) -> float:
        if not self._samples:
            return 0.0
        return sum(s.cpu_utilization_pct for s in self._samples) / len(self._samples)

    def avg_memory(self) -> float:
        if not self._samples:
            return 0.0
        return sum(s.memory_utilization_pct for s in self._samples) / len(self._samples)

    def max_queue_depth(self) -> int:
        if not self._samples:
            return 0
        return max(s.queue_depth for s in self._samples)

    def latest(self) -> ServingMetricsSnapshot | None:
        return self._samples[-1] if self._samples else None

    def sample_count(self) -> int:
        return len(self._samples)


# ── 핵심 클래스 ───────────────────────────────────────────────────────

class ModelServingEndpointV2:
    """ModelServingEndpoint v2.0 — Kubernetes HPA 지원.

    주요 추가 기능 (v1.0 대비):
      - HPAConfig 관리 및 유효성 검사
      - 레플리카 계산 (RPS 기반 희망 레플리카 추정)
      - MetricsCollector 통합
      - HPA 상태 리포트
      - K8s liveness / readiness 프로브 응답
      - generate_hpa_manifest() YAML 생성
    """

    VERSION = "2.0.0"

    def __init__(
        self,
        hpa_config: HPAConfig | None = None,
        metrics_window_sec: float = 60.0,
    ) -> None:
        self._hpa = hpa_config or HPAConfig()
        self._hpa.validate()
        self._metrics = MetricsCollector(window_sec=metrics_window_sec)
        self._current_replicas: int = self._hpa.min_replicas
        self._last_scale_up: float = 0.0
        self._last_scale_down: float = 0.0
        self._healthy: bool = True
        self._ready: bool = True
        self._start_time: float = time.monotonic()

    # ── 프로브 ────────────────────────────────────────────────────────

    def liveness_probe(self) -> dict[str, Any]:
        """K8s liveness 프로브 응답."""
        return {
            "status": "alive" if self._healthy else "unhealthy",
            "uptime_sec": round(time.monotonic() - self._start_time, 1),
            "version": self.VERSION,
        }

    def readiness_probe(self) -> dict[str, Any]:
        """K8s readiness 프로브 응답."""
        return {
            "status": "ready" if (self._healthy and self._ready) else "not_ready",
            "replicas": self._current_replicas,
            "version": self.VERSION,
        }

    def set_healthy(self, healthy: bool) -> None:
        self._healthy = healthy

    def set_ready(self, ready: bool) -> None:
        self._ready = ready

    # ── HPA 연산 ──────────────────────────────────────────────────────

    def record_metrics(self, snapshot: ServingMetricsSnapshot) -> None:
        """메트릭 기록 (MetricsCollector로 위임)."""
        self._metrics.record(snapshot)

    def compute_desired_replicas(self) -> int:
        """현재 메트릭 기반 희망 레플리카 수 계산.

        CPU 사용률 우선, QPS 기반 병렬 계산 후 최댓값 채택.
        결과는 [min_replicas, max_replicas] 범위로 클램핑.
        """
        avg_cpu = self._metrics.avg_cpu()
        avg_qps = self._metrics.avg_qps()

        # CPU 기반
        if avg_cpu > 0:
            cpu_ratio = avg_cpu / self._hpa.target_cpu_utilization_pct
            cpu_desired = max(1, round(self._current_replicas * cpu_ratio))
        else:
            cpu_desired = self._current_replicas

        # QPS 기반
        if self._hpa.target_rps > 0 and avg_qps > 0:
            qps_desired = max(1, -(-int(avg_qps) // int(self._hpa.target_rps)))
        else:
            qps_desired = self._current_replicas

        desired = max(cpu_desired, qps_desired)
        return max(self._hpa.min_replicas, min(self._hpa.max_replicas, desired))

    def maybe_scale(self) -> HPAStatus:
        """쿨다운 기간 고려 후 스케일 조정. HPAStatus 반환."""
        desired = self.compute_desired_replicas()
        now = time.monotonic()
        direction = "none"
        conditions: list[str] = []

        if desired > self._current_replicas:
            if now - self._last_scale_up >= self._hpa.scale_up_cooldown_sec:
                self._current_replicas = desired
                self._last_scale_up = now
                direction = "up"
            else:
                conditions.append(
                    f"scale-up cooldown: {int(self._hpa.scale_up_cooldown_sec - (now - self._last_scale_up))}s remaining"
                )
        elif desired < self._current_replicas:
            if now - self._last_scale_down >= self._hpa.scale_down_cooldown_sec:
                self._current_replicas = desired
                self._last_scale_down = now
                direction = "down"
            else:
                conditions.append(
                    f"scale-down cooldown: {int(self._hpa.scale_down_cooldown_sec - (now - self._last_scale_down))}s remaining"
                )

        return HPAStatus(
            current_replicas=self._current_replicas,
            desired_replicas=desired,
            min_replicas=self._hpa.min_replicas,
            max_replicas=self._hpa.max_replicas,
            last_scale_time=self._last_scale_up if direction == "up" else (
                self._last_scale_down if direction == "down" else 0.0
            ),
            scale_direction=direction,
            conditions=conditions,
        )

    def force_scale(self, replicas: int) -> HPAStatus:
        """쿨다운 무시하고 즉시 스케일 (테스트/긴급 용도)."""
        clamped = max(self._hpa.min_replicas, min(self._hpa.max_replicas, replicas))
        direction = (
            "up" if clamped > self._current_replicas
            else "down" if clamped < self._current_replicas
            else "none"
        )
        self._current_replicas = clamped
        now = time.monotonic()
        if direction == "up":
            self._last_scale_up = now
        elif direction == "down":
            self._last_scale_down = now
        return HPAStatus(
            current_replicas=self._current_replicas,
            desired_replicas=clamped,
            min_replicas=self._hpa.min_replicas,
            max_replicas=self._hpa.max_replicas,
            last_scale_time=now,
            scale_direction=direction,
        )

    # ── 상태 조회 ─────────────────────────────────────────────────────

    def hpa_config(self) -> dict[str, Any]:
        return self._hpa.to_dict()

    def status(self) -> dict[str, Any]:
        """전체 상태 딕셔너리."""
        latest = self._metrics.latest()
        return {
            "version": self.VERSION,
            "healthy": self._healthy,
            "ready": self._ready,
            "current_replicas": self._current_replicas,
            "hpa": self._hpa.to_dict(),
            "metrics": {
                "avg_qps": round(self._metrics.avg_qps(), 2),
                "avg_cpu_pct": round(self._metrics.avg_cpu(), 2),
                "avg_memory_pct": round(self._metrics.avg_memory(), 2),
                "max_queue_depth": self._metrics.max_queue_depth(),
                "sample_count": self._metrics.sample_count(),
                "latest": latest.to_dict() if latest else None,
            },
        }


# ── HPA YAML 생성 ─────────────────────────────────────────────────────

def generate_hpa_manifest(config: HPAConfig) -> str:
    """Kubernetes HPA 매니페스트 YAML 문자열 생성.

    autoscaling/v2 API 사용 (K8s 1.23+).
    """
    config.validate()
    return f"""\
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {config.deployment_name}-hpa
  namespace: {config.namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {config.deployment_name}
  minReplicas: {config.min_replicas}
  maxReplicas: {config.max_replicas}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {config.target_cpu_utilization_pct}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {config.target_memory_utilization_pct}
  behavior:
    scaleUp:
      stabilizationWindowSeconds: {config.scale_up_cooldown_sec}
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: {config.scale_down_cooldown_sec}
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
"""
