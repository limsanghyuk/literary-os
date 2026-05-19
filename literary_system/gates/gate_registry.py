"""
V578 — GATE_REGISTRY
ADR-032: 릴리즈 게이트 단일 소스 레지스트리.

설계 원칙:
  - 모든 게이트 메타데이터의 단일 정보 소스 (Single Source of Truth)
  - gate_id / name / fn / adr_ref / version_added / layer 5개 필드 표준화
  - release_gate.py의 GATES 튜플을 GateRegistryEntry 데이터클래스로 승격
  - CI에서 `python -m literary_system.gates.gate_registry --validate` 로 레지스트리 검증 가능

계층 정의 (ADR-028 Gate Hierarchy):
  L0 = 핵심 불변 원칙 (LLM-0 등)
  L1 = 아키텍처 계약
  L2 = 모듈 생존
  L3 = 통합 무결성
  L4 = 품질 기준

사용 예시:
    from literary_system.gates.gate_registry import GATE_REGISTRY, get_gate, list_gates
    entry = get_gate("llm_zero")
    # entry.name, entry.layer 로 접근
"""
from __future__ import annotations
import logging

import sys

_logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# GateRegistryEntry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GateRegistryEntry:
    """
    단일 릴리즈 게이트의 메타데이터 레코드.

    Fields
    ------
    gate_id : str
        게이트 고유 식별자 (release_gate.py GATES 튜플의 첫 번째 원소)
    name : str
        게이트 표시 이름
    fn : Callable[[], dict]
        게이트 실행 함수 (lazy import로 순환 방지)
    adr_ref : str
        관련 ADR 참조 (예: "ADR-031", "ADR-035") — 없으면 ""
    version_added : str
        해당 게이트가 추가된 버전 (예: "V411", "V577")
    layer : str
        게이트 계층 (L0/L1/L2/L3/L4)
    """
    gate_id: str
    name: str
    fn: Callable[[], dict]
    adr_ref: str = ""
    version_added: str = ""
    layer: str = "L2"

    def run(self) -> dict:
        """게이트 실행 — fn() 위임."""
        return self.fn()


# ---------------------------------------------------------------------------
# GATE_REGISTRY 구축 헬퍼
# ---------------------------------------------------------------------------

def _build_registry() -> Dict[str, GateRegistryEntry]:
    """
    release_gate.py의 GATES 튜플 목록에서 레지스트리를 구축.
    순환 임포트 방지를 위해 지연 임포트 사용.
    """
    from literary_system.gates.release_gate import GATES

    # gate_id → (adr_ref, version_added, layer) 보충 메타데이터
    _META: Dict[str, tuple] = {
        # gate_id: (adr_ref, version_added, layer)
        "llm_zero":                       ("ADR-001",  "V411",  "L0"),
        "arc_integrity":                  ("ADR-002",  "V380",  "L1"),
        "reveal_budget":                  ("ADR-003",  "V380",  "L1"),
        "knowledge_leakage":              ("ADR-004",  "V380",  "L1"),
        "packaging":                      ("ADR-005",  "V381",  "L1"),
        "pipeline_survival":              ("ADR-006",  "V382",  "L2"),
        "drse_quality":                   ("ADR-007",  "V403",  "L3"),
        "llm_adapter_contract":           ("ADR-008",  "V411",  "L2"),
        "studio_api_contract":            ("ADR-009",  "V430",  "L2"),
        "rag_stack_survival":             ("ADR-007",  "V437",  "L2"),
        "slm_subphase3_survival":         ("ADR-008",  "V443",  "L2"),
        "quality_subphase4_survival":     ("ADR-009",  "V447",  "L2"),
        "live_adapter_sp1":               ("ADR-010",  "V455",  "L3"),
        "sp2_tenant_survival":            ("ADR-011",  "V461",  "L2"),
        "subphase1_adapter_survival":     ("ADR-008",  "V436",  "L2"),
        "sp3_compliance_sovereignty":     ("ADR-018",  "V461",  "L3"),
        "sp4_finetune_lora_poc":          ("ADR-019",  "V473",  "L3"),
        "sp5_ops_survival":               ("ADR-020",  "V479",  "L2"),
        "scene_pipeline_survival":        ("ADR-021",  "V546",  "L3"),
        "drama_generator_survival":       ("ADR-022",  "V546",  "L3"),
        "rag_sp2_integration":            ("ADR-007",  "V546",  "L3"),
        "slm_sp3_integration":            ("ADR-008",  "V546",  "L3"),
        "nie_convergence_gate25":         ("ADR-028",  "V546",  "L2"),
        "narrative_blast_gate26":         ("ADR-028",  "V546",  "L3"),
        "code_coupling_gate27":           ("ADR-028",  "V546",  "L3"),
        "story_quality_gate28":           ("ADR-026",  "V546",  "L4"),
        "llm0_static_analysis":           ("ADR-031",  "V548",  "L0"),
        "pne_convergence_gate29":         ("ADR-029",  "V555",  "L2"),
        "corpus_quality_gate30":          ("ADR-030",  "V561",  "L2"),
        "multiwork_gate31":               ("ADR-027",  "V571",  "L3"),
        "logging_discipline_g32":         ("ADR-034",  "V575",  "L1"),
        "schema_roundtrip_g33":           ("ADR-034",  "V576",  "L1"),
        "auth_regression_g34":            ("ADR-034",  "V576",  "L0"),
        "adapter_canonical_g35":          ("ADR-035",  "V577",  "L2"),
        "gate_registry_g36":              ("ADR-032",  "V578",  "L1"),
        "duplicate_zero_g37":             ("ADR-033",  "V579",  "L1"),
    }

    registry: Dict[str, GateRegistryEntry] = {}
    for gate_id, gate_name, gate_fn in GATES:
        meta = _META.get(gate_id, ("", "", "L2"))
        registry[gate_id] = GateRegistryEntry(
            gate_id=gate_id,
            name=gate_name,
            fn=gate_fn,
            adr_ref=meta[0],
            version_added=meta[1],
            layer=meta[2],
        )
    return registry


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

