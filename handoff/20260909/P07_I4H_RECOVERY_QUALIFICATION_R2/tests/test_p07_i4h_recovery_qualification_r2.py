"""P07-I4H Recovery Qualification R2.

NEW recovery evidence only. This file is not, and must never be described as,
the missing historical tests/test_p07_i4h_runtime_promotion.py body.

The suite exercises the durable I4H contract without authoring literary prose.
Full parent-targeted and nonhistorical regressions remain separate promotion gates.
"""
from __future__ import annotations

from copy import deepcopy
import inspect
import pathlib

import pytest

import literary_os_runtime.i4h_intervention_policy as policy
import literary_os_runtime.i4h_runtime_renderer as rr
import literary_os_runtime.i4h_episode_render_wiring as ew


def profile(**overrides):
    p = {
        "exposition_risk": 0,
        "procedural_pressure": 0,
        "social_texture": 0,
        "voice_specificity": 0,
        "already_playable": 0,
        "physicalizable_subtext": 0,
    }
    p.update(overrides)
    return p


def scene(dialogue="alpha beta gamma delta", subtext="steady"):
    return {
        "beats": [
            {"kind": "DIALOGUE", "speaker": "A", "text": dialogue},
            {"kind": "ACTION", "text": "action"},
        ],
        "subtext": subtext,
    }


def reliability_pass():
    return {k: "PASS" for k in rr.RELIABILITY_FIELDS}


def craft_pass():
    return {"verdict": "PASS"}


class FakeProvider:
    def __init__(self, revision=None, error=None):
        self.revision = deepcopy(revision)
        self.error = error
        self.baseline_calls = 0
        self.revision_calls = 0
        self.transport_adapter = None

    def generate(self, payload):
        self.revision_calls += 1
        if self.error is not None:
            raise self.error
        return deepcopy(self.revision)


def committed_baseline():
    return {
        "status": "COMMIT",
        "scene_render": scene(),
        "provenance": {"baseline": True},
        "attempts": [{"n": 1}],
    }


def revision_ok(candidate=None, *, test_double=False):
    return {
        "status": "OK",
        "scene_render": deepcopy(candidate or scene("alpha beta gamma", "moved")),
        "provenance": {"test_double": bool(test_double)},
    }


def install_render_flow(monkeypatch, provider, *, baseline=None, claim=None, delta=None):
    baseline = deepcopy(baseline if baseline is not None else committed_baseline())
    claim = deepcopy(claim if claim is not None else {"decision": "PASS"})
    delta = deepcopy(delta if delta is not None else {"decision": "PASS"})

    def fake_baseline(*args, **kwargs):
        provider.baseline_calls += 1
        return deepcopy(baseline), {"baseline_trace": True}

    monkeypatch.setattr(rr, "render_scene_provider_backed", fake_baseline)
    monkeypatch.setattr(rr, "make_trace", lambda *a, **k: {"trace": True})
    monkeypatch.setattr(
        rr,
        "build_scene_render_payload",
        lambda *a, **k: {"authorized_speakers": ["A"], "synthetic": True},
    )
    monkeypatch.setattr(rr, "validate_provider_claim", lambda *a, **k: deepcopy(claim))
    monkeypatch.setattr(rr, "evaluate_i4h_delta_guards", lambda *a, **k: deepcopy(delta))
    return baseline


def call_render(provider, p, *, reliability=None, craft=None, allow_test_double=False):
    reliability = reliability if reliability is not None else (lambda *a: reliability_pass())
    craft = craft if craft is not None else (lambda *a: craft_pass())
    return rr.render_scene_i4h(
        provider,
        {"scene_id": "SC01"},
        {"exit_state": "E"},
        {"characters": ["A"]},
        {"ensemble": True},
        {"texture": True},
        lambda *a: {"verdict": "PASS"},
        p,
        reliability,
        craft,
        allow_test_double=allow_test_double,
    )


# ---------------------------------------------------------------------------
# Profile schema and selector contract
# ---------------------------------------------------------------------------

def test_01_profile_must_be_mapping():
    with pytest.raises(ValueError, match="I4H_PROFILE_MUST_BE_MAPPING"):
        policy.validate_i4h_profile(None)


