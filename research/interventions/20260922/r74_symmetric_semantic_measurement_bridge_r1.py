"""R74 symmetric semantic-transaction measurement bridge R1.

Measurement-only reference implementation.
No literary generation. No arm label is accepted.
"""

from collections import Counter, defaultdict
from copy import deepcopy


class BridgeUnresolved(ValueError):
    pass


REQUIRED_F04_FIELDS = (
    "transaction_stage",
    "transaction_kind_role",
    "causal_role_profile",
    "state_delta_role_profile",
    "resolution_role",
)


def _freeze(value):
    if isinstance(value, dict):
        return tuple(sorted((str(k), _freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple, set)):
        return tuple(_freeze(v) for v in value)
    return value


def _required(scene, key):
    if key not in scene or scene[key] is None:
        raise BridgeUnresolved(f"missing required field: {key}")
    return scene[key]


def canonical_scene(scene):
    """Build an arm-independent canonical record. Fails closed on missing semantics."""
    out = {
        "canonical_scene_id": _required(scene, "canonical_scene_id"),
        "canonical_sequence_id": _required(scene, "canonical_sequence_id"),
        "source_obligation_ids": tuple(sorted(_required(scene, "source_obligation_ids"))),
        "transaction_stage": _required(scene, "transaction_stage"),
        "transaction_kind_role": _freeze(_required(scene, "transaction_kind_role")),
        "causal_role_profile": _freeze(_required(scene, "causal_role_profile")),
        "state_delta_role_profile": _freeze(_required(scene, "state_delta_role_profile")),
        "resolution_role": _required(scene, "resolution_role"),
        "deferred_open_pressure_set": tuple(sorted(scene.get("deferred_open_pressure_set", ()))),
        "factual_delta_roles": _freeze(scene.get("factual_delta_roles", ())),
        "dependency_profile": _freeze(scene.get("dependency_profile", ())),
        "protected_contributions": tuple(sorted(scene.get("protected_contributions", ()))),
    }
    if not out["source_obligation_ids"]:
        raise BridgeUnresolved("source_obligation_ids must be non-empty")
    return out


def canonicalize_graph(scenes):
    return [canonical_scene(s) for s in scenes]


def f04_signature(scene):
    # Exact R68 field family. RESOLVE scenes are excluded by caller.
    for key in REQUIRED_F04_FIELDS:
        _required(scene, key)
    return (
        scene["transaction_stage"],
        _freeze(scene["transaction_kind_role"]),
        _freeze(scene["causal_role_profile"]),
        _freeze(scene["state_delta_role_profile"]),
        scene["resolution_role"],
    )


def f04_repetition_groups(canonical_scenes):
    groups = defaultdict(list)
    for scene in canonical_scenes:
        if scene["transaction_stage"] == "RESOLVE":
            continue
        groups[f04_signature(scene)].append(scene["canonical_scene_id"])
    return {
        sig: tuple(ids)
        for sig, ids in groups.items()
        if len(ids) >= 3
    }


def _coverage(canonical_scenes):
    c = Counter()
    for scene in canonical_scenes:
        for contribution in scene["protected_contributions"]:
            c[contribution] += 1
    return c


def _removal_loss(canonical_scenes, idx):
    before = _coverage(canonical_scenes)
    after = _coverage(canonical_scenes[:idx] + canonical_scenes[idx + 1 :])
    lost = sorted(k for k, n in before.items() if n > 0 and after.get(k, 0) == 0)
    return bool(lost), tuple(lost)


def _same_sequence(a, b):
    return a["canonical_sequence_id"] == b["canonical_sequence_id"]


def _same_obligation_set(a, b):
    return a["source_obligation_ids"] == b["source_obligation_ids"]


def _lossless_adjacent_merge(a, b):
    if not _same_sequence(a, b):
        return False
    if not _same_obligation_set(a, b):
        return False
    # Frozen R69 atomicity: distinct transaction stages cannot be one lossless scene.
    if a["transaction_stage"] != b["transaction_stage"]:
        return False
    # Protected contributions are union-compatible when no explicit contradiction exists.
    # The bridge is conservative: unresolved conflict evidence must be encoded upstream.
    return True


def f06_scene_necessity(canonical_scenes):
    verdicts = []
    for i, scene in enumerate(canonical_scenes):
        removal_loss, lost = _removal_loss(canonical_scenes, i)
        mergeable = []
        if i > 0 and _lossless_adjacent_merge(canonical_scenes[i - 1], scene):
            mergeable.append(canonical_scenes[i - 1]["canonical_scene_id"])
        if i + 1 < len(canonical_scenes) and _lossless_adjacent_merge(scene, canonical_scenes[i + 1]):
            mergeable.append(canonical_scenes[i + 1]["canonical_scene_id"])
        necessary = removal_loss and not mergeable
        verdicts.append({
            "scene_id": scene["canonical_scene_id"],
            "verdict": "NECESSARY_SEPARATE_SCENE" if necessary else "REDUNDANT_OR_MERGEABLE_SCENE",
            "removal_loss": removal_loss,
            "lost_protected_contributions": lost,
            "mergeable_with": tuple(mergeable),
        })
    return verdicts


def score_graph(raw_scenes):
    canonical = canonicalize_graph(raw_scenes)
    f04 = f04_repetition_groups(canonical)
    f06 = f06_scene_necessity(canonical)
    return {
        "canonical_records": canonical,
        "f04_repetition_group_count": len(f04),
        "f04_groups": f04,
        "f06_redundant_or_mergeable_count": sum(
            1 for v in f06 if v["verdict"] == "REDUNDANT_OR_MERGEABLE_SCENE"
        ),
        "f06_verdicts": f06,
    }


def identity_parity(graph):
    return score_graph(deepcopy(graph)) == score_graph(deepcopy(graph))


def serialization_invariant(graph):
    # Dict insertion order is intentionally irrelevant to canonicalization.
    reversed_graph = [dict(reversed(list(scene.items()))) for scene in graph]
    return score_graph(graph) == score_graph(reversed_graph)
