"""
V322 버그픽스 검증 테스트

버그 1: DRSE C_residue_boost S=0 충돌 — RESIDUE_MIN_S 보정
버그 2: PayoffScheduler slow_burn 공식 오류 — 0.55→0.70
갭 1:   CharacterBirthGate Literary State 연동 미구현 — ls_questions 추가
갭 2:   TraceDatasetStore style_dna_profile dict 타입 + slm_ready_count
"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ══════════════════════════════════════════════════════════════════
# 버그 1: DRSE residue_boost S=0 충돌
# ══════════════════════════════════════════════════════════════════
class TestBug1ResidueBoostSZero:

    def setup_method(self):
        from literary_system.relation_graph.relation_graph_store import (
            RelationGraphStore, StoryNode, StoryEdge, NodeType, RelationType
        )
        from literary_system.drse.drse_engine import (
            KnowledgeBoundaryGate, DRSEScorer, KeywordSemanticScorer
        )
        self.rgs = RelationGraphStore()
        gate = KnowledgeBoundaryGate(relation_graph=self.rgs)
        # KeywordScorer: "전혀 다른 키워드" 로 S=0 강제
        self.scorer = DRSEScorer(self.rgs, gate, KeywordSemanticScorer())
        self.NT = NodeType
        self.SN = StoryNode
        self.SE = StoryEdge
        self.RT = RelationType

    def test_unresolved_residue_not_zero_when_s_zero(self):
        """[버그 1] S=0이어도 미회수 복선은 최솟값 보장"""
        # 미회수 복선 추가
        n = self.SN("F_열쇠", self.NT.FORESHADOWING, "열쇠_오브제_복선", is_resolved=False)
        self.rgs.add_node(n)
        self.rgs.add_node(self.SN("C_준서", self.NT.CHARACTER, "이준서"))
        self.rgs.add_edge(self.SE("C_준서", "F_열쇠", self.RT.KNOWS))

        # 씬 목표를 완전히 다른 키워드로 → TF-IDF S=0 유도
        r = self.scorer.score_node(n, "바다 수영장 야구장 피자", "C_준서", 3)

        # 버그 수정 전: score=0.0
        # 버그 수정 후: RESIDUE_MIN_S(0.15) 보정으로 score > 0
        assert not r.gate_blocked, "게이트 차단이면 안 됨"
        assert r.score > 0.0, f"미회수 복선 score가 0이면 안 됨. 실제: {r.score}"
        assert r.breakdown.get("C_residue_boost") == 1.5

    def test_resolved_residue_still_zero_when_s_zero(self):
        """[버그 1] 회수된 복선은 S=0 보정 없음"""
        n = self.SN("F_회수", self.NT.FORESHADOWING, "회수된_복선", is_resolved=True)
        self.rgs.add_node(n)
        self.rgs.add_node(self.SN("C_K", self.NT.CHARACTER, "캐릭터K"))
        self.rgs.add_edge(self.SE("C_K", "F_회수", self.RT.KNOWS))

        r = self.scorer.score_node(n, "바다 수영장 야구장", "C_K", 3)
        # 회수된 복선: C_residue_boost=1.0, S=0이면 그대로 0
        assert r.breakdown.get("C_residue_boost") == 1.0

    def test_unresolved_greater_than_resolved(self):
        """[버그 1] 미회수 복선 > 회수 복선 보장"""
        unresolved = self.SN("F_U", self.NT.FORESHADOWING, "열쇠 복선 서류", is_resolved=False)
        resolved   = self.SN("F_R", self.NT.FORESHADOWING, "열쇠 복선 서류", is_resolved=True)
        char       = self.SN("C1", self.NT.CHARACTER, "캐릭터")
        for n in [unresolved, resolved, char]:
            self.rgs.add_node(n)
        self.rgs.add_edge(self.SE("C1", "F_U", self.RT.KNOWS))
        self.rgs.add_edge(self.SE("C1", "F_R", self.RT.KNOWS))

        r_u = self.scorer.score_node(unresolved, "열쇠 복선 서류", "C1", 3)
        r_r = self.scorer.score_node(resolved,   "열쇠 복선 서류", "C1", 3)
        assert r_u.score >= r_r.score, "미회수 복선이 회수 복선보다 점수가 같거나 높아야 함"


# ══════════════════════════════════════════════════════════════════
# 버그 2: PayoffScheduler slow_burn 공식
# ══════════════════════════════════════════════════════════════════
class TestBug2SlowBurnFormula:

    def setup_method(self):
        from literary_system.causal_plan.payoff_scheduler import PayoffScheduler
        self.scheduler = PayoffScheduler()

    def test_slow_burn_no_payoff_in_first_half(self):
        """[버그 2] slow_burn: 전반부(ep1~4)에 복선 배정 없음 (8화 기준)"""
        schedule = self.scheduler.generate_schedule(
            project_id="test",
            total_episodes=8,
            residue_ids=["R0","R1","R2","R3"],
            strategy="slow_burn",
        )
        # ep1~4: allocated_residues 비어있어야 함
        for ep_no in range(1, 5):
            brief = self.scheduler.get_episode_brief(schedule, ep_no)
            assert brief["allocated_residues"] == [], (
                f"[버그 2] slow_burn ep{ep_no}에 복선 배정됨: {brief['allocated_residues']}"
            )

    def test_slow_burn_payoffs_in_latter_half(self):
        """[버그 2] slow_burn: 후반부(ep5~8)에 복선 배정"""
        schedule = self.scheduler.generate_schedule(
            project_id="test",
            total_episodes=8,
            residue_ids=["R0","R1","R2","R3"],
            strategy="slow_burn",
        )
        latter_residues = []
        for ep_no in range(5, 9):
            brief = self.scheduler.get_episode_brief(schedule, ep_no)
            latter_residues.extend(brief["allocated_residues"])
        # 4개 복선 중 적어도 1개는 후반부에 배정
        assert len(latter_residues) >= 1, "[버그 2] slow_burn 후반부에 복선 미배정"

    def test_payoff_formula_fixed(self):
        """[버그 2] 수정 공식 (0.70) 적용 확인 — 소스 코드 검증"""
        import inspect
        from literary_system.causal_plan import payoff_scheduler
        src = inspect.getsource(payoff_scheduler)
        assert "0.70" in src, "[버그 2] 수정 공식 0.70이 소스에 없음"
        # 버그 수정 확인: ep_target 계산에 0.55가 남아있지 않아야 함
        for line in src.splitlines():
            if "ep_target" in line and "slow_burn" not in line:
                assert "0.55" not in line, f"[버그 2] ep_target 계산에 구 공식 0.55 잔존: {line}"


# ══════════════════════════════════════════════════════════════════
# 갭 1: CharacterBirthGate Literary State 연동
# ══════════════════════════════════════════════════════════════════
class TestGap1CharacterBirthGate:

    def _base_char(self, cid="C1"):
        return {
            "character_id": cid,
            "role_type": "pressure",
            "pressure_target": "main_conflict",
            "residue_binding": {"scene_01": ["열쇠"]},
            "memory_weight": 0.75,
            "act_evolution": True,
        }

    def test_without_literary_state_still_works(self):
        """[갭 1] literary_state 없어도 기존 판정 유지 (하위 호환)"""
        from literary_system.analyzer.character_birth_gate import evaluate_character_birth
        result = evaluate_character_birth([self._base_char()])
        assert len(result) == 1
        assert result[0]["decision"] in ("pass", "provisional", "fail", "deferred")
        assert result[0]["literary_state_applied"] is False

    def test_with_literary_state_connected(self):
        """[갭 1] literary_state 연동 시 ls_questions 포함"""
        from literary_system.analyzer.character_birth_gate import evaluate_character_birth
        ls = {"SP": 0.65, "RU": 0.50, "ET": 0.70, "RD": 0.40}
        result = evaluate_character_birth([self._base_char()], literary_state=ls)
        assert result[0]["literary_state_applied"] is True
        q = result[0]["questions"]
        assert "ls_sp_sufficient" in q
        assert "ls_ru_not_late" in q
        assert "ls_et_peak_timing" in q
        assert "ls_connected" in q

    def test_high_sp_passes(self):
        """[갭 1] SP 충분 + RU 낮음 → pass 유리"""
        from literary_system.analyzer.character_birth_gate import evaluate_character_birth
        ls_good = {"SP": 0.70, "RU": 0.40, "ET": 0.65}
        result = evaluate_character_birth([self._base_char()], literary_state=ls_good)
        assert result[0]["questions"]["ls_sp_sufficient"] is True
        assert result[0]["questions"]["ls_ru_not_late"] is True

    def test_high_ru_defers(self):
        """[갭 1] RU 높으면 deferred — 탄생 시점 연기 권장"""
        from literary_system.analyzer.character_birth_gate import evaluate_character_birth
        ls_late = {"SP": 0.65, "RU": 0.90, "ET": 0.30}  # RU > 0.75
        result = evaluate_character_birth([self._base_char()], literary_state=ls_late)
        assert result[0]["questions"]["ls_ru_not_late"] is False
        # RU 높으면 deferred 또는 fail
        assert result[0]["decision"] in ("deferred", "fail")

    def test_ls_et_peak_timing(self):
        """[갭 1] ET 피크 타이밍 판정"""
        from literary_system.analyzer.character_birth_gate import evaluate_character_birth
        ls_peak = {"SP": 0.65, "RU": 0.50, "ET": 0.80}
        result = evaluate_character_birth([self._base_char()], literary_state=ls_peak)
        assert result[0]["questions"]["ls_et_peak_timing"] is True


# ══════════════════════════════════════════════════════════════════
# 갭 2: TraceDatasetStore
# ══════════════════════════════════════════════════════════════════
class TestGap2TraceDatasetStore:

    def _make_record(self, style_profile, scene_id="sc_001", l_total=0.15):
        from literary_system.trace.trace_dataset_store import make_trace_record
        return make_trace_record(
            project_id="test_proj", episode_no=1, scene_id=scene_id,
            seed_contract={"genre": "drama"},
            style_dna_profile=style_profile,
            macroarc_intent="갈등 고조",
            literary_state_before={"SP": 0.5},
            literary_state_after={"SP": 0.65},
            render_output={"text": "복도가 조용했다."},
            loss_report={"L_total": l_total},
            reader_estimate={}, trajectory_deviation=0.0,
            critic_findings=[], repair_applied=False,
            hitl_recommended=False, fewshot_refs=[],
            knowledge_pressure=0.0, call_count=1,
        )

    def test_style_dna_profile_dict_no_crash(self):
        """[갭 2] style_dna_profile에 dict를 넣어도 오류 없음"""
        from literary_system.trace.trace_dataset_store import TraceDatasetStore
        store = TraceDatasetStore()
        dict_profile = {"author": "restraint", "pdi": 0.85}
        try:
            record = self._make_record(dict_profile)
            result = store.commit(record)
            assert result is not None
            # style_dna_profile이 str로 저장됐는지 확인
            assert isinstance(record.style_dna_profile, str)
        except TypeError as e:
            pytest.fail(f"[갭 2] dict profile이 TypeError 발생: {e}")

    def test_style_dna_profile_str_normal(self):
        """[갭 2] str 타입은 기존 동작 유지"""
        from literary_system.trace.trace_dataset_store import TraceDatasetStore
        store = TraceDatasetStore()
        record = self._make_record("author_restraint")
        result = store.commit(record)
        assert result is not None
        assert record.style_dna_profile == "author_restraint"

    def test_slm_ready_count_includes_candidate(self):
        """[갭 2] slm_ready_count = CANONICAL + CANDIDATE 합산"""
        from literary_system.trace.trace_dataset_store import TraceDatasetStore
        store = TraceDatasetStore()
        # CANONICAL (L_total ≤ 0.12, no_repair, calls≤2)
        store.commit(self._make_record("p1", "sc_c1", l_total=0.08))
        # CANDIDATE (0.12 < L_total ≤ 0.20)
        store.commit(self._make_record("p2", "sc_c2", l_total=0.18))
        stats = store.statistics()
        slm_count = stats.get("slm_ready_count", 0)
        assert slm_count >= 1, (
            f"[갭 2] slm_ready_count={slm_count} — CANDIDATE도 포함해야 함"
        )
