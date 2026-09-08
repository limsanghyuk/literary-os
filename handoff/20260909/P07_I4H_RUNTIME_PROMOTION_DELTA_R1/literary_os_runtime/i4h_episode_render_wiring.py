"""P07-I4H episode-level runtime wiring.

Deterministic orchestration only; no literary prose is authored by Python.
"""
from __future__ import annotations
from copy import deepcopy
from .semantic_render_bridge import materialize_renderer_input_from_semantic_scene
from .i4h_runtime_renderer import render_scene_i4h

def render_episode_i4h(
    provider,scene_plan,profile_by_scene_id,
    baseline_independent_judge,external_reliability_judge,external_craft_judge,
    *,character_voice_by_name=None,ensemble_context=None,
    max_baseline_attempts=2,fallback_renderer=None,allow_test_double=False,
):
    sp=deepcopy(scene_plan or {})
    profiles=deepcopy(profile_by_scene_id or {})
    results=[]; traces=[]
    for seq in sp.get("sequences") or []:
        sequence_id=seq.get("sequence_id")
        for scene in seq.get("scenes") or []:
            sid=scene.get("scene_id")
            if sid not in profiles:
                raise ValueError("I4H_PROFILE_MISSING_FOR_SCENE:"+str(sid))
            lowered,bridge_trace=materialize_renderer_input_from_semantic_scene(
                scene,character_voice_by_name=character_voice_by_name
            )
            result,trace=render_scene_i4h(
                provider,
                lowered["scene_blueprint"],lowered["scene_contract"],lowered["character_context"],
                deepcopy(ensemble_context or lowered["ensemble_context"]),lowered["texture_contract"],
                baseline_independent_judge,profiles[sid],
                external_reliability_judge,external_craft_judge,
                max_baseline_attempts=max_baseline_attempts,
                fallback_renderer=fallback_renderer,allow_test_double=allow_test_double,
            )
            results.append({
                "sequence_id":sequence_id,
                "scene_id":sid,
                "result":result,
                "python_literary_prose_generated":False,
            })
            traces.extend([bridge_trace,trace])
    return {
        "decision":"PASS",
        "scene_count":len(results),
        "results":results,
        "python_literary_prose_generated":False,
    },traces
