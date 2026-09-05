"""P07 R-B Narrative Architecture Closure(서사구조 폐쇄) mechanical sentinel.

NONFORMAL(비정식) only.

The module proves a mechanical LLM-1 -> Runtime -> LLM-2 consumer chain for:
- Social Ecology Graph(사회생태 그래프)
- Event Ownership(사건 소유권)
- Group Membership(집단 소속)
- Detailed Episode Synopsis(상세 회차 시놉시스)
- THICK Sequence/Boundary(심층 시퀀스·경계)

Python(파이썬) owns validation, references, hashes and packet assembly only.
It never authors or repairs final literary surface prose.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Mapping


REQUIRED_LAYERS = (
    "social_ecology",
    "event_ownership",
    "group_membership",
    "detailed_episode_synopsis",
    "thick_sequences",
)


class ArchitectureContractError(ValueError):
    """Raised when Narrative Architecture Contract(서사구조 계약) is invalid."""


def stable_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ArchitectureContractError(f"{label}:EXPECTED_MAPPING")
    return value


def _require_list(value: Any, label: str, *, nonempty: bool = True) -> list[Any]:
    if not isinstance(value, list):
        raise ArchitectureContractError(f"{label}:EXPECTED_LIST")
    if nonempty and not value:
        raise ArchitectureContractError(f"{label}:EMPTY")
    return value


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ArchitectureContractError(f"{label}:EXPECTED_NONEMPTY_TEXT")
    return value.strip()


def _unique_ids(records: Iterable[Mapping[str, Any]], key: str, label: str) -> set[str]:
    ids: list[str] = []
    for idx, record in enumerate(records):
        ids.append(_require_text(record.get(key), f"{label}[{idx}].{key}"))
    if len(ids) != len(set(ids)):
        raise ArchitectureContractError(f"{label}:DUPLICATE_{key.upper()}")
    return set(ids)


def compile_narrative_architecture(architecture: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate five architecture layers and compile immutable Runtime IR(실행체 중간표현)."""
    architecture = _require_mapping(architecture, "architecture")
    missing = [layer for layer in REQUIRED_LAYERS if layer not in architecture]
    if missing:
        raise ArchitectureContractError("MISSING_LAYER:" + ",".join(sorted(missing)))

    # Deep canonical copy so later caller mutation cannot alter the compiled IR.
    frozen: Dict[str, Any] = json.loads(
        json.dumps(dict(architecture), ensure_ascii=False, sort_keys=True)
    )

    # 1) Social Ecology Graph(사회생태 그래프)
    social = _require_mapping(frozen["social_ecology"], "social_ecology")
    characters = _require_list(social.get("characters"), "social_ecology.characters")
    groups = _require_list(social.get("groups"), "social_ecology.groups")
    _require_list(social.get("relationships"), "social_ecology.relationships", nonempty=False)
    character_ids = _unique_ids(
        [_require_mapping(x, "social_ecology.character") for x in characters],
        "character_id",
        "social_ecology.characters",
    )
    group_maps = [_require_mapping(x, "social_ecology.group") for x in groups]
    group_ids = _unique_ids(group_maps, "group_id", "social_ecology.groups")
    for idx, group in enumerate(group_maps):
        member_ids = _require_list(group.get("member_ids"), f"social_ecology.groups[{idx}].member_ids")
        for member_id in member_ids:
            if _require_text(member_id, "group.member_id") not in character_ids:
                raise ArchitectureContractError(f"UNKNOWN_CHARACTER_IN_GROUP:{member_id}")

    # 2) Group Membership(집단 소속)
    memberships = _require_list(frozen["group_membership"], "group_membership")
    membership_pairs: set[tuple[str, str]] = set()
    for idx, raw in enumerate(memberships):
        m = _require_mapping(raw, f"group_membership[{idx}]")
        char_id = _require_text(m.get("character_id"), f"group_membership[{idx}].character_id")
        group_id = _require_text(m.get("group_id"), f"group_membership[{idx}].group_id")
        _require_text(m.get("role"), f"group_membership[{idx}].role")
        _require_text(m.get("obligation"), f"group_membership[{idx}].obligation")
        if char_id not in character_ids:
            raise ArchitectureContractError(f"MEMBERSHIP_UNKNOWN_CHARACTER:{char_id}")
        if group_id not in group_ids:
            raise ArchitectureContractError(f"MEMBERSHIP_UNKNOWN_GROUP:{group_id}")
        membership_pairs.add((char_id, group_id))

    for group in group_maps:
        group_id = group["group_id"]
        for member_id in group["member_ids"]:
            if (member_id, group_id) not in membership_pairs:
                raise ArchitectureContractError(
                    f"GROUP_MEMBER_WITHOUT_MEMBERSHIP:{member_id}:{group_id}"
                )

    # 3) Event Ownership(사건 소유권)
    events = _require_list(frozen["event_ownership"], "event_ownership")
    event_maps = [_require_mapping(x, "event_ownership.event") for x in events]
    event_ids = _unique_ids(event_maps, "event_id", "event_ownership")
    for idx, event in enumerate(event_maps):
        owner_id = _require_text(event.get("owner_id"), f"event_ownership[{idx}].owner_id")
        if owner_id not in character_ids:
            raise ArchitectureContractError(f"EVENT_UNKNOWN_OWNER:{owner_id}")
        affected = _require_list(
            event.get("affected_group_ids"),
            f"event_ownership[{idx}].affected_group_ids",
        )
        for group_id in affected:
            if _require_text(group_id, "event.affected_group_id") not in group_ids:
                raise ArchitectureContractError(f"EVENT_UNKNOWN_GROUP:{group_id}")
        _require_text(event.get("pressure"), f"event_ownership[{idx}].pressure")

    # 4) Detailed Episode Synopsis(상세 회차 시놉시스)
    synopsis = _require_mapping(
        frozen["detailed_episode_synopsis"], "detailed_episode_synopsis"
    )
    _require_text(synopsis.get("episode_goal"), "detailed_episode_synopsis.episode_goal")
    beats = _require_list(synopsis.get("beats"), "detailed_episode_synopsis.beats")
    beat_maps = [_require_mapping(x, "detailed_episode_synopsis.beat") for x in beats]
    beat_ids = _unique_ids(beat_maps, "beat_id", "detailed_episode_synopsis.beats")
    for idx, beat in enumerate(beat_maps):
        _require_text(beat.get("summary"), f"detailed_episode_synopsis.beats[{idx}].summary")
        beat_event_ids = _require_list(
            beat.get("event_ids"),
            f"detailed_episode_synopsis.beats[{idx}].event_ids",
        )
        for event_id in beat_event_ids:
            if _require_text(event_id, "beat.event_id") not in event_ids:
                raise ArchitectureContractError(f"SYNOPSIS_UNKNOWN_EVENT:{event_id}")

    # 5) THICK Sequence/Boundary(심층 시퀀스·경계)
    sequences = _require_list(frozen["thick_sequences"], "thick_sequences")
    sequence_maps = [_require_mapping(x, "thick_sequences.sequence") for x in sequences]
    _unique_ids(sequence_maps, "sequence_id", "thick_sequences")
    for idx, seq in enumerate(sequence_maps):
        for beat_id in _require_list(
            seq.get("synopsis_beat_ids"), f"thick_sequences[{idx}].synopsis_beat_ids"
        ):
            if _require_text(beat_id, "sequence.synopsis_beat_id") not in beat_ids:
                raise ArchitectureContractError(f"SEQUENCE_UNKNOWN_BEAT:{beat_id}")
        for event_id in _require_list(
            seq.get("event_ids"), f"thick_sequences[{idx}].event_ids"
        ):
            if _require_text(event_id, "sequence.event_id") not in event_ids:
                raise ArchitectureContractError(f"SEQUENCE_UNKNOWN_EVENT:{event_id}")
        for participant in _require_list(
            seq.get("participants"), f"thick_sequences[{idx}].participants"
        ):
            if _require_text(participant, "sequence.participant") not in character_ids:
                raise ArchitectureContractError(f"SEQUENCE_UNKNOWN_CHARACTER:{participant}")
        for group_id in _require_list(
            seq.get("group_ids"), f"thick_sequences[{idx}].group_ids"
        ):
            if _require_text(group_id, "sequence.group_id") not in group_ids:
                raise ArchitectureContractError(f"SEQUENCE_UNKNOWN_GROUP:{group_id}")
        boundary = _require_mapping(seq.get("boundary"), f"thick_sequences[{idx}].boundary")
        _require_text(boundary.get("value_shift"), f"thick_sequences[{idx}].boundary.value_shift")
        _require_text(boundary.get("turn_type"), f"thick_sequences[{idx}].boundary.turn_type")
        _require_text(boundary.get("exit_pressure"), f"thick_sequences[{idx}].boundary.exit_pressure")

    ir_core: Dict[str, Any] = {
        "schema": "P07_RB_NARRATIVE_ARCHITECTURE_IR_V1",
        "architecture": {layer: frozen[layer] for layer in REQUIRED_LAYERS},
        "phase1_output_digest": stable_digest({layer: frozen[layer] for layer in REQUIRED_LAYERS}),
        "surface_text_authored_by_python": False,
        "provider_generation_required": True,
    }
    ir = dict(ir_core)
    ir["runtime_ir_digest"] = stable_digest(ir_core)
    return ir


