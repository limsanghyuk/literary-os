"""literary_system/serving/canary_controller.py

CanaryController v1.0 — 4단계 Canary 배포 컨트롤러
ADR-065 참조.

역할:
    모델 서빙 환경에서 신규 LoRA/PPO 모델을 4단계 트래픽 비율
    (5 → 25 → 50 → 100 %)로 점진 배포하고, 각 단계에서
    Gate 통과 여부를 판정한다.

LLM-0 원칙: 외부 LLM API 호출 없음.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

STAGE_WEIGHTS: List[int] = [5, 25, 50, 100]  # 각 단계 트래픽 비율 (%)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class CanaryStage(IntEnum):
    """Canary 배포 단계 (0-based index)."""

    STAGE_0 = 0   # 5 %
    STAGE_1 = 1   # 25 %
    STAGE_2 = 2   # 50 %
    STAGE_3 = 3   # 100 %


class CanaryStatus(str):
    """Canary 상태 문자열 상수."""

    PENDING = "pending"        # 아직 시작 전
    IN_PROGRESS = "in_progress"  # 진행 중
    PROMOTED = "promoted"      # 전 단계 통과 → 다음 단계 진입
    COMPLETED = "completed"    # 100 % 완료
    ROLLED_BACK = "rolled_back"  # 롤백 발생


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------


@dataclass
class CanaryConfig:
    """CanaryController 설정.

    Args:
        model_id: 배포 대상 모델 식별자.
        min_requests_per_stage: 단계 판정에 필요한 최소 요청 수.
        error_rate_threshold: 허용 최대 오류율 (0.0~1.0).
        latency_p95_threshold_ms: P95 레이턴시 허용 상한 (밀리초).
        reward_threshold: 보상 모델 평균 최소값.
    """

    model_id: str = "default-model"
    min_requests_per_stage: int = 10
    error_rate_threshold: float = 0.05      # 5 %
    latency_p95_threshold_ms: float = 1500.0  # 1.5초
    reward_threshold: float = 0.75


@dataclass
class StageMetrics:
    """단계별 수집 메트릭.

    Args:
        stage: 해당 Canary 단계 (0~3).
        requests: 처리된 요청 수.
        errors: 오류 발생 수.
        latencies_ms: 응답 시간 목록 (밀리초).
        rewards: 보상 모델 점수 목록.
    """

    stage: int
    requests: int = 0
    errors: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    rewards: List[float] = field(default_factory=list)

    @property
    def error_rate(self) -> float:
        """오류율 (0.0~1.0)."""
        if self.requests == 0:
            return 0.0
        return self.errors / self.requests

    @property
    def latency_p95(self) -> float:
        """P95 레이턴시 (ms). 데이터 없으면 0.0."""
        if not self.latencies_ms:
            return 0.0
        sorted_lat = sorted(self.latencies_ms)
        idx = max(0, int(len(sorted_lat) * 0.95) - 1)
        return sorted_lat[idx]

    @property
    def mean_reward(self) -> float:
        """보상 평균. 데이터 없으면 0.0."""
        if not self.rewards:
            return 0.0
        return sum(self.rewards) / len(self.rewards)


@dataclass
class PromotionRecord:
    """단계 승격 또는 롤백 기록.

    Args:
        from_stage: 이전 단계.
        to_stage: 다음 단계 (롤백이면 -1).
        reason: 판정 사유.
        promoted: True=승격, False=롤백.
    """

    from_stage: int
    to_stage: int
    reason: str
    promoted: bool


@dataclass
class CanaryState:
    """CanaryController 전체 상태."""

    current_stage: int = 0
    status: str = CanaryStatus.PENDING
    stage_metrics: Dict[int, StageMetrics] = field(default_factory=dict)
    promotion_records: List[PromotionRecord] = field(default_factory=list)
    total_promoted: int = 0
    total_rolled_back: int = 0


# ---------------------------------------------------------------------------
# 핵심 컨트롤러
# ---------------------------------------------------------------------------


class CanaryController:
    """Canary 4단계 배포 컨트롤러.

    사용 예::

        cfg = CanaryConfig(model_id="ppo-v1")
        ctrl = CanaryController(cfg)
        ctrl.start()
        ctrl.record_request(stage=0, latency_ms=300.0, reward=0.80, error=False)
        result = ctrl.evaluate_stage(0)
        # result["promoted"] == True  →  ctrl.advance()
    """

    def __init__(self, config: Optional[CanaryConfig] = None) -> None:
        self.config: CanaryConfig = config or CanaryConfig()
        self.state: CanaryState = CanaryState()

    # ------------------------------------------------------------------
    # 생명주기
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Canary 배포를 시작한다 (PENDING → IN_PROGRESS)."""
        self.state.status = CanaryStatus.IN_PROGRESS
        self.state.current_stage = 0
        self._ensure_stage_metrics(0)

    def reset(self) -> None:
        """컨트롤러를 초기 상태로 되돌린다."""
        self.state = CanaryState()

    # ------------------------------------------------------------------
    # 메트릭 수집
    # ------------------------------------------------------------------

    def record_request(
        self,
        stage: int,
        latency_ms: float,
        reward: float,
        error: bool = False,
    ) -> None:
        """단계 메트릭에 요청 1건을 기록한다.

        Args:
            stage: 기록 대상 Canary 단계 (0~3).
            latency_ms: 이 요청의 응답 시간 (밀리초).
            reward: 보상 모델 점수.
            error: 오류 발생 여부.
        """
        self._ensure_stage_metrics(stage)
        m = self.state.stage_metrics[stage]
        m.requests += 1
        m.latencies_ms.append(latency_ms)
        m.rewards.append(reward)
        if error:
            m.errors += 1

    # ------------------------------------------------------------------
    # 단계 판정
    # ------------------------------------------------------------------

    def evaluate_stage(self, stage: int) -> Dict:
        """현재 단계의 Gate 통과 여부를 판정한다.

        반환 딕셔너리 키:
            stage (int): 판정 단계.
            traffic_pct (int): 해당 단계 트래픽 비율.
            requests (int): 누적 요청 수.
            error_rate (float): 오류율.
            latency_p95 (float): P95 레이턴시 (ms).
            mean_reward (float): 보상 평균.
            gate_passed (bool): Gate 통과 여부.
            promoted (bool): 승격 가능 여부 (gate_passed 와 동일).
            fail_reasons (list): 실패 사유 목록.
        """
        self._ensure_stage_metrics(stage)
        m = self.state.stage_metrics[stage]
        cfg = self.config

        fail_reasons: List[str] = []

        # 최소 요청 수 미달
        if m.requests < cfg.min_requests_per_stage:
            fail_reasons.append(
                f"requests({m.requests}) < min({cfg.min_requests_per_stage})"
            )

        # 오류율 초과
        if m.error_rate > cfg.error_rate_threshold:
            fail_reasons.append(
                f"error_rate({m.error_rate:.3f}) > threshold({cfg.error_rate_threshold})"
            )

        # P95 레이턴시 초과
        if m.latency_p95 > cfg.latency_p95_threshold_ms:
            fail_reasons.append(
                f"latency_p95({m.latency_p95:.1f}ms) > threshold({cfg.latency_p95_threshold_ms}ms)"
            )

        # 보상 미달
        if m.mean_reward < cfg.reward_threshold:
            fail_reasons.append(
                f"mean_reward({m.mean_reward:.3f}) < threshold({cfg.reward_threshold})"
            )

        gate_passed = len(fail_reasons) == 0
        return {
            "stage": stage,
            "traffic_pct": STAGE_WEIGHTS[stage],
            "requests": m.requests,
            "error_rate": m.error_rate,
            "latency_p95": m.latency_p95,
            "mean_reward": m.mean_reward,
            "gate_passed": gate_passed,
            "promoted": gate_passed,
            "fail_reasons": fail_reasons,
        }

    # ------------------------------------------------------------------
    # 단계 전환
    # ------------------------------------------------------------------

    def advance(self) -> PromotionRecord:
        """현재 단계에서 다음 단계로 승격한다.

        Returns:
            PromotionRecord: 승격 기록.

        Raises:
            ValueError: 이미 최종 단계(100%)이거나 IN_PROGRESS가 아닌 경우.
        """
        if self.state.status != CanaryStatus.IN_PROGRESS:
            raise ValueError(
                f"advance() 호출 불가 — status={self.state.status!r}"
            )
        cur = self.state.current_stage
        if cur >= len(STAGE_WEIGHTS) - 1:
            raise ValueError(
                f"이미 최종 단계(STAGE_{cur})입니다. complete()를 호출하세요."
            )

        nxt = cur + 1
        record = PromotionRecord(
            from_stage=cur,
            to_stage=nxt,
            reason=f"Gate PASS at {STAGE_WEIGHTS[cur]}%",
            promoted=True,
        )
        self.state.promotion_records.append(record)
        self.state.total_promoted += 1
        self.state.current_stage = nxt
        self._ensure_stage_metrics(nxt)
        return record

    def complete(self) -> None:
        """최종 단계(100%) 완료 처리 (IN_PROGRESS → COMPLETED)."""
        self.state.status = CanaryStatus.COMPLETED

    def rollback(self, reason: str = "Gate FAIL") -> PromotionRecord:
        """현재 단계에서 롤백한다.

        Args:
            reason: 롤백 사유.

        Returns:
            PromotionRecord: 롤백 기록.
        """
        cur = self.state.current_stage
        record = PromotionRecord(
            from_stage=cur,
            to_stage=-1,
            reason=reason,
            promoted=False,
        )
        self.state.promotion_records.append(record)
        self.state.total_rolled_back += 1
        self.state.status = CanaryStatus.ROLLED_BACK
        return record

    # ------------------------------------------------------------------
    # 요약
    # ------------------------------------------------------------------

    def summary(self) -> Dict:
        """컨트롤러 현재 상태 요약을 반환한다.

        반환 딕셔너리 키:
            model_id (str): 모델 식별자.
            status (str): 현재 상태.
            current_stage (int): 현재 단계 (0~3).
            current_traffic_pct (int): 현재 트래픽 비율.
            total_promoted (int): 총 승격 횟수.
            total_rolled_back (int): 총 롤백 횟수.
            stage_count (int): 메트릭이 기록된 단계 수.
        """
        cur = self.state.current_stage
        return {
            "model_id": self.config.model_id,
            "status": self.state.status,
            "current_stage": cur,
            "current_traffic_pct": STAGE_WEIGHTS[cur],
            "total_promoted": self.state.total_promoted,
            "total_rolled_back": self.state.total_rolled_back,
            "stage_count": len(self.state.stage_metrics),
        }

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------

    def _ensure_stage_metrics(self, stage: int) -> None:
        if stage not in self.state.stage_metrics:
            self.state.stage_metrics[stage] = StageMetrics(stage=stage)
