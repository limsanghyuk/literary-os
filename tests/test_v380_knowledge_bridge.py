"""
V380 테스트 — world/character_knowledge_prose_bridge.py
CharacterKnowledgeProseBridge: 5상태 제약, 게이트, Contract 주입
"""
import pytest
from literary_system.world.knowledge_state_tracker import (
    KnowledgeStateTracker, KnowledgeStatus, InformationType,
)
from literary_system.world.character_knowledge_prose_bridge import (
    CharacterKnowledgeProseBridge,
    KnowledgeLeakageError, UnawarnessViolationError,
    KnowledgeRenderConstraint,
)
from literary_system.prose.contract import ProseRenderContract


@pytest.fixture
def tracker():
    t = KnowledgeStateTracker(project_id="test_proj")
    t.register_fact("fact_killer", InformationType.IDENTITY,
                    "살인자의 정체", "박형사", reader_knows=True)
    t.register_fact("fact_alibi", InformationType.EVENT,
                    "알리바이 거짓", "거짓", reader_knows=True)
    t.register_fact("fact_plan", InformationType.PLAN,
                    "범행 계획", "독약 사용", reader_knows=True)
    # 인물별 지식 설정
    t.set_knowledge("형사_김", "fact_killer", KnowledgeStatus.KNOWS, 14)
    t.set_knowledge("수지", "fact_killer", KnowledgeStatus.UNAWARE, 1)
    t.set_knowledge("조력자", "fact_killer", KnowledgeStatus.SUSPECTS, 8)
    t.set_knowledge("용의자", "fact_killer", KnowledgeStatus.MISBELIEVES, 5,
                    believed_value="자신이 범인이 아님")
    t.set_knowledge("내레이터", "fact_killer", KnowledgeStatus.READER_ONLY, 1)
    return t


@pytest.fixture
def bridge(tracker):
    return CharacterKnowledgeProseBridge(tracker)


class TestCheckGate:
    def test_knows_passes(self, bridge):
        bridge.check("형사_김", "fact_killer")  # KNOWS → 통과

    def test_unaware_passes(self, bridge):
        bridge.check("수지", "fact_killer")  # UNAWARE → 통과 (상태 체크만)

    def test_suspects_passes(self, bridge):
        bridge.check("조력자", "fact_killer")  # SUSPECTS → 통과

    def test_misbelieves_passes(self, bridge):
        bridge.check("용의자", "fact_killer")  # MISBELIEVES → 통과

    def test_reader_only_raises_leakage_error(self, bridge):
        with pytest.raises(KnowledgeLeakageError):
            bridge.check("내레이터", "fact_killer")

    def test_unknown_char_defaults_to_unaware(self, bridge):
        bridge.check("unknown_char", "fact_killer")  # UNAWARE → 통과

    def test_unknown_fact_defaults_to_unaware(self, bridge):
        bridge.check("수지", "unknown_fact")  # 미등록 → UNAWARE → 통과

    def test_leakage_error_has_char_and_fact(self, bridge):
        try:
            bridge.check("내레이터", "fact_killer")
        except KnowledgeLeakageError as e:
            assert e.char_id == "내레이터"
            assert e.fact_id == "fact_killer"


class TestCheckScene:
    def test_check_scene_no_violations(self, bridge):
        violations = bridge.check_scene("형사_김", ["fact_killer", "fact_alibi"])
        assert violations == []

    def test_check_scene_with_reader_only(self, bridge):
        violations = bridge.check_scene("내레이터", ["fact_killer", "fact_alibi"])
        assert "fact_killer" in violations

    def test_check_scene_empty_list(self, bridge):
        assert bridge.check_scene("수지", []) == []

    def test_check_scene_multiple_reader_only(self, tracker):
        tracker.set_knowledge("내레이터", "fact_alibi",
                               KnowledgeStatus.READER_ONLY, 1)
        bridge = CharacterKnowledgeProseBridge(tracker)
        violations = bridge.check_scene("내레이터",
                                         ["fact_killer", "fact_alibi"])
        assert len(violations) == 2


class TestAssertNoLeakage:
    def test_no_leakage_passes(self, bridge):
        bridge.assert_no_leakage(["형사_김", "수지"], ["fact_killer"])

    def test_leakage_raises(self, bridge):
        with pytest.raises(KnowledgeLeakageError):
            bridge.assert_no_leakage(["내레이터", "형사_김"], ["fact_killer"])


