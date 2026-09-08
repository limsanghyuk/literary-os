"""P07-I4H fail-closed two-pass runtime overlay.

Pass 1 is the existing I4D provider-backed renderer. Python never writes literary prose.
LOW/STANDARD may request one provider revision; every failed guard returns the committed
I4D baseline result unchanged.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib, json, re
from .trace import make_trace
from .verified_runtime import validate_provider_claim
from .provider_backed_renderer import (
    OpenAIResponsesProvider,
    build_scene_render_payload,
    evaluate_render_contract_locally,
    render_scene_provider_backed,
    validate_scene_render_shape,
)
from .i4h_intervention_policy import (
    select_i4h_intervention, revision_constraints, canonical_i4h_profile,
)

RELIABILITY_FIELDS=(
    "semantic_source_future_fidelity",
    "new_principal_character",
    "korean_morphology_grammar",
    "voice_social_texture",
    "dialogue_overcompression",
    "direction_bloat",
)
I4H_RUNTIME_VERSION="I4HRuntimeOverlayR1"
_LATIN_TOKEN=re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_TOKEN=re.compile(r"[0-9A-Za-z가-힣]+")

def _canon(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"))

def _sha(v):
    return hashlib.sha256(_canon(v).encode("utf-8")).hexdigest()

def _beats(render):
    validate_scene_render_shape(render)
    return list(render.get("beats") or [])

def _surface_text(render):
    return "\n".join([b["text"] for b in _beats(render)] + [render.get("subtext","")])

def _dialogue_text(render):
    return "\n".join(b["text"] for b in _beats(render) if b.get("kind")=="DIALOGUE")

def _token_counter(text):
    return Counter(x.casefold() for x in _TOKEN.findall(str(text or "")))

def dialogue_retention_ratio(baseline_render,candidate_render):
    base=_token_counter(_dialogue_text(baseline_render))
    cand=_token_counter(_dialogue_text(candidate_render))
    total=sum(base.values())
    if total==0:
        return 1.0
    retained=sum(min(n,cand.get(tok,0)) for tok,n in base.items())
    return retained/total

def total_character_ratio(baseline_render,candidate_render):
    b=len(_surface_text(baseline_render))
    c=len(_surface_text(candidate_render))
    return (c/b) if b else (1.0 if c==0 else float("inf"))

def new_foreign_script_tokens(baseline_render,candidate_render):
    base={x.casefold() for x in _LATIN_TOKEN.findall(_surface_text(baseline_render))}
    cand={x.casefold() for x in _LATIN_TOKEN.findall(_surface_text(candidate_render))}
    return sorted(cand-base)

def build_i4h_revision_payload(
    scene_blueprint,scene_contract,character_context,ensemble_context,texture_contract,
    baseline_scene,profile,decision,
):
    d=str(decision).upper()
    if d not in {"LOW","STANDARD"}:
        raise ValueError("I4H_REVISION_REQUIRES_LOW_OR_STANDARD")
    payload=build_scene_render_payload(
        scene_blueprint,scene_contract,character_context,ensemble_context,texture_contract
    )
    payload["i4h_intervention_policy"]={
        "runtime_version":I4H_RUNTIME_VERSION,
        "decision":d,
        "profile":canonical_i4h_profile(profile),
        "constraints":revision_constraints(d),
        "fail_closed_to_baseline":True,
    }
    payload["i4h_baseline_scene"]=deepcopy(baseline_scene)
    return payload

def evaluate_i4h_delta_guards(render_payload,baseline_render,candidate_render,decision):
    d=str(decision).upper()
    constraints=revision_constraints(d)
    try:
        validate_scene_render_shape(candidate_render)
    except Exception as e:
        return {"decision":"BLOCK","reason":"OUTPUT_SCHEMA_INVALID","critical":[str(e)]}
    provider_result={"status":"OK","scene_render":deepcopy(candidate_render)}
    local=evaluate_render_contract_locally(render_payload,provider_result)
    if local.get("decision")!="PASS":
        return {"decision":"BLOCK","reason":local.get("reason"),"critical":deepcopy(local.get("critical") or [])}
    foreign=new_foreign_script_tokens(baseline_render,candidate_render)
    if foreign:
        return {"decision":"BLOCK","reason":"NEW_FOREIGN_SCRIPT_TOKEN","critical":foreign}
    retention=dialogue_retention_ratio(baseline_render,candidate_render)
    if retention+1e-12 < float(constraints["dialogue_retention_min"]):
        return {"decision":"BLOCK","reason":"DIALOGUE_RETENTION_BELOW_FLOOR","critical":[retention]}
    char_ratio=total_character_ratio(baseline_render,candidate_render)
    if char_ratio-1e-12 > float(constraints["total_char_ratio_max"]):
        return {"decision":"BLOCK","reason":"TOTAL_CHAR_RATIO_ABOVE_CEILING","critical":[char_ratio]}
    return {
        "decision":"PASS",
        "reason":"I4H_DETERMINISTIC_DELTA_GUARDS_PASS",
        "critical":[],
        "dialogue_retention_ratio":retention,
        "total_char_ratio":char_ratio,
        "new_foreign_script_tokens":foreign,
    }

def validate_external_reliability_judgment(judgment):
    if not isinstance(judgment,dict):
        return {"decision":"BLOCK","reason":"EXTERNAL_RELIABILITY_JUDGMENT_MISSING"}
    missing=[k for k in RELIABILITY_FIELDS if k not in judgment]
    if missing:
        return {"decision":"BLOCK","reason":"EXTERNAL_RELIABILITY_FIELDS_MISSING","missing":missing}
    failed=[k for k in RELIABILITY_FIELDS if judgment.get(k)!="PASS"]
    if failed:
        return {"decision":"BLOCK","reason":"EXTERNAL_RELIABILITY_NONPASS","failed":failed}
    return {"decision":"PASS","reason":"EXTERNAL_RELIABILITY_PASS"}

def validate_external_craft_judgment(judgment):
    if not isinstance(judgment,dict):
        return {"decision":"BLOCK","reason":"EXTERNAL_CRAFT_JUDGMENT_MISSING"}
    if judgment.get("verdict")!="PASS":
        return {"decision":"BLOCK","reason":"EXTERNAL_CRAFT_NONPASS","verdict":judgment.get("verdict")}
    return {"decision":"PASS","reason":"EXTERNAL_CRAFT_PASS"}

class I4HOpenAIResponsesProvider(OpenAIResponsesProvider):
    """OpenAI provider whose ordinary I4D request is exactly parent behavior.

    Only payloads containing i4h_intervention_policy receive an extra revision instruction.
    """
    def build_request(self,render_payload,max_output_tokens=None):
        req=super().build_request(render_payload,max_output_tokens)
        if "i4h_intervention_policy" not in (render_payload or {}):
            return req
        policy=(render_payload or {}).get("i4h_intervention_policy") or {}
        decision=str(policy.get("decision") or "")
        constraints=policy.get("constraints") or {}
        req=deepcopy(req)
        req["instructions"] += (
            " I4H revision pass: revise the supplied i4h_baseline_scene only within the "
            f"{decision} intervention constraints. Preserve authorized story facts, speakers, "
            "exit state, character-bearing dialogue, voice and social texture. "
            f"Dialogue-retention floor={constraints.get('dialogue_retention_min')}; "
            f"total-character-ratio ceiling={constraints.get('total_char_ratio_max')}. "
            "Do not introduce new foreign-script tokens. Return only the requested scene schema."
        )
        return req

def _baseline_fallback(baseline_result,reason,details=None):
    return deepcopy(baseline_result), {
        "used_candidate":False,
        "fallback_to_baseline":True,
        "reason":reason,
        "details":deepcopy(details),
    }

def render_scene_i4h(
    provider,scene_blueprint,scene_contract,character_context,ensemble_context,texture_contract,
    baseline_independent_judge,intervention_profile,
    external_reliability_judge,external_craft_judge,
    *,max_baseline_attempts=2,fallback_renderer=None,allow_test_double=False,
):
    policy=select_i4h_intervention(intervention_profile)
    baseline_result,baseline_trace=render_scene_provider_backed(
        provider,scene_blueprint,scene_contract,character_context,ensemble_context,texture_contract,
        baseline_independent_judge,max_attempts=max_baseline_attempts,
        fallback_renderer=fallback_renderer,allow_test_double=allow_test_double,
    )
    if baseline_result.get("status")!="COMMIT" or baseline_result.get("scene_render") is None:
        out=deepcopy(baseline_result)
        trace=make_trace(
            "I4HRuntimeOverlay",{"profile":policy,"baseline_status":baseline_result.get("status")},
            out,out.get("status"),["I4D baseline","I4H profile"],["baseline result"],
            "P07_I4H_RUNTIME_PROMOTION",["I4D","I4H-R3","I4H-R4"],
            "Baseline did not commit; I4H never attempts revision."
        )
        return out,trace

    if policy["decision"]=="ABSTAIN":
        out=deepcopy(baseline_result)
        trace=make_trace(
            "I4HRuntimeOverlay",{"profile":policy,"baseline_hash":_sha(baseline_result)},
            out,"ABSTAIN",["I4D baseline","I4H profile"],["exact baseline result"],
            "P07_I4H_RUNTIME_PROMOTION",["I4D","I4H-R3","I4H-R4"],
            "ABSTAIN performs zero revision calls and returns the exact baseline result."
        )
        return out,trace

    baseline_scene=deepcopy(baseline_result["scene_render"])
    revision_payload=build_i4h_revision_payload(
        scene_blueprint,scene_contract,character_context,ensemble_context,texture_contract,
        baseline_scene,intervention_profile,policy["decision"],
    )
    try:
        revision_result=provider.generate(revision_payload)
    except Exception as e:
        out,meta=_baseline_fallback(baseline_result,"REVISION_PROVIDER_EXCEPTION",type(e).__name__)
        trace=make_trace("I4HRuntimeOverlay",revision_payload,out,"FALLBACK",["baseline","revision provider"],["baseline result"],"P07_I4H_RUNTIME_PROMOTION",["I4D","I4H-R4"],str(meta))
        return out,trace

    adapter=getattr(provider,"transport_adapter",None)
    claim=validate_provider_claim(revision_result,adapter,require_trusted_transport=adapter is not None)
    test_double=bool(((revision_result or {}).get("provenance") or {}).get("test_double"))
    provider_admissible=(claim.get("decision")=="PASS") or (allow_test_double and test_double)
    if revision_result.get("status")!="OK" or not provider_admissible or revision_result.get("scene_render") is None:
        out,meta=_baseline_fallback(baseline_result,"REVISION_PROVIDER_REJECT",{"claim":claim,"status":revision_result.get("status")})
        trace=make_trace("I4HRuntimeOverlay",revision_payload,out,"FALLBACK",["baseline","revision provider"],["baseline result"],"P07_I4H_RUNTIME_PROMOTION",["I4D","I4H-R4"],str(meta))
        return out,trace

    candidate=deepcopy(revision_result["scene_render"])
    delta=evaluate_i4h_delta_guards(revision_payload,baseline_scene,candidate,policy["decision"])
    if delta.get("decision")!="PASS":
        out,meta=_baseline_fallback(baseline_result,"DETERMINISTIC_DELTA_GUARD_REJECT",delta)
        trace=make_trace("I4HRuntimeOverlay",revision_payload,out,"FALLBACK",["baseline","candidate"],["baseline result"],"P07_I4H_RUNTIME_PROMOTION",["I4D","I4H-R4"],str(meta))
        return out,trace

    reliability_raw=external_reliability_judge(revision_payload,baseline_scene,candidate,deepcopy(policy))
    reliability=validate_external_reliability_judgment(reliability_raw)
    if reliability.get("decision")!="PASS":
        out,meta=_baseline_fallback(baseline_result,"EXTERNAL_RELIABILITY_REJECT",{"validated":reliability,"raw":reliability_raw})
        trace=make_trace("I4HRuntimeOverlay",revision_payload,out,"FALLBACK",["baseline","candidate","external reliability"],["baseline result"],"P07_I4H_RUNTIME_PROMOTION",["I4D","I4H-R4"],str(meta))
        return out,trace

    craft_raw=external_craft_judge(revision_payload,baseline_scene,candidate,deepcopy(policy))
    craft=validate_external_craft_judgment(craft_raw)
    if craft.get("decision")!="PASS":
        out,meta=_baseline_fallback(baseline_result,"EXTERNAL_CRAFT_REJECT",{"validated":craft,"raw":craft_raw})
        trace=make_trace("I4HRuntimeOverlay",revision_payload,out,"FALLBACK",["baseline","candidate","external craft"],["baseline result"],"P07_I4H_RUNTIME_PROMOTION",["I4D","I4H-R4"],str(meta))
        return out,trace

    out={
        "status":"COMMIT",
        "scene_render":candidate,
        "provenance":deepcopy(revision_result.get("provenance")),
        "attempts":deepcopy(baseline_result.get("attempts") or []),
        "i4h_runtime":{
            "runtime_version":I4H_RUNTIME_VERSION,
            "policy":deepcopy(policy),
            "baseline_scene_hash":_sha(baseline_scene),
            "candidate_scene_hash":_sha(candidate),
            "provider_claim_validation":claim,
            "deterministic_delta_guard":delta,
            "external_reliability_judgment":deepcopy(reliability_raw),
            "external_craft_judgment":deepcopy(craft_raw),
            "fallback_to_baseline":False,
            "python_literary_prose_generated":False,
        },
    }
    trace=make_trace(
        "I4HRuntimeOverlay",revision_payload,out,"COMMIT",
        ["I4D baseline","I4H profile","revision provider","external reliability","external craft"],
        ["candidate scene","I4H runtime receipt"],
        "P07_I4H_RUNTIME_PROMOTION",["I4D","I4H-R3","I4H-R4"],
        "Candidate replaces baseline only after every fail-closed guard passes."
    )
    return out,trace
