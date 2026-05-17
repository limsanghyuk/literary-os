"""V370 ProseRenderContract 확장 테스트."""
import pytest
from literary_system.prose.contract import (
    ProseRenderContract,
    ProseContractViolationError,
    SurfaceOnlyViolationError,
    NewFactViolationError,
    ReaderScoreBelowThresholdError,
)


class TestContractPresets:
    def test_default_surface_only(self):
        c = ProseRenderContract.default()
        assert c.surface_only is True

    def test_default_no_new_facts(self):
        c = ProseRenderContract.default()
        assert c.allow_new_facts is False

    def test_default_no_reveal_change(self):
        c = ProseRenderContract.default()
        assert c.allow_reveal_change is False

    def test_default_no_causal_change(self):
        c = ProseRenderContract.default()
        assert c.allow_causal_change is False

    def test_default_min_score(self):
        c = ProseRenderContract.default()
        assert c.min_surface_score == 9.0

    def test_strict_min_score(self):
        c = ProseRenderContract.strict()
        assert c.min_surface_score == 9.5

    def test_relaxed_min_score(self):
        c = ProseRenderContract.relaxed()
        assert c.min_surface_score == 7.0

    def test_strict_surface_only(self):
        c = ProseRenderContract.strict()
        assert c.surface_only is True

    def test_relaxed_surface_only(self):
        c = ProseRenderContract.relaxed()
        assert c.surface_only is True

    def test_genre_plugin_default(self):
        c = ProseRenderContract.default()
        assert c.genre_plugin_required is True

    def test_cluster_weight_default(self):
        c = ProseRenderContract.default()
        assert c.cluster_weight_enabled is True


class TestContractAssertValid:
    def test_valid_default_passes(self):
        ProseRenderContract.default().assert_valid()

    def test_valid_strict_passes(self):
        ProseRenderContract.strict().assert_valid()

    def test_valid_relaxed_passes(self):
        ProseRenderContract.relaxed().assert_valid()

    def test_surface_only_false_raises(self):
        c = ProseRenderContract(surface_only=False)
        with pytest.raises(SurfaceOnlyViolationError):
            c.assert_valid()

    def test_allow_new_facts_raises(self):
        c = ProseRenderContract(allow_new_facts=True)
        with pytest.raises(NewFactViolationError):
            c.assert_valid()

    def test_allow_reveal_change_raises(self):
        c = ProseRenderContract(allow_reveal_change=True)
        with pytest.raises(ProseContractViolationError):
            c.assert_valid()

    def test_allow_causal_change_raises(self):
        c = ProseRenderContract(allow_causal_change=True)
        with pytest.raises(ProseContractViolationError):
            c.assert_valid()

    def test_min_score_zero_raises(self):
        c = ProseRenderContract(min_surface_score=0.0)
        with pytest.raises(ProseContractViolationError):
            c.assert_valid()

    def test_min_score_negative_raises(self):
        c = ProseRenderContract(min_surface_score=-1.0)
        with pytest.raises(ProseContractViolationError):
            c.assert_valid()

    def test_min_score_above_10_raises(self):
        c = ProseRenderContract(min_surface_score=10.1)
        with pytest.raises(ProseContractViolationError):
            c.assert_valid()


class TestContractAssertScore:
    def test_passing_score(self):
        c = ProseRenderContract.default()
        c.assert_score(9.5)  # no exception

    def test_exact_min_score_passes(self):
        c = ProseRenderContract.default()
        c.assert_score(9.0)  # exactly at threshold — should pass

    def test_below_threshold_raises(self):
        c = ProseRenderContract.default()
        with pytest.raises(ReaderScoreBelowThresholdError):
            c.assert_score(8.9)

    def test_relaxed_lower_threshold(self):
        c = ProseRenderContract.relaxed()
        c.assert_score(7.5)  # passes relaxed

    def test_relaxed_below_raises(self):
        c = ProseRenderContract.relaxed()
        with pytest.raises(ReaderScoreBelowThresholdError):
            c.assert_score(6.9)

    def test_strict_high_threshold_passes(self):
        c = ProseRenderContract.strict()
        c.assert_score(9.5)

    def test_strict_at_9_raises(self):
        c = ProseRenderContract.strict()
        with pytest.raises(ReaderScoreBelowThresholdError):
            c.assert_score(9.4)

    def test_error_contains_score_info(self):
        c = ProseRenderContract.default()
        with pytest.raises(ReaderScoreBelowThresholdError) as exc_info:
            c.assert_score(5.0)
        err = exc_info.value
        assert hasattr(err, "score") or str(5.0) in str(err) or "5" in str(err)


class TestContractEquality:
    def test_two_defaults_equal(self):
        c1 = ProseRenderContract.default()
        c2 = ProseRenderContract.default()
        assert c1 == c2

    def test_default_vs_strict_not_equal(self):
        assert ProseRenderContract.default() != ProseRenderContract.strict()

    def test_default_vs_relaxed_not_equal(self):
        assert ProseRenderContract.default() != ProseRenderContract.relaxed()

    def test_strict_vs_relaxed_not_equal(self):
        assert ProseRenderContract.strict() != ProseRenderContract.relaxed()


class TestContractInheritance:
    def test_violation_error_is_exception(self):
        assert issubclass(ProseContractViolationError, Exception)

    def test_surface_only_violation_is_contract_violation(self):
        assert issubclass(SurfaceOnlyViolationError, ProseContractViolationError)

    def test_new_fact_violation_is_contract_violation(self):
        assert issubclass(NewFactViolationError, ProseContractViolationError)

    def test_score_error_is_contract_violation(self):
        assert issubclass(ReaderScoreBelowThresholdError, ProseContractViolationError)
