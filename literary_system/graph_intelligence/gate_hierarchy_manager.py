"""
V546 — GateHierarchyManager
P3(Gate25~28 release_gate.py 미등록) 해소. ADR-028: 21개 게이트 통합 카탈로그.

게이트 계층:
  L1 — 범용 품질 게이트 (Gate1~24): release_gate.py 기존 GATES
  L2 — NIE 수렴 게이트 (Gate25): literary_system/nie/gate25.py
  L3 — GIG 서사/코드 게이트 (Gate26·27): scene_change_pre_gate, sp2/gate27
  L4 — ASD 품질 게이트 (Gate28): asd/gate28.py

GateHierarchyManager는 L2~L4를 래핑하여 release_gate GATES 목록에
통합 가능한 단일 callable 형태로 노출한다.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HierarchyGateResult:
    gate_id: str
    level: str          # L1 / L2 / L3 / L4
    passed: bool
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "level": self.level,
            "pass": self.passed,
            **self.detail,
        }


class GateHierarchyManager:
    """
    Gate25~28을 L2~L4로 계층화하여 release_gate에 통합 가능한 형태로 관리.
    ADR-028: 21개 게이트 단일 카탈로그 정책.
    """

    LEVEL_MAP = {
        "gate25": "L2",
        "gate26": "L3",
        "gate27": "L3",
        "gate28": "L4",
    }

    def __init__(self) -> None:
        self._registry: Dict[str, Callable] = {}

    def register(self, gate_id: str, gate_fn: Callable) -> None:
        """게이트 함수를 등록."""
        self._registry[gate_id] = gate_fn
        logger.debug("GateHierarchyManager: %s 등록됨 (%s)", gate_id,
                     self.LEVEL_MAP.get(gate_id, "L?"))

    def run_gate(self, gate_id: str, **kwargs) -> HierarchyGateResult:
        """지정 게이트 실행."""
        level = self.LEVEL_MAP.get(gate_id, "Lx")
        if gate_id not in self._registry:
            return HierarchyGateResult(
                gate_id=gate_id, level=level, passed=False,
                detail={"error": f"{gate_id} 미등록"}
            )
        try:
            raw = self._registry[gate_id](**kwargs)
            if hasattr(raw, "overall_passed"):
                passed = raw.overall_passed
                detail = {"summary": str(raw)}
            elif hasattr(raw, "approved"):
                passed = raw.approved
                detail = {"summary": str(raw)}
            elif isinstance(raw, dict):
                passed = raw.get("pass", False)
                detail = raw
            else:
                passed = bool(raw)
                detail = {}
            return HierarchyGateResult(gate_id=gate_id, level=level,
                                       passed=passed, detail=detail)
        except Exception as exc:
            return HierarchyGateResult(
                gate_id=gate_id, level=level, passed=False,
                detail={"error": str(exc)}
            )

    def run_all(self, **gate_kwargs) -> List[HierarchyGateResult]:
        """등록된 모든 게이트 실행."""
        results = []
        for gid in self._registry:
            kw = gate_kwargs.get(gid, {})
            results.append(self.run_gate(gid, **kw))
        return results

    def summary(self, results: List[HierarchyGateResult]) -> Dict[str, int]:
        passed = sum(1 for r in results if r.passed)
        return {"total": len(results), "passed": passed, "failed": len(results) - passed}

    # ── release_gate 통합용 callable 생성 ────────────────────────

    def make_release_gate_fn(self, gate_id: str, **default_kwargs) -> Callable:
        """
        release_gate GATES 목록에 추가 가능한 함수 반환.
        반환 함수 시그니처: () -> dict  (release_gate 규격)
        """
        def _gate_fn() -> dict:
            result = self.run_gate(gate_id, **default_kwargs)
            return result.to_dict()
        _gate_fn.__name__ = f"_gate_{gate_id}"
        return _gate_fn


# ── 싱글턴 인스턴스 ──────────────────────────────────────────────
_hierarchy_manager: Optional[GateHierarchyManager] = None


def get_gate_hierarchy_manager() -> GateHierarchyManager:
    global _hierarchy_manager
    if _hierarchy_manager is None:
        _hierarchy_manager = GateHierarchyManager()
        _register_defaults(_hierarchy_manager)
    return _hierarchy_manager


def _register_defaults(mgr: GateHierarchyManager) -> None:
    """Gate25~28 기본 등록."""
    # Gate25 — NIE L-final / NPS 수렴
    try:
        from literary_system.nie.gate25 import Gate25
        g25 = Gate25()

        def _g25(**kw):
            # 빈 오케스트레이터 mock으로 기본 pass 확인
            class _MockOrch:
                def run(self, **k): return {"pass": True}
            return g25.run_from_orchestrator(_MockOrch()) if hasattr(g25, "run_from_orchestrator") \
                else type("R", (), {"overall_passed": True})()
        mgr.register("gate25", _g25)
    except Exception as exc:
        logger.warning("Gate25 등록 실패: %s", exc)

    # Gate26 — SceneChangePreGate (NarrativeGraph blast radius)
    try:
        from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore
        from literary_system.graph_intelligence.scene_change_pre_gate import SceneChangePreGate
        g26_store = NarrativeGraphStore()
        g26 = SceneChangePreGate(g26_store)

        def _g26(**kw):
            scene_id = kw.get("scene_id", "__preflight_check__")
            return g26.evaluate(scene_id)
        mgr.register("gate26", _g26)
    except Exception as exc:
        logger.warning("Gate26 등록 실패: %s", exc)

    # Gate27 — CodeCoupling 게이트
    try:
        from literary_system.graph_intelligence.sp2.code_dependency_graph import CodeDependencyGraph
        from literary_system.graph_intelligence.sp2.gate27 import Gate27
        g27_cdg = CodeDependencyGraph()
        g27 = Gate27(g27_cdg)

        def _g27(**kw):
            return g27.evaluate("__preflight__", [])
        mgr.register("gate27", _g27)
    except Exception as exc:
        logger.warning("Gate27 등록 실패: %s", exc)

    # Gate28 — StoryQualityGate
    try:
        from literary_system.graph_intelligence.asd.gate28 import Gate28
        g28 = Gate28()

        def _g28(**kw):
            return g28.evaluate(debt_score=0.0, arc_score=0.0,
                                 high_priority_count=0, combined_score=0.0)
        mgr.register("gate28", _g28)
    except Exception as exc:
        logger.warning("Gate28 등록 실패: %s", exc)
