# EXT6 Layer–Gate Execution Matrix V1.0.2

- Status: ACTIVE
- Rule: a required gate not executed is `UNVERIFIED`, never PASS.

| Layer | Required tool | Required result |
|---|---|---|
| EntityBridge / CastPresence / CharacterLoad | `ext6_phase01_derived_gate.py` | ERRORS 0 and exact CharacterLoad equality |
| DesignSeed / Admissibility / BoundaryManifest | `ext6_seed_gate_v1_0_2.py --phase seal` | PASS |
| Prediction / Contamination | `ext6_seed_gate_v1_0_2.py --phase evaluate` | PASS |
| Terminal ending/cost observations | hash-bound indicator evidence audit | PASS |
| Corpus FK | mandatory `--corpus-index` | available and all IDs exist |
| Package | checksum + fresh extraction | 0 mismatch |

Execution order: Phase01 gate → blind seal → full seal → evaluation → atomic metadata/checksum → fresh extraction.

- Proper-name check ignores generic role nouns but blocks work-specific names.
- Opposition persistence resolves RelationshipArc labels through bridge aliases before aggregation.
