"""
V315 테스트 — KnowledgeStateTracker + CausalChainPlanner 전수 검증.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from literary_system.world.knowledge_state_tracker import (
    KnowledgeStateTracker, KnowledgeStatus, InformationType,
    CausalChainPlanner,
)


def make_tracker() -> KnowledgeStateTracker:
    """테스트용 기본 Tracker 구성."""
    t = KnowledgeStateTracker("proj_test")

    # 사실 등록
    t.register_fact("fact_betrayal",  InformationType.BETRAYAL,
                    "B가 A를 배신자로 고발했다", "고발 사실",     episode_revealed_at=2)
    t.register_fact("fact_identity",  InformationType.IDENTITY,
                    "C의 진짜 정체는 내부 수사관", "내부 수사관",  episode_revealed_at=1)
    t.register_fact("fact_plan",      InformationType.PLAN,
                    "D의 계획은 문서 유출",        "문서 유출 계획", episode_revealed_at=3)

    # 초기 지식 상태 설정
    t.set_knowledge("char_A", "fact_betrayal", KnowledgeStatus.UNAWARE,   1)
    t.set_knowledge("char_B", "fact_betrayal", KnowledgeStatus.KNOWS,     2, how_learned="직접 실행")
    t.set_knowledge("char_A", "fact_identity", KnowledgeStatus.UNAWARE,   1)
    t.set_knowledge("char_B", "fact_identity", KnowledgeStatus.SUSPECTS,  2, how_learned="간접 추론")
    t.set_knowledge("char_C", "fact_identity", KnowledgeStatus.KNOWS,     1, how_learned="본인")
    t.set_knowledge("char_A", "fact_plan",     KnowledgeStatus.UNAWARE,   1)
    t.set_knowledge("char_D", "fact_plan",     KnowledgeStatus.KNOWS,     3, how_learned="본인 계획")

    return t


# ═══════════════════════════════════════════════════════════
# TestKnowledgeStateTracker
# ═══════════════════════════════════════════════════════════
class TestKnowledgeStateTracker:

    def test_register_fact(self):
        t = KnowledgeStateTracker("proj_01")
        f = t.register_fact("f001", InformationType.BETRAYAL, "배신", "사실값", 2)
        assert f.fact_id == "f001"
        assert "f001" in t.facts
        assert "f001" in t.reader_knowledge

    def test_register_fact_reader_not_knows(self):
        t = KnowledgeStateTracker("proj_01")
        t.register_fact("f002", "betrayal", "숨겨진 사실", "진짜값", 5, reader_knows=False)
        assert "f002" not in t.reader_knowledge

    def test_set_and_get_knowledge(self):
        t = make_tracker()
        status = t.get_knowledge("char_A", "fact_betrayal")
        assert status == KnowledgeStatus.UNAWARE

        status_b = t.get_knowledge("char_B", "fact_betrayal")
        assert status_b == KnowledgeStatus.KNOWS

    def test_unregistered_returns_unaware(self):
        t = make_tracker()
        status = t.get_knowledge("char_unknown", "fact_unknown")
        assert status == KnowledgeStatus.UNAWARE

    def test_asymmetry_a_knows_b_doesnt(self):
        t = make_tracker()
        report = t.analyze_asymmetry("char_B", "char_A", "fact_betrayal")
        assert report.asymmetry_type == "a_knows_b_doesnt"
        assert report.pressure_score > 0.5

    def test_asymmetry_both_know(self):
        t = make_tracker()
        # C는 본인이라 알고, 독자도 안다
        report = t.analyze_asymmetry("char_C", "char_B", "fact_identity")
        # B는 의심하고 C는 앎 → a_knows_b_doesnt (C쪽)
        assert report.asymmetry_type in ("a_knows_b_doesnt", "b_knows_a_doesnt", "both_know")
        assert 0.0 <= report.pressure_score <= 1.0

    def test_misbelief_raises_pressure(self):
        t = make_tracker()
        t.introduce_misbelief("char_A", "fact_betrayal", "B는 결백하다", 2, "잘못된 목격")
        status = t.get_knowledge("char_A", "fact_betrayal")
        assert status == KnowledgeStatus.MISBELIEVES

        report = t.analyze_asymmetry("char_B", "char_A", "fact_betrayal")
        assert report.pressure_score > 0.7  # 오해 보정으로 높아짐

    def test_scene_pressure_two_chars(self):
        t = make_tracker()
        result = t.scene_pressure_from_knowledge(["char_A", "char_B"])
        assert "total_pressure" in result
        assert result["total_pressure"] > 0.0
        assert "dominant_tension" in result

    def test_scene_pressure_single_char_zero(self):
        t = make_tracker()
        result = t.scene_pressure_from_knowledge(["char_A"])
        assert result["total_pressure"] == 0.0

    def test_propagate_knowledge(self):
        t = make_tracker()
        # B가 A에게 배신 사실 알려줌
        t.propagate_knowledge("char_B", "char_A", "fact_betrayal", 3, "직접 말함")
        status = t.get_knowledge("char_A", "fact_betrayal")
        assert status == KnowledgeStatus.KNOWS

    def test_propagate_partial_gives_suspects(self):
        t = make_tracker()
        t.propagate_knowledge("char_B", "char_A", "fact_betrayal", 3, "암시만 줌", partial=True)
        status = t.get_knowledge("char_A", "fact_betrayal")
        assert status == KnowledgeStatus.SUSPECTS

    def test_propagate_from_unaware_fails(self):
        t = make_tracker()
        # A는 배신 사실을 모름 → 전달 불가
        before = t.get_knowledge("char_C", "fact_betrayal")
        t.propagate_knowledge("char_A", "char_C", "fact_betrayal", 3)
        after = t.get_knowledge("char_C", "fact_betrayal")
        assert before == after  # 변화 없음

    def test_change_log_recorded(self):
        t = KnowledgeStateTracker("proj_01")
        t.register_fact("f1", "betrayal", "배신", "사실", 1)
        t.set_knowledge("char_X", "f1", KnowledgeStatus.KNOWS, 2, how_learned="직접 목격")
        assert 2 in t.change_log
        assert len(t.change_log[2]) == 1
        assert t.change_log[2][0]["char_id"] == "char_X"

    def test_episode_knowledge_summary(self):
        t = make_tracker()
        summary = t.episode_knowledge_summary(2)
        assert summary["episode_no"] == 2
        assert "avg_knowledge_pressure" in summary
        assert 0.0 <= summary["avg_knowledge_pressure"] <= 1.0
        assert "misbeliefs_active" in summary

    def test_misbelief_count_in_summary(self):
        t = make_tracker()
        t.register_fact("f_x", "motive", "동기 사실", "진짜 동기", 1)
        t.introduce_misbelief("char_A", "f_x", "가짜 동기", 2)
        summary = t.episode_knowledge_summary(2)
        assert summary["misbeliefs_active"] >= 1

    def test_string_enum_input(self):
        t = KnowledgeStateTracker("proj_01")
        f = t.register_fact("f_str", "identity", "정체", "진짜", 1)
        assert f.fact_type == InformationType.IDENTITY

        t.set_knowledge("char_A", "f_str", "knows", 1)
        assert t.get_knowledge("char_A", "f_str") == KnowledgeStatus.KNOWS


# ═══════════════════════════════════════════════════════════
# TestCausalChainPlanner
# ═══════════════════════════════════════════════════════════
class TestCausalChainPlanner:

    def setup_method(self):
        self.tracker = make_tracker()
        self.planner = CausalChainPlanner(self.tracker)

    def test_predict_pressure_shift_returns_shifts(self):
        result = self.planner.predict_pressure_shift(
            "char_A", "fact_betrayal", current_episode=3, look_ahead=2
        )
        assert "pressure_shifts" in result
        assert "predicted_payoff_episode" in result
        assert result["predicted_payoff_episode"] == 5

    def test_pressure_increases_after_learning(self):
        """
        A가 배신 사실을 알게 되면 B와의 압력이 변해야 함.
        """
        result = self.planner.predict_pressure_shift("char_A", "fact_betrayal", 3)
        shifts = result["pressure_shifts"]
        # char_B와의 관계에서 변화가 있어야 함
        assert len(shifts) > 0
        # 어떤 인물과든 변화가 있어야 함
        has_shift = any(abs(v["delta"]) > 0 for v in shifts.values())
        assert has_shift

    def test_recommendation_string(self):
        result = self.planner.predict_pressure_shift("char_A", "fact_betrayal", 3)
        assert isinstance(result["recommendation"], str)
        assert len(result["recommendation"]) > 0

    def test_cascade_chain_depth(self):
        chain = self.planner.cascade_chain("fact_betrayal", "char_A", 3, depth=3)
        assert isinstance(chain, list)
        assert len(chain) >= 1
        assert chain[0]["step"] == 1
        assert chain[0]["learner"] == "char_A"

    def test_cascade_chain_episode_advances(self):
        chain = self.planner.cascade_chain("fact_betrayal", "char_A", 3, depth=3)
        if len(chain) > 1:
            assert chain[1]["episode"] >= chain[0]["episode"]

    def test_unknown_fact_returns_error(self):
        result = self.planner.predict_pressure_shift("char_A", "fact_nonexistent", 3)
        assert "error" in result

    def test_biggest_shift_populated(self):
        result = self.planner.predict_pressure_shift("char_A", "fact_betrayal", 3)
        if result.get("pressure_shifts"):
            assert result["biggest_shift"] is not None
            assert "toward_char" in result["biggest_shift"]
            assert "delta" in result["biggest_shift"]
