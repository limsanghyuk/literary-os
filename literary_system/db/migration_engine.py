"""literary_system.db.migration_engine — LOSDB Phase B: MigrationEngine

MigrationEngine은 복수의 BaseMigrationAdapter를 조율하는 통합 오케스트레이터입니다.
SQL(REAL) + Graph(Mock) + Vector(Mock) 어댑터를 단일 진입점으로 실행·롤백합니다.

ADR-042 | V583 | L1
LLM-0 원칙: 외부 LLM 호출 없음
G32 준수: print() 없음, 모든 로그는 logging 모듈 사용
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from literary_system.db.migration_manager import BaseMigrationAdapter, Migration

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# MigrationPlan
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MigrationPlan:
    """마이그레이션 실행 계획.

    Attributes:
        plan_id: 계획 고유 식별자
        migrations: 순서대로 실행할 Migration 목록
        target_adapters: 적용할 어댑터 키 목록 (예: ["sql", "graph"])
        description: 계획 설명
    """
    plan_id: str
    migrations: List[Migration]
    target_adapters: List[str]
    description: str = ""

    def __post_init__(self) -> None:
        if not self.plan_id:
            raise ValueError("plan_id는 빈 문자열일 수 없습니다.")
        if not self.migrations:
            raise ValueError("migrations 목록이 비어있습니다.")
        if not self.target_adapters:
            raise ValueError("target_adapters 목록이 비어있습니다.")


# ─────────────────────────────────────────────────────────────────────────────
# MigrationExecutionRecord
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MigrationExecutionRecord:
    """마이그레이션 실행 결과 감사 레코드.

    Attributes:
        plan_id: 실행된 계획 ID
        executed_at: ISO 8601 실행 시각 (UTC)
        results: 어댑터별 단위 실행 결과 목록
        success: 전체 성공 여부
        rolled_back: 롤백 체이닝 발생 여부
        error: 실패 원인 (성공 시 None)
    """
    plan_id: str
    executed_at: str
    results: List[Dict] = field(default_factory=list)
    success: bool = False
    rolled_back: bool = False
    error: Optional[str] = None

    def to_json(self) -> str:
        """JSON 문자열로 직렬화합니다."""
        return json.dumps(
            {
                "plan_id": self.plan_id,
                "executed_at": self.executed_at,
                "results": self.results,
                "success": self.success,
                "rolled_back": self.rolled_back,
                "error": self.error,
            },
            ensure_ascii=False,
            indent=2,
        )

    @classmethod
    def from_json(cls, data: str) -> "MigrationExecutionRecord":
        """JSON 문자열에서 복원합니다."""
        d = json.loads(data)
        return cls(
            plan_id=d["plan_id"],
            executed_at=d["executed_at"],
            results=d.get("results", []),
            success=d.get("success", False),
            rolled_back=d.get("rolled_back", False),
            error=d.get("error"),
        )


# ─────────────────────────────────────────────────────────────────────────────
# MigrationEngine
# ─────────────────────────────────────────────────────────────────────────────

class MigrationEngine:
    """LOSDB 통합 마이그레이션 오케스트레이터.

    복수의 BaseMigrationAdapter를 받아 MigrationPlan에 따라 순차 실행하고,
    실패 시 역순으로 롤백 체이닝을 수행합니다.

    Example::

        from literary_system.db import SQLiteRealAdapter, BackendType
        from literary_system.db.migration_engine import MigrationEngine, MigrationPlan

        sql_adapter = SQLiteRealAdapter(connection_url="sqlite:///:memory:")
        engine = MigrationEngine(adapters={"sql": sql_adapter})
        plan = MigrationPlan(
            plan_id="plan_001",
            migrations=[migration],
            target_adapters=["sql"],
        )
        record = engine.execute(plan)
        assert record.success
    """

    def __init__(self, adapters: Dict[str, BaseMigrationAdapter]) -> None:
        """MigrationEngine 초기화.

        Args:
            adapters: 어댑터 키 → 어댑터 인스턴스 매핑
                      (예: {"sql": SQLiteRealAdapter(), "graph": MockAdapter()})
        """
        if not adapters:
            raise ValueError("adapters 딕셔너리가 비어있습니다.")
        self._adapters = adapters
        logger.debug("MigrationEngine 초기화 완료: 어댑터=%s", list(adapters.keys()))

    # ── 공개 API ────────────────────────────────────────────────────────────

    def execute(self, plan: MigrationPlan) -> MigrationExecutionRecord:
        """MigrationPlan을 실행합니다.

        모든 target_adapters에 대해 migrations 목록을 순서대로 적용합니다.
        하나라도 실패하면 즉시 중단하고 이미 성공한 항목을 역순 롤백합니다.

        Args:
            plan: 실행할 마이그레이션 계획

        Returns:
            MigrationExecutionRecord: 실행 결과 감사 레코드
        """
        executed_at = datetime.now(tz=timezone.utc).isoformat()
        results: List[Dict] = []
        executed_stack: List[tuple] = []  # (adapter_key, migration) — 롤백용

        logger.info("MigrationEngine.execute 시작: plan_id=%s", plan.plan_id)

        for migration in plan.migrations:
            for adapter_key in plan.target_adapters:
                adapter = self._resolve_adapter(adapter_key)
                if adapter is None:
                    error_msg = f"어댑터 키 '{adapter_key}'를 찾을 수 없습니다."
                    logger.error(error_msg)
                    # 롤백 체이닝
                    rb_results = self._rollback_chain(executed_stack)
                    results.extend(rb_results)
                    return MigrationExecutionRecord(
                        plan_id=plan.plan_id,
                        executed_at=executed_at,
                        results=results,
                        success=False,
                        rolled_back=True,
                        error=error_msg,
                    )

                try:
                    ok = adapter.apply(migration)
                except Exception as exc:  # noqa: BLE001
                    ok = False
                    logger.exception(
                        "apply 예외: adapter=%s migration=%s",
                        adapter_key,
                        migration.migration_id,
                    )
                    results.append({
                        "adapter": adapter_key,
                        "migration_id": migration.migration_id,
                        "ok": False,
                        "error": str(exc),
                    })
                    rb_results = self._rollback_chain(executed_stack)
                    results.extend(rb_results)
                    return MigrationExecutionRecord(
                        plan_id=plan.plan_id,
                        executed_at=executed_at,
                        results=results,
                        success=False,
                        rolled_back=True,
                        error=str(exc),
                    )

                result_entry = {
                    "adapter": adapter_key,
                    "migration_id": migration.migration_id,
                    "ok": ok,
                }
                results.append(result_entry)

                if ok:
                    executed_stack.append((adapter_key, migration))
                    logger.debug(
                        "apply 성공: adapter=%s migration=%s",
                        adapter_key,
                        migration.migration_id,
                    )
                else:
                    error_msg = (
                        f"apply 실패: adapter={adapter_key} "
                        f"migration={migration.migration_id}"
                    )
                    logger.warning(error_msg)
                    rb_results = self._rollback_chain(executed_stack)
                    results.extend(rb_results)
                    return MigrationExecutionRecord(
                        plan_id=plan.plan_id,
                        executed_at=executed_at,
                        results=results,
                        success=False,
                        rolled_back=True,
                        error=error_msg,
                    )

        logger.info("MigrationEngine.execute 완료: plan_id=%s", plan.plan_id)
        return MigrationExecutionRecord(
            plan_id=plan.plan_id,
            executed_at=executed_at,
            results=results,
            success=True,
            rolled_back=False,
            error=None,
        )

    def rollback_plan(self, plan: MigrationPlan) -> MigrationExecutionRecord:
        """MigrationPlan을 역순으로 롤백합니다.

        Args:
            plan: 롤백할 마이그레이션 계획 (migrations 역순으로 처리)

        Returns:
            MigrationExecutionRecord: 롤백 결과 감사 레코드
        """
        executed_at = datetime.now(tz=timezone.utc).isoformat()
        results: List[Dict] = []

        logger.info("MigrationEngine.rollback_plan 시작: plan_id=%s", plan.plan_id)

        for migration in reversed(plan.migrations):
            for adapter_key in reversed(plan.target_adapters):
                adapter = self._resolve_adapter(adapter_key)
                if adapter is None:
                    results.append({
                        "adapter": adapter_key,
                        "migration_id": migration.migration_id,
                        "rollback": False,
                        "error": f"어댑터 '{adapter_key}' 없음",
                    })
                    continue
                try:
                    ok = adapter.rollback(migration)
                except Exception as exc:  # noqa: BLE001
                    ok = False
                    logger.exception("rollback 예외: adapter=%s", adapter_key)
                    results.append({
                        "adapter": adapter_key,
                        "migration_id": migration.migration_id,
                        "rollback": False,
                        "error": str(exc),
                    })
                    continue

                results.append({
                    "adapter": adapter_key,
                    "migration_id": migration.migration_id,
                    "rollback": ok,
                })
                logger.debug("rollback: adapter=%s ok=%s", adapter_key, ok)

        all_ok = all(r.get("rollback", False) for r in results)
        return MigrationExecutionRecord(
            plan_id=plan.plan_id,
            executed_at=executed_at,
            results=results,
            success=all_ok,
            rolled_back=True,
            error=None if all_ok else "일부 롤백 실패",
        )

    def adapter_keys(self) -> List[str]:
        """등록된 어댑터 키 목록을 반환합니다."""
        return list(self._adapters.keys())

    # ── 내부 메서드 ──────────────────────────────────────────────────────────

    def _resolve_adapter(self, key: str) -> Optional[BaseMigrationAdapter]:
        """어댑터 키로 인스턴스를 조회합니다."""
        return self._adapters.get(key)

    def _rollback_chain(self, executed_stack: List[tuple]) -> List[Dict]:
        """실행 스택을 역순으로 롤백합니다. 결과 목록을 반환합니다."""
        results = []
        for adapter_key, migration in reversed(executed_stack):
            adapter = self._resolve_adapter(adapter_key)
            if adapter is None:
                results.append({
                    "adapter": adapter_key,
                    "migration_id": migration.migration_id,
                    "rollback_chain": False,
                    "error": "어댑터 없음",
                })
                continue
            try:
                ok = adapter.rollback(migration)
            except Exception as exc:  # noqa: BLE001
                ok = False
                logger.exception("rollback_chain 예외: adapter=%s", adapter_key)
                results.append({
                    "adapter": adapter_key,
                    "migration_id": migration.migration_id,
                    "rollback_chain": False,
                    "error": str(exc),
                })
                continue
            results.append({
                "adapter": adapter_key,
                "migration_id": migration.migration_id,
                "rollback_chain": ok,
            })
            logger.debug("rollback_chain: adapter=%s ok=%s", adapter_key, ok)
        return results