def test_02_profile_missing_field_rejected():
    p = profile()
    p.pop("physicalizable_subtext")
    with pytest.raises(ValueError, match="I4H_PROFILE_MISSING"):
        policy.validate_i4h_profile(p)


def test_03_profile_extra_field_rejected():
    with pytest.raises(ValueError, match="I4H_PROFILE_EXTRA"):
        policy.validate_i4h_profile({**profile(), "unexpected": 1})


def test_04_profile_bool_rejected_as_integer():
    with pytest.raises(ValueError, match="I4H_PROFILE_RANGE"):
        policy.validate_i4h_profile(profile(exposition_risk=True))


def test_05_profile_negative_rejected():
    with pytest.raises(ValueError, match="I4H_PROFILE_RANGE"):
        policy.validate_i4h_profile(profile(exposition_risk=-1))


def test_06_profile_above_three_rejected():
    with pytest.raises(ValueError, match="I4H_PROFILE_RANGE"):
        policy.validate_i4h_profile(profile(exposition_risk=4))


def test_07_profile_boundaries_zero_and_three_pass():
    out = policy.validate_i4h_profile(
        profile(
            exposition_risk=3,
            procedural_pressure=3,
            social_texture=3,
            voice_specificity=3,
            already_playable=3,
            physicalizable_subtext=3,
        )
    )
    assert out["decision"] == "PASS"
    assert all(0 <= v <= 3 for v in out["profile"].values())


def test_08_selector_abstains_on_already_playable_low_exposition():
    out = policy.select_i4h_intervention(profile(already_playable=2, exposition_risk=1))
    assert out["decision"] == "ABSTAIN"
    assert out["reason"] == "ALREADY_PLAYABLE_LOW_EXPOSITION"


def test_09_selector_abstains_to_protect_high_social_texture():
    out = policy.select_i4h_intervention(profile(social_texture=3, exposition_risk=1))
    assert out["decision"] == "ABSTAIN"
    assert out["reason"] == "PROTECT_HIGH_SOCIAL_OR_VOICE_TEXTURE"


def test_10_selector_standard_for_procedural_exposition_case():
    out = policy.select_i4h_intervention(
        profile(exposition_risk=3, procedural_pressure=3, already_playable=0)
    )
    assert out["decision"] == "STANDARD"


def test_11_selector_low_for_physicalizable_subtext():
    out = policy.select_i4h_intervention(profile(physicalizable_subtext=2))
    assert out["decision"] == "LOW"


def test_12_selector_low_for_exposition_without_standard_conditions():
    out = policy.select_i4h_intervention(profile(exposition_risk=2, procedural_pressure=0))
    assert out["decision"] == "LOW"


def test_13_selector_defaults_to_abstain():
    out = policy.select_i4h_intervention(profile())
    assert out["decision"] == "ABSTAIN"


def test_14_selector_never_authors_literary_prose():
    for p in (
        profile(),
        profile(physicalizable_subtext=2),
        profile(exposition_risk=3, procedural_pressure=3),
    ):
        assert policy.select_i4h_intervention(p)["python_literary_prose_generated"] is False


# ---------------------------------------------------------------------------
# Revision constraints and external judgment validation
# ---------------------------------------------------------------------------

def test_15_low_constraints_are_frozen():
    c = policy.revision_constraints("LOW")
    assert c["dialogue_retention_min"] == pytest.approx(0.75)
    assert c["total_char_ratio_max"] == pytest.approx(1.35)


def test_16_standard_constraints_are_frozen():
    c = policy.revision_constraints("STANDARD")
    assert c["dialogue_retention_min"] == pytest.approx(0.55)
    assert c["total_char_ratio_max"] == pytest.approx(1.25)


def test_17_abstain_constraints_are_exact_no_revision():
    c = policy.revision_constraints("ABSTAIN")
    assert c["dialogue_retention_min"] == 1.0
    assert c["total_char_ratio_max"] == 1.0
    assert c["operation"] == "NO_REVISION"


def test_18_unknown_revision_decision_rejected():
    with pytest.raises(ValueError, match="I4H_DECISION_UNKNOWN"):
        policy.revision_constraints("OTHER")


