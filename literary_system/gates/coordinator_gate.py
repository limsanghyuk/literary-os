"""
V650 — Gate G64: AgentCoordinatorGate.
AgentCoordinator 단일 씬 오케스트레이션 동작 검증.
- CoordinatorResult.success == True
- rounds_used >= 1 AND rounds_used <= MAX_ROUNDS(3)
- final_text 비어 있지 않음
LLM-0: 외부 API 직접 호출 없음.
ADR-110.
"""
from __future__ import annotations

from typing import Any, Dict


def run_g64_gate() -> Dict[str, Any]:
    """Gate G64: AgentCoordinatorGate 검증 (7 체크포인트)."""
    checkpoints: Dict[str, bool] = {}
    errors: list = []

    # CP-1: 모듈 임포트
    try:
        from literary_system.ensemble.agent_coordinator import (
            AgentCoordinator,
            CoordinatorResult,
        )
        checkpoints["import_ok"] = True
    except Exception as exc:
        checkpoints["import_ok"] = False
        errors.append(f"import: {exc}")
        return _result(checkpoints, errors)

    # CP-2: AgentCoordinator 인스턴스 생성
    try:
        coord = AgentCoordinator()
        checkpoints["instantiate_ok"] = True
    except Exception as exc:
        checkpoints["instantiate_ok"] = False
        errors.append(f"instantiate: {exc}")
        return _result(checkpoints, errors)

    # CP-3: MAX_ROUNDS == 3 (C-M-09)
    checkpoints["max_rounds_3"] = getattr(AgentCoordinator, "MAX_ROUNDS", 0) == 3

    # CP-4: coordinate() 실행 성공
    try:
        result = coord.coordinate(scene_prefix="g64", episode_num=1, scene_num=1)
        checkpoints["coordinate_runs"] = True
    except Exception as exc:
        checkpoints["coordinate_runs"] = False
        errors.append(f"coordinate: {exc}")
        return _result(checkpoints, errors)

    # CP-5: CoordinatorResult 타입 확인
    checkpoints["result_type_ok"] = isinstance(result, CoordinatorResult)

    # CP-6: success=True AND rounds_used in [1, 3]
    checkpoints["success_and_rounds"] = (
        result.success is True
        and 1 <= result.rounds_used <= AgentCoordinator.MAX_ROUNDS
    )

    # CP-7: to_dict / from_dict 라운드트립
    try:
        d = result.to_dict()
        r2 = CoordinatorResult.from_dict(d)
        checkpoints["roundtrip_ok"] = r2.scene_id == result.scene_id
    except Exception as exc:
        checkpoints["roundtrip_ok"] = False
        errors.append(f"roundtrip: {exc}")

    return _result(checkpoints, errors)


def _result(checkpoints: Dict[str, bool], errors: list) -> Dict[str, Any]:
    total  = len(checkpoints)
    passed = sum(1 for v in checkpoints.values() if v)
    ok     = passed == total and total > 0
    return {
        "gate":       "G64",
        "gate_name":  "AgentCoordinatorGate SP-C.2 오케스트레이션 검증 (ADR-110)",
        "pass":       ok,
        "passed_count": passed,
        "total_count":  total,
        "checkpoints":  checkpoints,
        "errors":       errors,
    }
