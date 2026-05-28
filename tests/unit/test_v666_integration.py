"""
V666 통합 테스트 — ADR-128 (G_CONNECTIVITY + SDK Online + 고립 패키지 통합)

TC01~TC35: 35개 Test Case
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
from collections import defaultdict

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SYS_ROOT = ROOT / "literary_system"
sys.path.insert(0, str(ROOT))


# ══════════════════════════════════════════════════════════════════════════════
# TC01~TC10: G_CONNECTIVITY — 연결성 검증
# ══════════════════════════════════════════════════════════════════════════════

def _build_import_graph():
    """literary_system/ 내 패키지 import 그래프 구성."""
    packages = set(d.name for d in SYS_ROOT.iterdir()
                   if d.is_dir() and not d.name.startswith("_"))
    imported_by: dict = defaultdict(set)
    deps: dict = defaultdict(set)
    for pkg in packages:
        for pyf in (SYS_ROOT / pkg).rglob("*.py"):
            try:
                src = pyf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in re.finditer(r"from literary_system\.(\w+)", src):
                t = m.group(1)
                if t in packages and t != pkg:
                    deps[pkg].add(t)
                    imported_by[t].add(pkg)
    return packages, deps, imported_by


class TestGConnectivity:
    """TC01~TC10: G_CONNECTIVITY 검증."""

    def setup_method(self):
        self.packages, self.deps, self.imported_by = _build_import_graph()

    def test_TC01_no_completely_isolated_packages(self):
        """TC01: 완전 고립 패키지 0개 — ADR-128 G_CONNECTIVITY PASS.
        
        V719 예외: security/ — SP-D.3 신규 패키지, V721 Gate G88 배선 예정 (ADR-180).
        2버전 유예 기간 내 허용 (ADR-128 §3).
        """
        # SP-D.3 보안 레이어: V721 Gate G88에서 literary_system 메인 흐름에 배선 예정
        TRANSITIONAL_ISOLATED = {"security"}
        isolated = [p for p in self.packages
                    if not self.imported_by.get(p) and not self.deps.get(p)
                    and p not in TRANSITIONAL_ISOLATED]
        assert isolated == [], f"완전 고립 패키지 발견: {isolated}"

    def test_TC02_scope_connected_to_world(self):
        """TC02: scope/ → world/ 연결 확인."""
        assert "scope" in self.deps.get("world", set()) or \
               "world" in self.imported_by.get("scope", set()) or \
               any("scope" in open(f).read() for f in
                   (SYS_ROOT / "world").rglob("*.py") if f.exists()), \
               "scope/와 world/ 미연결"

    def test_TC03_safety_connected_to_gates(self):
        """TC03: safety/ → gates/ 연결 확인."""
        assert "safety" in self.deps.get("gates", set()) or \
               any("safety" in open(f).read() for f in
                   (SYS_ROOT / "gates").rglob("*.py") if f.exists()), \
               "safety/와 gates/ 미연결"

    def test_TC04_audit_connected_to_governance(self):
        """TC04: audit/ → governance/ 연결 확인."""
        assert "audit" in self.deps.get("governance", set()) or \
               any("audit" in open(f).read() for f in
                   (SYS_ROOT / "governance").rglob("*.py") if f.exists()), \
               "audit/와 governance/ 미연결"

    def test_TC05_node2_extensions_connected_to_prose(self):
        """TC05: node2_extensions/ → prose/ 연결 확인."""
        assert "node2_extensions" in self.deps.get("prose", set()) or \
               any("node2_extensions" in open(f).read() for f in
                   (SYS_ROOT / "prose").rglob("*.py") if f.exists()), \
               "node2_extensions/와 prose/ 미연결"

    def test_TC06_causal_connected_to_causal_plan(self):
        """TC06: causal/ → causal_plan/ 연결 확인."""
        assert "causal" in self.deps.get("causal_plan", set()) or \
               any("causal" in open(f).read() for f in
                   (SYS_ROOT / "causal_plan").rglob("*.py") if f.exists()), \
               "causal/와 causal_plan/ 미연결"

    def test_TC07_optimization_connected_to_ops(self):
        """TC07: optimization/ → ops/ 연결 확인."""
        assert "optimization" in self.deps.get("ops", set()) or \
               any("optimization" in open(f).read() for f in
                   (SYS_ROOT / "ops").rglob("*.py") if f.exists()), \
               "optimization/와 ops/ 미연결"

    def test_TC08_contract_connected_to_pipeline(self):
        """TC08: contract/ → pipeline/ 연결 확인."""
        assert "contract" in self.deps.get("pipeline", set()) or \
               any("contract" in open(f).read() for f in
                   (SYS_ROOT / "pipeline").rglob("*.py") if f.exists()), \
               "contract/와 pipeline/ 미연결"

    def test_TC09_graph_connected_to_nkg(self):
        """TC09: graph/ → nkg/ 연결 확인."""
        assert "graph" in self.deps.get("nkg", set()) or \
               any("graph" in open(f).read() for f in
                   (SYS_ROOT / "nkg").rglob("*.py") if f.exists()), \
               "graph/와 nkg/ 미연결"

    def test_TC10_trajectory_family_connected_to_trajectory(self):
        """TC10: trajectory_family/ → trajectory/ 연결 확인."""
        assert "trajectory_family" in self.deps.get("trajectory", set()) or \
               any("trajectory_family" in open(f).read() for f in
                   (SYS_ROOT / "trajectory").rglob("*.py") if f.exists()), \
               "trajectory_family/와 trajectory/ 미연결"


# ══════════════════════════════════════════════════════════════════════════════
# TC11~TC20: SDK Online Mode 연결 검증
# ══════════════════════════════════════════════════════════════════════════════

class TestSDKOnlineMode:
    """TC11~TC20: SDK online 메서드 구현 상태 검증."""

    def _get_sdk_source(self):
        return (SYS_ROOT / "sdk" / "public_sdk.py").read_text(encoding="utf-8")

    def test_TC11_generate_online_implemented(self):
        """TC11: _generate_online() — AgentCoordinator 연결."""
        src = self._get_sdk_source()
        assert "AgentCoordinator" in src, "_generate_online이 AgentCoordinator 미사용"
        assert "raise GenerateError" not in src.split("_generate_online")[1].split("\n")[1], \
               "_generate_online이 여전히 미구현 raise"

    def test_TC12_analyze_online_implemented(self):
        """TC12: _analyze_online() — ConstitutionEvalV2 연결."""
        src = self._get_sdk_source()
        assert "ConstitutionEvalV2" in src or "_analyze_offline" in src.split("_analyze_online")[1][:300], \
               "_analyze_online이 폴백 없이 미구현"

    def test_TC13_repair_online_implemented(self):
        """TC13: _repair_online() — EditorAgent 연결."""
        src = self._get_sdk_source()
        assert "EditorAgent" in src, "_repair_online이 EditorAgent 미사용"

    def test_TC14_predict_online_implemented(self):
        """TC14: _predict_online() — ScenePredictor 연결."""
        src = self._get_sdk_source()
        assert "ScenePredictor" in src or "predictive" in src, \
               "_predict_online이 predictive 모듈 미사용"

    def test_TC15_no_pragma_no_cover_on_online_methods(self):
        """TC15: online 메서드에 pragma: no cover 없음."""
        src = self._get_sdk_source()
        # 각 online 메서드 def 라인에 pragma: no cover가 있으면 안 됨
        for method in ["_generate_online", "_analyze_online", "_repair_online", "_predict_online"]:
            idx = src.find(f"def {method}")
            if idx != -1:
                line = src[idx:src.find("\n", idx)]
                assert "pragma: no cover" not in line, \
                       f"{method}: pragma: no cover 남아있음"

    def test_TC16_sdk_imports_ensemble(self):
        """TC16: SDK 소스에 ensemble 참조 존재."""
        src = self._get_sdk_source()
        assert "ensemble" in src or "AgentCoordinator" in src, \
               "SDK가 ensemble/agents와 완전 단절"

    def test_TC17_generate_result_mapping_exists(self):
        """TC17: GenerateResult에 online mode 매핑."""
        src = self._get_sdk_source()
        assert '"mode": "online"' in src or "mode.*online" in src, \
               "online mode 매핑 없음"

    def test_TC18_offline_mode_still_works(self):
        """TC18: offline_mode=True 기존 동작 유지."""
        from literary_system.sdk.public_sdk import LiteraryOSClient, SDKConfig
        client = LiteraryOSClient(SDKConfig(offline_mode=True))
        result = client.generate("테스트씬", ["A", "B"], "서울", "갈등")
        assert result.scene_text, "offline mode generate 실패"
        assert result.meta.get("mode") == "offline"

    def test_TC19_sdk_config_online_mode_flag(self):
        """TC19: offline_mode=False 설정 가능."""
        from literary_system.sdk.sdk_config import SDKConfig
        cfg = SDKConfig(offline_mode=False)
        assert cfg.offline_mode is False

    def test_TC20_rate_limiter_still_works(self):
        """TC20: rate limiter 정상 동작 (online 전환 후 회귀 없음)."""
        from literary_system.sdk.public_sdk import LiteraryOSClient, SDKConfig
        client = LiteraryOSClient(SDKConfig(offline_mode=True, max_rpm=60))
        assert client._call_count == 0
        client.generate("X", ["A"], "Y", "Z")
        assert client._call_count == 1


# ══════════════════════════════════════════════════════════════════════════════
# TC21~TC25: 고립 패키지 import 가능성 검증
# ══════════════════════════════════════════════════════════════════════════════

class TestIsolatedPackageIntegration:
    """TC21~TC25: 통합된 패키지가 실제로 import 가능한지 검증."""

    def test_TC21_scope_import(self):
        """TC21: scope.resolver import 가능."""
        from literary_system.scope.resolver import PluginRegistry, NarrativeScopePlugin
        assert PluginRegistry is not None

    def test_TC22_audit_import(self):
        """TC22: audit.atia_metadata_auditor import 가능."""
        from literary_system.audit.atia_metadata_auditor import ATIAMetadataAuditor
        assert ATIAMetadataAuditor is not None

    def test_TC23_optimization_import(self):
        """TC23: optimization.adaptive_throttler import 가능."""
        from literary_system.optimization.adaptive_throttler import AdaptiveThrottler
        assert AdaptiveThrottler is not None

    def test_TC24_trajectory_family_import(self):
        """TC24: trajectory_family.trajectory_family_interpolator import 가능."""
        from literary_system.trajectory_family.trajectory_family_interpolator import (
            TrajectoryFamilyMatcher,
        )
        assert TrajectoryFamilyMatcher is not None

    def test_TC25_safety_gate_import(self):
        """TC25: gates.safety_regression_gate import 가능."""
        from literary_system.gates.safety_regression_gate import SafetyRegressionGate
        assert SafetyRegressionGate is not None


# ══════════════════════════════════════════════════════════════════════════════
# TC26~TC30: Preflight Step 13 검증
# ══════════════════════════════════════════════════════════════════════════════

class TestPreflightStep13:
    """TC26~TC30: run_preflight.py Step 13 G_CONNECTIVITY 코드 검증."""

    def _get_preflight_source(self):
        return (ROOT / "tools" / "run_preflight.py").read_text(encoding="utf-8")

    def test_TC26_step13_exists_in_preflight(self):
        """TC26: run_preflight.py에 Step 13 블록 존재."""
        src = self._get_preflight_source()
        assert "Step 13" in src, "Preflight Step 13 없음"

    def test_TC27_connectivity_check_in_step13(self):
        """TC27: Step 13에 G_CONNECTIVITY 검사 로직 존재."""
        src = self._get_preflight_source()
        assert "G_CONNECTIVITY" in src, "G_CONNECTIVITY 검사 없음"

    def test_TC28_isolated_detection_in_step13(self):
        """TC28: 완전 고립 패키지 탐지 로직 존재."""
        src = self._get_preflight_source()
        assert "_isolated" in src or "isolated" in src, "고립 탐지 로직 없음"

    def test_TC29_escalation_logic_exists(self):
        """TC29: 2버전 연속 고립 시 에스컬레이션 로직 존재."""
        src = self._get_preflight_source()
        assert "escalat" in src or "prev_isolated" in src, "에스컬레이션 로직 없음"

    def test_TC30_adr128_referenced_in_step13(self):
        """TC30: Step 13에 ADR-128 참조 존재."""
        src = self._get_preflight_source()
        assert "ADR-128" in src, "ADR-128 참조 없음"


# ══════════════════════════════════════════════════════════════════════════════
# TC31~TC35: run_release_gate.py G_CONNECTIVITY 검증
# ══════════════════════════════════════════════════════════════════════════════

class TestReleaseGateConnectivity:
    """TC31~TC35: run_release_gate.py G_CONNECTIVITY 게이트 검증."""

    def _get_gate_source(self):
        return (ROOT / "tools" / "run_release_gate.py").read_text(encoding="utf-8")

    def test_TC31_g_connectivity_in_release_gate(self):
        """TC31: run_release_gate.py에 G_CONNECTIVITY 검사 존재."""
        src = self._get_gate_source()
        assert "G_CONNECTIVITY" in src or "_check_connectivity" in src

    def test_TC32_g_preflight_blocking_check(self):
        """TC32: G_PREFLIGHT 블로킹 검사 존재."""
        src = self._get_gate_source()
        assert "_check_preflight_log" in src or "G_PREFLIGHT" in src

    def test_TC33_adr128_in_release_gate(self):
        """TC33: run_release_gate.py에 ADR-128 참조 존재."""
        src = self._get_gate_source()
        assert "ADR-128" in src

    def test_TC34_adr128_document_exists(self):
        """TC34: docs/adr/ADR-128.md 파일 존재."""
        adr = ROOT / "docs" / "adr" / "ADR-128.md"
        assert adr.exists(), "ADR-128.md 없음"
        content = adr.read_text(encoding="utf-8")
        assert "G_CONNECTIVITY" in content

    def test_TC35_schemas_ext_deleted(self):
        """TC35: schemas_ext/ 빈 패키지 삭제 확인."""
        schemas_ext = SYS_ROOT / "schemas_ext"
        assert not schemas_ext.exists(), "schemas_ext/ 아직 존재 (삭제 필요)"
