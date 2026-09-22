"""R74 symmetric semantic-transaction measurement bridge R2.

Measurement-only. No arm label is accepted.
R2 adds a deterministic adapter from frozen R68/R69 runtime-case schemas
to the shared canonical representation. No literary generation.
"""

from collections import Counter, defaultdict
from copy import deepcopy


class BridgeUnresolved(ValueError):
    pass


def _freeze(value):
    if isinstance(value, dict):
        return tuple(sorted((str(k), _freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple, set)):
        return tuple(_freeze(v) for v in value)
    return value


def _required(mapping, key):
    if key not in mapping or mapping[key] is None:
        raise BridgeUnresolved(f"missing required field: {key}")
    return mapping[key]


def _obligation_map(portfolio):
    obs = portfolio.get("obligations")
    if not isinstance(obs, list):
        raise BridgeUnresolved("portfolio.obligations missing")
    out = {}
    for ob in obs:
        oid = ob.get("id")
        if not oid:
            raise BridgeUnresolved("obligation.id missing")
        out[str(oid)] = ob
    return out


def _kind_profile(scene, obligations):
    kinds = scene.get("transaction_kinds")
    if not kinds:
        kinds = [ob.get("kind") for ob in obligations if ob.get("kind")]
    kinds = tuple(sorted(set(str(k) for k in kinds if k)))
    if not kinds:
        raise BridgeUnresolved("transaction kind role unresolved")
    return kinds


def _causal_profile(obligations, portfolio):
    blocked_ids = set(str(x) for x in portfolio.get("blocked_ids", []))
    defer_ids = set(str(x) for x in portfolio.get("defer_ids", []))
    return {
        "has_dependency": any(bool(ob.get("depends_on")) for ob in obligations),
        "multi_owner": any(len(ob.get("owners", [])) > 1 or bool(ob.get("group_refs")) for ob in obligations),
        "deferred": any(bool(ob.get("can_defer")) or str(ob.get("id")) in defer_ids for ob in obligations),
        "blocked": any(str(ob.get("id")) in blocked_ids for ob in obligations),
    }


def _state_profile(obligations):
    kinds = set(str(ob.get("kind", "")).upper() for ob in obligations)
    return {
        "information": "INFORMATION" in kinds or any(ob.get("information_delta") for ob in obligations),
        "relationship": "RELATIONSHIP" in kinds or any(ob.get("relationship_delta") for ob in obligations),
        "social": "SOCIAL" in kinds or any(ob.get("social_delta") for ob in obligations),
        "physical_event": "EVENT" in kinds,
        "payoff": "PAYOFF" in kinds or any(ob.get("payoff_delta") for ob in obligations),
    }


def f04_signature(scene):
    if scene["transaction_stage"] == "RESOLVE":
        raise BridgeUnresolved("RESOLVE has no F04 comparison signature")
    return (
        scene["transaction_stage"],
        _freeze(scene["transaction_kind_role"]),
        _freeze(scene["causal_role_profile"]),
        _freeze(scene["state_delta_role_profile"]),
        "PRE_RESOLUTION_ADVANCE",
    )


def _terminal_deferred_ids(sequence_graph):
    ledger = (sequence_graph or {}).get("terminal_deferred_ledger", [])
    out = []
    for item in ledger:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            val = item.get("id") or item.get("pressure_id") or item.get("deferred_pressure_id")
            if val:
                out.append(str(val))
    return tuple(sorted(set(out)))


def adapt_runtime_case(case):
    portfolio = _required(case, "portfolio")
    scene_graph = _required(case, "scene_graph")
    scenes = _required(scene_graph, "scenes")
    obmap = _obligation_map(portfolio)
    canonical = []

    for idx, scene in enumerate(scenes):
        if "transaction_obligation_ids" not in scene:
            raise BridgeUnresolved(f"scene {idx}: transaction_obligation_ids field missing")
        oids = tuple(sorted(str(x) for x in scene["transaction_obligation_ids"]))
        try:
            obligations = [obmap[oid] for oid in oids]
        except KeyError as e:
            raise BridgeUnresolved(f"scene {idx}: obligation not in portfolio: {e}")

        stage = scene.get("transaction_stage") or scene.get("scene_phase")
        if not stage:
            raise BridgeUnresolved(f"scene {idx}: transaction stage unresolved")
        stage = str(stage)

        rec = {
            "canonical_scene_id": str(scene.get("scene_id") or f"S{idx+1}"),
            "canonical_sequence_id": str(scene.get("sequence_id") or "SEQ_DEFAULT"),
            "source_obligation_ids": oids,
            "transaction_stage": stage,
            "transaction_kind_role": _kind_profile(scene, obligations),
            "causal_role_profile": _causal_profile(obligations, portfolio),
            "state_delta_role_profile": _state_profile(obligations),
            "resolution_role": "RESOLUTION" if stage == "RESOLVE" else "PRE_RESOLUTION_ADVANCE",
            "deferred_open_pressure_set": tuple(sorted(str(x) for x in scene.get("deferred_pressure_ids", []))),
            "factual_delta_roles": (),
            "dependency_profile": tuple(sorted(
                (str(ob.get("id")), tuple(sorted(str(x) for x in ob.get("depends_on", []))))
                for ob in obligations if ob.get("depends_on")
            )),
            "protected_contributions": (),
            "resolves_obligation": bool(scene.get("resolves_obligation")),
            "resolved_obligation_ids": tuple(sorted(str(x) for x in scene.get("resolved_obligation_ids", []))),
            "state_delta_required": bool(scene.get("state_delta_required")),
        }

        protected = set()

        # N1 — unique obligation resolution contribution.
        resolved_ids = set(rec["resolved_obligation_ids"])
        if rec["resolves_obligation"] and not resolved_ids:
            resolved_ids.update(oids)
        for oid in resolved_ids:
            protected.add(f"RESOLVE_OBLIGATION:{oid}")

        # N2 — deferred/open pressure contribution.
        for pid in rec["deferred_open_pressure_set"]:
            protected.add(f"DEFERRED_PRESSURE:{pid}")

        # N3 — supported factual state-delta contribution.
        factual_roles = []
        if rec["state_delta_required"]:
            sp = rec["state_delta_role_profile"]
            for oid in oids:
                if sp["information"]:
                    protected.add(f"STATE_DELTA:{oid}:INFORMATION")
                    factual_roles.append((oid, "INFORMATION"))
                if sp["relationship"]:
                    protected.add(f"STATE_DELTA:{oid}:RELATIONSHIP")
                    factual_roles.append((oid, "RELATIONSHIP"))
                if sp["social"]:
                    protected.add(f"STATE_DELTA:{oid}:SOCIAL")
                    factual_roles.append((oid, "SOCIAL"))
                if sp["physical_event"]:
                    protected.add(f"STATE_DELTA:{oid}:EVENT")
                    factual_roles.append((oid, "EVENT"))
                if sp["payoff"]:
                    protected.add(f"STATE_DELTA:{oid}:PAYOFF")
                    factual_roles.append((oid, "PAYOFF"))
        rec["factual_delta_roles"] = tuple(sorted(factual_roles))

        # N4 — obligation-specific semantic advance.
        if stage != "RESOLVE":
            sig = f04_signature(rec)
            for oid in oids:
                protected.add(f"ADVANCE:{oid}:{repr(sig)}")

        # N5 — dependency-aware causal bridge.
        for ob in obligations:
            deps = tuple(sorted(str(x) for x in ob.get("depends_on", [])))
            if deps and stage != "RESOLVE":
                protected.add(f"CAUSAL_BRIDGE:{ob['id']}:{repr(deps)}")

        rec["protected_contributions"] = tuple(sorted(protected))
        canonical.append(rec)

    terminal = tuple(f"DEFERRED_PRESSURE:{x}" for x in _terminal_deferred_ids(case.get("sequence_graph", {})))
    return {"scenes": canonical, "terminal_protected_contributions": terminal}


def f04_repetition_groups(canonical_scenes):
    groups = defaultdict(list)
    for scene in canonical_scenes:
        if scene["transaction_stage"] == "RESOLVE":
            continue
        if not scene["source_obligation_ids"]:
            # Explicitly obligationless scenes are valid F06 inputs but do not
            # define an obligation-level semantic transaction for F04.
            continue
        groups[f04_signature(scene)].append(scene["canonical_scene_id"])
    return {sig: tuple(ids) for sig, ids in groups.items() if len(ids) >= 3}


def _coverage(canonical_scenes, terminal=()):
    c = Counter(terminal)
    for scene in canonical_scenes:
        for contribution in scene["protected_contributions"]:
            c[contribution] += 1
    return c


def _removal_loss(canonical_scenes, idx, terminal=()):
    before = _coverage(canonical_scenes, terminal)
    after = _coverage(canonical_scenes[:idx] + canonical_scenes[idx + 1:], terminal)
    lost = tuple(sorted(k for k, n in before.items() if n > 0 and after.get(k, 0) == 0))
    return bool(lost), lost


def _lossless_adjacent_merge(a, b):
    if a["canonical_sequence_id"] != b["canonical_sequence_id"]:
        return False
    if a["source_obligation_ids"] != b["source_obligation_ids"]:
        return False
    if a["transaction_stage"] != b["transaction_stage"]:
        return False
    if a["resolves_obligation"] and b["resolves_obligation"]:
        if set(a["resolved_obligation_ids"]) != set(b["resolved_obligation_ids"]):
            return False
    # Same-stage/same-obligation semantic work can be co-represented; protected
    # contributions are unioned. Distinct-stage atomicity is blocked above.
    return True


def f06_scene_necessity(canonical_scenes, terminal=()):
    verdicts = []
    for i, scene in enumerate(canonical_scenes):
        removal_loss, lost = _removal_loss(canonical_scenes, i, terminal)
        mergeable = []
        if i > 0 and _lossless_adjacent_merge(canonical_scenes[i-1], scene):
            mergeable.append(canonical_scenes[i-1]["canonical_scene_id"])
        if i + 1 < len(canonical_scenes) and _lossless_adjacent_merge(scene, canonical_scenes[i+1]):
            mergeable.append(canonical_scenes[i+1]["canonical_scene_id"])
        necessary = removal_loss and not mergeable
        verdicts.append({
            "scene_id": scene["canonical_scene_id"],
            "verdict": "NECESSARY_SEPARATE_SCENE" if necessary else "REDUNDANT_OR_MERGEABLE_SCENE",
            "removal_loss": removal_loss,
            "lost_protected_contributions": lost,
            "mergeable_with": tuple(mergeable),
        })
    return verdicts


def score_case(case):
    graph = adapt_runtime_case(case)
    scenes = graph["scenes"]
    terminal = graph["terminal_protected_contributions"]
    f04 = f04_repetition_groups(scenes)
    f06 = f06_scene_necessity(scenes, terminal)
    return {
        "canonical_records": scenes,
        "terminal_protected_contributions": terminal,
        "f04_repetition_group_count": len(f04),
        "f04_groups": f04,
        "f06_redundant_or_mergeable_count": sum(
            1 for x in f06 if x["verdict"] == "REDUNDANT_OR_MERGEABLE_SCENE"
        ),
        "f06_verdicts": f06,
    }


def score_graph(raw_scenes):
    # Compatibility helper for direct canonical records used by M1/M2/M3/M6.
    for scene in raw_scenes:
        for key in (
            "canonical_scene_id","canonical_sequence_id","source_obligation_ids",
            "transaction_stage","transaction_kind_role","causal_role_profile",
            "state_delta_role_profile","resolution_role","protected_contributions"
        ):
            if key not in scene or scene[key] is None:
                raise BridgeUnresolved(f"missing required field: {key}")
    f04 = f04_repetition_groups(raw_scenes)
    f06 = f06_scene_necessity(raw_scenes, ())
    return {
        "canonical_records": deepcopy(raw_scenes),
        "f04_repetition_group_count": len(f04),
        "f04_groups": f04,
        "f06_redundant_or_mergeable_count": sum(
            1 for x in f06 if x["verdict"] == "REDUNDANT_OR_MERGEABLE_SCENE"
        ),
        "f06_verdicts": f06,
    }


def serialization_invariant_case(case):
    def reverse_dicts(x):
        if isinstance(x, dict):
            return {k: reverse_dicts(v) for k, v in reversed(list(x.items()))}
        if isinstance(x, list):
            return [reverse_dicts(v) for v in x]
        return x
    return score_case(case) == score_case(reverse_dicts(case))