def build_surface_provider_packet(ir: Mapping[str, Any]) -> Dict[str, Any]:
    """Compile Runtime IR(실행체 중간표현) into LLM-2 provider packet without writing prose."""
    ir = _require_mapping(ir, "runtime_ir")
    architecture = _require_mapping(ir.get("architecture"), "runtime_ir.architecture")
    missing = [layer for layer in REQUIRED_LAYERS if layer not in architecture]
    if missing:
        raise ArchitectureContractError("IR_MISSING_LAYER:" + ",".join(sorted(missing)))

    packet_core: Dict[str, Any] = {
        "schema": "P07_RB_LLM2_SURFACE_PROVIDER_PACKET_V1",
        "runtime_ir_digest": _require_text(ir.get("runtime_ir_digest"), "runtime_ir_digest"),
        "instructions": [
            "Consume every architecture layer as an active narrative constraint.",
            "Preserve ownership, group obligations, synopsis causality and THICK boundaries.",
            "Write final literary surface freely; do not expose analytic metadata as screenplay prose.",
            "Do not allow Python-authored or Python-repaired literary sentences.",
        ],
        "architecture": {layer: copy.deepcopy(architecture[layer]) for layer in REQUIRED_LAYERS},
        "surface_policy": {
            "surface_text_authored_by_python": False,
            "provider_generation_required": True,
            "semantic_contract_fidelity_required": True,
        },
    }
    packet = dict(packet_core)
    packet["phase2_packet_digest"] = stable_digest(packet_core)
    return packet