# 모듈 로드 시 레지스트리 구축 (지연 임포트로 순환 방지)
GATE_REGISTRY: Dict[str, GateRegistryEntry] = _build_registry()


def get_gate(gate_id: str) -> Optional[GateRegistryEntry]:
    """gate_id로 게이트 항목 조회. 없으면 None."""
    return GATE_REGISTRY.get(gate_id)


def list_gates(layer: str = "") -> List[GateRegistryEntry]:
    """
    레지스트리의 모든 게이트 목록 반환.
    layer 지정 시 해당 계층만 필터링.
    """
    gates = list(GATE_REGISTRY.values())
    if layer:
        gates = [g for g in gates if g.layer == layer]
    return gates


def run_all_gates() -> Dict[str, dict]:
    """
    레지스트리의 모든 게이트 실행 후 결과 반환.
    release_gate.run_release_gate()와 동일한 실행이지만 레지스트리 경유.
    """
    import traceback
    results = {}
    for gate_id, entry in GATE_REGISTRY.items():
        try:
            result = entry.run()
            results[gate_id] = {
                "gate_name": entry.name,
                "adr_ref": entry.adr_ref,
                "version_added": entry.version_added,
                "layer": entry.layer,
                **result,
            }
        except Exception as exc:
            results[gate_id] = {
                "gate_name": entry.name,
                "pass": False,
                "error": traceback.format_exc(),
            }
    return results


def validate_registry() -> dict:
    """
    레지스트리 무결성 검증 (CI 진입점).

    검증 항목:
      1. 모든 gate_id가 release_gate.GATES와 1:1 매핑
      2. 모든 fn이 callable
      3. layer가 L0/L1/L2/L3/L4 중 하나
      4. gate_id 중복 없음
    """
    errors = []
    valid_layers = {"L0", "L1", "L2", "L3", "L4"}

    from literary_system.gates.release_gate import GATES
    registry_ids = set(GATE_REGISTRY.keys())
    gates_ids = {g[0] for g in GATES}

    # 1:1 매핑 확인
    only_in_registry = registry_ids - gates_ids
    only_in_gates = gates_ids - registry_ids
    if only_in_registry:
        errors.append(f"레지스트리에만 있는 gate_id: {only_in_registry}")
    if only_in_gates:
        errors.append(f"GATES에만 있는 gate_id: {only_in_gates}")

    # callable 확인
    for gate_id, entry in GATE_REGISTRY.items():
        if not callable(entry.fn):
            errors.append(f"{gate_id}: fn이 callable이 아님")

    # layer 확인
    for gate_id, entry in GATE_REGISTRY.items():
        if entry.layer not in valid_layers:
            errors.append(f"{gate_id}: 유효하지 않은 layer '{entry.layer}'")

    passed = len(errors) == 0
    return {
        "pass": passed,
        "total_gates": len(GATE_REGISTRY),
        "errors": errors,
        "details": f"GateRegistry 검증 {'PASS' if passed else 'FAIL'} — {len(GATE_REGISTRY)}개 게이트",
    }


# ---------------------------------------------------------------------------
# CLI 진입점
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--validate" in sys.argv:
        result = validate_registry()
        _logger.info("%s", result["details"])
        if not result["pass"]:
            for err in result["errors"]:
                _logger.error("  ERROR: %s", err)
            sys.exit(1)
        sys.exit(0)
    elif "--list" in sys.argv:
        for entry in list_gates():
            _logger.info("[%s] %-40s %-10s %s", entry.layer, entry.gate_id, entry.adr_ref, entry.version_added)
    else:
        _logger.info("Usage: python -m literary_system.gates.gate_registry --validate | --list")
