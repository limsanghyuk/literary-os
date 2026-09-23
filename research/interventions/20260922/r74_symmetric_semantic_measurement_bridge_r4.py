"""R74 symmetric semantic-transaction measurement bridge R4.

R4 is a measurement-only packed-stage extension.
Legacy/runtime scoring delegates byte-for-byte semantics to the frozen R3 bridge.
No arm label is accepted.
"""

from __future__ import annotations

from collections import defaultdict
import importlib.util
from pathlib import Path

_R3_PATH = Path(__file__).with_name("r74_symmetric_semantic_measurement_bridge_r3.py")
_spec = importlib.util.spec_from_file_location("r74_bridge_r3_frozen", _R3_PATH)
_r3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_r3)

BridgeUnresolved = _r3.BridgeUnresolved

# Frozen R3 legacy/runtime interfaces.
score_case = _r3.score_case
serialization_invariant_case = _r3.serialization_invariant_case
f04_signature = _r3.f04_signature
f04_repetition_groups = _r3.f04_repetition_groups
f06_scene_necessity = _r3.f06_scene_necessity


def _required(mapping, key):
    if key not in mapping or mapping[key] is None:
        raise BridgeUnresolved(f"missing required field: {key}")
    return mapping[key]


def _stage_chunks(stages, occurrence_count):
    """Map an ordered semantic stage plan onto ordered physical scene occurrences.

    When one physical scene carries more than one semantic stage, the stages remain
    together as a tuple. When physical fragmentation exceeds semantic stages, a
    stage may repeat across adjacent physical scenes; the final occurrence always
    receives the final semantic stage.
    """
    stages = tuple(str(x) for x in stages if x is not None)
    if not stages:
        raise BridgeUnresolved("empty obligation stage plan")
    if occurrence_count <= 0:
        raise BridgeUnresolved("obligation has no packed-scene occurrence")

    m = len(stages)
    k = int(occurrence_count)
    out = []
    if k <= m:
        for i in range(k):
            start = (i * m) // k
            end = ((i + 1) * m) // k
            chunk = stages[start:end]
            if not chunk:
                raise BridgeUnresolved("stage partition produced empty chunk")
            out.append(chunk)
    else:
        for i in range(k):
            idx = min(m - 1, (i * m) // k)
            out.append((stages[idx],))
        out[-1] = (stages[-1],)
    return tuple(out)


def _scene_stage_token(stage_map):
    flat = sorted({stage for stages in stage_map.values() for stage in stages})
    if not flat:
        raise BridgeUnresolved("packed scene has no semantic stage")
    if len(flat) == 1:
        return flat[0]
    return "MIXED[" + "|".join(flat) + "]"


def _advance_present(stages):
    return any(x not in {"RESOLVE", "DEFERRED_PRESSURE"} for x in stages)


def _resolved(stages):
    return "RESOLVE" in stages


def _deferred(stages):
    return "DEFERRED_PRESSURE" in stages


def adapt_packed_case(case):
    """Project an unchanged-F05 packed physical scene graph to the R74 canonical schema.

    Required packed-case fields:
      portfolio: exact frozen source obligation portfolio
      packed_scene_graph.scenes[*].atom_ids
      atom_bindings[atom_id].source_obligation_id
      obligation_stage_plans[obligation_id] = ordered semantic stage list

    Physical scenes are preserved one-for-one.
    """
    portfolio = _required(case, "portfolio")
    packed = _required(case, "packed_scene_graph")
    scenes = _required(packed, "scenes")
    atom_bindings = _required(case, "atom_bindings")
    stage_plans = _required(case, "obligation_stage_plans")

    obmap = _r3._obligation_map(portfolio)

    if isinstance(atom_bindings, list):
        tmp = {}
        for row in atom_bindings:
            aid = row.get("atom_id")
            oid = row.get("source_obligation_id")
            if not aid or not oid:
                raise BridgeUnresolved("atom binding missing atom_id/source_obligation_id")
            if str(aid) in tmp:
                raise BridgeUnresolved(f"duplicate atom binding: {aid}")
            tmp[str(aid)] = str(oid)
        atom_bindings = tmp
    elif isinstance(atom_bindings, dict):
        atom_bindings = {
            str(aid): (
                str(row.get("source_obligation_id"))
                if isinstance(row, dict) else str(row)
            )
            for aid, row in atom_bindings.items()
        }
    else:
        raise BridgeUnresolved("atom_bindings must be list or dict")

    # Record every physical occurrence of each source obligation.
    occurrences = defaultdict(list)
    seen_atoms = set()
    scene_atom_ids = []
    for idx, scene in enumerate(scenes):
        aids = tuple(str(x) for x in _required(scene, "atom_ids"))
        if not aids:
            raise BridgeUnresolved(f"packed scene {idx}: empty atom_ids")
        for aid in aids:
            if aid in seen_atoms:
                raise BridgeUnresolved(f"packed atom allocated more than once: {aid}")
            seen_atoms.add(aid)
            if aid not in atom_bindings:
                raise BridgeUnresolved(f"packed atom has no source binding: {aid}")
            oid = atom_bindings[aid]
            if oid not in obmap:
                raise BridgeUnresolved(f"packed atom binds unknown obligation: {oid}")
            if not occurrences[oid] or occurrences[oid][-1] != idx:
                occurrences[oid].append(idx)
        scene_atom_ids.append(aids)

    # Atom bindings not allocated to a physical scene are unresolved, never silently dropped.
    unallocated = sorted(set(atom_bindings) - seen_atoms)
    if unallocated:
        raise BridgeUnresolved(f"unallocated packed atoms: {unallocated[:8]}")

    # Per-obligation semantic stage assignments to physical scene occurrences.
    scene_stage_maps = [defaultdict(tuple) for _ in scenes]
    for oid, occs in sorted(occurrences.items()):
        plan = stage_plans.get(oid)
        if not isinstance(plan, (list, tuple)) or not plan:
            raise BridgeUnresolved(f"missing obligation stage plan: {oid}")
        chunks = _stage_chunks(plan, len(occs))
        for scene_idx, chunk in zip(occs, chunks):
            scene_stage_maps[scene_idx][oid] = tuple(chunk)

    canonical = []
    for idx, scene in enumerate(scenes):
        stage_map = dict(scene_stage_maps[idx])
        oids = tuple(sorted(stage_map))
        if not oids:
            raise BridgeUnresolved(f"packed scene {idx}: no source obligations")
        obligations = [obmap[oid] for oid in oids]
        stage = _scene_stage_token(stage_map)

        resolved_ids = tuple(sorted(oid for oid in oids if _resolved(stage_map[oid])))
        deferred_ids = tuple(sorted(oid for oid in oids if _deferred(stage_map[oid])))
        any_advance = any(_advance_present(stage_map[oid]) for oid in oids)
        any_resolve = bool(resolved_ids)

        if any_resolve and any_advance:
            resolution_role = "MIXED_RESOLUTION_ADVANCE"
        elif any_resolve:
            resolution_role = "RESOLUTION"
        elif deferred_ids and not any_advance:
            resolution_role = "DEFERRED_PRESSURE"
        else:
            resolution_role = "PRE_RESOLUTION_ADVANCE"

        rec = {
            "canonical_scene_id": str(scene.get("scene_id") or f"S{idx+1}"),
            "canonical_sequence_id": str(scene.get("sequence_id") or "SEQ_DEFAULT"),
            "source_obligation_ids": oids,
            "transaction_stage": stage,
            "transaction_kind_role": _r3._kind_profile(scene, obligations),
            "causal_role_profile": _r3._causal_profile(obligations, portfolio),
            "state_delta_role_profile": _r3._state_profile(obligations),
            "resolution_role": resolution_role,
            "deferred_open_pressure_set": deferred_ids,
            "factual_delta_roles": (),
            "dependency_profile": tuple(sorted(
                (str(ob.get("id")), tuple(sorted(str(x) for x in ob.get("depends_on", []))))
                for ob in obligations if ob.get("depends_on")
            )),
            "protected_contributions": (),
            "resolves_obligation": bool(resolved_ids),
            "resolved_obligation_ids": resolved_ids,
            "state_delta_required": bool(resolved_ids),
            "obligation_stage_profile": tuple(
                (oid, tuple(stage_map[oid])) for oid in sorted(stage_map)
            ),
            "packed_atom_ids": scene_atom_ids[idx],
        }

        protected = set()
        factual_roles = []

        # N1 and N3 only for obligations that actually resolve in this physical scene.
        for oid in resolved_ids:
            protected.add(f"RESOLVE_OBLIGATION:{oid}")
            sp = _r3._state_profile([obmap[oid]])
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

        # N2 for deferred/open pressure represented in the packed scene.
        for oid in deferred_ids:
            protected.add(f"DEFERRED_PRESSURE:{oid}")

        # N4/N5 only for obligations performing non-resolution advance work here.
        if stage != "RESOLVE":
            sig = _r3.f04_signature(rec)
            for oid in oids:
                if not _advance_present(stage_map[oid]):
                    continue
                protected.add(f"ADVANCE:{oid}:{repr(sig)}")
                deps = tuple(sorted(str(x) for x in obmap[oid].get("depends_on", [])))
                if deps:
                    protected.add(f"CAUSAL_BRIDGE:{oid}:{repr(deps)}")

        rec["factual_delta_roles"] = tuple(sorted(factual_roles))
        rec["protected_contributions"] = tuple(sorted(protected))
        canonical.append(rec)

    terminal = tuple(
        f"DEFERRED_PRESSURE:{x}"
        for x in _r3._terminal_deferred_ids(case.get("sequence_graph", {}))
    )
    return {
        "scenes": canonical,
        "terminal_protected_contributions": terminal,
    }


def score_packed_case(case):
    graph = adapt_packed_case(case)
    scenes = graph["scenes"]
    terminal = graph["terminal_protected_contributions"]
    f04 = _r3.f04_repetition_groups(scenes)
    f06 = _r3.f06_scene_necessity(scenes, terminal)
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