@dataclass(frozen=True)
class ChainRun:
    status: str
    attempt_index: int
    phase1_output_digest: str | None
    runtime_ir_digest: str | None
    phase2_packet_digest: str | None
    phase2_receipt: Dict[str, Any] | None
    error: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "attempt_index": self.attempt_index,
            "phase1_output_digest": self.phase1_output_digest,
            "runtime_ir_digest": self.runtime_ir_digest,
            "phase2_packet_digest": self.phase2_packet_digest,
            "phase2_receipt": self.phase2_receipt,
            "error": self.error,
        }


def run_llm_runtime_llm_chain(
    source_seed: Mapping[str, Any],
    phase1_provider: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    phase2_provider: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    *,
    attempt_index: int = 1,
) -> ChainRun:
    """Run mechanical LLM-1 -> Runtime -> LLM-2 chain with fail-closed behavior."""
    phase1_digest: str | None = None
    try:
        phase1_output = dict(phase1_provider(source_seed))
        phase1_digest = stable_digest(phase1_output)
        ir = compile_narrative_architecture(phase1_output)
        packet = build_surface_provider_packet(ir)
        receipt = dict(phase2_provider(packet))
        if receipt.get("consumed_packet_digest") != packet["phase2_packet_digest"]:
            raise ArchitectureContractError("PHASE2_RECEIPT_DIGEST_MISMATCH")
        return ChainRun(
            status="ALLOW_PROVIDER_RENDER",
            attempt_index=attempt_index,
            phase1_output_digest=phase1_digest,
            runtime_ir_digest=ir["runtime_ir_digest"],
            phase2_packet_digest=packet["phase2_packet_digest"],
            phase2_receipt=receipt,
        )
    except ArchitectureContractError as exc:
        return ChainRun(
            status="HOLD_ARCHITECTURE_CONTRACT",
            attempt_index=attempt_index,
            phase1_output_digest=phase1_digest,
            runtime_ir_digest=None,
            phase2_packet_digest=None,
            phase2_receipt=None,
            error=str(exc),
        )


