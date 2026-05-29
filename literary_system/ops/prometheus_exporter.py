"""literary_system/ops/prometheus_exporter.py

V628: Literary OS Prometheus 메트릭 익스포터.

설계 원칙:
  LLM-0: 외부 LLM 호출 없음 (순수 메트릭 수집/포매팅).
  G32: print() 사용 금지 — 모든 출력은 logger 또는 반환값.
  G37: PrometheusExporter, MetricSnapshot, MonitoringConfig — literary_system/ 내 유일.

노출 메트릭:
  literary_os_gates_total         — 총 Gate 수
  literary_os_gates_passed        — PASS Gate 수
  literary_os_gates_pass_ratio    — Gate PASS 비율 (0~1)
  literary_os_tests_total         — 총 TC 수
  literary_os_cost_slo_used_usd   — GPU 비용 SLO 사용액 ($)
  literary_os_cost_slo_hard_usd   — GPU 비용 SLO 하드 한도 ($)
  literary_os_serve_latency_ms    — ServePlane 평균 지연시간 (ms)
  literary_os_train_jobs_active   — 활성 TrainPlane 학습 작업 수
  literary_os_lora_promoted_count — PROMOTED 상태 LoRA 모델 수
  literary_os_build_info          — 빌드 정보 레이블 (version, phase)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────────────────────

METRIC_PREFIX = "literary_os"

METRIC_NAMES: Tuple[str, ...] = (
    "gates_total",
    "gates_passed",
    "gates_pass_ratio",
    "tests_total",
    "cost_slo_used_usd",
    "cost_slo_hard_usd",
    "serve_latency_ms",
    "train_jobs_active",
    "lora_promoted_count",
    "build_info",
)

DEFAULT_HARD_LIMIT_USD: float = 120.0
DEFAULT_SCRAPE_INTERVAL_SEC: int = 15


# ─────────────────────────────────────────────────────────────────────────────
# Dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MonitoringConfig:
    """Prometheus 익스포터 설정."""

    scrape_interval_sec: int = DEFAULT_SCRAPE_INTERVAL_SEC
    cost_slo_hard_usd: float = DEFAULT_HARD_LIMIT_USD
    metric_prefix: str = METRIC_PREFIX
    include_build_info: bool = True
    version: str = "10.32.0"
    phase: str = "B"

    def validate(self) -> List[str]:
        """설정 유효성 검사 — 에러 목록 반환."""
        errors: List[str] = []
        if self.scrape_interval_sec <= 0:
            errors.append(f"scrape_interval_sec={self.scrape_interval_sec} must be > 0")
        if self.cost_slo_hard_usd <= 0:
            errors.append(f"cost_slo_hard_usd={self.cost_slo_hard_usd} must be > 0")
        if not self.metric_prefix:
            errors.append("metric_prefix must not be empty")
        return errors


@dataclass
class MetricSnapshot:
    """특정 시점의 Literary OS 핵심 메트릭 스냅샷."""

    timestamp: float = field(default_factory=time.time)
    gates_total: int = 60
    gates_passed: int = 60
    tests_total: int = 7060
    cost_slo_used_usd: float = 0.0
    cost_slo_hard_usd: float = DEFAULT_HARD_LIMIT_USD
    serve_latency_ms: float = 0.0
    train_jobs_active: int = 0
    lora_promoted_count: int = 0
    labels: Dict[str, str] = field(default_factory=dict)

    @property
    def gates_pass_ratio(self) -> float:
        """Gate PASS 비율 (0~1)."""
        if self.gates_total <= 0:
            return 0.0
        return min(1.0, self.gates_passed / self.gates_total)

    @property
    def cost_slo_utilization(self) -> float:
        """비용 SLO 사용률 (0~1)."""
        if self.cost_slo_hard_usd <= 0:
            return 0.0
        return min(1.0, self.cost_slo_used_usd / self.cost_slo_hard_usd)

    def is_healthy(self) -> bool:
        """기본 헬스 판단: Gate PASS율 ≥ 0.95, 비용 SLO ≤ 1.0."""
        return (
            self.gates_pass_ratio >= 0.95
            and self.cost_slo_utilization <= 1.0
            and self.serve_latency_ms >= 0
        )

    def validate(self) -> List[str]:
        """스냅샷 유효성 검사."""
        errors: List[str] = []
        if self.gates_total < 0:
            errors.append(f"gates_total={self.gates_total} must be >= 0")
        if self.gates_passed < 0:
            errors.append(f"gates_passed={self.gates_passed} must be >= 0")
        if self.gates_passed > self.gates_total:
            errors.append(
                f"gates_passed({self.gates_passed}) > gates_total({self.gates_total})"
            )
        if self.tests_total < 0:
            errors.append(f"tests_total={self.tests_total} must be >= 0")
        if self.cost_slo_used_usd < 0:
            errors.append(f"cost_slo_used_usd={self.cost_slo_used_usd} must be >= 0")
        if self.cost_slo_hard_usd <= 0:
            errors.append(f"cost_slo_hard_usd={self.cost_slo_hard_usd} must be > 0")
        if self.serve_latency_ms < 0:
            errors.append(f"serve_latency_ms={self.serve_latency_ms} must be >= 0")
        if self.train_jobs_active < 0:
            errors.append(f"train_jobs_active={self.train_jobs_active} must be >= 0")
        if self.lora_promoted_count < 0:
            errors.append(
                f"lora_promoted_count={self.lora_promoted_count} must be >= 0"
            )
        return errors


# ─────────────────────────────────────────────────────────────────────────────
# PrometheusExporter
# ─────────────────────────────────────────────────────────────────────────────

class PrometheusExporter:
    """Literary OS 핵심 메트릭을 Prometheus exposition format으로 출력.

    사용 예::

        config = MonitoringConfig(version="10.32.0", phase="B")
        exporter = PrometheusExporter(config)
        snapshot = MetricSnapshot(gates_passed=60, tests_total=7060)
        text = exporter.render(snapshot)

    외부 의존성 없음 — prometheus_client 라이브러리 불필요.
    """

    VERSION = "1.0.0"

    def __init__(self, config: Optional[MonitoringConfig] = None) -> None:
        self.config: MonitoringConfig = config or MonitoringConfig()
        self._snapshots: List[MetricSnapshot] = []
        logger.info(
            "[PrometheusExporter] 초기화 완료 — prefix=%s, version=%s",
            self.config.metric_prefix,
            self.config.version,
        )

    # ── 공개 API ──────────────────────────────────────────────────────────────

    def collect(self, snapshot: MetricSnapshot) -> None:
        """스냅샷을 내부 버퍼에 추가. 최근 100개 보관."""
        errors = snapshot.validate()
        if errors:
            logger.error("[PrometheusExporter] 스냅샷 검증 실패: %s", errors)
            raise ValueError(f"MetricSnapshot 유효성 오류: {errors}")
        self._snapshots.append(snapshot)
        if len(self._snapshots) > 100:
            self._snapshots = self._snapshots[-100:]
        logger.info(
            "[PrometheusExporter] 스냅샷 수집 — gates=%d/%d, tests=%d",
            snapshot.gates_passed,
            snapshot.gates_total,
            snapshot.tests_total,
        )

    def render(self, snapshot: Optional[MetricSnapshot] = None) -> str:
        """Prometheus exposition format 텍스트 생성.

        Args:
            snapshot: 렌더링할 스냅샷. None이면 마지막 수집 스냅샷 사용.

        Returns:
            Prometheus exposition format 문자열.

        Raises:
            RuntimeError: 스냅샷이 없을 때.
        """
        if snapshot is None:
            if not self._snapshots:
                raise RuntimeError(
                    "렌더링할 MetricSnapshot 없음 — collect() 먼저 호출 필요"
                )
            snapshot = self._snapshots[-1]

        errors = snapshot.validate()
        if errors:
            raise ValueError(f"MetricSnapshot 유효성 오류: {errors}")

        prefix = self.config.metric_prefix
        lines: List[str] = []

        # build_info
        if self.config.include_build_info:
            lines += [
                f"# HELP {prefix}_build_info Literary OS build information",
                f"# TYPE {prefix}_build_info gauge",
                (
                    f'{prefix}_build_info{{version="{self.config.version}",'
                    f'phase="{self.config.phase}"}} 1'
                ),
            ]

        # gates_total
        lines += self._gauge(
            f"{prefix}_gates_total",
            "Total number of release gates",
            snapshot.gates_total,
        )

        # gates_passed
        lines += self._gauge(
            f"{prefix}_gates_passed",
            "Number of PASS release gates",
            snapshot.gates_passed,
        )

        # gates_pass_ratio
        lines += self._gauge(
            f"{prefix}_gates_pass_ratio",
            "Ratio of PASS gates (0..1)",
            snapshot.gates_pass_ratio,
        )

        # tests_total
        lines += self._gauge(
            f"{prefix}_tests_total",
            "Total number of test cases",
            snapshot.tests_total,
        )

        # cost_slo_used_usd
        lines += self._gauge(
            f"{prefix}_cost_slo_used_usd",
            "GPU cost SLO used amount in USD",
            snapshot.cost_slo_used_usd,
        )

        # cost_slo_hard_usd
        lines += self._gauge(
            f"{prefix}_cost_slo_hard_usd",
            "GPU cost SLO hard limit in USD",
            snapshot.cost_slo_hard_usd,
        )

        # serve_latency_ms
        lines += self._gauge(
            f"{prefix}_serve_latency_ms",
            "ServePlane average inference latency in milliseconds",
            snapshot.serve_latency_ms,
        )

        # train_jobs_active
        lines += self._gauge(
            f"{prefix}_train_jobs_active",
            "Active TrainPlane LoRA fine-tuning jobs",
            snapshot.train_jobs_active,
        )

        # lora_promoted_count
        lines += self._gauge(
            f"{prefix}_lora_promoted_count",
            "Number of LoRA models in PROMOTED stage",
            snapshot.lora_promoted_count,
        )

        return "\n".join(lines) + "\n"

    def latest_snapshot(self) -> Optional[MetricSnapshot]:
        """마지막으로 수집된 스냅샷 반환."""
        return self._snapshots[-1] if self._snapshots else None

    def snapshot_count(self) -> int:
        """수집된 스냅샷 수 반환."""
        return len(self._snapshots)

    def metric_names(self) -> List[str]:
        """노출하는 메트릭 이름 목록 반환."""
        prefix = self.config.metric_prefix
        return [f"{prefix}_{name}" for name in METRIC_NAMES]

    def reset(self) -> None:
        """내부 스냅샷 버퍼 초기화."""
        self._snapshots.clear()
        logger.info("[PrometheusExporter] 버퍼 초기화 완료")

    # ── 내부 헬퍼 ────────────────────────────────────────────────────────────

    @staticmethod
    def _gauge(name: str, help_text: str, value: float) -> List[str]:
        """HELP + TYPE + 값 라인 3종 반환."""
        return [
            f"# HELP {name} {help_text}",
            f"# TYPE {name} gauge",
            f"{name} {value}",
        ]

    @staticmethod
    def _format_value(v: float) -> str:
        """Prometheus 숫자 포맷 — 정수면 정수형, 소수면 소수형."""
        if v == int(v):
            return str(int(v))
        return f"{v:.6g}"
