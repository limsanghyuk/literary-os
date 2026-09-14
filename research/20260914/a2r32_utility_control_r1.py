"""A2R32 Utility-Controlled Minimal Novelty Gate R1.

PRE-OUTPUT implementation only.
Scientific outputs MUST NOT be generated until runtime recovery, SHA256 sealing,
and frozen parent-component byte verification required by A2R32 preregistration.

This module does not retrieve data and does not replace the DB59 protected
baseline. It only decides whether an already-structured optional advisory may
be USED or must ABSTAIN, and if used which <=2 novelty atoms may be realized.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

AXIS_ORDER = (
    "CHARACTER_STATE",
    "RELATIONSHIP_PRESSURE",
    "CAUSAL_ESCALATION",
    "ENSEMBLE_OWNERSHIP",
    "PHYSICALIZATION",
    "PLANT_PAYOFF",
)

TOKEN_KEYWORDS: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "CHARACTER_STATE": {
        "REVERSAL": ("반전", "뒤집", "변경", "재판단", "오류", "불일치"),
        "BELIEF_CHANGE": ("판단", "믿음", "의심", "증거", "확인"),
        "STATE_CHANGE": ("역할", "선택", "책임", "결정"),
        "ACCESS_CHANGE": ("출입", "접근", "권한", "카드", "열쇠", "문"),
        "ROLE_CHANGE": ("역할", "책임", "후계", "담당"),
        "REVEAL": ("공개", "증거", "기록", "발견"),
        "CONFIRM": ("확인", "검증", "기록", "증거"),
        "PUBLICIZE": ("공개", "보도", "정정"),
    },
    "RELATIONSHIP_PRESSURE": {
        "BETRAYAL": ("배신", "은폐", "조작", "위조"),
        "RESPONSIBILITY": ("책임", "인계", "배정", "의무"),
        "ACCESS": ("출입", "접근", "권한", "열쇠", "카드", "문"),
        "POWER": ("권한", "결정", "지휘"),
        "PROMISE": ("약속", "협약", "서약", "계약", "유언"),
        "TRUST": ("신뢰", "보호", "불일치"),
        "PROTECTION": ("보호", "안전", "가족"),
        "CONTROL": ("통제", "제한", "잠금"),
        "COOPERATION": ("협력", "공동", "조직", "팀"),
        "DEBT": ("보상", "부채", "의무"),
        "SEPARATION": ("폐쇄", "철수", "중단"),
        "RECONCILIATION": ("재협상", "회복", "화해"),
    },
    "CAUSAL_ESCALATION": {
        "EVIDENCE": ("증거", "기록", "로그", "표본", "검체", "센서"),
        "TIME_PRESSURE": ("폭풍", "호우", "긴급", "즉시", "위기", "대피"),
        "FAILURE": ("오류", "누락", "고장", "훼손", "분실", "공백"),
        "CONSEQUENCE": ("사고", "피해", "위기", "폐쇄", "장애"),
        "DECISION": ("결정", "승인", "선택", "중단", "폐기", "철수"),
        "BLOCKER": ("보류", "제한", "잠금", "압류", "통관"),
        "INFO_REVEAL": ("공개", "발견", "기록", "증거"),
        "INFO_REVERSAL": ("불일치", "반전", "뒤집", "다르"),
        "THREAD_ESCALATION": ("확대", "위기", "사고"),
        "THREAD_PAYOFF": ("회수", "약속", "의무", "협약"),
        "THREAD_REACTIVATION": ("다시", "재발", "과거", "약속"),
        "THREAD_REVERSAL": ("반전", "의미변화", "뒤집"),
    },
}

PHYSICAL_TOKEN_TO_AFFORDANCE: Dict[str, Tuple[str, ...]] = {
    "RECORD": ("record",),
    "DOCUMENT": ("document",),
    "CAMERA": ("camera",),
    "PHONE": ("phone",),
    "KEY": ("key",),
    "SCREEN": ("screen",),
    "SEAL": ("seal",),
    "DOOR": ("door",),
    "HAND": ("hand",),
    "STOP": ("stop", "button"),
    "EVIDENCE": ("record", "sample", "seal", "label", "sensor", "box", "card", "document"),
    "GRAB_RELEASE": ("hand", "card", "key", "document", "rope", "box", "vest", "container"),
    "POSITION": ("door", "gate", "container", "lever"),
    "PHOTO": ("camera",),
}

LIFECYCLE_ATOMS = {
    "PLANT", "PAYOFF", "COMPLETE", "CALLBACK", "REACTIVATION", "LONGER_SPAN"
}
LIFECYCLE_CASE_TERMS = (
    "약속", "협약", "계약", "유언", "서약", "의무", "보상", "보관", "상속",
    "후원", "기부", "소유", "회수",
)

# Deterministic tie-break order. This is fixed before outputs and follows the
# preregistered token family ordering rather than any observed result.
ATOM_ORDER: Dict[str, Tuple[str, ...]] = {
    "CHARACTER_STATE": tuple(TOKEN_KEYWORDS["CHARACTER_STATE"].keys()),
    "RELATIONSHIP_PRESSURE": tuple(TOKEN_KEYWORDS["RELATIONSHIP_PRESSURE"].keys()),
    "CAUSAL_ESCALATION": tuple(TOKEN_KEYWORDS["CAUSAL_ESCALATION"].keys()),
    "ENSEMBLE_OWNERSHIP": (
        "PRIMARY", "OPPOSITION", "SECONDARY", "SUPPORT", "WITNESS", "MENTOR",
        "AUTHORITY", "FAMILY", "OTHER",
    ),
    "PHYSICALIZATION": (
        "RECORD", "DOCUMENT", "CAMERA", "PHONE", "KEY", "SCREEN", "SEAL",
        "DOOR", "HAND", "STOP", "PROP", "EVIDENCE", "GRAB_RELEASE", "POSITION",
        "PHOTO", "FALL", "BLOOD",
    ),
    "PLANT_PAYOFF": (
        "PLANT", "PAYOFF", "COMPLETE", "CALLBACK", "REACTIVATION", "LONGER_SPAN",
        "CONTINUE", "ESCALATION", "REVERSAL", "REVEAL", "HOOK", "LINK",
    ),
}


@dataclass(frozen=True)
class AtomDecision:
    atom: str
    relevance_score: int
    accepted: bool
    reason: str


@dataclass(frozen=True)
class AdvisoryDecision:
    decision: str
    reason: str
    target_axis: str | None
    realized_atoms: Tuple[str, ...]
    discarded_atoms: Tuple[str, ...]
    atom_decisions: Tuple[AtomDecision, ...]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["realized_atoms"] = list(self.realized_atoms)
        d["discarded_atoms"] = list(self.discarded_atoms)
        d["atom_decisions"] = [asdict(x) for x in self.atom_decisions]
        return d


def _case_text(case: Mapping[str, Any]) -> str:
    pieces: List[str] = [str(case.get("title") or ""), str(case.get("premise") or "")]
    pieces.extend(str(x) for x in (case.get("query_terms") or []))
    return " ".join(pieces)


def _ordered_unique(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    for value in values:
        v = str(value or "").upper()
        if v and v not in out:
            out.append(v)
    return out


def extract_novelty_atoms(advisory: Mapping[str, Any]) -> List[str]:
    """Extract structured novelty atoms without reading raw donor prose."""
    axis = str(advisory.get("ADVISORY_TARGET_AXIS") or advisory.get("target_axis") or "").upper()
    atoms: List[str] = []

    if axis == "CHARACTER_STATE":
        atoms.extend(advisory.get("STATE_MODE_SET") or [])
    elif axis == "RELATIONSHIP_PRESSURE":
        atoms.extend(advisory.get("RELATIONSHIP_SIGNAL_SET") or [])
    elif axis == "CAUSAL_ESCALATION":
        atoms.extend(advisory.get("CAUSAL_SIGNAL_SET") or [])
        atoms.extend(advisory.get("THREAD_KIND_SET") or [])
    elif axis == "ENSEMBLE_OWNERSHIP":
        for role, count in (advisory.get("ROLE_COMPOSITION") or {}).items():
            if int(count or 0) > 0:
                atoms.append(str(role))
    elif axis == "PHYSICALIZATION":
        atoms.extend(advisory.get("PHYSICAL_MARKER_SET") or [])
    elif axis == "PLANT_PAYOFF":
        atoms.extend(advisory.get("THREAD_KIND_SET") or [])
        if bool(advisory.get("COMPLETE_LIFECYCLE")):
            atoms.append("COMPLETE")
        if int(advisory.get("LIFECYCLE_SPAN") or 0) > 0:
            atoms.append("LONGER_SPAN")

    return _ordered_unique(atoms)


def _keyword_score(axis: str, atom: str, case_text: str) -> int:
    family = TOKEN_KEYWORDS.get(axis, {}).get(atom, ())
    return sum(1 for kw in family if kw and kw in case_text)


def _physical_match(atom: str, case: Mapping[str, Any]) -> bool:
    affordances = {str(x).lower() for x in (case.get("physical_affordances") or [])}
    if atom == "PROP":
        return bool(affordances)
    if atom == "FALL":
        text = _case_text(case)
        return any(k in text for k in ("넘어", "붕괴", "추락", "부상"))
    if atom == "BLOOD":
        text = _case_text(case)
        # Stored blood/material is not enough; require an injury/bleeding event.
        return any(k in text for k in ("출혈", "피가", "부상", "상처"))
    required = set(PHYSICAL_TOKEN_TO_AFFORDANCE.get(atom, ()))
    return bool(required & affordances)


def _lifecycle_case_match(case: Mapping[str, Any], atoms: Sequence[str]) -> bool:
    if not bool(case.get("long_horizon_affordance")):
        return False
    if not (set(atoms) & LIFECYCLE_ATOMS):
        return False
    text = _case_text(case)
    return any(k in text for k in LIFECYCLE_CASE_TERMS)


def _ensemble_actor_group_count(case: Mapping[str, Any]) -> int:
    """Conservative deterministic test for explicit >=3 actor groups.

    The fresh pool encodes multi-party premises primarily with middle dots. We
    also count a small frozen institution/actor vocabulary present literally in
    the premise. This does not infer hidden actors.
    """
    premise = str(case.get("premise") or "")
    if premise.count("·") >= 2:
        return premise.count("·") + 1
    vocab = (
        "시청", "시설팀", "주민대표", "재단", "극장", "학생회", "생활관", "보호자",
        "기자", "데스크", "법무", "본부", "현장", "오케스트라", "후원재단", "관리소",
        "소방", "입주자대표", "세관", "운송사", "화주", "보안팀", "가족", "교사",
    )
    return sum(1 for term in vocab if term in premise)


def _atom_rank(axis: str, atom: str) -> int:
    order = ATOM_ORDER.get(axis, ())
    try:
        return order.index(atom)
    except ValueError:
        return len(order) + 100


def evaluate_advisory(case: Mapping[str, Any], advisory: Mapping[str, Any]) -> AdvisoryDecision:
    axis = str(advisory.get("ADVISORY_TARGET_AXIS") or advisory.get("target_axis") or "").upper()
    target_axes = {str(x).upper() for x in (case.get("target_axes") or [])}

    if axis not in target_axes:
        return AdvisoryDecision(
            decision="ABSTAIN",
            reason="ABSTAIN__NON_TARGET_AXIS",
            target_axis=axis or None,
            realized_atoms=(),
            discarded_atoms=tuple(extract_novelty_atoms(advisory)),
            atom_decisions=(),
        )

    atoms = extract_novelty_atoms(advisory)
    if not atoms:
        return AdvisoryDecision(
            decision="ABSTAIN",
            reason="ABSTAIN__NO_NOVELTY",
            target_axis=axis,
            realized_atoms=(),
            discarded_atoms=(),
            atom_decisions=(),
        )

    if axis == "PLANT_PAYOFF" and not _lifecycle_case_match(case, atoms):
        return AdvisoryDecision(
            decision="ABSTAIN",
            reason="ABSTAIN__LIFECYCLE_COHERENCE_FAIL",
            target_axis=axis,
            realized_atoms=(),
            discarded_atoms=tuple(atoms),
            atom_decisions=(),
        )

    if axis == "ENSEMBLE_OWNERSHIP" and _ensemble_actor_group_count(case) < 3:
        return AdvisoryDecision(
            decision="ABSTAIN",
            reason="ABSTAIN__ENSEMBLE_GROUP_COUNT_FAIL",
            target_axis=axis,
            realized_atoms=(),
            discarded_atoms=tuple(atoms),
            atom_decisions=(),
        )

    case_text = _case_text(case)
    accepted: List[Tuple[str, int]] = []
    atom_decisions: List[AtomDecision] = []

    for atom in atoms:
        if axis == "PHYSICALIZATION":
            ok = _physical_match(atom, case)
            score = 1 if ok else 0
            reason = "ACCEPT__PHYSICAL_AFFORDANCE_MATCH" if ok else "REJECT__PHYSICAL_AFFORDANCE_MISMATCH"
        elif axis == "PLANT_PAYOFF":
            # Lifecycle coherence already passed at advisory level. Individual
            # lifecycle atoms are legal; generic ESCALATION alone never passes
            # because advisory-level lifecycle matching requires a lifecycle atom.
            score = 2 if atom in LIFECYCLE_ATOMS else _keyword_score(axis, atom, case_text)
            ok = atom in LIFECYCLE_ATOMS or score > 0
            reason = "ACCEPT__LIFECYCLE_COHERENT" if ok else "REJECT__ZERO_CASE_SUPPORT"
        elif axis == "ENSEMBLE_OWNERSHIP":
            # Explicit >=3 groups already passed. One role/ownership atom only.
            score = 1
            ok = True
            reason = "ACCEPT__EXPLICIT_MULTI_ACTOR_CASE"
        else:
            score = _keyword_score(axis, atom, case_text)
            ok = score > 0
            reason = "ACCEPT__CASE_KEYWORD_SUPPORT" if ok else "REJECT__ZERO_CASE_SUPPORT"

        atom_decisions.append(AtomDecision(atom=atom, relevance_score=score, accepted=ok, reason=reason))
        if ok:
            accepted.append((atom, score))

    if not accepted:
        return AdvisoryDecision(
            decision="ABSTAIN",
            reason="ABSTAIN__NO_ATOM_SURVIVES_UTILITY_GATE",
            target_axis=axis,
            realized_atoms=(),
            discarded_atoms=tuple(atoms),
            atom_decisions=tuple(atom_decisions),
        )

    # Minimal sufficient signature: highest case relevance, then frozen per-axis order.
    accepted.sort(key=lambda x: (-x[1], _atom_rank(axis, x[0]), x[0]))
    budget = 1 if axis == "ENSEMBLE_OWNERSHIP" else 2
    realized = [atom for atom, _ in accepted[:budget]]
    discarded = [a for a in atoms if a not in realized]

    return AdvisoryDecision(
        decision="USE",
        reason="USE__UTILITY_CONTROLLED_MINIMAL_NOVELTY",
        target_axis=axis,
        realized_atoms=tuple(realized),
        discarded_atoms=tuple(discarded),
        atom_decisions=tuple(atom_decisions),
    )


def choose_single_advisory(case: Mapping[str, Any], advisories: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """At most one advisory is USED; all others explicitly ABSTAIN.

    Candidate ordering is deterministic and outcome-independent:
      1) number of realized atoms (more supported function first),
      2) total relevance score,
      3) frozen case target-axis order,
      4) advisory slot,
      5) original candidate order.
    """
    evaluated: List[Tuple[int, Mapping[str, Any], AdvisoryDecision]] = []
    for idx, advisory in enumerate(advisories):
        evaluated.append((idx, advisory, evaluate_advisory(case, advisory)))

    usable = []
    case_axis_order = [str(x).upper() for x in (case.get("target_axes") or [])]
    for idx, advisory, decision in evaluated:
        if decision.decision != "USE":
            continue
        total_score = sum(x.relevance_score for x in decision.atom_decisions if x.atom in decision.realized_atoms)
        try:
            axis_rank = case_axis_order.index(str(decision.target_axis))
        except ValueError:
            axis_rank = len(case_axis_order) + 1
        slot = int(advisory.get("slot") or 0)
        usable.append((
            -len(decision.realized_atoms),
            -total_score,
            axis_rank,
            slot,
            idx,
            advisory,
            decision,
        ))

    chosen_idx = None
    chosen_decision = None
    if usable:
        usable.sort(key=lambda x: x[:5])
        chosen_idx = usable[0][4]
        chosen_decision = usable[0][6]

    trace = []
    for idx, advisory, decision in evaluated:
        row = decision.to_dict()
        row["candidate_index"] = idx
        row["slot"] = advisory.get("slot")
        if chosen_idx is not None and idx != chosen_idx and row["decision"] == "USE":
            row["decision"] = "ABSTAIN"
            row["reason"] = "ABSTAIN__ANOTHER_ADVISORY_WON_SINGLE_USE_ARBITRATION"
            row["discarded_atoms"] = list(row["realized_atoms"]) + list(row["discarded_atoms"])
            row["realized_atoms"] = []
        trace.append(row)

    return {
        "case_id": case.get("case_id"),
        "decision": "USE" if chosen_decision is not None else "ABSTAIN",
        "chosen_candidate_index": chosen_idx,
        "target_axis": None if chosen_decision is None else chosen_decision.target_axis,
        "minimal_realized_atoms": [] if chosen_decision is None else list(chosen_decision.realized_atoms),
        "trace": trace,
        "novelty_budget_max": 2,
        "used_advisory_count": 0 if chosen_decision is None else 1,
    }


def realization_slot(axis: str) -> Tuple[int, ...]:
    """Frozen A2R32 target-axis sequence placement."""
    mapping = {
        "CHARACTER_STATE": (5,),
        "RELATIONSHIP_PRESSURE": (2,),
        "CAUSAL_ESCALATION": (4,),
        "ENSEMBLE_OWNERSHIP": (4, 6),
        "PHYSICALIZATION": (3,),
        "PLANT_PAYOFF": (1, 6),
    }
    return mapping.get(str(axis).upper(), ())


def validate_decision(case: Mapping[str, Any], result: Mapping[str, Any]) -> List[str]:
    """Mechanical invariant checker used before any blind release."""
    errors: List[str] = []
    used = int(result.get("used_advisory_count") or 0)
    atoms = list(result.get("minimal_realized_atoms") or [])
    if used not in (0, 1):
        errors.append("USED_ADVISORY_COUNT_GT_1")
    if len(atoms) > 2:
        errors.append("NOVELTY_BUDGET_GT_2")
    axis = result.get("target_axis")
    if used == 1 and str(axis).upper() not in {str(x).upper() for x in (case.get("target_axes") or [])}:
        errors.append("NON_TARGET_AXIS_USED")
    if used == 1 and not realization_slot(str(axis)):
        errors.append("NO_FROZEN_REALIZATION_SLOT")
    return errors