def make_fixture_architecture(marker: str = "BASE") -> Dict[str, Any]:
    """Frozen synthetic fixture(동결 합성 고정자료) for NONFORMAL mechanical testing."""
    return {
        "social_ecology": {
            "characters": [
                {"character_id": "C_A", "name": "A"},
                {"character_id": "C_B", "name": "B"},
                {"character_id": "C_C", "name": "C"},
            ],
            "groups": [
                {"group_id": "G_HOME", "name": "HOME", "member_ids": ["C_A", "C_B"]},
                {"group_id": "G_WORK", "name": "WORK", "member_ids": ["C_B", "C_C"]},
            ],
            "relationships": [
                {"from": "C_A", "to": "C_B", "state": f"trust_under_pressure::{marker}"},
                {"from": "C_B", "to": "C_C", "state": "professional_dependency"},
            ],
        },
        "group_membership": [
            {"character_id": "C_A", "group_id": "G_HOME", "role": "protector", "obligation": "keep_family_secret"},
            {"character_id": "C_B", "group_id": "G_HOME", "role": "mediator", "obligation": "prevent_split"},
            {"character_id": "C_B", "group_id": "G_WORK", "role": "operator", "obligation": "deliver_evidence"},
            {"character_id": "C_C", "group_id": "G_WORK", "role": "superior", "obligation": "contain_risk"},
        ],
        "event_ownership": [
            {"event_id": "E_SECRET", "owner_id": "C_A", "affected_group_ids": ["G_HOME"], "pressure": "secret_may_surface"},
            {"event_id": "E_EVIDENCE", "owner_id": "C_B", "affected_group_ids": ["G_WORK", "G_HOME"], "pressure": "evidence_forces_choice"},
        ],
        "detailed_episode_synopsis": {
            "episode_goal": "force a choice that transfers pressure across home and work groups",
            "beats": [
                {"beat_id": "B1", "summary": "evidence appears and destabilizes work obligations", "event_ids": ["E_EVIDENCE"]},
                {"beat_id": "B2", "summary": "the work choice threatens the family secret", "event_ids": ["E_EVIDENCE", "E_SECRET"]},
            ],
        },
        "thick_sequences": [
            {
                "sequence_id": "S1",
                "synopsis_beat_ids": ["B1"],
                "event_ids": ["E_EVIDENCE"],
                "participants": ["C_B", "C_C"],
                "group_ids": ["G_WORK"],
                "boundary": {
                    "value_shift": "control_to_exposure_risk",
                    "turn_type": "forced_commitment",
                    "exit_pressure": "C_B must choose whether to carry evidence home",
                },
            },
            {
                "sequence_id": "S2",
                "synopsis_beat_ids": ["B2"],
                "event_ids": ["E_EVIDENCE", "E_SECRET"],
                "participants": ["C_A", "C_B"],
                "group_ids": ["G_HOME"],
                "boundary": {
                    "value_shift": "trust_to_conditional_alliance",
                    "turn_type": "relationship_reframe",
                    "exit_pressure": "family duty and work duty can no longer be separated",
                },
            },
        ],
    }


def phase1_architecture_test_double(source_seed: Mapping[str, Any]) -> Dict[str, Any]:
    marker = str(source_seed.get("marker", "BASE"))
    return make_fixture_architecture(marker)


