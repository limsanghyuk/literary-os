"""V740: Phase E Manifest Validator 테스트 (20 TC)

ADR-201: PhaseEManifestValidator ME-1~ME-8 검증
"""
import os
import tempfile
from pathlib import Path

import pytest

from literary_system.deploy.phase_e_manifest import (
    ManifestCheckResult,
    PhaseEManifestValidator,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _make_validator(root: str) -> PhaseEManifestValidator:
    return PhaseEManifestValidator(repo_root=root)


# ---------------------------------------------------------------------------
# TC01~TC05: ManifestCheckResult data class
# ---------------------------------------------------------------------------

class TestManifestCheckResult:
    def test_tc01_fields_accessible(self):
        """TC01: ManifestCheckResult 필드가 정확히 노출된다."""
        r = ManifestCheckResult(
            check_id="ME-1", description="test", passed=True, message="ok"
        )
        assert r.check_id == "ME-1"
        assert r.description == "test"
        assert r.passed is True
        assert r.message == "ok"
        assert r.manifest_path is None

    def test_tc02_to_dict_shape(self):
        """TC02: to_dict()가 5개 키를 반환한다."""
        r = ManifestCheckResult(
            check_id="ME-2", description="d", passed=False, message="m",
            manifest_path="/path/to/file"
        )
        d = r.to_dict()
        assert set(d.keys()) == {"check_id", "description", "passed", "message", "manifest_path"}
        assert d["manifest_path"] == "/path/to/file"

    def test_tc03_to_dict_passed_false(self):
        """TC03: passed=False가 to_dict()에 보존된다."""
        r = ManifestCheckResult(check_id="X", description="y", passed=False, message="fail")
        assert r.to_dict()["passed"] is False

    def test_tc04_manifest_path_optional(self):
        """TC04: manifest_path 없이 생성 가능하다."""
        r = ManifestCheckResult(check_id="ME-5", description="d", passed=True, message="ok")
        assert r.manifest_path is None
        assert r.to_dict()["manifest_path"] is None

    def test_tc05_message_preserved(self):
        """TC05: message 값이 to_dict()에 정확히 반영된다."""
        msg = "All 4 Helm files present"
        r = ManifestCheckResult(check_id="ME-1", description="d", passed=True, message=msg)
        assert r.to_dict()["message"] == msg


# ---------------------------------------------------------------------------
# TC06~TC10: PhaseEManifestValidator constructor
# ---------------------------------------------------------------------------

class TestPhaseEManifestValidatorInit:
    def test_tc06_default_repo_root_inferred(self):
        """TC06: repo_root 미지정 시 리포 루트를 자동 추론한다."""
        v = PhaseEManifestValidator()
        # Should resolve to /tmp/repo when running from that environment
        assert v._root.is_dir()

    def test_tc07_explicit_repo_root_accepted(self):
        """TC07: 명시적 repo_root가 수용된다."""
        with tempfile.TemporaryDirectory() as tmp:
            v = _make_validator(tmp)
            assert str(v._root) == tmp

    def test_tc08_results_empty_before_run(self):
        """TC08: run_all_checks() 호출 전 results 리스트가 비어 있다."""
        v = _make_validator("/tmp")
        assert v.results == []

    def test_tc09_results_property_returns_copy(self):
        """TC09: results property가 내부 리스트의 복사본을 반환한다."""
        v = _make_validator(str(_REPO_ROOT))
        v.run_all_checks()
        r1 = v.results
        r1.clear()
        assert len(v.results) > 0  # original unaffected

    def test_tc10_run_returns_dict_with_required_keys(self):
        """TC10: run_all_checks() 반환값이 필수 키를 갖는다."""
        v = _make_validator(str(_REPO_ROOT))
        result = v.run_all_checks()
        required_keys = {"validator", "version", "repo_root", "total_checks",
                         "passed", "failed", "all_passed", "checks", "summary"}
        assert required_keys.issubset(result.keys())


# ---------------------------------------------------------------------------
# TC11~TC15: Checks on real repo (should all PASS)
# ---------------------------------------------------------------------------

class TestRealRepoChecks:
    @pytest.fixture(autouse=True)
    def validator(self):
        self.v = PhaseEManifestValidator(repo_root=str(_REPO_ROOT))
        self.result = self.v.run_all_checks()

    def test_tc11_all_checks_pass(self):
        """TC11: 실 레포에서 8개 체크 모두 PASS한다."""
        assert self.result["all_passed"], self.result["summary"]

    def test_tc12_total_checks_is_8(self):
        """TC12: 총 체크 수가 8이다 (ME-1~ME-8)."""
        assert self.result["total_checks"] == 8

    def test_tc13_passed_count_equals_8(self):
        """TC13: 실 레포에서 passed == 8."""
        assert self.result["passed"] == 8

    def test_tc14_summary_format(self):
        """TC14: summary가 '8/8 checks passed' 형식이다."""
        assert "8/8" in self.result["summary"]

    def test_tc15_check_ids_complete(self):
        """TC15: ME-1~ME-8 모든 check_id가 등장한다."""
        ids = {c["check_id"] for c in self.result["checks"]}
        expected = {f"ME-{i}" for i in range(1, 9)}
        assert ids == expected


# ---------------------------------------------------------------------------
# TC16~TC20: Failure scenarios (temp dir with missing files)
# ---------------------------------------------------------------------------

class TestFailureScenarios:
    def test_tc16_missing_helm_files_fail_me1(self):
        """TC16: Helm 파일 없으면 ME-1 FAIL."""
        with tempfile.TemporaryDirectory() as tmp:
            v = _make_validator(tmp)
            result = v.run_all_checks()
            checks = {c["check_id"]: c for c in result["checks"]}
            assert checks["ME-1"]["passed"] is False

    def test_tc17_wrong_chart_version_fail_me2(self):
        """TC17: Chart.yaml version != 13.0.0 이면 ME-2 FAIL."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "deploy/phase_e/helm/literary-os"
            p.mkdir(parents=True)
            (p / "Chart.yaml").write_text("apiVersion: v2\nversion: 12.0.0\n")
            v = _make_validator(tmp)
            v.run_all_checks()
            checks = {c.check_id: c for c in v.results}
            assert checks["ME-2"].passed is False
            assert "12.0.0" in checks["ME-2"].message

    def test_tc18_missing_fl_keys_fail_me3(self):
        """TC18: values.yaml에 fl: 섹션 없으면 ME-3 FAIL."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "deploy/phase_e/helm/literary-os"
            p.mkdir(parents=True)
            (p / "values.yaml").write_text("replicaCount: 3\n")
            v = _make_validator(tmp)
            v.run_all_checks()
            checks = {c.check_id: c for c in v.results}
            assert checks["ME-3"].passed is False

    def test_tc19_missing_keda_files_fail_me4(self):
        """TC19: KEDA 파일 없으면 ME-4 FAIL."""
        with tempfile.TemporaryDirectory() as tmp:
            v = _make_validator(tmp)
            result = v.run_all_checks()
            checks = {c["check_id"]: c for c in result["checks"]}
            assert checks["ME-4"]["passed"] is False

    def test_tc20_all_passed_false_when_failures_exist(self):
        """TC20: 체크 1개라도 실패 시 all_passed==False, failed>0."""
        with tempfile.TemporaryDirectory() as tmp:
            v = _make_validator(tmp)
            result = v.run_all_checks()
            assert result["all_passed"] is False
            assert result["failed"] > 0
