"""tests/unit/test_v621_sp_b2_retrofit.py

V621 SP-B.2 retrofit 60 TC — ADR-088 전체 커버리지.

커버 범위:
  §A  AgentRole + AgentEnvelope         (TC-01 ~ TC-12)
  §B  RoutingPolicy 4축                  (TC-13 ~ TC-24)
  §C  _bridge_generate_with_envelope()  (TC-25 ~ TC-32)
  §D  ReaderFeedback + RewardSignal     (TC-33 ~ TC-47)
  §E  OpenAPI SemVer (P-IF-04)          (TC-48 ~ TC-55)
  §F  detect_openapi_breaking + Rule-9  (TC-56 ~ TC-60)
"""
from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# 경로 설정
# ──────────────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from literary_system.llm_bridge.agent_envelope import (
    AgentRole,
    AgentEnvelope,
    RoutingDecision,
    RoutingPolicy,
)
from literary_system.llm_bridge.canonical_bridge_v2 import (
    _bridge_generate_with_envelope,
)
from literary_system.multiwork.reader_feedback_ingest import (
    ReaderFeedback,
    RewardSignal,
    RewardSignalAdapter,
    ReaderFeedbackIngest,
)
from literary_system.serving.model_serving_endpoint import (
    SEMVER,
    SEMVER_MAJOR,
    SEMVER_MINOR,
    SEMVER_PATCH,
    get_api_version_response,
    get_openapi_schema,
)


# ==============================================================================
# §A  AgentRole + AgentEnvelope  (TC-01 ~ TC-12)
# ==============================================================================


class TestAgentRole:
    """TC-01 ~ TC-05: AgentRole Enum 5종 검증."""

    def test_tc01_scene_writer_value(self):
        assert AgentRole.SCENE_WRITER.value == "scene_writer"

    def test_tc02_critic_value(self):
        assert AgentRole.CRITIC.value == "critic"

    def test_tc03_editor_value(self):
        assert AgentRole.EDITOR.value == "editor"

    def test_tc04_historian_value(self):
        assert AgentRole.HISTORIAN.value == "historian"

    def test_tc05_reader_voice_value(self):
        assert AgentRole.READER_VOICE.value == "reader_voice"


class TestAgentEnvelope:
    """TC-06 ~ TC-12: AgentEnvelope 기본값 + 필드 검증."""

    def test_tc06_default_agent_id(self):
        env = AgentEnvelope()
        assert env.agent_id == "default"

    def test_tc07_default_role_is_scene_writer(self):
        env = AgentEnvelope()
        assert env.role == AgentRole.SCENE_WRITER

    def test_tc08_default_prompt_empty(self):
        env = AgentEnvelope()
        assert env.prompt == ""

    def test_tc09_default_context_empty_dict(self):
        env = AgentEnvelope()
        assert env.context == {}

    def test_tc10_parent_agent_id_none(self):
        env = AgentEnvelope()
        assert env.parent_agent_id is None

    def test_tc11_session_id_none(self):
        env = AgentEnvelope()
        assert env.session_id is None

    def test_tc12_custom_fields_assigned(self):
        env = AgentEnvelope(
            agent_id="critic-01",
            role=AgentRole.CRITIC,
            prompt="Evaluate this scene.",
            context={"scene_id": "s001"},
            parent_agent_id="orchestrator",
            session_id="sess-xyz",
            metadata={"priority": 1},
        )
        assert env.agent_id == "critic-01"
        assert env.role == AgentRole.CRITIC
        assert env.prompt == "Evaluate this scene."
        assert env.context["scene_id"] == "s001"
        assert env.parent_agent_id == "orchestrator"
        assert env.session_id == "sess-xyz"
        assert env.metadata["priority"] == 1


# ==============================================================================
# §B  RoutingPolicy 4축  (TC-13 ~ TC-24)
# ==============================================================================


class TestRoutingPolicyWeights:
    """TC-13 ~ TC-18: 가중치 합 1.0 강제."""

    def test_tc13_default_weights_sum_to_one(self):
        policy = RoutingPolicy()
        total = (
            policy.cost_weight
            + policy.latency_weight
            + policy.quality_weight
            + policy.role_weight
        )
        assert abs(total - 1.0) < 1e-9

    def test_tc14_default_role_weight_is_0_1(self):
        policy = RoutingPolicy()
        assert policy.role_weight == pytest.approx(0.1)

    def test_tc15_custom_valid_weights(self):
        policy = RoutingPolicy(
            cost_weight=0.4,
            latency_weight=0.2,
            quality_weight=0.3,
            role_weight=0.1,
        )
        assert policy.cost_weight == pytest.approx(0.4)

    def test_tc16_invalid_weights_raise_value_error(self):
        with pytest.raises(ValueError, match="1.0"):
            RoutingPolicy(
                cost_weight=0.4,
                latency_weight=0.4,
                quality_weight=0.4,
                role_weight=0.1,
            )

    def test_tc17_zero_role_weight_valid(self):
        policy = RoutingPolicy(
            cost_weight=0.4,
            latency_weight=0.3,
            quality_weight=0.3,
            role_weight=0.0,
        )
        assert policy.role_weight == pytest.approx(0.0)

    def test_tc18_float_precision_tolerance(self):
        policy = RoutingPolicy(
            cost_weight=1 / 3,
            latency_weight=1 / 3,
            quality_weight=1 / 6,
            role_weight=1 / 6,
        )
        total = (1 / 3) + (1 / 3) + (1 / 6) + (1 / 6)
        assert abs(total - 1.0) < 1e-6


