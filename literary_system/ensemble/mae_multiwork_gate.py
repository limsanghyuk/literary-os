"""
V654 — MAEMultiWorkGate G66 (SP-C.2 Multi-Agent Ensemble).
3개 작품(project) 동시 앙상블 실행 성능 게이트.
P95(95th percentile) latency <= 8.0초 기준.
LLM-0: 외부 API 직접 호출 없음. ADR-114.
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

GATE_ID = "G66"
GATE_NAME = "MAE-MultiWork"
P95_THRESHOLD_SEC = 8.0
MIN_PROJECTS = 3
MAX_WORKERS = 4
STUB_SCENE_LATENCY_SEC = 0.05


@dataclass
class ProjectRunSpec:
    """단일 작품 실행 명세."""
    project_id: str
    scenes: List[Dict[str, Any]] = field(default_factory=list)
    max_rounds: int = 3


@dataclass
class ProjectRunResult:
    """단일 작품 실행 결과."""
    project_id: str
    latency_sec: float
    scene_count: int
    success: bool
    error: Optional[str] = None
    ensemble_scores: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "latency_sec": self.latency_sec,
            "scene_count": self.scene_count,
            "success": self.success,
            "error": self.error,
            "ensemble_scores": self.ensemble_scores,
        }


@dataclass
class MultiWorkGateResult:
    """G66 게이트 결과."""
    gate_id: str = GATE_ID
    gate_name: str = GATE_NAME
    passed: bool = False
    project_count: int = 0
    p95_latency_sec: float = 0.0
    p50_latency_sec: float = 0.0
    max_latency_sec: float = 0.0
    all_latencies: List[float] = field(default_factory=list)
    project_results: List[ProjectRunResult] = field(default_factory=list)
    failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "passed": self.passed,
            "project_count": self.project_count,
            "p95_latency_sec": self.p95_latency_sec,
            "p50_latency_sec": self.p50_latency_sec,
            "max_latency_sec": self.max_latency_sec,
            "all_latencies": self.all_latencies,
            "project_results": [r.to_dict() for r in self.project_results],
            "failure_reason": self.failure_reason,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MultiWorkGateResult":
        results = [ProjectRunResult(**r) for r in d.get("project_results", [])]
        return cls(
            gate_id=d.get("gate_id", GATE_ID),
            gate_name=d.get("gate_name", GATE_NAME),
            passed=d.get("passed", False),
            project_count=d.get("project_count", 0),
            p95_latency_sec=d.get("p95_latency_sec", 0.0),
            p50_latency_sec=d.get("p50_latency_sec", 0.0),
            max_latency_sec=d.get("max_latency_sec", 0.0),
            all_latencies=d.get("all_latencies", []),
            project_results=results,
            failure_reason=d.get("failure_reason"),
        )


def _percentile(data: List[float], pct: float) -> float:
    """p-번째 백분위수 계산 (선형 보간법)."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    n = len(sorted_data)
    k = (pct / 100.0) * (n - 1)
    lo = int(k)
    hi = lo + 1
    if hi >= n:
        return sorted_data[-1]
    frac = k - lo
    return sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo])


