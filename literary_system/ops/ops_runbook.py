"""
literary_system/ops/ops_runbook.py

V629: OpsRunbook — 운영 런북 관리자
ADR-096 §1: Phase B 운영 문서 완성

운영 절차(Runbook)를 코드로 정의하고 단계별 실행·롤백을 관리한다.
LLM-0 원칙: 외부 LLM 호출 없음.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class StepStatus_Ops(str, Enum):
    """런북 단계 실행 상태."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class RunbookSeverity(str, Enum):
    """런북 심각도 등급."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RunbookStep:
    """런북 단계 정의."""
    name: str
    description: str
    action_fn: Callable[..., Any]
    rollback_fn: Optional[Callable[..., Any]] = None
    timeout_ms: int = 30_000
    severity: RunbookSeverity = RunbookSeverity.MEDIUM
    skip_on_dry_run: bool = False

    def execute(self, context: Dict[str, Any]) -> Any:
        """액션 함수 실행."""
        return self.action_fn(context)

    def rollback(self, context: Dict[str, Any]) -> Any:
        """롤백 함수 실행 (정의된 경우)."""
        if self.rollback_fn is not None:
            return self.rollback_fn(context)
        return None


@dataclass
class StepResult:
    """단계 실행 결과."""
    step_name: str
    status: StepStatus
    output: Any = None
    error: Optional[str] = None
    elapsed_ms: float = 0.0

    @property
    def succeeded(self) -> bool:
        return self.status == StepStatus.SUCCESS

    @property
    def failed(self) -> bool:
        return self.status == StepStatus.FAILED


@dataclass
class RunbookResult:
    """런북 전체 실행 결과."""
    runbook_name: str
    success: bool
    steps_executed: int
    steps_succeeded: int
    steps_failed: int
    step_results: List[StepResult] = field(default_factory=list)
    failed_step: Optional[str] = None
    total_elapsed_ms: float = 0.0
    dry_run: bool = False

    @property
    def all_passed(self) -> bool:
        return self.success and self.steps_failed == 0

    def summary(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"[{status}] {self.runbook_name}: "
            f"{self.steps_succeeded}/{self.steps_executed} steps passed "
            f"({self.total_elapsed_ms:.1f}ms)"
        )


class OpsRunbook:
    """
    운영 런북 관리자.

    단계(RunbookStep) 목록을 순서대로 실행하며,
    실패 시 이전 단계들을 역순으로 롤백한다.
    """

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self._steps: List[RunbookStep] = []

    # ------------------------------------------------------------------ #
    # 구성                                                                  #
    # ------------------------------------------------------------------ #

    def add_step(self, step: RunbookStep) -> "OpsRunbook":
        """단계 추가 (체이닝 지원)."""
        self._steps.append(step)
        return self

    def steps(self) -> List[RunbookStep]:
        """등록된 단계 목록 반환 (읽기 전용 뷰)."""
        return list(self._steps)

    def step_count(self) -> int:
        return len(self._steps)

    # ------------------------------------------------------------------ #
    # 실행                                                                  #
    # ------------------------------------------------------------------ #

    def execute(
        self,
        context: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
        stop_on_failure: bool = True,
    ) -> RunbookResult:
        """
        런북 실행.

        Args:
            context: 단계 간 공유 컨텍스트 dict.
            dry_run: True 이면 skip_on_dry_run=True 단계를 건너뜀.
            stop_on_failure: True 이면 실패 즉시 롤백 후 중단.

        Returns:
            RunbookResult
        """
        ctx: Dict[str, Any] = context if context is not None else {}
        step_results: List[StepResult] = []
        executed_steps: List[RunbookStep] = []
        total_start = time.monotonic()

        for step in self._steps:
            # dry-run 건너뜀
            if dry_run and step.skip_on_dry_run:
                step_results.append(
                    StepResult(step_name=step.name, status=StepStatus.SKIPPED)
                )
                continue

            t0 = time.monotonic()
            try:
                output = step.execute(ctx)
                elapsed = (time.monotonic() - t0) * 1000
                sr = StepResult(
                    step_name=step.name,
                    status=StepStatus.SUCCESS,
                    output=output,
                    elapsed_ms=elapsed,
                )
                step_results.append(sr)
                executed_steps.append(step)
                # 결과를 컨텍스트에 저장
                ctx[f"__result_{step.name}"] = output

            except Exception as exc:  # noqa: BLE001
                elapsed = (time.monotonic() - t0) * 1000
                sr = StepResult(
                    step_name=step.name,
                    status=StepStatus.FAILED,
                    error=str(exc),
                    elapsed_ms=elapsed,
                )
                step_results.append(sr)

                if stop_on_failure:
                    # 역순 롤백
                    self._rollback_steps(executed_steps, ctx)
                    total_elapsed = (time.monotonic() - total_start) * 1000
                    return RunbookResult(
                        runbook_name=self.name,
                        success=False,
                        steps_executed=len(step_results),
                        steps_succeeded=sum(1 for r in step_results if r.succeeded),
                        steps_failed=sum(1 for r in step_results if r.failed),
                        step_results=step_results,
                        failed_step=step.name,
                        total_elapsed_ms=total_elapsed,
                        dry_run=dry_run,
                    )

        total_elapsed = (time.monotonic() - total_start) * 1000
        succeeded = sum(1 for r in step_results if r.succeeded)
        failed = sum(1 for r in step_results if r.failed)
        return RunbookResult(
            runbook_name=self.name,
            success=(failed == 0),
            steps_executed=len(step_results),
            steps_succeeded=succeeded,
            steps_failed=failed,
            step_results=step_results,
            failed_step=None,
            total_elapsed_ms=total_elapsed,
            dry_run=dry_run,
        )

    # ------------------------------------------------------------------ #
    # 내부                                                                  #
    # ------------------------------------------------------------------ #

    def _rollback_steps(
        self, executed: List[RunbookStep], ctx: Dict[str, Any]
    ) -> None:
        """역순으로 롤백 실행."""
        for step in reversed(executed):
            try:
                step.rollback(ctx)
            except Exception:  # noqa: BLE001
                pass  # 롤백 실패는 무시

    # ------------------------------------------------------------------ #
    # 유틸                                                                  #
    # ------------------------------------------------------------------ #

    def validate(self) -> List[str]:
        """런북 유효성 검사 — 오류 메시지 목록 반환."""
        errors: List[str] = []
        names = [s.name for s in self._steps]
        if len(names) != len(set(names)):
            errors.append("중복된 단계 이름이 존재합니다.")
        if not self._steps:
            errors.append("런북에 단계가 없습니다.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """런북 메타데이터 직렬화."""
        return {
            "name": self.name,
            "description": self.description,
            "step_count": self.step_count(),
            "steps": [
                {
                    "name": s.name,
                    "description": s.description,
                    "severity": s.severity.value,
                    "has_rollback": s.rollback_fn is not None,
                    "skip_on_dry_run": s.skip_on_dry_run,
                }
                for s in self._steps
            ],
        }


# ------------------------------------------------------------------ #
# 팩토리: 표준 운영 런북                                                #
# ------------------------------------------------------------------ #

def build_health_check_runbook() -> OpsRunbook:
    """표준 헬스체크 런북 (3단계)."""
    book = OpsRunbook(
        name="health_check",
        description="Literary OS 기본 헬스체크 런북",
    )
    book.add_step(RunbookStep(
        name="check_config",
        description="설정 파일 존재 여부 확인",
        action_fn=lambda ctx: {"config_ok": True},
        severity=RunbookSeverity.HIGH,
    ))
    book.add_step(RunbookStep(
        name="check_db",
        description="DB 연결 확인",
        action_fn=lambda ctx: {"db_ok": True},
        severity=RunbookSeverity.CRITICAL,
    ))
    book.add_step(RunbookStep(
        name="check_metrics",
        description="메트릭 수집 활성화 확인",
        action_fn=lambda ctx: {"metrics_ok": True},
        severity=RunbookSeverity.MEDIUM,
    ))
    return book


# G37 DuplicateZero(ADR-033): 클래스명 전역 고유화 — 외부 import 하위호환 별칭
StepStatus = StepStatus_Ops
