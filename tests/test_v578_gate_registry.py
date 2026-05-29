"""
V578 — test_v578_gate_registry.py
ADR-032: GATE_REGISTRY 단일 소스 + Gate G36 검증

TC-01~05: GateRegistryEntry 데이터클래스
TC-06~10: GATE_REGISTRY 구조 검증
TC-11~13: 공개 API (get_gate, list_gates)
TC-14~16: validate_registry() CI 검증
TC-17~19: Gate G36 GateRegistry
TC-20~22: run_all_gates() 통합
TC-23~25: tools/extract_adr.py ADR 자동 추출
"""
from __future__ import annotations

import pytest
from pathlib import Path


# ══════════════════════════════════════════════════════════════════
# TC-01~05: GateRegistryEntry 데이터클래스
# ══════════════════════════════════════════════════════════════════

class TestGateRegistryEntry:
    """TC-01~05: GateRegistryEntry 타입 검증."""

    def test_01_import_gate_registry_entry(self):
        """TC-01: GateRegistryEntry 임포트 가능."""
        from literary_system.gates.gate_registry import GateRegistryEntry
        assert GateRegistryEntry is not None

    def test_02_entry_is_frozen_dataclass(self):
        """TC-02: GateRegistryEntry는 불변(frozen) 데이터클래스."""
        from literary_system.gates.gate_registry import GateRegistryEntry
        entry = GateRegistryEntry(
            gate_id="test", name="Test Gate",
            fn=lambda: {"pass": True}, adr_ref="ADR-001",
            version_added="V578", layer="L1",
        )
        with pytest.raises((AttributeError, TypeError)):
            entry.gate_id = "modified"  # type: ignore

    def test_03_entry_run_delegates_to_fn(self):
        """TC-03: entry.run() → fn() 결과 반환."""
        from literary_system.gates.gate_registry import GateRegistryEntry
        entry = GateRegistryEntry(
            gate_id="run_test", name="Run Test",
            fn=lambda: {"pass": True, "details": "ok"},
        )
        result = entry.run()
        assert result["pass"] is True
        assert result["details"] == "ok"

    def test_04_entry_defaults(self):
        """TC-04: 기본값 — adr_ref='', version_added='', layer='L2'."""
        from literary_system.gates.gate_registry import GateRegistryEntry
        entry = GateRegistryEntry(gate_id="d", name="D", fn=lambda: {})
        assert entry.adr_ref == ""
        assert entry.version_added == ""
        assert entry.layer == "L2"

    def test_05_entry_fields_accessible(self):
        """TC-05: 5개 필드 접근 가능."""
        from literary_system.gates.gate_registry import GateRegistryEntry
        fn = lambda: {}
        entry = GateRegistryEntry(
            gate_id="g", name="G Gate", fn=fn,
            adr_ref="ADR-032", version_added="V578", layer="L3",
        )
        assert entry.gate_id == "g"
        assert entry.name == "G Gate"
        assert entry.fn is fn
        assert entry.adr_ref == "ADR-032"
        assert entry.version_added == "V578"
        assert entry.layer == "L3"


# ══════════════════════════════════════════════════════════════════
# TC-06~10: GATE_REGISTRY 구조 검증
# ══════════════════════════════════════════════════════════════════

class TestGateRegistryStructure:
    """TC-06~10: GATE_REGISTRY dict 구조 검증."""

    def test_06_gate_registry_is_dict(self):
        """TC-06: GATE_REGISTRY가 dict 타입."""
        from literary_system.gates.gate_registry import GATE_REGISTRY
        assert isinstance(GATE_REGISTRY, dict)

    def test_07_registry_size_matches_gates(self):
        """TC-07: GATE_REGISTRY 크기 == GATES 크기."""
        from literary_system.gates.gate_registry import GATE_REGISTRY
        from literary_system.gates.release_gate import GATES
        assert len(GATE_REGISTRY) == len(GATES)

    def test_08_registry_keys_match_gates_ids(self):
        """TC-08: GATE_REGISTRY 키가 GATES gate_id와 1:1 매핑."""
        from literary_system.gates.gate_registry import GATE_REGISTRY
        from literary_system.gates.release_gate import GATES
        registry_ids = set(GATE_REGISTRY.keys())
        gates_ids = {g[0] for g in GATES}
        assert registry_ids == gates_ids

    def test_09_all_entries_are_gate_registry_entry(self):
        """TC-09: 모든 값이 GateRegistryEntry 인스턴스."""
        from literary_system.gates.gate_registry import GATE_REGISTRY, GateRegistryEntry
        for gid, entry in GATE_REGISTRY.items():
            assert isinstance(entry, GateRegistryEntry), f"{gid}: {type(entry)}"

    def test_10_all_layers_valid(self):
        """TC-10: 모든 layer가 L0/L1/L2/L3/L4 중 하나."""
        from literary_system.gates.gate_registry import GATE_REGISTRY
        valid = {"L0", "L1", "L2", "L3", "L4"}
        for gid, entry in GATE_REGISTRY.items():
            assert entry.layer in valid, f"{gid}: layer='{entry.layer}'"


# ══════════════════════════════════════════════════════════════════
# TC-11~13: 공개 API
# ══════════════════════════════════════════════════════════════════