class MAEMultiWorkGate:
    """
    G66 — MAE-MultiWork 성능 게이트.

    3개 이상 작품 앙상블을 동시 실행하여 P95 지연이
    P95_THRESHOLD_SEC(8.0초) 이하인지 검증한다.

    coordinator: AgentCoordinator 인스턴스 (없으면 내부 스텁 사용).
    """

    def __init__(
        self,
        coordinator: Optional[Any] = None,
        p95_threshold_sec: float = P95_THRESHOLD_SEC,
        max_workers: int = MAX_WORKERS,
    ) -> None:
        self.coordinator = coordinator
        self.p95_threshold = p95_threshold_sec
        self.max_workers = max_workers

    def run_gate(
        self,
        projects: List[ProjectRunSpec],
        per_project_timeout: float = 15.0,
    ) -> MultiWorkGateResult:
        """게이트 실행 엔트리 포인트 (최소 3개 작품 필요)."""
        if len(projects) < MIN_PROJECTS:
            return MultiWorkGateResult(
                passed=False,
                project_count=len(projects),
                failure_reason=f"프로젝트 수 부족: {len(projects)} < {MIN_PROJECTS}",
            )

        project_results = self._run_concurrent(projects, per_project_timeout)
        return self._evaluate(project_results)

    def benchmark(
        self,
        projects: List[ProjectRunSpec],
        repeat: int = 5,
        per_project_timeout: float = 15.0,
    ) -> MultiWorkGateResult:
        """반복 벤치마크 — repeat 회 실행 후 합산 P95 계산."""
        all_latencies: List[float] = []
        all_results: List[ProjectRunResult] = []

        for _ in range(repeat):
            run_results = self._run_concurrent(projects, per_project_timeout)
            for r in run_results:
                all_latencies.append(r.latency_sec)
            all_results.extend(run_results)

        return self._make_gate_result(all_latencies, all_results)

    def _run_concurrent(
        self,
        projects: List[ProjectRunSpec],
        per_project_timeout: float,
    ) -> List[ProjectRunResult]:
        """ThreadPoolExecutor로 작품 동시 실행."""
        results: List[ProjectRunResult] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map = {
                executor.submit(self._run_single_project, spec, per_project_timeout): spec
                for spec in projects
            }
            for future in as_completed(future_map, timeout=per_project_timeout * 2):
                spec = future_map[future]
                try:
                    result = future.result(timeout=per_project_timeout)
                    results.append(result)
                except FuturesTimeout:
                    results.append(ProjectRunResult(
                        project_id=spec.project_id,
                        latency_sec=per_project_timeout,
                        scene_count=len(spec.scenes),
                        success=False,
                        error="timeout",
                    ))
                except Exception as exc:
                    results.append(ProjectRunResult(
                        project_id=spec.project_id,
                        latency_sec=0.0,
                        scene_count=len(spec.scenes),
                        success=False,
                        error=str(exc),
                    ))

        return results

    def _run_single_project(
        self,
        spec: ProjectRunSpec,
        timeout: float,
    ) -> ProjectRunResult:
        """단일 작품 실행 — coordinator 또는 스텁 사용."""
        t_start = time.perf_counter()
        scores: List[float] = []

        if self.coordinator is not None:
            for scene_bp in spec.scenes:
                result = self.coordinator.run(scene_bp)
                if hasattr(result, "ensemble_score"):
                    scores.append(result.ensemble_score)
        else:
            for _scene_bp in spec.scenes:
                time.sleep(STUB_SCENE_LATENCY_SEC)
                scores.append(0.85)

        latency = time.perf_counter() - t_start
        return ProjectRunResult(
            project_id=spec.project_id,
            latency_sec=latency,
            scene_count=len(spec.scenes),
            success=True,
            ensemble_scores=scores,
        )

    def _evaluate(self, results: List[ProjectRunResult]) -> MultiWorkGateResult:
        """결과로부터 G66 통과 여부 판정."""
        latencies = [r.latency_sec for r in results]
        return self._make_gate_result(latencies, results)

    def _make_gate_result(
        self,
        latencies: List[float],
        results: List[ProjectRunResult],
    ) -> MultiWorkGateResult:
        if not latencies:
            return MultiWorkGateResult(passed=False, failure_reason="실행 결과 없음")

        p95 = _percentile(latencies, 95)
        p50 = _percentile(latencies, 50)
        max_lat = max(latencies)
        passed = p95 <= self.p95_threshold

        failure_reason = None
        if not passed:
            failure_reason = f"P95={p95:.3f}s > 임계값={self.p95_threshold}s"

        return MultiWorkGateResult(
            passed=passed,
            project_count=len(results),
            p95_latency_sec=round(p95, 4),
            p50_latency_sec=round(p50, 4),
            max_latency_sec=round(max_lat, 4),
            all_latencies=[round(l, 4) for l in latencies],
            project_results=results,
            failure_reason=failure_reason,
        )
