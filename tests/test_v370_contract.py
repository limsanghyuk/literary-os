"""test_v370_contract.py — ProseRenderContract 테스트 (V370)"""
import pytest
from literary_system.prose.contract import (
    ProseRenderContract, ProseContractViolationError,
    SurfaceOnlyViolationError, NewFactViolationError,
    ReaderScoreBelowThresholdError,
)


class TestProseRenderContractDefaults:
    def test_default_surface_only(self):
        c = ProseRenderContract.default()
        assert c.surface_only is True

    def test_default_allow_new_facts_false(self):
        c = ProseRenderContract.default()
        assert c.allow_new_facts is False

    def test_default_allow_reveal_change_false(self):
        c = ProseRenderContract.default()
        assert c.allow_reveal_change is False

    def test_default_allow_causal_change_false(self):
        c = ProseRenderContract.default()
        assert c.allow_causal_change is False

    def test_default_min_surface_score(self):
        c = ProseRenderContract.default()
        assert c.min_surface_score == pytest.approx(9.0)

    def test_strict_min_score(self):
        c = ProseRenderContract.strict()
        assert c.min_surface_score == pytest.approx(9.5)

    def test_relaxed_min_score(self):
        c = ProseRenderContract.relaxed()
        assert c.min_surface_score == pytest.approx(7.0)

    def test_default_genre_plugin_required(self):
        c = ProseRenderContract.default()
        assert c.genre_plugin_required is True

    def test_default_cluster_weight_enabled(self):
        c = ProseRenderContract.default()
        assert c.cluster_weight_enabled is True


class TestAssertValid:
    def test_valid_default_passes(self):
        c = ProseRenderContract.default()
        c.assert_valid()  # no exception

    def test_surface_only_false_raises(self):
        c = ProseRenderContract(surface_only=False)
        with pytest.raises(SurfaceOnlyViolationError):
            c.assert_valid()

    def test_allow_new_facts_true_raises(self):
        c = ProseRenderContract(allow_new_facts=True)
        with pytest.raises(NewFactViolationError):
            c.assert_valid()

    def test_allow_reveal_change_true_raises(self):
        c = ProseRenderContract(allow_reveal_change=True)
        with pytest.raises(ProseContractViolationError):
            c.assert_valid()

    def test_allow_causal_change_true_raises(self):
        c = ProseRenderContract(allow_causal_change=True)
        with pytest.raises(ProseContractViolationError):
            c.assert_valid()

    def test_score_out_of_range_raises(self):
        c = ProseRenderContract(min_surface_score=11.0)
        with pytest.raises(ProseContractViolationError):
            c.assert_valid()

    def test_score_negative_raises(self):
        c = ProseRenderContract(min_surface_score=-1.0)
        with pytest.raises(ProseContractViolationError):
            c.assert_valid()

    def test_strict_passes(self):
        ProseRenderContract.strict().assert_valid()

    def test_relaxed_passes(self):
        ProseRenderContract.relaxed().assert_valid()


class TestAssertScore:
    def test_score_above_threshold_passes(self):
        c = ProseRenderContract.default()
        c.assert_score(9.5)  # no exception

    def test_score_at_threshold_passes(self):
        c = ProseRenderContract.default()
        c.assert_score(9.0)

    def test_score_below_threshold_raises(self):
        c = ProseRenderContract.default()
        with pytest.raises(ReaderScoreBelowThresholdError) as ei:
            c.assert_score(8.0)
        assert ei.value.score == pytest.approx(8.0)
        assert ei.value.threshold == pytest.approx(9.0)

    def test_score_zero_raises(self):
        c = ProseRenderContract.default()
        with pytest.raises(ReaderScoreBelowThresholdError):
            c.assert_score(0.0)


class TestExceptionHierarchy:
    def test_surface_only_is_contract_violation(self):
        assert issubclass(SurfaceOnlyViolationError, ProseContractViolationError)

    def test_new_fact_is_contract_violation(self):
        assert issubclass(NewFactViolationError, ProseContractViolationError)

    def test_reader_score_is_contract_violation(self):
        assert issubclass(ReaderScoreBelowThresholdError, ProseContractViolationError)

    def test_rule_attribute(self):
        e = ProseContractViolationError("TEST_RULE", "msg")
        assert e.rule == "TEST_RULE"

    def test_reader_score_error_attributes(self):
        e = ReaderScoreBelowThresholdError(8.5, 9.0)
        assert e.score == pytest.approx(8.5)
        assert e.threshold == pytest.approx(9.0)
