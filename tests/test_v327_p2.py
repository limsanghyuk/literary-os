"""
V327 Phase 2 통합 테스트
P2: V326 동시성 엔진 (CharacterIntentAgent → ConcurrentIntentCollector →
    ConcurrentActionResolver → CollisionFocusInjector) SGO 배선 검증
"""
from __future__ import annotations
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# ──────────────────────────────────────────────────────────────
# 공통 픽스처
# ──────────────────────────────────────────────────────────────

def _make_seq_plan(scene_count=2):
    from literary_system.orchestrators.sequence_planner import SequencePlan, SequenceType
    return SequencePlan(
        seq_id="seq_p2",
        episode_no=1,
        seq_index=0,
        goal="갈등 정점 씬",
        tension_target=0.85,
        scene_count=scene_count,
        act_index=1,
        pct_start=0.0,
        pct_end=1.0,
        seq_type=SequenceType.CONFLICT_PEAK.value,
    )

def _make_mock_bridge(text="씬 텍스트"):
    b = MagicMock()
    b.generate.return_value = text
    return b

def _make_mae(consensus=True, score=0.8):
    mae = MagicMock()
    vote = MagicMock(); vote.score = score
    result = MagicMock()
    result.consensus = consensus
    result.votes = [vote, vote, vote]
    mae.evaluate.return_value = result
    return mae

def _make_intent_packet(char_id="캐릭터A", location="서재", tension_boost=0.0):
    """IntentPacket Mock."""
    pkt = MagicMock()
    pkt.character_id  = char_id
    pkt.location      = location
    pkt.time_start    = 0.0
    pkt.time_end      = 0.5
    return pkt

def _make_collision_event(tension_boost=0.3):
    """CollisionEvent Mock."""
    evt = MagicMock()
    evt.tension_boost = tension_boost
    evt.involved_characters = ["캐릭터A", "캐릭터B"]
    return evt

def _make_sgo(**kwargs):
    from literary_system.orchestrators.scene_generation_orchestrator import (
        SceneGenerationOrchestrator,
    )
    defaults = dict(bridge=_make_mock_bridge(), mae_orchestrator=_make_mae())
    defaults.update(kwargs)
    return SceneGenerationOrchestrator(**defaults)


# ──────────────────────────────────────────────────────────────
# P2 테스트
# ──────────────────────────────────────────────────────────────

class TestV327P2ConcurrentEngineWiring:
    """P2: SGO가 동시성 엔진 파라미터를 정상 수용하는지 검증."""

    def test_intent_collector_param_accepted(self):
        """SGO __init__이 intent_collector 파라미터를 받아들임."""
        collector = MagicMock()
        sgo = _make_sgo(intent_collector=collector)
        assert sgo._intent_collector is collector

    def test_action_resolver_param_accepted(self):
        """SGO __init__이 action_resolver 파라미터를 받아들임."""
        resolver = MagicMock()
        sgo = _make_sgo(action_resolver=resolver)
        assert sgo._action_resolver is resolver

    def test_both_none_by_default(self):
        """기본값 — 동시성 엔진 없이 정상 동작."""
        sgo = _make_sgo()
        assert sgo._intent_collector is None
        assert sgo._action_resolver  is None

    def test_pipeline_works_without_concurrent_engine(self):
        """동시성 엔진 없을 때 기존 파이프라인 완전 유지."""
        sgo = _make_sgo()
        result = sgo.run_episode([_make_seq_plan(scene_count=2)])
        assert result.success
        assert result.total_scenes_generated == 2


class TestV327P2IntentCollectorCalled:
    """P2: intent_collector가 씬마다 호출되는지 검증."""

    def test_collect_sync_called_per_scene(self):
        """씬 생성 시 intent_collector.collect_sync()가 호출됨."""
        collector = MagicMock()
        collector.collect_sync.return_value = []
        sgo = _make_sgo(intent_collector=collector)
        sgo.run_episode([_make_seq_plan(scene_count=3)])
        assert collector.collect_sync.call_count == 3

    def test_collect_sync_receives_tension(self):
        """collect_sync에 seq_plan.tension_target이 전달됨."""
        collector = MagicMock()
        collector.collect_sync.return_value = []
        sgo = _make_sgo(intent_collector=collector)
        plan = _make_seq_plan(scene_count=1)
        sgo.run_episode([plan])
        call_kwargs = collector.collect_sync.call_args
        # tension 키워드 또는 positional로 0.85 전달
        assert call_kwargs is not None
        passed_tension = (
            call_kwargs.kwargs.get("tension") or
            (call_kwargs.args[0] if call_kwargs.args else None)
        )
        assert passed_tension == pytest.approx(0.85)

    def test_action_resolver_called_when_packets_exist(self):
        """패킷이 있을 때 action_resolver.resolve()가 호출됨."""
        packets = [_make_intent_packet("A"), _make_intent_packet("B")]
        collector = MagicMock()
        collector.collect_sync.return_value = packets
        resolver = MagicMock()
        resolver.resolve.return_value = []
        sgo = _make_sgo(intent_collector=collector, action_resolver=resolver)
        sgo.run_episode([_make_seq_plan(scene_count=1)])
        resolver.resolve.assert_called_once_with(packets)

    def test_action_resolver_not_called_when_no_packets(self):
        """패킷이 없으면 action_resolver.resolve() 호출 안 됨."""
        collector = MagicMock()
        collector.collect_sync.return_value = []
        resolver = MagicMock()
        sgo = _make_sgo(intent_collector=collector, action_resolver=resolver)
        sgo.run_episode([_make_seq_plan(scene_count=1)])
        resolver.resolve.assert_not_called()