def test_19_missing_external_reliability_judgment_blocks():
    out = rr.validate_external_reliability_judgment(None)
    assert out == {"decision": "BLOCK", "reason": "EXTERNAL_RELIABILITY_JUDGMENT_MISSING"}


def test_20_missing_external_reliability_field_blocks():
    j = reliability_pass()
    j.pop(rr.RELIABILITY_FIELDS[0])
    out = rr.validate_external_reliability_judgment(j)
    assert out["decision"] == "BLOCK"
    assert out["reason"] == "EXTERNAL_RELIABILITY_FIELDS_MISSING"


def test_21_any_external_reliability_nonpass_blocks():
    j = reliability_pass()
    j["voice_social_texture"] = "HOLD"
    out = rr.validate_external_reliability_judgment(j)
    assert out["decision"] == "BLOCK"
    assert out["reason"] == "EXTERNAL_RELIABILITY_NONPASS"
    assert "voice_social_texture" in out["failed"]


def test_22_all_external_reliability_fields_pass():
    assert rr.validate_external_reliability_judgment(reliability_pass())["decision"] == "PASS"


def test_23_missing_external_craft_judgment_blocks():
    out = rr.validate_external_craft_judgment(None)
    assert out["decision"] == "BLOCK"
    assert out["reason"] == "EXTERNAL_CRAFT_JUDGMENT_MISSING"


def test_24_external_craft_nonpass_blocks():
    out = rr.validate_external_craft_judgment({"verdict": "HOLD"})
    assert out["decision"] == "BLOCK"
    assert out["reason"] == "EXTERNAL_CRAFT_NONPASS"


def test_25_external_craft_pass_is_accepted():
    assert rr.validate_external_craft_judgment(craft_pass())["decision"] == "PASS"


# ---------------------------------------------------------------------------
# Deterministic text-delta helpers
# ---------------------------------------------------------------------------

def test_26_dialogue_retention_ratio(monkeypatch):
    monkeypatch.setattr(rr, "validate_scene_render_shape", lambda x: None)
    base = scene("alpha beta gamma delta")
    cand = scene("alpha beta gamma")
    assert rr.dialogue_retention_ratio(base, cand) == pytest.approx(0.75)


def test_27_total_character_ratio(monkeypatch):
    monkeypatch.setattr(rr, "validate_scene_render_shape", lambda x: None)
    base = scene("abcd", "")
    cand = scene("abcdefgh", "")
    ratio = rr.total_character_ratio(base, cand)
    assert ratio > 1.0


def test_28_new_foreign_script_tokens_are_delta_only(monkeypatch):
    monkeypatch.setattr(rr, "validate_scene_render_shape", lambda x: None)
    base = scene("기존 QR 유지")
    cand = scene("기존 QR 유지 NEWTOKEN")
    out = rr.new_foreign_script_tokens(base, cand)
    assert "qr" not in out
    assert "newtoken" in out


def test_29_revision_payload_rejects_abstain(monkeypatch):
    monkeypatch.setattr(rr, "build_scene_render_payload", lambda *a, **k: {})
    with pytest.raises(ValueError, match="I4H_REVISION_REQUIRES_LOW_OR_STANDARD"):
        rr.build_i4h_revision_payload({}, {}, {}, {}, {}, scene(), profile(), "ABSTAIN")


def test_30_revision_payload_carries_exact_baseline_and_policy(monkeypatch):
    monkeypatch.setattr(rr, "build_scene_render_payload", lambda *a, **k: {"parent": True})
    base = scene()
    out = rr.build_i4h_revision_payload(
        {}, {}, {}, {}, {}, base, profile(physicalizable_subtext=2), "LOW"
    )
    assert out["i4h_baseline_scene"] == base
    assert out["i4h_baseline_scene"] is not base
    assert out["i4h_intervention_policy"]["decision"] == "LOW"
    assert out["i4h_intervention_policy"]["fail_closed_to_baseline"] is True


# ---------------------------------------------------------------------------
# Fail-closed scene runtime flow
# ---------------------------------------------------------------------------

