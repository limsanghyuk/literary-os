# EXT6 Layer–Gate Execution Matrix V1.0

- Status: ACTIVE
- Purpose: prevent a declared gate from being omitted from release execution.
- Rule: a layer without an executed gate is `UNVERIFIED`, not PASS.

| Layer | Authority class | Required gate/tool | Required result | Release effect |
|---|---|---|---|---|
| EntityBridge | authored | `ext6_gate_ab.py` Gate A | ERRORS 0 | blocks work freeze |
| CastPresence | authored | `ext6_gate_ab.py` Gate A/B + source-grounded audit | ERRORS 0 | blocks work freeze |
| CharacterLoad | derived | `ext6_gate_ab.py` recomputation | exact equality | blocks work freeze |
| CastCoverageLedger | audit | `ext6_gate_ab.py` B6 | complete disjoint union | blocks work freeze |
| SourceHeadingRegistry | authored/audit | source-heading validator | complete source coverage | blocks work freeze |
| SourceSceneAlignment | authored/audit | monotonic non-overlap validator | ERRORS 0 | blocks work freeze |
| DesignSeedRecord | advisory | `ext6_seed_gate.py` SEED-A/B/C | PASS or HOLD, never implicit | blocks Phase02 pilot seal only |
| SeedAdmissibility | advisory | `ext6_seed_gate.py` SEED-A/C | ADMISSIBLE | blocks Phase02 pilot seal only |
| SeedAuthoringBoundaryManifest | advisory/provenance | `ext6_seed_gate.py` A/B/C | hashes and boundaries valid | blocks Phase02 pilot seal only |
| SeedStructurePrediction | derived | `ext6_seed_gate.py` A/D | five indicators per mode | blocks SEED-D decision |
| SeedContamination | derived | `ext6_seed_gate.py` A/D | formula exact | blocks SEED-D decision |

## Mandatory execution order

```text
Phase01/V1.2 gates
→ baseline immutability
→ Phase02 SEED-A
→ Phase02 SEED-B with source files
→ Phase02 SEED-C
→ blind seal
→ optional full-read comparison
→ deterministic prediction/contamination
→ SEED-D
→ fresh extraction
```

## Status vocabulary

```text
PASS                  gate executed, all hard checks zero
HOLD_SOURCE_REQUIRED  source verification could not run
FAIL                  one or more hard checks failed
UNVERIFIED            required gate was not executed
PROMOTE/REVISE/REJECT SEED-D advisory decision only
```

A release report must list every row applicable to the package and the exact command, timestamp, exit code, report path, and input SHA.