class TestRoutingPolicyDecide:
    """TC-19 ~ TC-24: decide_for_agent() 로직."""

    def _policy(self):
        return RoutingPolicy(
            cost_weight=0.3,
            latency_weight=0.3,
            quality_weight=0.3,
            role_weight=0.1,
            agent_routing={
                "special-agent": RoutingDecision.EXTERNAL_LLM,
                "cascade-agent": RoutingDecision.CASCADE,
                "critic": RoutingDecision.EXTERNAL_LLM,
            },
        )

    def test_tc19_agent_id_direct_mapping(self):
        policy = self._policy()
        env = AgentEnvelope(agent_id="special-agent")
        assert policy.decide_for_agent(env) == RoutingDecision.EXTERNAL_LLM

    def test_tc20_cascade_agent_mapping(self):
        policy = self._policy()
        env = AgentEnvelope(agent_id="cascade-agent")
        assert policy.decide_for_agent(env) == RoutingDecision.CASCADE

    def test_tc21_role_value_fallback(self):
        policy = self._policy()
        env = AgentEnvelope(agent_id="unknown-id", role=AgentRole.CRITIC)
        assert policy.decide_for_agent(env) == RoutingDecision.EXTERNAL_LLM

    def test_tc22_default_local_lora(self):
        policy = self._policy()
        env = AgentEnvelope(agent_id="nobody", role=AgentRole.HISTORIAN)
        assert policy.decide_for_agent(env) == RoutingDecision.LOCAL_LORA

    def test_tc23_empty_routing_always_local_lora(self):
        policy = RoutingPolicy()
        for role in AgentRole:
            env = AgentEnvelope(role=role)
            assert policy.decide_for_agent(env) == RoutingDecision.LOCAL_LORA

    def test_tc24_agent_id_priority_over_role(self):
        policy = RoutingPolicy(
            cost_weight=0.3,
            latency_weight=0.3,
            quality_weight=0.3,
            role_weight=0.1,
            agent_routing={
                "agent-x": RoutingDecision.LOCAL_LORA,
                "critic": RoutingDecision.EXTERNAL_LLM,
            },
        )
        env = AgentEnvelope(agent_id="agent-x", role=AgentRole.CRITIC)
        assert policy.decide_for_agent(env) == RoutingDecision.LOCAL_LORA


# ==============================================================================
# §C  _bridge_generate_with_envelope()  (TC-25 ~ TC-32)
# ==============================================================================