class TestV327P2CollisionInjectorSwap:
    """P2: 충돌 감지 시 CollisionFocusInjector로 동적 교체되는지 검증."""

    def test_collision_injector_created_in_init(self):
        """SGO 초기화 시 _collision_injector 인스턴스 생성."""
        sgo = _make_sgo()
        # _CONCURRENT_AVAILABLE=True 환경이면 인스턴스가 존재해야 함
        from literary_system.orchestrators.scene_generation_orchestrator import _CONCURRENT_AVAILABLE
        if _CONCURRENT_AVAILABLE:
            assert sgo._collision_injector is not None
        else:
            assert sgo._collision_injector is None

    def test_collision_event_triggers_collision_injector(self):
        """충돌 이벤트 존재 시 CollisionFocusInjector.build_collision() 호출."""
        from literary_system.orchestrators.scene_generation_orchestrator import _CONCURRENT_AVAILABLE
        if not _CONCURRENT_AVAILABLE:
            pytest.skip("동시성 모듈 미설치")

        collision_event = _make_collision_event(tension_boost=0.3)
        collector = MagicMock()
        collector.collect_sync.return_value = [_make_intent_packet()]
        resolver  = MagicMock()
        resolver.resolve.return_value = [collision_event]

        sgo = _make_sgo(intent_collector=collector, action_resolver=resolver)

        # _collision_injector.build_collision mock 교체
        mock_injector = MagicMock()
        mock_focus = MagicMock()
        mock_focus.scene_id = "test_collision_scene"
        mock_focus.to_dict.return_value = {}
        mock_focus.micro_context = "충돌 컨텍스트"
        mock_focus.emotional_pressure = 0.9
        mock_injector.build_collision.return_value = mock_focus
        sgo._collision_injector = mock_injector

        sgo.run_episode([_make_seq_plan(scene_count=1)])
        mock_injector.build_collision.assert_called_once()

    def test_no_collision_uses_normal_injector(self):
        """충돌 없을 때 기본 SceneFocusInjector 사용."""
        collector = MagicMock()
        collector.collect_sync.return_value = [_make_intent_packet()]
        resolver  = MagicMock()
        resolver.resolve.return_value = []  # 충돌 없음

        sgo = _make_sgo(intent_collector=collector, action_resolver=resolver)

        with patch.object(sgo._focus_injector, "build", wraps=sgo._focus_injector.build) as mock_build:
            sgo.run_episode([_make_seq_plan(scene_count=1)])
            mock_build.assert_called_once()

    def test_highest_tension_event_selected(self):
        """여러 충돌 이벤트 중 tension_boost 최댓값 선택."""
        from literary_system.orchestrators.scene_generation_orchestrator import _CONCURRENT_AVAILABLE
        if not _CONCURRENT_AVAILABLE:
            pytest.skip("동시성 모듈 미설치")

        evt_low  = _make_collision_event(tension_boost=0.2)
        evt_high = _make_collision_event(tension_boost=0.8)
        evt_mid  = _make_collision_event(tension_boost=0.5)

        collector = MagicMock()
        collector.collect_sync.return_value = [_make_intent_packet()]
        resolver  = MagicMock()
        resolver.resolve.return_value = [evt_low, evt_high, evt_mid]

        sgo = _make_sgo(intent_collector=collector, action_resolver=resolver)
        mock_injector = MagicMock()
        mock_focus = MagicMock()
        mock_focus.scene_id = "s"; mock_focus.to_dict.return_value = {}
        mock_focus.micro_context = "ctx"; mock_focus.emotional_pressure = 0.9
        mock_injector.build_collision.return_value = mock_focus
        sgo._collision_injector = mock_injector

        sgo.run_episode([_make_seq_plan(scene_count=1)])
        # 가장 높은 tension_boost(0.8) 이벤트가 전달됐는지 확인
        call_args = mock_injector.build_collision.call_args
        assert call_args.kwargs["collision_event"].tension_boost == pytest.approx(0.8)


class TestV327P2ErrorIsolation:
    """P2: 동시성 엔진 오류가 씬 생성을 중단시키지 않음."""

    def test_intent_collector_error_doesnt_break_pipeline(self):
        """intent_collector.collect_sync()가 예외를 던져도 씬 생성 계속."""
        collector = MagicMock()
        collector.collect_sync.side_effect = RuntimeError("의도 수집 실패")
        sgo = _make_sgo(intent_collector=collector)
        result = sgo.run_episode([_make_seq_plan(scene_count=2)])
        assert result.success
        assert result.total_scenes_generated == 2

    def test_action_resolver_error_doesnt_break_pipeline(self):
        """action_resolver.resolve()가 예외를 던져도 씬 생성 계속."""
        collector = MagicMock()
        collector.collect_sync.return_value = [_make_intent_packet()]
        resolver  = MagicMock()
        resolver.resolve.side_effect = RuntimeError("충돌 해석 실패")
        sgo = _make_sgo(intent_collector=collector, action_resolver=resolver)
        result = sgo.run_episode([_make_seq_plan(scene_count=2)])
        assert result.success
        assert result.total_scenes_generated == 2