class TestGetConstraint:
    def test_knows_constraint(self, bridge):
        c = bridge.get_constraint("형사_김", "fact_killer")
        assert c.render_mode == "direct"
        assert c.is_blocked is False

    def test_unaware_constraint(self, bridge):
        c = bridge.get_constraint("수지", "fact_killer")
        assert c.render_mode == "ignorant"
        assert c.is_blocked is False

    def test_suspects_constraint(self, bridge):
        c = bridge.get_constraint("조력자", "fact_killer")
        assert c.render_mode == "suggestive"

    def test_misbelieves_constraint(self, bridge):
        c = bridge.get_constraint("용의자", "fact_killer")
        assert c.render_mode == "mistaken"

    def test_reader_only_constraint(self, bridge):
        c = bridge.get_constraint("내레이터", "fact_killer")
        assert c.render_mode == "blocked"
        assert c.is_blocked is True

    def test_constraint_has_behavioral_hint(self, bridge):
        c = bridge.get_constraint("수지", "fact_killer")
        assert len(c.behavioral_hint) > 0

    def test_constraint_to_dict(self, bridge):
        c = bridge.get_constraint("형사_김", "fact_killer")
        d = c.to_dict()
        assert "char_id" in d
        assert "fact_id" in d
        assert "render_mode" in d
        assert "is_blocked" in d


class TestGetSceneConstraints:
    def test_returns_list_of_constraints(self, bridge):
        constraints = bridge.get_scene_constraints("형사_김",
                                                    ["fact_killer", "fact_alibi"])
        assert len(constraints) == 2
        assert all(isinstance(c, KnowledgeRenderConstraint) for c in constraints)

    def test_empty_fact_ids(self, bridge):
        assert bridge.get_scene_constraints("수지", []) == []


class TestEnrichContract:
    def test_enrich_adds_metadata(self, bridge):
        contract = ProseRenderContract.default()
        enriched = bridge.enrich_contract(contract, "수지", ["fact_killer"])
        assert "knowledge_constraints" in enriched.metadata

    def test_enriched_contract_has_blocked_list(self, bridge):
        contract = ProseRenderContract.default()
        enriched = bridge.enrich_contract(contract, "내레이터", ["fact_killer"])
        kc = enriched.metadata["knowledge_constraints"]
        assert "fact_killer" in kc["blocked"]

    def test_enrich_does_not_modify_original(self, bridge):
        contract = ProseRenderContract.default()
        original_meta = dict(contract.metadata)
        bridge.enrich_contract(contract, "수지", ["fact_killer"])
        assert contract.metadata == original_meta

    def test_enriched_has_char_id(self, bridge):
        contract = ProseRenderContract.default()
        enriched = bridge.enrich_contract(contract, "형사_김", ["fact_killer"])
        assert enriched.metadata["knowledge_constraints"]["char_id"] == "형사_김"

    def test_enriched_has_hints(self, bridge):
        contract = ProseRenderContract.default()
        enriched = bridge.enrich_contract(contract, "수지", ["fact_killer"])
        kc = enriched.metadata["knowledge_constraints"]
        assert "fact_killer" in kc["hints"]

    def test_enriched_contract_assert_valid_still_passes(self, bridge):
        contract = ProseRenderContract.default()
        enriched = bridge.enrich_contract(contract, "수지", ["fact_killer"])
        enriched.assert_valid()  # ProseRenderContract 유효성 유지 확인


class TestAsymmetryPressure:
    def test_knows_vs_unaware_high_pressure(self, bridge):
        pressure = bridge.asymmetry_pressure(
            "형사_김", "수지", ["fact_killer"]
        )
        assert pressure >= 0.8

    def test_both_know_low_pressure(self, tracker):
        tracker.set_knowledge("수지", "fact_killer", KnowledgeStatus.KNOWS, 14)
        bridge = CharacterKnowledgeProseBridge(tracker)
        pressure = bridge.asymmetry_pressure("형사_김", "수지", ["fact_killer"])
        assert pressure == 0.0

    def test_suspects_vs_unaware_medium_pressure(self, bridge):
        pressure = bridge.asymmetry_pressure(
            "조력자", "수지", ["fact_killer"]
        )
        assert 0.4 <= pressure <= 0.8

    def test_empty_facts_zero_pressure(self, bridge):
        pressure = bridge.asymmetry_pressure("형사_김", "수지", [])
        assert pressure == 0.0

    def test_pressure_capped_at_one(self, bridge):
        pressure = bridge.asymmetry_pressure(
            "형사_김", "수지",
            ["fact_killer", "fact_alibi", "fact_plan"]
        )
        assert pressure <= 1.0


class TestBlockedFacts:
    def test_blocked_facts_for_reader_only_char(self, bridge):
        blocked = bridge.blocked_facts_for("내레이터")
        assert "fact_killer" in blocked

    def test_blocked_facts_for_knowing_char(self, bridge):
        blocked = bridge.blocked_facts_for("형사_김")
        assert "fact_killer" not in blocked

    def test_blocked_facts_for_unknown_char(self, bridge):
        blocked = bridge.blocked_facts_for("unknown_char")
        assert blocked == []