def phase2_surface_test_double(packet: Mapping[str, Any]) -> Dict[str, Any]:
    """Receipt-only Test Double(영수증 전용 시험 모사); it does not author screenplay prose."""
    architecture = _require_mapping(packet.get("architecture"), "packet.architecture")
    return {
        "provider": "TEST_DOUBLE_ONLY",
        "consumed_packet_digest": packet["phase2_packet_digest"],
        "consumed_layer_digests": {
            layer: stable_digest(architecture[layer]) for layer in REQUIRED_LAYERS
        },
        "all_required_layers_consumed": all(layer in architecture for layer in REQUIRED_LAYERS),
        "surface_text_generated": False,
    }


def mutate_one_layer(architecture: Mapping[str, Any], layer: str) -> Dict[str, Any]:
    mutated = copy.deepcopy(dict(architecture))
    if layer == "social_ecology":
        mutated[layer]["relationships"][0]["state"] += "::MUT_SOCIAL"
    elif layer == "group_membership":
        mutated[layer][0]["obligation"] += "::MUT_MEMBERSHIP"
    elif layer == "event_ownership":
        mutated[layer][0]["pressure"] += "::MUT_OWNERSHIP"
    elif layer == "detailed_episode_synopsis":
        mutated[layer]["beats"][0]["summary"] += "::MUT_SYNOPSIS"
    elif layer == "thick_sequences":
        mutated[layer][0]["boundary"]["exit_pressure"] += "::MUT_BOUNDARY"
    else:
        raise KeyError(layer)
    return mutated


