"""P07-I4H fail-closed intervention policy.

Python validates and selects an intervention mode only. It authors no literary prose.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, asdict

PROFILE_FIELDS=(
    "exposition_risk","procedural_pressure","social_texture",
    "voice_specificity","already_playable","physicalizable_subtext",
)
ALLOWED_DECISIONS={"ABSTAIN","LOW","STANDARD"}
POLICY_VERSION="I4HInterventionPolicyR1"

@dataclass(frozen=True)
class I4HInterventionProfile:
    exposition_risk:int
    procedural_pressure:int
    social_texture:int
    voice_specificity:int
    already_playable:int
    physicalizable_subtext:int

def validate_i4h_profile(profile:dict)->dict:
    if not isinstance(profile,dict):
        raise ValueError("I4H_PROFILE_MUST_BE_MAPPING")
    missing=[k for k in PROFILE_FIELDS if k not in profile]
    if missing:
        raise ValueError("I4H_PROFILE_MISSING:"+",".join(missing))
    extra=[k for k in profile if k not in PROFILE_FIELDS]
    if extra:
        raise ValueError("I4H_PROFILE_EXTRA:"+",".join(sorted(extra)))
    vals={}
    for k in PROFILE_FIELDS:
        v=profile[k]
        if isinstance(v,bool) or not isinstance(v,int) or not 0 <= v <= 3:
            raise ValueError("I4H_PROFILE_RANGE:"+k)
        vals[k]=v
    return {"decision":"PASS","policy_version":POLICY_VERSION,"profile":vals}

def canonical_i4h_profile(profile:dict)->dict:
    validated=validate_i4h_profile(profile)
    return deepcopy(validated["profile"])

def select_i4h_intervention(profile:dict)->dict:
    p=canonical_i4h_profile(profile)
    er=p["exposition_risk"]
    pp=p["procedural_pressure"]
    st=p["social_texture"]
    vs=p["voice_specificity"]
    ap=p["already_playable"]
    ps=p["physicalizable_subtext"]

    if ap>=2 and er<=1:
        decision="ABSTAIN"; reason="ALREADY_PLAYABLE_LOW_EXPOSITION"
    elif max(st,vs)>=3 and er<=2 and not (ps==3):
        decision="ABSTAIN"; reason="PROTECT_HIGH_SOCIAL_OR_VOICE_TEXTURE"
    elif er>=2 and pp>=2 and max(st,vs)<=1 and ap<=1:
        decision="STANDARD"; reason="PROCEDURAL_EXPOSITION_RESTRUCTURE_ELIGIBLE"
    elif ps>=2 or er>=2:
        decision="LOW"; reason="ADDITIVE_PHYSICALIZATION_OR_LIGHT_EXPOSITION_REPOSITION"
    else:
        decision="ABSTAIN"; reason="NO_INTERVENTION_THRESHOLD_MET"
    return {
        "decision":decision,
        "reason":reason,
        "policy_version":POLICY_VERSION,
        "profile":p,
        "python_literary_prose_generated":False,
    }

def revision_constraints(decision:str)->dict:
    d=str(decision or "").upper()
    if d=="LOW":
        return {
            "dialogue_retention_min":0.75,
            "total_char_ratio_max":1.35,
            "operation":"ADD_OR_REPOSITION_PLAYABLE_PHYSICALIZATION__PRESERVE_CHARACTER_BEARING_DIALOGUE",
        }
    if d=="STANDARD":
        return {
            "dialogue_retention_min":0.55,
            "total_char_ratio_max":1.25,
            "operation":"RESTRUCTURE_ACTION_DIALOGUE_FOR_INFORMATION_ECONOMY__PRESERVE_REASONING_VOICE_STATUS_SPEECH",
        }
    if d=="ABSTAIN":
        return {
            "dialogue_retention_min":1.0,
            "total_char_ratio_max":1.0,
            "operation":"NO_REVISION",
        }
    raise ValueError("I4H_DECISION_UNKNOWN")