class TestBridgeGenerateWithEnvelope:
    """TC-25 ~ TC-32: str/envelope 이중 입력 + 라우팅 분기."""

    def _mock_bridge(self, return_value="generated"):
        bridge = MagicMock()
        bridge.generate.return_value = return_value
        return bridge

    def test_tc25_str_input_calls_generate(self):
        bridge = self._mock_bridge("scene text")
        result = _bridge_generate_with_envelope(bridge, "Hello prompt")
        bridge.generate.assert_called_once_with("Hello prompt")
        assert result == "scene text"

    def test_tc26_str_input_returns_generate_output(self):
        bridge = self._mock_bridge("output-abc")
        result = _bridge_generate_with_envelope(bridge, "test")
        assert result == "output-abc"

    def test_tc27_envelope_default_local_lora(self):
        """TC-27: 봉투 + 빈 정책 → LOCAL_LORA → generate() 호출 (model_type='local' 주입)."""
        bridge = self._mock_bridge("envelope-out")
        env = AgentEnvelope(prompt="Envelope prompt")
        result = _bridge_generate_with_envelope(bridge, env, policy=RoutingPolicy())
        # LOCAL_LORA 경로: model_type='local' 자동 주입
        bridge.generate.assert_called_once_with("Envelope prompt", model_type="local")
        assert result == "envelope-out"

    def test_tc28_envelope_without_policy_uses_local_lora(self):
        bridge = self._mock_bridge("no-policy")
        env = AgentEnvelope(prompt="No policy prompt")
        _bridge_generate_with_envelope(bridge, env)
        bridge.generate.assert_called_once()

    def test_tc29_envelope_external_llm_routing(self):
        bridge = self._mock_bridge("external-out")
        policy = RoutingPolicy(
            cost_weight=0.3,
            latency_weight=0.3,
            quality_weight=0.3,
            role_weight=0.1,
            agent_routing={"agent-ext": RoutingDecision.EXTERNAL_LLM},
        )
        env = AgentEnvelope(agent_id="agent-ext", prompt="External prompt")
        result = _bridge_generate_with_envelope(bridge, env, policy=policy)
        assert result is not None

    def test_tc30_envelope_cascade_routing(self):
        bridge = self._mock_bridge("cascade-out")
        policy = RoutingPolicy(
            cost_weight=0.3,
            latency_weight=0.3,
            quality_weight=0.3,
            role_weight=0.1,
            agent_routing={"agent-cas": RoutingDecision.CASCADE},
        )
        env = AgentEnvelope(agent_id="agent-cas", prompt="Cascade prompt")
        result = _bridge_generate_with_envelope(bridge, env, policy=policy)
        assert result is not None

    def test_tc31_envelope_passes_kwargs_to_generate(self):
        bridge = self._mock_bridge()
        _bridge_generate_with_envelope(bridge, "prompt", max_tokens=256)
        bridge.generate.assert_called_once_with("prompt", max_tokens=256)

    def test_tc32_envelope_prompt_forwarded(self):
        bridge = self._mock_bridge("result")
        env = AgentEnvelope(prompt="specific-prompt")
        _bridge_generate_with_envelope(bridge, env)
        call_args = bridge.generate.call_args
        assert "specific-prompt" in str(call_args)


# ==============================================================================
# §D  ReaderFeedback + ReaderFeedbackIngest  (TC-33 ~ TC-47)
# ==============================================================================


class TestReaderFeedback:
    """TC-33 ~ TC-40: ReaderFeedback 데이터 검증."""

    def _make_fb(self, rating=4, **kwargs):
        defaults = dict(reader_id="r1", work_id="w1", scene_id="s1", rating=rating)
        defaults.update(kwargs)
        return ReaderFeedback(**defaults)

    def test_tc33_valid_rating_1(self):
        fb = self._make_fb(rating=1)
        assert fb.rating == 1

    def test_tc34_valid_rating_5(self):
        fb = self._make_fb(rating=5)
        assert fb.rating == 5

    def test_tc35_invalid_rating_0_raises(self):
        with pytest.raises(ValueError, match="rating"):
            self._make_fb(rating=0)

    def test_tc36_invalid_rating_6_raises(self):
        with pytest.raises(ValueError, match="rating"):
            self._make_fb(rating=6)

    def test_tc37_timestamp_auto_set_utc(self):
        before = datetime.now(tz=timezone.utc)
        fb = self._make_fb()
        after = datetime.now(tz=timezone.utc)
        assert fb.timestamp is not None
        assert before <= fb.timestamp <= after

    def test_tc38_explicit_timestamp_preserved(self):
        ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        fb = self._make_fb(timestamp=ts)
        assert fb.timestamp == ts

    def test_tc39_to_dict_has_required_keys(self):
        fb = self._make_fb(rating=3, comment="Nice!")
        d = fb.to_dict()
        for key in ["reader_id", "work_id", "scene_id", "rating",
                    "comment", "timestamp", "reader_demographic", "engagement_seconds"]:
            assert key in d, f"키 누락: {key}"

    def test_tc40_to_dict_rating_value(self):
        fb = self._make_fb(rating=2)
        assert fb.to_dict()["rating"] == 2


