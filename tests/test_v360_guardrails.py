"""V360 T11-3: NKGGuardrails — GR-01~GR-05 테스트."""
import sys
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.gdap.guardrails import (
    NKGGuardrails, GuardrailCheck, GuardrailViolation,
)
from literary_system.gdap.plan_gate import PlanBuildGate, WorkDeclaration, GateResult
from literary_system.gdap.blast_radius import BlastRadiusCalculator, BlastRadius


class TestGR01:
    def test_pass_no_shared(self):
        c = NKGGuardrails.check_gr01_impact_required(False, ["f1"], [])
        assert c.passed and c.rule == "GR-01"

    def test_pass_impact_run(self):
        c = NKGGuardrails.check_gr01_impact_required(True, ["f1"], ["f1"])
        assert c.passed

    def test_fail_shared_no_impact(self):
        c = NKGGuardrails.check_gr01_impact_required(False, ["f1","f2"], ["f1"])
        assert not c.passed

    def test_empty_targets(self):
        c = NKGGuardrails.check_gr01_impact_required(False, [], ["f1"])
        assert c.passed

    def test_returns_guardrail_check(self):
        c = NKGGuardrails.check_gr01_impact_required(True, [], [])
        assert isinstance(c, GuardrailCheck)


class TestGR02:
    def test_pass_no_rename(self):
        c = NKGGuardrails.check_gr02_rename_dry_run(False, False)
        assert c.passed

    def test_pass_rename_with_dry_run(self):
        c = NKGGuardrails.check_gr02_rename_dry_run(True, True)
        assert c.passed

    def test_fail_rename_no_dry_run(self):
        c = NKGGuardrails.check_gr02_rename_dry_run(True, False)
        assert not c.passed

    def test_rule_name(self):
        c = NKGGuardrails.check_gr02_rename_dry_run(False, False)
        assert c.rule == "GR-02"

    def test_message_ok(self):
        c = NKGGuardrails.check_gr02_rename_dry_run(False, False)
        assert "OK" in c.message


class TestGR03:
    def test_pass_within_threshold(self):
        c = NKGGuardrails.check_gr03_blast_radius(0.20, threshold=0.30)
        assert c.passed

    def test_pass_at_threshold(self):
        c = NKGGuardrails.check_gr03_blast_radius(0.30, threshold=0.30)
        assert c.passed

    def test_fail_over_threshold(self):
        c = NKGGuardrails.check_gr03_blast_radius(0.31, threshold=0.30)
        assert not c.passed

    def test_custom_threshold(self):
        c = NKGGuardrails.check_gr03_blast_radius(0.50, threshold=0.60)
        assert c.passed

    def test_zero_ratio(self):
        c = NKGGuardrails.check_gr03_blast_radius(0.0)
        assert c.passed


class TestGR04:
    def test_pass_frozen(self):
        c = NKGGuardrails.check_gr04_semantic_frozen(True)
        assert c.passed

    def test_fail_not_frozen(self):
        c = NKGGuardrails.check_gr04_semantic_frozen(False)
        assert not c.passed

    def test_rule_name(self):
        c = NKGGuardrails.check_gr04_semantic_frozen(True)
        assert c.rule == "GR-04"


class TestGR05:
    def test_pass_single_edit(self):
        c = NKGGuardrails.check_gr05_detect_changes(False, False)
        assert c.passed

    def test_pass_multi_with_detect(self):
        c = NKGGuardrails.check_gr05_detect_changes(True, True)
        assert c.passed

    def test_fail_multi_no_detect(self):
        c = NKGGuardrails.check_gr05_detect_changes(True, False)
        assert not c.passed

    def test_rule_name(self):
        c = NKGGuardrails.check_gr05_detect_changes(False, False)
        assert c.rule == "GR-05"


class TestRunAll:
    def _all_pass_args(self):
        return dict(impact_analysis_run=True, target_nodes=["f1"], shared_nodes=["f1"],
                    rename_requested=True, dry_run_completed=True, blast_ratio=0.10,
                    is_frozen=True, multi_scene_edit=True, changes_detected=True,
                    blast_threshold=0.30, raise_on_violation=False)

    def test_all_pass(self):
        checks = NKGGuardrails.run_all(**self._all_pass_args())
        assert len(checks) == 5 and all(c.passed for c in checks)

    def test_one_fail(self):
        args = self._all_pass_args()
        args["is_frozen"] = False
        checks = NKGGuardrails.run_all(**args)
        failed = [c for c in checks if not c.passed]
        assert any(c.rule == "GR-04" for c in failed)

    def test_raise_on_violation(self):
        args = self._all_pass_args()
        args["is_frozen"] = False; args["raise_on_violation"] = True
        with pytest.raises(GuardrailViolation) as exc:
            NKGGuardrails.run_all(**args)
        assert "GR-04" in str(exc.value)

    def test_returns_list_of_checks(self):
        checks = NKGGuardrails.run_all(**self._all_pass_args())
        assert all(isinstance(c, GuardrailCheck) for c in checks)

    def test_rules_present(self):
        checks = NKGGuardrails.run_all(**self._all_pass_args())
        rules = {c.rule for c in checks}
        assert rules == {"GR-01","GR-02","GR-03","GR-04","GR-05"}


class TestPlanGate:
    def test_all_pass(self):
        decl = WorkDeclaration(target_files=["f1"], impact_analysis_run=True,
                               semantic_frozen=True, multi_scene_edit=False)
        r = PlanBuildGate().validate(decl)
        assert isinstance(r, GateResult) and r.passed

    def test_frozen_required(self):
        decl = WorkDeclaration(semantic_frozen=False)
        r = PlanBuildGate().validate(decl)
        assert not r.passed

    def test_preserved_file_in_target_fails(self):
        decl = WorkDeclaration(target_files=["f1"], preserved_files=["f1"],
                               semantic_frozen=True, impact_analysis_run=True)
        r = PlanBuildGate().validate(decl)
        assert not r.passed

    def test_blast_ratio_enforced(self):
        from literary_system.nkg.graph_store import NKGGraphStore
        from literary_system.nkg.schema import NKGNodeType, SceneNode
        g = NKGGraphStore()
        for i in range(10):
            g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id=f"s{i}", label=f"씬{i}"))
        decl = WorkDeclaration(target_files=[f"s{i}" for i in range(10)],
                               semantic_frozen=True, impact_analysis_run=True,
                               max_blast_ratio=0.01)
        calc = BlastRadiusCalculator(nkg=g)
        r = PlanBuildGate(calc).validate(decl)
        assert not r.passed

    def test_gate_result_has_checks(self):
        decl = WorkDeclaration(semantic_frozen=True)
        r = PlanBuildGate().validate(decl)
        assert isinstance(r.checks, list)

    def test_violations_list(self):
        decl = WorkDeclaration(semantic_frozen=False)
        r = PlanBuildGate().validate(decl)
        assert isinstance(r.violations, list) and len(r.violations) > 0
