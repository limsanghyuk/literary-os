# P07-I4G Pre-output Gate — Checkpoint R1

Date: 2026-09-08
Classification: DEVELOPMENT PREFORMAL / INTERRUPTION-SAFE CHECKPOINT

Preregistration commit: `dff1c990d72eff1b8f8acf228d856aa212eebe64`.
Prospective sample checkpoint commit: `ae8ec6bc1bb6eb10f5eea96259809e3799a05f54`.
Sample Root SHA256: `ab7a562f9df6e1e99952719039cccc26eaa6ebd8030895d25dde292a22d76f5e`.

## Pre-output result
`PASS__PERFORMANCE_DIRECTION_CONTRACT_VALIDATED__TREATMENT_OUTPUTS_0`

- PerformanceDirectionContractR1 count: 12
- validation: 12/12 PASS
- semantic/speaker binding: PASS
- selected consumed-field mutation changes provider literary-payload hash: 12/12
- irrelevant metadata mutation leaves provider literary payload invariant: 12/12
- focused research-runtime tests: 6/6 PASS
- Human Anchor inspected: FALSE
- Treatment prose output count: 0

PerformanceDirection contract file SHA256:
`290090d70ce1df00a2cf03b0f8fe40e590e657dc90d719165cfa77236ccd9bba`

Pre-output gate JSON SHA256:
`5d95ea6388fd8e2697f65456e5b19e936adcf9479ed94286d8bd09d6c80b289c`

## Research-only code
The research runtime adds `PerformanceDirectionContractR1` canonicalization/validation and passes it into the copied I4D renderer payload/instructions. This code is NOT active policy and is not yet in canonical C2.

Focused tests prove:
- contract validation/canonicalization;
- consumed-field mutation causally changes payload;
- irrelevant metadata does not;
- binding mismatch fails closed;
- renderer payload contains the contract;
- no-contract backward compatibility.

## Next exact action
Generate exactly 12 Treatment scenes for the frozen sample with the same semantic invariants, speaker authorization and current I4D mode status (`NONE`). Then seal exact Treatment bytes and run mechanical gates. Do not inspect Human Anchors.

If a new session resumes from this checkpoint, do not reselect scenes, do not modify thresholds, and do not regenerate contracts. Resume with Treatment generation only.