class TestReaderFeedbackIngest:
    """TC-41 ~ TC-47: ReaderFeedbackIngest Phase B/C+ 이중 동작."""

    def _fb(self):
        return ReaderFeedback(
            reader_id="r1", work_id="w1", scene_id="s1", rating=4
        )

    def test_tc41_phase_b_ingest_raises_not_implemented(self):
        ingest = ReaderFeedbackIngest()
        with pytest.raises(NotImplementedError):
            ingest.ingest(self._fb())

    def test_tc42_is_phase_c_active_false_when_no_adapter(self):
        ingest = ReaderFeedbackIngest()
        assert ingest.is_phase_c_active() is False

    def test_tc43_is_phase_c_active_true_when_adapter_injected(self):
        adapter = MagicMock(spec=RewardSignalAdapter)
        ingest = ReaderFeedbackIngest(reward_adapter=adapter)
        assert ingest.is_phase_c_active() is True

    def test_tc44_phase_c_ingest_calls_adapter(self):
        fb = self._fb()
        adapter = MagicMock()
        adapter.from_feedback.return_value = RewardSignal(scene_id="s1", reward=0.8)
        ingest = ReaderFeedbackIngest(reward_adapter=adapter)
        ingest.ingest(fb)
        adapter.from_feedback.assert_called_once_with(fb)

    def test_tc45_ingested_count_increments(self):
        adapter = MagicMock()
        adapter.from_feedback.return_value = RewardSignal(scene_id="s1", reward=0.5)
        ingest = ReaderFeedbackIngest(reward_adapter=adapter)
        for _ in range(3):
            ingest.ingest(self._fb())
        assert ingest.ingested_count() == 3

    def test_tc46_summary_reflects_state(self):
        ingest = ReaderFeedbackIngest()
        s = ingest.summary()
        assert s["phase_c_active"] is False
        assert s["ingested_count"] == 0
        assert s["history_size"] == 0

    def test_tc47_type_error_on_invalid_feedback(self):
        adapter = MagicMock()
        ingest = ReaderFeedbackIngest(reward_adapter=adapter)
        with pytest.raises(TypeError):
            ingest.ingest("not-a-feedback")


# ==============================================================================
# §E  OpenAPI SemVer (P-IF-04)  (TC-48 ~ TC-55)
# ==============================================================================


class TestOpenAPISemver:
    """TC-48 ~ TC-55: SEMVER 상수 + get_openapi_schema() + get_api_version_response()."""

    def test_tc48_semver_major_is_1(self):
        assert SEMVER_MAJOR == 1

    def test_tc49_semver_minor_is_0(self):
        assert SEMVER_MINOR == 0

    def test_tc50_semver_patch_is_0(self):
        assert SEMVER_PATCH == 0

    def test_tc51_semver_string_format(self):
        assert SEMVER == f"{SEMVER_MAJOR}.{SEMVER_MINOR}.{SEMVER_PATCH}"

    def test_tc52_get_api_version_response_key(self):
        resp = get_api_version_response()
        assert "semver" in resp

    def test_tc53_get_api_version_response_value(self):
        resp = get_api_version_response()
        assert resp["semver"] == SEMVER

    def test_tc54_get_openapi_schema_has_openapi_field(self):
        schema = get_openapi_schema()
        assert "openapi" in schema

    def test_tc55_get_openapi_schema_paths_has_api_version(self):
        schema = get_openapi_schema()
        assert "paths" in schema
        assert "/api_version" in schema["paths"]


# ==============================================================================
# §F  detect_openapi_breaking + Rule-9 (V621-PRE)  (TC-56 ~ TC-60)
# ==============================================================================


class TestDetectOpenAPIBreaking:
    """TC-56 ~ TC-58: detect_openapi_breaking.py CLI 동작."""

    SCRIPT = str(REPO_ROOT / "tools" / "detect_openapi_breaking.py")

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, self.SCRIPT, *args],
            capture_output=True,
            text=True,
        )

    def test_tc56_major_match_exit_0(self):
        result = self._run("--baseline", "1")
        assert result.returncode == 0, result.stderr

    def test_tc57_major_mismatch_exit_1(self):
        result = self._run("--baseline", "2")
        assert result.returncode == 1

    def test_tc58_warn_only_mismatch_exit_0(self):
        result = self._run("--baseline", "2", "--warn-only")
        assert result.returncode == 0


class TestPreflight15Rule9:
    """TC-59 ~ TC-60: Rule-9 check_v3_handoff() Violation 검증."""

    def _load_pf15(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "preflight_step15_tc59",
            str(REPO_ROOT / "tools" / "preflight_step15.py"),
        )
        pf15 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pf15)
        return pf15

    def test_tc59_rule9_violation_code_is_v3_handoff_missing(self):
        import tempfile
        pf15 = self._load_pf15()
        with tempfile.TemporaryDirectory() as tmp:
            original = pf15.REPO_ROOT
            pf15.REPO_ROOT = Path(tmp)
            try:
                violations = pf15.check_v3_handoff()
            finally:
                pf15.REPO_ROOT = original
        assert len(violations) >= 1
        codes = [v.code for v in violations]
        assert "V3_HANDOFF_MISSING" in codes

    def test_tc60_rule9_violation_level_high(self):
        import tempfile
        pf15 = self._load_pf15()
        with tempfile.TemporaryDirectory() as tmp:
            original = pf15.REPO_ROOT
            pf15.REPO_ROOT = Path(tmp)
            try:
                violations = pf15.check_v3_handoff()
            finally:
                pf15.REPO_ROOT = original
        high_violations = [v for v in violations if v.code == "V3_HANDOFF_MISSING"]
        assert len(high_violations) >= 1
        assert high_violations[0].level == "HIGH"
