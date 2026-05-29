"""tests/test_gdap_plan_gate.py — WorkDeclaration + PlanBuildGate 단위 테스트 (25 tests)."""
import pytest
from literary_system.gdap.plan_gate import WorkDeclaration, GateResult, PlanBuildGate


# ── WorkDeclaration ───────────────────────────────────────────

class TestWorkDeclaration:
    def test_all_known_files_union(self):
        d = WorkDeclaration(
            target_files    = ["a.py"],
            affected_files  = ["b.py"],
            preserved_files = ["c.py"],
        )
        known = d.all_known_files()
        assert known == {"a.py", "b.py", "c.py"}

    def test_has_overlap_true(self):
        d = WorkDeclaration(
            target_files    = ["a.py", "b.py"],
            preserved_files = ["b.py", "c.py"],
        )
        assert d.has_overlap()

    def test_has_overlap_false(self):
        d = WorkDeclaration(
            target_files    = ["a.py"],
            preserved_files = ["c.py"],
        )
        assert not d.has_overlap()

    def test_is_minimal_with_target(self):
        d = WorkDeclaration(target_files=["a.py"])
        assert d.is_minimal()

    def test_is_minimal_empty_target_false(self):
        d = WorkDeclaration()
        assert not d.is_minimal()

    def test_is_minimal_overlap_false(self):
        d = WorkDeclaration(
            target_files    = ["a.py"],
            preserved_files = ["a.py"],
        )
        assert not d.is_minimal()

    def test_to_text_contains_sections(self):
        d = WorkDeclaration(
            target_files    = ["a.py"],
            affected_files  = ["b.py"],
            preserved_files = ["c.py"],
            reason          = "bugfix",
        )
        text = d.to_text()
        assert "[변경 대상 파일]" in text
        assert "[영향받는 파일" in text
        assert "[보존 파일" in text
        assert "bugfix" in text

    def test_to_text_reason_empty_shows_placeholder(self):
        d = WorkDeclaration(target_files=["a.py"])
        text = d.to_text()
        assert "(미기재)" in text


# ── PlanBuildGate ─────────────────────────────────────────────

@pytest.fixture
def gate():
    return PlanBuildGate(total_file_count=100)


class TestGateApproval:
    def test_approve_valid_declaration(self, gate):
        d = WorkDeclaration(
            target_files    = ["a.py"],
            affected_files  = ["b.py"],
            preserved_files = ["c.py"],
            reason          = "test fix",
        )
        assert gate.approve(d)

    def test_reject_empty_target(self, gate):
        d = WorkDeclaration(
            target_files    = [],
            preserved_files = ["c.py"],
            reason          = "reason",
        )
        result = gate.validate(d)
        assert not result.approved
        assert any("비어" in v for v in result.violations)

    def test_reject_overlap(self, gate):
        d = WorkDeclaration(
            target_files    = ["a.py"],
            preserved_files = ["a.py"],
            reason          = "reason",
        )
        result = gate.validate(d)
        assert not result.approved
        assert any("중복" in v for v in result.violations)

    def test_reject_hard_limit_exceeded(self):
        # 총 10개 파일, target 7 → 70% > 60% HARD LIMIT
        gate = PlanBuildGate(total_file_count=10)
        d = WorkDeclaration(
            target_files = [f"f{i}.py" for i in range(7)],
            reason       = "refactor",
        )
        result = gate.validate(d)
        assert not result.approved
        assert any("허용 한계" in v for v in result.violations)

    def test_warning_max_blast_ratio(self):
        # 총 10개 파일, target 2 + affected 2 = 40% > 30% MAX
        gate = PlanBuildGate(total_file_count=10)
        d = WorkDeclaration(
            target_files   = ["a.py", "b.py"],
            affected_files = ["c.py", "d.py"],
            reason         = "refactor",
        )
        result = gate.validate(d)
        assert result.approved  # 경고만, 거부 아님
        assert any("권고" in w for w in result.warnings)

    def test_warning_high_risk_level(self, gate):
        d = WorkDeclaration(
            target_files = ["a.py"],
            reason       = "reason",
            risk_level   = "high",
        )
        result = gate.validate(d)
        assert any("HIGH" in w for w in result.warnings)

    def test_warning_regression_risk_high(self, gate):
        d = WorkDeclaration(
            target_files    = ["a.py"],
            reason          = "reason",
            regression_risk = "high",
        )
        result = gate.validate(d)
        assert any("회귀" in w for w in result.warnings)

    def test_warning_no_reason(self, gate):
        d = WorkDeclaration(target_files=["a.py"])
        result = gate.validate(d)
        assert any("이유" in w for w in result.warnings)

    def test_no_warning_when_reason_given(self, gate):
        d = WorkDeclaration(target_files=["a.py"], reason="bugfix")
        result = gate.validate(d)
        reason_warnings = [w for w in result.warnings if "이유" in w]
        assert not reason_warnings


class TestGateResult:
    def test_summary_approved(self, gate):
        d = WorkDeclaration(target_files=["a.py"], reason="fix")
        result = gate.validate(d)
        assert "APPROVED" in result.summary()

    def test_summary_rejected(self, gate):
        d = WorkDeclaration(target_files=[])
        result = gate.validate(d)
        assert "REJECTED" in result.summary()

    def test_blast_ratio_calculation(self):
        gate = PlanBuildGate(total_file_count=10)
        d = WorkDeclaration(
            target_files   = ["a.py", "b.py"],
            affected_files = ["c.py"],
        )
        result = gate.validate(d)
        assert abs(result.blast_ratio - 0.3) < 1e-9

    def test_require_approved_passes(self, gate):
        d = WorkDeclaration(target_files=["a.py"], reason="fix")
        result = gate.require_approved(d)
        assert result.approved

    def test_require_approved_raises_on_rejection(self, gate):
        d = WorkDeclaration(target_files=[])
        with pytest.raises(RuntimeError, match="거부"):
            gate.require_approved(d)