def evaluate_mechanical_closure(attempt_index: int = 1) -> Dict[str, Any]:
    """Execute the preregistered G1-G8 sentinel and return a machine-readable result."""
    base_arch = make_fixture_architecture("BASE")
    base_run = run_llm_runtime_llm_chain(
        {"marker": "BASE"},
        lambda _: copy.deepcopy(base_arch),
        phase2_surface_test_double,
        attempt_index=attempt_index,
    )
    if base_run.status != "ALLOW_PROVIDER_RENDER":
        return {
            "schema": "P07_RB_MECHANICAL_SENTINEL_RESULT_V1",
            "attempt_index": attempt_index,
            "base_run": base_run.to_dict(),
            "gates": {f"G{i}": False for i in range(1, 9)},
            "verdict": "FAIL_NONFORMAL_MECHANICAL_ARCHITECTURE_CLOSURE_SENTINEL",
        }

    base_ir = compile_narrative_architecture(base_arch)
    base_packet = build_surface_provider_packet(base_ir)

    mutation_runs: Dict[str, Any] = {}
    for layer in REQUIRED_LAYERS:
        mutated = mutate_one_layer(base_arch, layer)
        run = run_llm_runtime_llm_chain(
            {"marker": layer},
            lambda _seed, payload=mutated: copy.deepcopy(payload),
            phase2_surface_test_double,
            attempt_index=attempt_index,
        )
        mutation_runs[layer] = {
            "run": run.to_dict(),
            "packet_changed": (
                run.status == "ALLOW_PROVIDER_RENDER"
                and run.phase2_packet_digest != base_run.phase2_packet_digest
            ),
        }

    missing_layer_runs: Dict[str, Any] = {}
    for layer in REQUIRED_LAYERS:
        missing = copy.deepcopy(base_arch)
        missing.pop(layer)
        run = run_llm_runtime_llm_chain(
            {"marker": f"missing:{layer}"},
            lambda _seed, payload=missing: copy.deepcopy(payload),
            phase2_surface_test_double,
            attempt_index=attempt_index,
        )
        missing_layer_runs[layer] = run.to_dict()

    broken_cases = {
        "unknown_event_owner": ("event_ownership", 0, "owner_id", "C_UNKNOWN"),
        "unknown_membership_group": ("group_membership", 0, "group_id", "G_UNKNOWN"),
        "unknown_synopsis_event": ("detailed_episode_synopsis", "beats", 0, "event_ids", ["E_UNKNOWN"]),
        "unknown_sequence_beat": ("thick_sequences", 0, "synopsis_beat_ids", ["B_UNKNOWN"]),
        "unknown_sequence_character": ("thick_sequences", 0, "participants", ["C_UNKNOWN"]),
        "unknown_sequence_group": ("thick_sequences", 0, "group_ids", ["G_UNKNOWN"]),
    }
    broken_runs: Dict[str, Any] = {}
    for name in broken_cases:
        broken = copy.deepcopy(base_arch)
        if name == "unknown_event_owner":
            broken["event_ownership"][0]["owner_id"] = "C_UNKNOWN"
        elif name == "unknown_membership_group":
            broken["group_membership"][0]["group_id"] = "G_UNKNOWN"
        elif name == "unknown_synopsis_event":
            broken["detailed_episode_synopsis"]["beats"][0]["event_ids"] = ["E_UNKNOWN"]
        elif name == "unknown_sequence_beat":
            broken["thick_sequences"][0]["synopsis_beat_ids"] = ["B_UNKNOWN"]
        elif name == "unknown_sequence_character":
            broken["thick_sequences"][0]["participants"] = ["C_UNKNOWN"]
        elif name == "unknown_sequence_group":
            broken["thick_sequences"][0]["group_ids"] = ["G_UNKNOWN"]
        run = run_llm_runtime_llm_chain(
            {"marker": name},
            lambda _seed, payload=broken: copy.deepcopy(payload),
            phase2_surface_test_double,
            attempt_index=attempt_index,
        )
        broken_runs[name] = run.to_dict()

    gates = {
        "G1_COMPLETE_FIVE_LAYER_PRESENCE": set(base_ir["architecture"].keys()) == set(REQUIRED_LAYERS),
        "G2_REFERENCE_INTEGRITY": base_run.status == "ALLOW_PROVIDER_RENDER",
        "G3_DOWNSTREAM_CONSUMPTION": (
            set(base_packet["architecture"].keys()) == set(REQUIRED_LAYERS)
            and bool(base_run.phase2_receipt)
            and bool(base_run.phase2_receipt.get("all_required_layers_consumed"))
        ),
        "G4_INDEPENDENT_PERTURBATION_PROPAGATION": all(
            item["packet_changed"] for item in mutation_runs.values()
        ),
        "G5_FAIL_CLOSED_MISSING_LAYER": all(
            item["status"] == "HOLD_ARCHITECTURE_CONTRACT"
            for item in missing_layer_runs.values()
        ),
        "G6_BROKEN_REFERENCE_HOLD": all(
            item["status"] == "HOLD_ARCHITECTURE_CONTRACT"
            for item in broken_runs.values()
        ),
        "G7_NO_PYTHON_SURFACE_AUTHORSHIP": (
            base_ir["surface_text_authored_by_python"] is False
            and base_ir["provider_generation_required"] is True
            and base_packet["surface_policy"]["surface_text_authored_by_python"] is False
            and base_packet["surface_policy"]["provider_generation_required"] is True
        ),
        "G8_RECEIPT_CHAIN": all(
            [
                bool(base_run.phase1_output_digest),
                bool(base_run.runtime_ir_digest),
                bool(base_run.phase2_packet_digest),
                bool(base_run.phase2_receipt),
                base_run.phase2_receipt.get("consumed_packet_digest") == base_run.phase2_packet_digest,
            ]
        ),
    }
    passed = all(gates.values())
    return {
        "schema": "P07_RB_MECHANICAL_SENTINEL_RESULT_V1",
        "attempt_index": attempt_index,
        "formal_experiment_count": 137,
        "r140_formal_attempt": 0,
        "r140_formal_output": 0,
        "r140_formal_score": 0,
        "base_run": base_run.to_dict(),
        "base_packet_digest": base_packet["phase2_packet_digest"],
        "mutation_runs": mutation_runs,
        "missing_layer_runs": missing_layer_runs,
        "broken_reference_runs": broken_runs,
        "gates": gates,
        "verdict": (
            "PASS_NONFORMAL_MECHANICAL_ARCHITECTURE_CLOSURE_SENTINEL"
            if passed
            else "FAIL_NONFORMAL_MECHANICAL_ARCHITECTURE_CLOSURE_SENTINEL"
        ),
        "claim_boundary": {
            "live_llm_used": False,
            "craft_quality_claim": False,
            "pre_r140_candidate_authority_modified": False,
            "production_modified": False,
        },
    }
