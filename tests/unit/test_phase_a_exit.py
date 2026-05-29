"""
SP-A.8 (V595) — test_phase_a_exit.py

Phase A Exit Gate G52: 6축 검증 + Gate 등록 + ADR-055

TC01~TC20: 20 cases / 목표 20/20 PASS
"""
from __future__ import annotations

import os
import sys

import pytest

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from literary_system.gates.phase_a_exit_gate import _gate_phase_a_exit_g52


# ===========================================================================
# TC01~TC06 : Gate G52 6축 개별 검증
# ===========================================================================

class TestPhaseAExitAxes:
    """TC01~TC06"""

    @pytest.fixture(scope="class")
    def gate_result(self):
        return _gate_phase_a_exit_g52()

    def test_tc01_gate_returns_dict(self, gate_result):
        """TC01: Gate G52 결과가 dict 타입"""
        assert isinstance(gate_result, dict)

    def test_tc02_gate_has_pass_key(self, gate_result):
        """TC02: 'pass' 키 존재"""
        assert "pass" in gate_result

    def test_tc03_gate_has_checkpoints(self, gate_result):
        """TC03: checkpoints 딕셔너리 — EA-1~EA-6 존재"""
        cp = gate_result.get("checkpoints", {})
        for ax in ("EA-1", "EA-2", "EA-3", "EA-4", "EA-5", "EA-6"):
            assert ax in cp, f"{ax} 체크포인트 없음"

    def test_tc04_ea1_cli_import(self, gate_result):
        """TC04: EA-1 PASS — CLI 3 commands"""
        assert gate_result["checkpoints"]["EA-1"] is True

    def test_tc05_ea2_score_scene_full(self, gate_result):
        """TC05: EA-2 PASS — score_scene_full 5축 기능"""
        assert gate_result["checkpoints"]["EA-2"] is True

    def test_tc06_ea3_pipeline_collect(self, gate_result):
        """TC06: EA-3 PASS — CorpusFallbackPipeline.collect(10)"""
        assert gate_result["checkpoints"]["EA-3"] is True


class TestPhaseAExitAxesPart2:
    """TC07~TC10"""

    @pytest.fixture(scope="class")
    def gate_result(self):
        return _gate_phase_a_exit_g52()

    def test_tc07_ea4_rich_scene_score(self, gate_result):
        """TC07: EA-4 PASS — R(scene) >= 0.60"""
        assert gate_result["checkpoints"]["EA-4"] is True

    def test_tc08_ea5_gates_count_and_g51(self, gate_result):
        """TC08: EA-5 PASS — GATES >= 51 + G51 PASS"""
        assert gate_result["checkpoints"]["EA-5"] is True

    def test_tc09_ea6_test_count(self, gate_result):
        """TC09: EA-6 PASS — 테스트 >= 6,000"""
        assert gate_result["checkpoints"]["EA-6"] is True

    def test_tc10_overall_pass(self, gate_result):
        """TC10: Gate G52 전체 PASS"""
        assert gate_result["pass"] is True, (
            f"G52 FAIL — errors: {gate_result.get('errors', [])}"
        )


# ===========================================================================
# TC11~TC15 : Gate 등록 및 구조
# ===========================================================================

class TestGateRegistration:
    """TC11~TC15"""

    def test_tc11_g52_in_gates_list(self):
        """TC11: 'phase_a_exit_g52'가 GATES 리스트에 존재"""
        from literary_system.gates.release_gate import GATES
        names = [name for name, _, _ in GATES]
        assert "phase_a_exit_g52" in names

    def test_tc12_gates_count_51(self):
        """TC12: GATES 리스트 총 51개 (G1~G51 등록, G52 포함)"""
        from literary_system.gates.release_gate import GATES
        assert len(GATES) >= 51

    def test_tc13_g52_in_registry(self):
        """TC13: gate_registry.py에 phase_a_exit_g52 등록"""
        from literary_system.gates.gate_registry import list_gates
        entries = {e.gate_id: e for e in list_gates()}
        assert "phase_a_exit_g52" in entries, "phase_a_exit_g52 미등록"
        entry = entries["phase_a_exit_g52"]
        assert entry.adr_ref == "ADR-055"

    def test_tc14_g52_adr_055(self):
        """TC14: G52 ADR 참조가 ADR-055"""
        from literary_system.gates.gate_registry import list_gates
        entries = {e.gate_id: e for e in list_gates()}
        entry = entries.get("phase_a_exit_g52")
        assert entry is not None
        assert "ADR-055" in entry.adr_ref

    def test_tc15_g52_version_v595(self):
        """TC15: G52 version_added = V595"""
        from literary_system.gates.gate_registry import list_gates
        entries = {e.gate_id: e for e in list_gates()}
        entry = entries.get("phase_a_exit_g52")
        assert entry is not None
        assert entry.version_added == "V595"


# ===========================================================================
# TC16~TC20 : ADR-055 + LLM-0 + 통합
# ===========================================================================

class TestADRAndCompliance:
    """TC16~TC20"""

    def test_tc16_adr_055_exists(self):
        """TC16: ADR-055.md 파일 존재"""
        adr_path = os.path.join(_ROOT, "docs", "adr", "ADR-055.md")
        assert os.path.isfile(adr_path), f"ADR-055.md 없음: {adr_path}"

    def test_tc17_adr_055_content(self):
        """TC17: ADR-055.md에 'Phase A Exit' 내용 포함"""
        adr_path = os.path.join(_ROOT, "docs", "adr", "ADR-055.md")
        with open(adr_path, encoding="utf-8") as f:
            content = f.read()
        assert "Phase A Exit" in content or "G52" in content

    def test_tc18_cli_file_exists(self):
        """TC18: apps/cli/literary_cli.py 파일 존재"""
        cli_path = os.path.join(_ROOT, "apps", "cli", "literary_cli.py")
        assert os.path.isfile(cli_path), f"literary_cli.py 없음"

    def test_tc19_phase_a_exit_llm0(self):
        """TC19: LLM-0 원칙 — phase_a_exit_gate.py에 외부 LLM 호출 없음"""
        import inspect
        import literary_system.gates.phase_a_exit_gate as mod
        src = inspect.getsource(mod)
        forbidden = [
            "openai.ChatCompletion",
            "anthropic.Anthropic",
            "requests.post",
            "httpx.post",
        ]
        for pat in forbidden:
            assert pat not in src, f"LLM-0 위반: {pat}"

    def test_tc20_constitution_g51_still_passes(self):
        """TC20: G51 (ConstitutionGate) — V595에서도 PASS 유지"""
        from literary_system.gates.release_gate import GATES
        g51_fn = None
        for name, _, fn in GATES:
            if name == "constitution_g51":
                g51_fn = fn
                break
        assert g51_fn is not None, "G51 없음"
        result = g51_fn()
        assert result.get("pass", False) is True, (
            f"G51 FAIL: {result.get('errors', [])}"
        )
