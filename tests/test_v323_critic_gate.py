"""
V323 Phase 3 - CriticComparisonGate 테스트 (21개)
[CSC] audit_mode 전용 V312 vs V323 비교 검증.
"""
import pytest
from literary_system.gate.critic_comparison_gate import (
    CriticComparisonGate,
    AuditResult,
    PipelineOutput,
)


# -- 헬퍼 -----------------------------------------------------------

def make_output(score=0.5, text="씬 텍스트", passed=True, label="GOOD") -> PipelineOutput:
    return PipelineOutput(
        scene_text=text,
        drse_score=score,
        judgment_label=label,
        passed=passed,
        metadata={},
    )


# ==================================================================
# 1. PipelineOutput
# ==================================================================

class TestPipelineOutput:
    def test_defaults(self):
        out = PipelineOutput(
            scene_text="test",
            drse_score=0.5,
            judgment_label="GOOD",
            passed=True,
        )
        assert out.metadata == {}

    def test_to_dict(self):
        out = make_output(score=0.7, text="씬", passed=True, label="GOOD")
        d = out.to_dict()
        assert d["drse_score"] == 0.7
        assert d["judgment_label"] == "GOOD"

    def test_from_dict_roundtrip(self):
        out = make_output(score=0.4, text="abc", passed=False, label="BAD")
        out2 = PipelineOutput.from_dict(out.to_dict())
        assert out2.drse_score == out.drse_score
        assert out2.passed == out.passed


# ==================================================================
# 2. AuditResult
# ==================================================================

class TestAuditResult:
    def test_delta_score(self):
        v312 = make_output(score=0.3)
        v323 = make_output(score=0.6)
        result = AuditResult(
            scene_id="s1",
            v312_output=v312,
            v323_output=v323,
        )
        assert result.delta_score == pytest.approx(0.3)

    def test_delta_score_negative(self):
        v312 = make_output(score=0.8)
        v323 = make_output(score=0.5)
        result = AuditResult(scene_id="s1", v312_output=v312, v323_output=v323)
        assert result.delta_score == pytest.approx(-0.3)

    def test_agreement(self):
        v312 = make_output(passed=True, label="GOOD")
        v323 = make_output(passed=True, label="GOOD")
        result = AuditResult(scene_id="s1", v312_output=v312, v323_output=v323)
        assert result.agreement is True

    def test_disagreement(self):
        v312 = make_output(passed=True, label="GOOD")
        v323 = make_output(passed=False, label="BAD")
        result = AuditResult(scene_id="s1", v312_output=v312, v323_output=v323)
        assert result.agreement is False

    def test_to_dict_fields(self):
        result = AuditResult(
            scene_id="s1",
            v312_output=make_output(0.3),
            v323_output=make_output(0.7),
        )
        d = result.to_dict()
        assert "scene_id" in d
        assert "delta_score" in d
        assert "agreement" in d
        assert "v312_output" in d
        assert "v323_output" in d


# ==================================================================
# 3. CriticComparisonGate - audit_mode=False (기본)
# ==================================================================

class TestCriticGateDefault:
    def test_audit_mode_false_by_default(self):
        gate = CriticComparisonGate()
        assert gate.audit_mode is False

    def test_no_audit_result_when_disabled(self):
        gate = CriticComparisonGate(audit_mode=False)
        v312 = make_output(0.4)
        v323 = make_output(0.7)
        result = gate.compare(scene_id="s1", v312_output=v312, v323_output=v323)
        assert result is None

    def test_audit_count_zero_when_disabled(self):
        gate = CriticComparisonGate(audit_mode=False)
        gate.compare("s1", make_output(0.4), make_output(0.7))
        assert gate.audit_count == 0


# ==================================================================
# 4. CriticComparisonGate - audit_mode=True
# ==================================================================

class TestCriticGateAudit:
    def test_returns_audit_result_when_enabled(self):
        gate = CriticComparisonGate(audit_mode=True)
        result = gate.compare("s1", make_output(0.3), make_output(0.6))
        assert isinstance(result, AuditResult)

    def test_audit_count_increments(self):
        gate = CriticComparisonGate(audit_mode=True)
        gate.compare("s1", make_output(0.3), make_output(0.6))
        gate.compare("s2", make_output(0.5), make_output(0.5))
        assert gate.audit_count == 2

    def test_delta_score_stored(self):
        gate = CriticComparisonGate(audit_mode=True)
        result = gate.compare("s1", make_output(0.3), make_output(0.8))
        assert result.delta_score == pytest.approx(0.5)

    def test_history_accumulates(self):
        gate = CriticComparisonGate(audit_mode=True)
        for i in range(3):
            gate.compare(f"s{i}", make_output(0.4), make_output(0.6))
        assert len(gate.history) == 3

    def test_history_cleared(self):
        gate = CriticComparisonGate(audit_mode=True)
        gate.compare("s1", make_output(0.3), make_output(0.7))
        gate.clear_history()
        assert len(gate.history) == 0

    def test_disagreement_recorded(self):
        gate = CriticComparisonGate(audit_mode=True)
        v312 = make_output(passed=True, label="GOOD")
        v323 = make_output(passed=False, label="BAD")
        result = gate.compare("s1", v312, v323)
        assert result.agreement is False

    def test_agreement_rate(self):
        gate = CriticComparisonGate(audit_mode=True)
        gate.compare("s1", make_output(passed=True, label="GOOD"),
                     make_output(passed=True, label="GOOD"))
        gate.compare("s2", make_output(passed=True, label="GOOD"),
                     make_output(passed=False, label="BAD"))
        stats = gate.stats()
        assert stats["agreement_rate"] == pytest.approx(0.5)


# ==================================================================
# 5. CriticComparisonGate - stats
# ==================================================================

class TestCriticGateStats:
    def test_stats_fields(self):
        gate = CriticComparisonGate(audit_mode=True)
        s = gate.stats()
        assert "audit_mode" in s
        assert "audit_count" in s
        assert "agreement_rate" in s
        assert "avg_delta_score" in s

    def test_avg_delta_score(self):
        gate = CriticComparisonGate(audit_mode=True)
        gate.compare("s1", make_output(0.2), make_output(0.4))  # delta=0.2
        gate.compare("s2", make_output(0.3), make_output(0.7))  # delta=0.4
        stats = gate.stats()
        assert stats["avg_delta_score"] == pytest.approx(0.3)

    def test_stats_empty(self):
        gate = CriticComparisonGate(audit_mode=True)
        s = gate.stats()
        assert s["agreement_rate"] == 0.0
        assert s["avg_delta_score"] == 0.0
