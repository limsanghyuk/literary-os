"""
V325 Phase 3 테스트 — SequencePlanner + SceneFocusInjector + SceneGenerationOrchestrator
목표: 40 케이스 전체 PASS → 누적 700+ PASS

커버리지:
  [A] SequencePlan 데이터클래스                        (5)
  [B] SequencePlanner — Rev.2 동적 연산 API            (10)
  [C] SceneFocusInjector — 컨텍스트 조립              (8)
  [D] SceneGenerationOrchestrator — 기본 속성/구조    (5)
  [E] SceneGenerationOrchestrator — 단절 A (MAE→계수) (6)
  [F] SceneGenerationOrchestrator — 단절 B (씬 루프)  (6)

【Rev.2 변경사항 반영】
  - GENRE_SEQ_COUNT / ACT_TENSION_RANGES 삭제 (동적 연산으로 대체)
  - SequencePlanner.seq_count 속성 삭제 → plan() 반환 길이 [3, 8] 범위 검증
  - genre는 참고용(연산 미개입) → format_type 기반 동적 연산
  - ACT_SEQ_PATTERNS 기반 단일 act_index → 에피소드 내 모든 seq가 동일 막
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from literary_system.orchestrators.sequence_planner import (
    SequencePlan,
    SequencePlanner,
    SequenceType,
    EPISODE_RUNTIME,
    AVG_SEQUENCE_DURATION_MIN,
)
from literary_system.orchestrators.scene_focus_injector import (
    SceneFocusInjector,
    SceneFocusContext,
)
from literary_system.orchestrators.scene_generation_orchestrator import (
    SceneGenerationOrchestrator,
    SceneRecord,
    E2ESceneGenerationResult,
)


# ════════════════════════════════════════════════════════════════
# 공통 픽스처
# ════════════════════════════════════════════════════════════════

MOCK_MACRO_ARC = {
    "act_breakpoints":  [4, 11, 16],
    "pressure_curve":   [0.3, 0.45, 0.6, 0.75, 0.8, 0.85, 0.9,
                         0.85, 0.8, 0.7, 0.6, 0.5, 0.45, 0.4, 0.35, 0.3],
    "total_episodes":   16,
    "reveal_budget":    12,
}


def _make_seq_plan(
    seq_id="ep01_seq01", episode_no=1, seq_index=1,
    goal="세계관 소개", tension_target=0.35,
    scene_count=4, act_index=1,
    pct_start=0.0, pct_end=0.15,
) -> SequencePlan:
    return SequencePlan(
        seq_id=seq_id, episode_no=episode_no, seq_index=seq_index,
        goal=goal, tension_target=tension_target,
        scene_count=scene_count, act_index=act_index,
        pct_start=pct_start, pct_end=pct_end,
    )


def _make_mock_bridge(text: str = "고애신이 교회 문을 밀며 들어섰다.") -> MagicMock:
    bridge = MagicMock()
    bridge.generate.return_value = text
    mock_packet = MagicMock()
    mock_packet.narrative_text = text
    mock_packet.actions = []
    bridge.parse_action_packet.return_value = mock_packet
    bridge.provider_name = "mock"
    return bridge


def _make_mock_mae(consensus: bool = True, score: float = 0.8) -> MagicMock:
    mae = MagicMock()
    verdict = MagicMock()
    verdict.score   = score
    verdict.passed  = consensus
    result = MagicMock()
    result.consensus = consensus
    result.votes     = [verdict, verdict, verdict]
    result.scene_id  = "test_scene"
    mae.evaluate.return_value = result
    return result, mae


# ════════════════════════════════════════════════════════════════
# [A] SequencePlan 데이터클래스 (5)
# ════════════════════════════════════════════════════════════════

class TestSequencePlan:

    def test_fields_accessible(self):
        """모든 필드가 접근 가능."""
        sp = _make_seq_plan()
        assert sp.seq_id         == "ep01_seq01"
        assert sp.episode_no     == 1
        assert sp.seq_index      == 1
        assert sp.tension_target == 0.35
        assert sp.act_index      == 1

    def test_to_dict_keys(self):
        """to_dict() 반환 키 완전성."""
        d = _make_seq_plan().to_dict()
        for key in ("seq_id","episode_no","seq_index","goal",
                    "tension_target","scene_count","act_index",
                    "pct_start","pct_end"):
            assert key in d

    def test_to_dict_tension_rounded(self):
        """tension_target이 4자리로 반올림."""
        sp = _make_seq_plan(tension_target=0.123456789)
        assert sp.to_dict()["tension_target"] == round(0.123456789, 4)

    def test_from_dict_roundtrip(self):
        """to_dict → from_dict 왕복 변환."""
        sp  = _make_seq_plan()
        sp2 = SequencePlan.from_dict(sp.to_dict())
        assert sp2.seq_id         == sp.seq_id
        assert sp2.tension_target == sp.tension_target

    def test_pct_range_0_to_1(self):
        """pct_start, pct_end가 0~1 범위."""
        sp = _make_seq_plan(pct_start=0.0, pct_end=0.15)
        assert 0.0 <= sp.pct_start <= 1.0
        assert 0.0 <= sp.pct_end   <= 1.0


# ════════════════════════════════════════════════════════════════
# [B] SequencePlanner — Rev.2 동적 연산 API (10)
# ════════════════════════════════════════════════════════════════

class TestSequencePlanner:
    """
    Rev.2: seq_count는 runtime × 막계수 × 압력 기반 동적 산출 [3, 8].
    genre 파라미터는 참고용 레이블이며 연산에 직접 개입하지 않는다.
    """

    def test_plan_returns_list(self):
        """plan() 반환 타입이 List[SequencePlan]."""
        pl    = SequencePlanner(format_type="standard")
        plans = pl.plan(MOCK_MACRO_ARC, episode_no=1)
        assert isinstance(plans, list)
        assert all(isinstance(p, SequencePlan) for p in plans)

    def test_seq_count_within_drama_range(self):
        """시퀀스 수가 실측 한국 드라마 범위 [3, 8] 안에 있다."""
        pl    = SequencePlanner(format_type="standard")
        plans = pl.plan(MOCK_MACRO_ARC, episode_no=1)
        assert 3 <= len(plans) <= 8

    def test_standard_format_seq_count_range(self):
        """standard(65분) 포맷에서 3~8 시퀀스."""
        pl    = SequencePlanner(format_type="standard")
        plans = pl.plan(MOCK_MACRO_ARC, episode_no=1)
        assert 3 <= len(plans) <= 8

    def test_miniseries_format_produces_plans(self):
        """miniseries(70분) 포맷에서도 유효한 plan 목록."""
        pl    = SequencePlanner(format_type="miniseries")
        plans = pl.plan(MOCK_MACRO_ARC, episode_no=1)
        assert 3 <= len(plans) <= 8

    def test_legacy_genre_param_accepted(self):
        """구 버전 genre 파라미터가 예외 없이 수용된다."""
        for g in ("historical_drama", "medical_drama", "romance_drama"):
            pl    = SequencePlanner(genre=g)
            plans = pl.plan(MOCK_MACRO_ARC, episode_no=1)
            assert isinstance(plans, list) and len(plans) >= 3

    def test_legacy_seq_count_param_accepted(self):
        """구 버전 seq_count 파라미터가 예외 없이 수용된다 (무시됨)."""
        pl    = SequencePlanner(genre="historical_drama", seq_count=7)
        plans = pl.plan(MOCK_MACRO_ARC, episode_no=1)
        # 구 seq_count는 무시되고 동적 연산 결과 [3, 8] 반환
        assert 3 <= len(plans) <= 8

    def test_plan_seq_ids_unique(self):
        """모든 seq_id가 고유."""
        pl    = SequencePlanner(format_type="standard")
        plans = pl.plan(MOCK_MACRO_ARC, episode_no=1)
        ids   = [p.seq_id for p in plans]
        assert len(ids) == len(set(ids))

    def test_plan_act_index_consistent(self):
        """에피소드 내 모든 시퀀스는 동일한 막 번호를 갖는다."""
        pl    = SequencePlanner(format_type="standard")
        plans = pl.plan(MOCK_MACRO_ARC, episode_no=1)
        acts  = {p.act_index for p in plans}
        # Rev.2: 에피소드 = 단일 막 → 모든 seq가 같은 act_index
        assert len(acts) == 1
        assert list(acts)[0] in {1, 2, 3, 4}

    def test_tension_target_range(self):
        """모든 tension_target이 0~1 범위."""
        pl    = SequencePlanner(format_type="standard")
        plans = pl.plan(MOCK_MACRO_ARC, episode_no=1)
        for p in plans:
            assert 0.0 <= p.tension_target <= 1.0, \
                f"{p.seq_id} tension={p.tension_target} 범위 초과"

    def test_total_scene_count_positive(self):
        """total_scene_count()가 양수이고 현실적 범위."""
        pl    = SequencePlanner(format_type="standard")
        plans = pl.plan(MOCK_MACRO_ARC, episode_no=1)
        total = pl.total_scene_count(plans)
        # 한국 드라마 1화 18~35씬 — 동적 연산 결과를 넓게 검증
        assert total > 0
        assert total <= 64   # 8시퀀스 × 8씬 = 64가 이론적 최대


# ════════════════════════════════════════════════════════════════
# [C] SceneFocusInjector — 컨텍스트 조립 (8)
# ════════════════════════════════════════════════════════════════

class TestSceneFocusInjector:

    def setup_method(self):
        self.injector = SceneFocusInjector(rag_bridge=None)
        self.seq_plan = _make_seq_plan(
            tension_target=0.65, act_index=2,
            pct_start=0.2, pct_end=0.3, scene_count=4,
        )

    def test_returns_scene_focus_context(self):
        """build() 반환 타입이 SceneFocusContext."""
        ctx = self.injector.build(self.seq_plan, 3, 4)
        assert isinstance(ctx, SceneFocusContext)

    def test_scene_id_auto_generated(self):
        """scene_id가 자동 생성됨."""
        ctx = self.injector.build(self.seq_plan, 0, 4)
        assert ctx.scene_id.startswith("ep01_seq01")

    def test_scene_id_custom(self):
        """scene_id 직접 지정 시 사용됨."""
        ctx = self.injector.build(self.seq_plan, 0, 4, scene_id="custom_sc001")
        assert ctx.scene_id == "custom_sc001"

    def test_temporal_delta_range(self):
        """temporal_delta가 0~1 범위."""
        for i in range(4):
            ctx = self.injector.build(self.seq_plan, i, 4)
            assert 0.0 <= ctx.temporal_delta <= 1.0

    def test_emotional_pressure_range(self):
        """emotional_pressure가 0~1 범위."""
        for i in range(4):
            ctx = self.injector.build(self.seq_plan, i, 4)
            assert 0.0 <= ctx.emotional_pressure <= 1.0

    def test_hidden_intent_from_character_states(self):
        """character_states의 intent가 hidden_intent에 반영."""
        states = {"고애신": {"intent": "일본군 저격"}, "유진": {"intent": "고애신 보호"}}
        ctx    = self.injector.build(self.seq_plan, 0, 4, character_states=states)
        assert "고애신" in ctx.hidden_intent
        assert "일본군 저격" in ctx.hidden_intent

    def test_no_intent_fallback(self):
        """character_states 없으면 fallback 문자열."""
        ctx = self.injector.build(self.seq_plan, 0, 4, character_states={})
        assert "없음" in ctx.hidden_intent or len(ctx.hidden_intent) > 0

    def test_micro_context_contains_goal(self):
        """micro_context에 시퀀스 목표가 포함됨."""
        ctx = self.injector.build(self.seq_plan, 0, 4)
        assert self.seq_plan.goal in ctx.micro_context


# ════════════════════════════════════════════════════════════════
# [D] SceneGenerationOrchestrator — 기본 속성/구조 (5)
# ════════════════════════════════════════════════════════════════

class TestSceneGenerationOrchestratorBasic:

    def setup_method(self):
        self.bridge = _make_mock_bridge()
        self.orch   = SceneGenerationOrchestrator(bridge=self.bridge)

    def test_instantiation(self):
        """기본 인스턴스 생성."""
        assert self.orch is not None

    def test_max_retries_constant(self):
        """MAX_RETRIES_PER_SCENE이 3."""
        assert SceneGenerationOrchestrator.MAX_RETRIES_PER_SCENE == 3

    def test_bridge_assigned(self):
        """bridge가 올바르게 할당."""
        assert self.orch.bridge is self.bridge

    def test_run_episode_returns_result(self):
        """run_episode() 반환 타입이 E2ESceneGenerationResult."""
        # 직접 만든 SequencePlan 목록으로 실행 (동적 연산 독립)
        plans = [
            _make_seq_plan(seq_id="ep01_seq01", seq_index=1, scene_count=2),
            _make_seq_plan(seq_id="ep01_seq02", seq_index=2, scene_count=2),
        ]
        result = self.orch.run_episode(plans, project_id="test")
        assert isinstance(result, E2ESceneGenerationResult)

    def test_result_summary_keys(self):
        """summary() 반환 dict에 필수 키 존재."""
        plans = [_make_seq_plan(seq_id="ep01_seq01", scene_count=1)]
        result = self.orch.run_episode(plans)
        s      = result.summary()
        for k in ("project_id","total_scenes_generated","total_llm_calls",
                  "mae_consensus_rate","success"):
            assert k in s


# ════════════════════════════════════════════════════════════════
# [E] SceneGenerationOrchestrator — 단절 A (MAE→계수) (6)
# ════════════════════════════════════════════════════════════════

class TestSceneGenerationOrchestratorDisconnectA:
    """
    단절 A 해결 검증: MAEResult → CoefficientMapper → LearnedCoefficientStore
    SequencePlan을 직접 생성하여 플래너 동적 연산과 독립적으로 테스트.
    """

    def _make_plans(self, n_scenes: int = 2, n_seqs: int = 1) -> list[SequencePlan]:
        return [
            _make_seq_plan(
                seq_id=f"ep01_seq{i+1:02d}",
                seq_index=i + 1,
                scene_count=n_scenes,
            )
            for i in range(n_seqs)
        ]

    def test_mae_evaluate_called_per_scene(self):
        """MAEOrchestrator.evaluate()가 씬마다 호출됨."""
        _, mae     = _make_mock_mae(consensus=True)
        bridge     = _make_mock_bridge()
        orch       = SceneGenerationOrchestrator(bridge=bridge, mae_orchestrator=mae)
        plans      = self._make_plans(n_scenes=3, n_seqs=1)
        orch.run_episode(plans)
        assert mae.evaluate.call_count == 3

    def test_coeff_update_count_tracked(self):
        """계수 갱신 횟수가 result에 기록됨."""
        _, mae       = _make_mock_mae(consensus=True)
        coeff_mapper = MagicMock()
        coeff_store  = MagicMock()
        coeff_store.get_latest_coefficients.return_value = MagicMock()
        bridge = _make_mock_bridge()
        orch   = SceneGenerationOrchestrator(
            bridge=bridge, mae_orchestrator=mae,
            coeff_mapper=coeff_mapper, coeff_store=coeff_store,
        )
        plans  = self._make_plans(n_scenes=2, n_seqs=1)
        result = orch.run_episode(plans)
        assert result.coeff_update_count > 0

    def test_consensus_true_no_retry(self):
        """consensus=True이면 재렌더 없이 씬 커밋."""
        _, mae  = _make_mock_mae(consensus=True)
        bridge  = _make_mock_bridge()
        orch    = SceneGenerationOrchestrator(bridge=bridge, mae_orchestrator=mae)
        plans   = self._make_plans(n_scenes=2, n_seqs=1)
        result  = orch.run_episode(plans)
        assert result.total_retries == 0

    def test_consensus_false_triggers_retry(self):
        """consensus=False이면 재렌더(retry) 발생."""
        _, mae  = _make_mock_mae(consensus=False, score=0.4)
        bridge  = _make_mock_bridge()
        orch    = SceneGenerationOrchestrator(bridge=bridge, mae_orchestrator=mae)
        plans   = self._make_plans(n_scenes=1, n_seqs=1)
        result  = orch.run_episode(plans)
        assert result.total_retries > 0

    def test_max_retries_not_exceeded(self):
        """재시도 횟수가 MAX_RETRIES_PER_SCENE을 초과하지 않음."""
        _, mae  = _make_mock_mae(consensus=False, score=0.3)
        bridge  = _make_mock_bridge()
        orch    = SceneGenerationOrchestrator(bridge=bridge, mae_orchestrator=mae)
        plans   = self._make_plans(n_scenes=1, n_seqs=1)
        result  = orch.run_episode(plans)
        for rec in result.scenes:
            assert rec.retries <= SceneGenerationOrchestrator.MAX_RETRIES_PER_SCENE

    def test_scene_records_have_mae_score(self):
        """SceneRecord에 mae_score가 기록됨."""
        _, mae  = _make_mock_mae(consensus=True, score=0.85)
        bridge  = _make_mock_bridge()
        orch    = SceneGenerationOrchestrator(bridge=bridge, mae_orchestrator=mae)
        plans   = self._make_plans(n_scenes=2, n_seqs=1)
        result  = orch.run_episode(plans)
        for rec in result.scenes:
            assert rec.mae_score >= 0.0


# ════════════════════════════════════════════════════════════════
# [F] SceneGenerationOrchestrator — 단절 B (씬 루프) (6)
# ════════════════════════════════════════════════════════════════

class TestSceneGenerationOrchestratorDisconnectB:

    def _make_plans_multi_seq(self, seq_cnt=3, scenes_each=2) -> list[SequencePlan]:
        return [
            _make_seq_plan(
                seq_id=f"ep01_seq{i+1:02d}",
                seq_index=i + 1,
                scene_count=scenes_each,
                pct_start=round(i / seq_cnt, 4),
                pct_end=round((i + 1) / seq_cnt, 4),
            )
            for i in range(seq_cnt)
        ]

    def test_total_scenes_equals_sum_of_seq_scene_counts(self):
        """생성된 씬 수 == 시퀀스별 scene_count 합계."""
        plans  = self._make_plans_multi_seq(seq_cnt=3, scenes_each=2)
        bridge = _make_mock_bridge()
        orch   = SceneGenerationOrchestrator(bridge=bridge)
        result = orch.run_episode(plans)
        expected = sum(p.scene_count for p in plans)
        assert result.total_scenes_generated == expected

    def test_scene_records_count_matches(self):
        """scenes 목록 길이 == total_scenes_generated."""
        plans  = self._make_plans_multi_seq(seq_cnt=2, scenes_each=3)
        bridge = _make_mock_bridge()
        orch   = SceneGenerationOrchestrator(bridge=bridge)
        result = orch.run_episode(plans)
        assert len(result.scenes) == result.total_scenes_generated

    def test_scene_indices_sequential(self):
        """SceneRecord.scene_index가 0부터 순차 증가."""
        plans  = self._make_plans_multi_seq(seq_cnt=2, scenes_each=2)
        bridge = _make_mock_bridge()
        orch   = SceneGenerationOrchestrator(bridge=bridge)
        result = orch.run_episode(plans)
        indices = [r.scene_index for r in result.scenes]
        assert indices == list(range(len(indices)))

    def test_each_scene_has_text(self):
        """모든 SceneRecord에 text가 있음."""
        plans  = self._make_plans_multi_seq(seq_cnt=2, scenes_each=2)
        bridge = _make_mock_bridge("테스트 씬 텍스트.")
        orch   = SceneGenerationOrchestrator(bridge=bridge)
        result = orch.run_episode(plans)
        for rec in result.scenes:
            assert isinstance(rec.text, str)

    def test_llm_call_count_tracked(self):
        """total_llm_calls이 양수로 추적됨."""
        plans  = self._make_plans_multi_seq(seq_cnt=2, scenes_each=2)
        bridge = _make_mock_bridge()
        orch   = SceneGenerationOrchestrator(bridge=bridge)
        result = orch.run_episode(plans)
        assert result.total_llm_calls > 0

    def test_success_flag_true_on_no_exception(self):
        """예외 없이 완료되면 success=True."""
        plans  = self._make_plans_multi_seq(seq_cnt=1, scenes_each=2)
        bridge = _make_mock_bridge()
        orch   = SceneGenerationOrchestrator(bridge=bridge)
        result = orch.run_episode(plans)
        assert result.success is True