class TestGateRegistryPublicAPI:
    """TC-11~13: get_gate(), list_gates() API 검증."""

    def test_11_get_gate_returns_entry(self):
        """TC-11: get_gate('llm_zero') → GateRegistryEntry 반환."""
        from literary_system.gates.gate_registry import get_gate, GateRegistryEntry
        entry = get_gate("llm_zero")
        assert isinstance(entry, GateRegistryEntry)
        assert entry.gate_id == "llm_zero"

    def test_12_get_gate_returns_none_for_unknown(self):
        """TC-12: get_gate('unknown') → None."""
        from literary_system.gates.gate_registry import get_gate
        assert get_gate("nonexistent_gate_id_xyz") is None

    def test_13_list_gates_layer_filter(self):
        """TC-13: list_gates(layer='L0') → L0 게이트만 반환."""
        from literary_system.gates.gate_registry import list_gates
        l0_gates = list_gates(layer="L0")
        assert len(l0_gates) >= 1
        for g in l0_gates:
            assert g.layer == "L0"
        # llm_zero는 L0이어야 함
        l0_ids = [g.gate_id for g in l0_gates]
        assert "llm_zero" in l0_ids


# ══════════════════════════════════════════════════════════════════
# TC-14~16: validate_registry() CI 검증
# ══════════════════════════════════════════════════════════════════

class TestValidateRegistry:
    """TC-14~16: validate_registry() 검증."""

    def test_14_validate_registry_passes(self):
        """TC-14: validate_registry() → pass=True."""
        from literary_system.gates.gate_registry import validate_registry
        result = validate_registry()
        assert result["pass"] is True, f"오류: {result.get('errors', [])}"

    def test_15_validate_registry_returns_total_count(self):
        """TC-15: validate_registry() 결과에 total_gates 포함."""
        from literary_system.gates.gate_registry import validate_registry, GATE_REGISTRY
        result = validate_registry()
        assert result["total_gates"] == len(GATE_REGISTRY)

    def test_16_validate_registry_no_errors(self):
        """TC-16: validate_registry() errors 목록이 비어있음."""
        from literary_system.gates.gate_registry import validate_registry
        result = validate_registry()
        assert result["errors"] == []


# ══════════════════════════════════════════════════════════════════
# TC-17~19: Gate G36 GateRegistry
# ══════════════════════════════════════════════════════════════════

class TestGateG36:
    """TC-17~19: G36 게이트 검증."""

    def test_17_gate_g36_function_exists(self):
        """TC-17: _gate_registry_g36 함수 존재."""
        from literary_system.gates.release_gate import _gate_registry_g36
        assert callable(_gate_registry_g36)

    def test_18_gate_g36_passes(self):
        """TC-18: G36 게이트 실행 결과 pass=True."""
        from literary_system.gates.release_gate import _gate_registry_g36
        result = _gate_registry_g36()
        assert result["pass"] is True, f"G36 실패: {result}"

    def test_19_gate_g36_registered_in_gates_list(self):
        """TC-19: GATES 목록에 gate_registry_g36 등록 확인."""
        from literary_system.gates.release_gate import GATES
        ids = [g[0] for g in GATES]
        assert "gate_registry_g36" in ids


# ══════════════════════════════════════════════════════════════════
# TC-20~22: run_all_gates() 통합
# ══════════════════════════════════════════════════════════════════

class TestRunAllGates:
    """TC-20~22: run_all_gates() 통합 검증."""

    def test_20_run_all_gates_returns_dict(self):
        """TC-20: run_all_gates() → dict 반환."""
        from literary_system.gates.gate_registry import run_all_gates
        result = run_all_gates()
        assert isinstance(result, dict)

    def test_21_run_all_gates_covers_all_registry(self):
        """TC-21: run_all_gates() 결과 수 == GATE_REGISTRY 크기."""
        from literary_system.gates.gate_registry import run_all_gates, GATE_REGISTRY
        result = run_all_gates()
        assert len(result) == len(GATE_REGISTRY)

    def test_22_run_all_gates_includes_adr_metadata(self):
        """TC-22: run_all_gates() 결과에 adr_ref, layer 메타데이터 포함."""
        from literary_system.gates.gate_registry import run_all_gates
        result = run_all_gates()
        llm_zero = result.get("llm_zero", {})
        assert "adr_ref" in llm_zero
        assert "layer" in llm_zero


# ══════════════════════════════════════════════════════════════════
# TC-23~25: tools/extract_adr.py ADR 자동 추출
# ══════════════════════════════════════════════════════════════════

class TestExtractADR:
    """TC-23~25: ADR 자동 추출 스크립트 검증."""

    def test_23_extract_adr_script_exists(self):
        """TC-23: tools/extract_adr.py 파일 존재."""
        import os
        repo_root = Path(__file__).parent.parent
        script = repo_root / "tools" / "extract_adr.py"
        assert script.exists(), f"파일 없음: {script}"

    def test_24_extract_adr_from_sources_finds_adr035(self):
        """TC-24: 소스 코드에서 ADR-035 참조 발견."""
        import sys
        repo_root = Path(__file__).parent.parent
        sys.path.insert(0, str(repo_root / "tools"))
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "extract_adr", repo_root / "tools" / "extract_adr.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            adrs = mod.extract_adr_from_sources(repo_root)
            assert "ADR-035" in adrs, f"ADR-035 미발견. 발견된 ADR: {sorted(adrs.keys())[:10]}"
        finally:
            sys.path.pop(0)

    def test_25_adr_index_file_generated(self):
        """TC-25: docs/adr/INDEX.md 파일 존재 (generate_index 실행 결과)."""
        repo_root = Path(__file__).parent.parent
        index_file = repo_root / "docs" / "adr" / "INDEX.md"
        assert index_file.exists(), "INDEX.md 파일이 생성되지 않음"
        content = index_file.read_text(encoding="utf-8")
        assert "ADR 자동 추출 인덱스" in content
        assert "ADR-035" in content