def test_31_baseline_noncommit_never_attempts_revision(monkeypatch):
    provider = FakeProvider(revision=revision_ok())
    baseline = {"status": "HOLD", "scene_render": None, "reason": "baseline hold"}
    install_render_flow(monkeypatch, provider, baseline=baseline)
    out, _ = call_render(provider, profile(exposition_risk=3, procedural_pressure=3))
    assert out == baseline
    assert provider.baseline_calls == 1
    assert provider.revision_calls == 0


def test_32_abstain_is_exact_baseline_and_one_baseline_call(monkeypatch):
    provider = FakeProvider(revision=revision_ok())
    baseline = install_render_flow(monkeypatch, provider)
    out, _ = call_render(provider, profile(already_playable=2, exposition_risk=1))
    assert out == baseline
    assert provider.baseline_calls == 1
    assert provider.revision_calls == 0


def test_33_revision_provider_exception_falls_back(monkeypatch):
    provider = FakeProvider(error=RuntimeError("synthetic provider error"))
    baseline = install_render_flow(monkeypatch, provider)
    out, _ = call_render(provider, profile(exposition_risk=3, procedural_pressure=3))
    assert out == baseline
    assert provider.baseline_calls == 1
    assert provider.revision_calls == 1


def test_34_revision_provider_status_reject_falls_back(monkeypatch):
    provider = FakeProvider(revision={"status": "HOLD", "scene_render": scene(), "provenance": {}})
    baseline = install_render_flow(monkeypatch, provider)
    out, _ = call_render(provider, profile(exposition_risk=3, procedural_pressure=3))
    assert out == baseline


def test_35_revision_provider_claim_reject_falls_back(monkeypatch):
    provider = FakeProvider(revision=revision_ok())
    baseline = install_render_flow(monkeypatch, provider, claim={"decision": "BLOCK"})
    out, _ = call_render(provider, profile(exposition_risk=3, procedural_pressure=3))
    assert out == baseline


def test_36_explicit_test_double_can_be_admissible_only_when_allowed(monkeypatch):
    provider = FakeProvider(revision=revision_ok(test_double=True))
    install_render_flow(monkeypatch, provider, claim={"decision": "BLOCK"})
    out, _ = call_render(
        provider,
        profile(exposition_risk=3, procedural_pressure=3),
        allow_test_double=True,
    )
    assert out["status"] == "COMMIT"
    assert out["i4h_runtime"]["fallback_to_baseline"] is False


def test_37_delta_guard_reject_falls_back(monkeypatch):
    provider = FakeProvider(revision=revision_ok())
    baseline = install_render_flow(
        monkeypatch,
        provider,
        delta={"decision": "BLOCK", "reason": "SYNTHETIC_DELTA_REJECT"},
    )
    out, _ = call_render(provider, profile(physicalizable_subtext=2))
    assert out == baseline


def test_38_external_reliability_reject_falls_back(monkeypatch):
    provider = FakeProvider(revision=revision_ok())
    baseline = install_render_flow(monkeypatch, provider)
    bad = reliability_pass()
    bad["semantic_source_future_fidelity"] = "BLOCK"
    out, _ = call_render(
        provider,
        profile(physicalizable_subtext=2),
        reliability=lambda *a: bad,
    )
    assert out == baseline


def test_39_external_craft_reject_falls_back(monkeypatch):
    provider = FakeProvider(revision=revision_ok())
    baseline = install_render_flow(monkeypatch, provider)
    out, _ = call_render(
        provider,
        profile(physicalizable_subtext=2),
        craft=lambda *a: {"verdict": "HOLD"},
    )
    assert out == baseline


def test_40_candidate_commits_only_after_all_gates_pass(monkeypatch):
    candidate = scene("alpha beta gamma", "moved")
    provider = FakeProvider(revision=revision_ok(candidate))
    install_render_flow(monkeypatch, provider)
    out, _ = call_render(provider, profile(physicalizable_subtext=2))
    assert out["status"] == "COMMIT"
    assert out["scene_render"] == candidate
    assert out["i4h_runtime"]["fallback_to_baseline"] is False
    assert out["i4h_runtime"]["python_literary_prose_generated"] is False
    assert provider.baseline_calls == 1
    assert provider.revision_calls == 1


