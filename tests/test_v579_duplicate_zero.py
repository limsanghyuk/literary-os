"""
test_v579_duplicate_zero.py — V579 DuplicateZero & G37 테스트 (25 TC)

검증 그룹:
  A. DuplicateZero 기본 검증 (TC-01~05)
  B. 중복 감지 로직 (TC-06~10)
  C. backward-compat alias 확인 (TC-11~15)
  D. Gate G37 검증 (TC-16~20)
  E. Gate Registry G37 통합 (TC-21~25)
"""
import ast
import os
import sys
import types
import textwrap
import tempfile
import pytest

LITERARY_ROOT = os.path.join(os.path.dirname(__file__), "..", "literary_system")
LITERARY_ROOT = os.path.abspath(LITERARY_ROOT)


# ─── A. DuplicateZero 기본 검증 (TC-01~05) ──────────────────────────────────

class TestDuplicateZeroBasic:
    """literary_system/ 전체에 이종 파일 중복 클래스가 0건인지 확인."""

    def _scan(self, root):
        from collections import defaultdict
        class_locs = defaultdict(list)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fname in filenames:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    src = open(fpath, encoding="utf-8").read()
                    tree = ast.parse(src)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_locs[node.name].append(fpath)
                except Exception:
                    pass
        dups = {}
        for cls, paths in class_locs.items():
            unique = list(dict.fromkeys(paths))
            if len(unique) > 1:
                dups[cls] = unique
        return dups

    def test_tc01_no_duplicate_classes(self):
        """TC-01: literary_system/ 전체 중복 클래스 0건."""
        dups = self._scan(LITERARY_ROOT)
        assert dups == {}, f"중복 클래스 발견: {list(dups.keys())}"

    def test_tc02_class_count_reasonable(self):
        """TC-02: 전체 클래스 수가 합리적 범위 내 (100~2000)."""
        from collections import defaultdict
        class_locs = defaultdict(list)
        for dirpath, dirnames, filenames in os.walk(LITERARY_ROOT):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fname in filenames:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    src = open(fpath, encoding="utf-8").read()
                    tree = ast.parse(src)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_locs[node.name].append(fpath)
                except Exception:
                    pass
        total = len(class_locs)
        assert 100 <= total <= 2000, f"클래스 수 이상: {total}"

    def test_tc03_canonical_classes_exist(self):
        """TC-03: 핵심 canonical 클래스들이 존재."""
        from literary_system.llm_bridge.canonical_adapter import CanonicalLLMBridge
        from literary_system.gates.gate_registry import GateRegistryEntry
        assert CanonicalLLMBridge is not None
        assert GateRegistryEntry is not None

    def test_tc04_renamed_classes_accessible(self):
        """TC-04: 리네임된 클래스들이 새 이름으로 임포트 가능."""
        from literary_system.pipeline.gate7_physics import PhysicsGateResult
        from literary_system.gates.endurance_gate import EnduranceGateResult
        from literary_system.gdap.plan_gate import PlanGateResult
        assert PhysicsGateResult is not None
        assert EnduranceGateResult is not None
        assert PlanGateResult is not None

    def test_tc05_alias_backward_compat(self):
        """TC-05: backward-compat alias가 원본 클래스와 동일한 객체."""
        from literary_system.pipeline.gate7_physics import PhysicsGateResult, GateResult
        assert GateResult is PhysicsGateResult


# ─── B. 중복 감지 로직 (TC-06~10) ───────────────────────────────────────────