# ---------------------------------------------------------------------------
# Episode wiring contract
# ---------------------------------------------------------------------------

def episode_plan():
    return {
        "sequences": [
            {
                "sequence_id": "SQ01",
                "scenes": [
                    {"scene_id": "SC01"},
                    {"scene_id": "SC02"},
                ],
            },
            {
                "sequence_id": "SQ02",
                "scenes": [
                    {"scene_id": "SC03"},
                ],
            },
        ]
    }


def lowered(scene_obj):
    return {
        "scene_blueprint": deepcopy(scene_obj),
        "scene_contract": {},
        "character_context": {},
        "ensemble_context": {},
        "texture_contract": {},
    }


def test_41_episode_wiring_rejects_missing_profile(monkeypatch):
    monkeypatch.setattr(
        ew,
        "materialize_renderer_input_from_semantic_scene",
        lambda s, character_voice_by_name=None: (lowered(s), {"bridge": s["scene_id"]}),
    )
    with pytest.raises(ValueError, match="I4H_PROFILE_MISSING_FOR_SCENE:SC02"):
        ew.render_episode_i4h(
            object(),
            episode_plan(),
            {"SC01": profile()},
            lambda *a: {},
            lambda *a: {},
            lambda *a: {},
        )


def test_42_episode_wiring_preserves_sequence_scene_order(monkeypatch):
    calls = []

    monkeypatch.setattr(
        ew,
        "materialize_renderer_input_from_semantic_scene",
        lambda s, character_voice_by_name=None: (lowered(s), {"bridge": s["scene_id"]}),
    )

    def fake_render(provider, scene_blueprint, *args, **kwargs):
        calls.append(scene_blueprint["scene_id"])
        return {"status": "COMMIT", "scene_render": scene()}, {"render": scene_blueprint["scene_id"]}

    monkeypatch.setattr(ew, "render_scene_i4h", fake_render)
    profiles = {sid: profile() for sid in ("SC01", "SC02", "SC03")}
    out, traces = ew.render_episode_i4h(
        object(),
        episode_plan(),
        profiles,
        lambda *a: {},
        lambda *a: {},
        lambda *a: {},
    )
    assert calls == ["SC01", "SC02", "SC03"]
    assert [(r["sequence_id"], r["scene_id"]) for r in out["results"]] == [
        ("SQ01", "SC01"),
        ("SQ01", "SC02"),
        ("SQ02", "SC03"),
    ]
    assert out["scene_count"] == 3
    assert out["python_literary_prose_generated"] is False
    assert len(traces) == 6


# ---------------------------------------------------------------------------
# Static recovery-safety checks
# ---------------------------------------------------------------------------

def test_43_runtime_modules_declare_python_no_literary_prose():
    assert "authors no literary prose" in (inspect.getdoc(policy) or "").lower()
    assert "python never writes literary prose" in (inspect.getdoc(rr) or "").lower()
    assert "no literary prose is authored by python" in (inspect.getdoc(ew) or "").lower()


def test_44_runtime_source_has_no_historical_test_identity_claim():
    source = "\n".join(
        [
            inspect.getsource(policy),
            inspect.getsource(rr),
            inspect.getsource(ew),
        ]
    )
    assert "9b7ef43744dfe094b2b1d1ec850c8712ba38a1f450a11c689ff43215f01fbf7a" not in source
    assert "tests/test_p07_i4h_runtime_promotion.py" not in source


def test_45_recovery_suite_self_identifies_as_new_evidence():
    text = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert "NEW recovery evidence only" in text
    assert "must never be described as" in text


# Promotion-gate note:
# - This file intentionally does not claim to execute parent targeted or full
#   nonhistorical regression. Those are separate required commands after the
#   exact Sync R6 materialization exists in a trustworthy execution runtime.
# - Actual pass count must be reported from pytest. Historical 42/42 labeling
#   is prohibited unless an independently implemented suite truly contains
#   exactly 42 tests and all execute PASS; this recovery suite currently has
#   its own explicit test count and identity.