class TestDuplicateDetectionLogic:
    """임시 디렉터리로 중복 감지 로직 단위 검증."""

    def _make_tmpdir_with_files(self, files: dict):
        """files: {filename: source_code} → tmpdir path"""
        tmpdir = tempfile.mkdtemp()
        for fname, code in files.items():
            open(os.path.join(tmpdir, fname), "w").write(textwrap.dedent(code))
        return tmpdir

    def _detect_dups(self, root):
        from collections import defaultdict
        locs = defaultdict(list)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fname in filenames:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    tree = ast.parse(open(fpath).read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            locs[node.name].append(fpath)
                except Exception:
                    pass
        return {k: list(dict.fromkeys(v)) for k, v in locs.items() if len(dict.fromkeys(v)) > 1}

    def test_tc06_detect_cross_file_duplicate(self):
        """TC-06: 이종 파일 간 중복 감지."""
        d = self._make_tmpdir_with_files({
            "a.py": "class Foo: pass",
            "b.py": "class Foo: pass",
        })
        dups = self._detect_dups(d)
        assert "Foo" in dups

    def test_tc07_no_false_positive_same_file(self):
        """TC-07: 동일 파일 내 조건 분기 정의는 중복으로 미감지."""
        d = self._make_tmpdir_with_files({
            "a.py": """
                if True:
                    class Bar: pass
                else:
                    class Bar: pass
            """,
        })
        dups = self._detect_dups(d)
        assert "Bar" not in dups

    def test_tc08_alias_not_detected_as_duplicate(self):
        """TC-08: alias 할당(NewName = OldName)은 ClassDef 아니라 중복 미감지."""
        d = self._make_tmpdir_with_files({
            "a.py": "class Alpha: pass\nOldAlpha = Alpha",
            "b.py": "OldAlpha = object  # assignment, not ClassDef",
        })
        dups = self._detect_dups(d)
        assert "Alpha" not in dups  # Alpha는 a.py에만 있음

    def test_tc09_three_file_duplicate_detected(self):
        """TC-09: 3개 파일에 같은 이름 → 감지."""
        d = self._make_tmpdir_with_files({
            "x.py": "class Multi: pass",
            "y.py": "class Multi: pass",
            "z.py": "class Multi: pass",
        })
        dups = self._detect_dups(d)
        assert "Multi" in dups
        assert len(dups["Multi"]) == 3

    def test_tc10_unique_classes_not_flagged(self):
        """TC-10: 이름이 다른 클래스들은 중복으로 미분류."""
        d = self._make_tmpdir_with_files({
            "p.py": "class Cat: pass",
            "q.py": "class Dog: pass",
        })
        dups = self._detect_dups(d)
        assert len(dups) == 0


# ─── C. backward-compat alias 확인 (TC-11~15) ───────────────────────────────

class TestBackwardCompatAliases:
    """V579에서 리네임된 클래스들의 alias가 정상 동작."""

    def test_tc11_gate_result_aliases(self):
        """TC-11: GateResult alias가 각 모듈에서 접근 가능."""
        from literary_system.pipeline.gate7_physics import GateResult as GR1
        from literary_system.gates.endurance_gate import GateResult as GR2
        from literary_system.gdap.plan_gate import GateResult as GR3
        assert GR1 is not None
        assert GR2 is not None
        assert GR3 is not None

    def test_tc12_relation_type_aliases(self):
        """TC-12: RelationType alias들이 접근 가능."""
        from literary_system.common.enums import NarrativeRelationType, RelationType
        from literary_system.multiwork.shared_character_db import CharacterRelationType, RelationType as RT2
        assert RelationType is NarrativeRelationType
        assert RT2 is CharacterRelationType

    def test_tc13_ensemble_gate_alias(self):
        """TC-13: EnsembleGate alias가 접근 가능."""
        from literary_system.ensemble.gate8_ensemble import EnsembleGate, EnsembleGateV1
        assert EnsembleGate is EnsembleGateV1

    def test_tc14_dr_controller_alias(self):
        """TC-14: DRController alias가 접근 가능."""
        from literary_system.ops.dr_controller import OpsDRController, DRController
        assert DRController is OpsDRController

    def test_tc15_search_result_aliases(self):
        """TC-15: SearchResult alias가 각 모듈에서 접근 가능."""
        from literary_system.rag.qdrant_bridge import QdrantSearchResult, SearchResult
        from literary_system.corpus.bgem3_embedder import BGESearchResult, SearchResult as SR2
        assert SearchResult is QdrantSearchResult
        assert SR2 is BGESearchResult


# ─── D. Gate G37 검증 (TC-16~20) ────────────────────────────────────────────

class TestGateG37:
    """Gate G37 DuplicateZero 직접 검증."""

    def test_tc16_g37_imports(self):
        """TC-16: _gate_duplicate_zero_g37 임포트 가능."""
        from literary_system.gates.release_gate import _gate_duplicate_zero_g37
        assert callable(_gate_duplicate_zero_g37)

    def test_tc17_g37_returns_pass(self):
        """TC-17: G37 실행 결과 pass=True."""
        from literary_system.gates.release_gate import _gate_duplicate_zero_g37
        result = _gate_duplicate_zero_g37()
        assert result["pass"] is True, f"G37 실패: {result.get('duplicates', {})}"

    def test_tc18_g37_duplicate_count_zero(self):
        """TC-18: G37 duplicate_count == 0."""
        from literary_system.gates.release_gate import _gate_duplicate_zero_g37
        result = _gate_duplicate_zero_g37()
        assert result["duplicate_count"] == 0

    def test_tc19_g37_in_gates_list(self):
        """TC-19: G37이 GATES 목록에 등록됨."""
        from literary_system.gates.release_gate import GATES
        gate_ids = [g[0] for g in GATES]
        assert "duplicate_zero_g37" in gate_ids

    def test_tc20_g37_position_in_gates(self):
        """TC-20: G37이 GATES 목록에 포함 (V580 이후 G38/G39 추가됨)."""
        from literary_system.gates.release_gate import GATES
        ids = [g[0] for g in GATES]
        assert "duplicate_zero_g37" in ids


# ─── E. Gate Registry G37 통합 (TC-21~25) ───────────────────────────────────

class TestGateRegistryG37Integration:
    """gate_registry.py와의 통합 검증."""

    def test_tc21_registry_has_g37(self):
        """TC-21: GATE_REGISTRY에 duplicate_zero_g37 등록."""
        from literary_system.gates.gate_registry import GATE_REGISTRY
        assert "duplicate_zero_g37" in GATE_REGISTRY

    def test_tc22_g37_metadata(self):
        """TC-22: G37 메타데이터가 올바름."""
        from literary_system.gates.gate_registry import GATE_REGISTRY
        entry = GATE_REGISTRY["duplicate_zero_g37"]
        assert entry.adr_ref == "ADR-033"
        assert entry.version_added == "V579"
        assert entry.layer == "L1"

    def test_tc23_g37_runnable_via_registry(self):
        """TC-23: registry를 통한 G37 실행 가능."""
        from literary_system.gates.gate_registry import get_gate
        entry = get_gate("duplicate_zero_g37")
        assert entry is not None
        result = entry.run()
        assert result["pass"] is True

    def test_tc24_validate_registry_gates(self):
        """TC-24: validate_registry()가 게이트 검증 통과 (V580: 38개)."""
        from literary_system.gates.gate_registry import validate_registry
        result = validate_registry()
        assert result["pass"] is True
        assert result["total_gates"] >= 36

    def test_tc25_full_release_gate_pass(self):
        """TC-25: run_release_gate() 전체 Gates PASS (V580: 38개)."""
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["pass"] is True
        assert result["total_gates"] >= 36
        assert result["gates_passed"] == result["total_gates"]
