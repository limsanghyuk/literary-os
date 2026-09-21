# START HERE — SYNC-R68 Post-R70 Session Handoff R1

Date: 2026-09-21

Status:
`SYNC_R68_PHYSICAL_SNAPSHOT_SEALED__R70_RESEARCH_CUSTODIED__REAL_PROVIDER_HOLD__R71_NOT_STARTED`

## 1. Canonical authority
- Physical Authority: **SYNC-R68**
- Parent Physical Authority: **SYNC-R67**
- Active Qualified Candidate: **R69 F06 / R68 F04 / R67 F07 / R66 F01 lineage**
- Active Runtime SHA256: `3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`
- Production Engine: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**
- Formal scored authority: unchanged
- R70 is NOT promoted to Candidate or Production.

SYNC-R68 is a physical research-state snapshot. It preserves the latest research state through R70 without asserting that R70 passed its real-provider surface-effect gate.

## 2. 5-Part / 9-Package read order
`CONTROL -> A -> B1 -> B2 -> C1 -> C2-A -> C2-B -> D1 -> D2`

SYNC-R68 Trust Root SHA256:
`38069b916f4d02f827f74cf76812e559d369e72c3c649895825c803c92d0c274`

9-Package Manifest SHA256:
`ae7d7714c4e453e823085c47631a882475271e32d4e5e885210d20ba36e58f1d`

Audit Receipt SHA256:
`4722835ecdffc715ab4166e5218259cc2750152444c12d41f42ead1590b9c7d8`

SHA256SUMS SHA256:
`d9b798534f94721793ddc32a0be034f407bbfd2c82e8932ed691e6661b6a57d2`

C2 logical SHA256:
`eefd5b853ff8957925d924573c1f0531506668c27b7e4c8438104ce60779dbea`

## 3. Session research chronology

### A. Part C delivery / packaging repair
The historical SYNC-R67 C1 original was no longer retained on the active conversation file surface.
A verified Recovery R1 was constructed without claiming byte identity to the lost historical C1.
C2-A historical bytes remained exact.

A later size audit found that C1 had grown mostly because multiple copies of Current/Candidate/Parent/Fallback runtimes and nested research-evidence archives duplicated the same ~19 MiB runtime repeatedly.

Packaging policy was corrected:
- C1 = **Slim Runtime Core**
- C2 = **Research / Evidence Archive**
- Developer Hub = **Canonical research/governance history**

SYNC-R67 Slim C1 was reduced to 140,372,821 bytes while preserving exact R69 current runtime.

SYNC-R68 continues this slim C1 policy.

### B. R70 Stage A — F08 Authorized Provider Context
Causal target:
`F08_AUTHORIZED_PROVIDER_CONTEXT`

Treatment context includes cutoff-safe:
- canonical character state;
- existing explicit voice/speech fields;
- cast-relevant relationship state;
- relevant information state;
- social ecology/group membership;
- explicit planner-only and future-source exclusion.

Deterministic result:
- 12/12 PASS
- planner/future leakage 0

This did not close R70 because Stage B real-provider surface effect remained required.

### C. R70 Stage B R1 — actual provider execution
Developer/Codex evidence was ingested and preserved.

Observed:
- actual generation calls: 48
- HTTP 200: 48/48
- Provider OK: 48/48
- valid arms: 0/24
- valid pairs: 0/12
- invalid pairs: 12/12
- local failure reason: `EXIT_STATE_MISMATCH` 48/48
- judges: 0
- mapping reveal: NO

Verdict:
`R70_STAGE_B_EXECUTED__VALIDITY_HOLD__NO_QUALITY_VERDICT__NO_PROMOTION`

Direct validity defect:
the local guard required exact string equality for `exit_state`, while renderer instructions requested semantic preservation and also prohibited mechanical blueprint wording repetition; schema allowed free-string `exit_state`.

Offline diagnostic:
changing only the output `exit_state` to the frozen expected literal made 48/48 attempts pass the unchanged guard.
This identifies the blocking mechanism only. It does not prove screenplay semantic fidelity or Treatment literary-quality superiority.

### D. R70 Stage B R2 — Exit-State Machine Contract Repair
R1 was preserved immutable.

R2 preregistered a narrow repair:
- `exit_state` becomes a machine-contract field;
- single-value enum equal to blueprint.exit_state;
- exact verbatim copy instruction;
- anti-mechanical-copy rule applies only to literary prose;
- local exact-match guard unchanged;
- Control/Treatment Provider Context logic unchanged.

Frozen R2 Runtime SHA256:
`34476d35f365a27e7e8e773b05c2951c4febc72bde8104e29f68e1e6d754d31d`

Fresh cases were created only after source freeze.

Fresh Input SHA256:
`2d16692cc970e3d54ce66b4dd318c83dcee08170fb2445739095f7750985c56e`

Paired Payload SHA256:
`bf0426e1c02c262a328c4691560048bcf737d7f4b3399ad1e0101b17a4e0ed76`

Hidden Mapping SHA256:
`c3340b146c3901b4e652b2b947ae76eb9a846fcbaad21a2bd17dda6b0e9cec17`

Mapping remains unrevealed.

### E. Pre-API Virtual Provider Analog
Real API/Codex execution became impractical, so the live R2 trial was suspended without modifying frozen scientific artifacts.

A transport-faithful virtual Responses-API analog was used to exercise the frozen request / retry / guard / custody path.

Initial virtual tests found a new execution-harness-only defect:
- HTTP 200 + malformed output_text could raise an uncaught JSON parse exception;
- HTTP 200 + refusal/no output_text could raise an uncaught exception;
- runner could terminate before the frozen retry rule operated.

A harness-only amendment was preregistered BEFORE modification.

The scientific runtime, prompt, output schema, local guard, Control/Treatment context, fresh inputs, paired payloads, hidden mapping, provider settings, retry count and literary quality gate did not change.

After containment repair, virtual scenarios passed:
- normal structured response -> 12/12 valid pairs;
- exit-state first failure -> retry -> 12/12;
- incomplete -> retry -> 12/12;
- HTTP error -> retry -> 12/12;
- failed status -> retry -> 12/12;
- malformed JSON -> retry -> 12/12;
- refusal -> retry -> 12/12;
- persistent model mismatch -> safe VALIDITY_HOLD;
- persistent malformed JSON -> safe VALIDITY_HOLD;
- persistent refusal -> safe VALIDITY_HOLD;
- no-key fail-closed -> PASS;
- rerun protection -> PASS;
- credential artifact leakage -> 0;
- hidden mapping inside live bundle -> 0.

Claim:
`R70_STAGE_B_R2_EXECUTION_HARNESS_PREAPI_QUALIFIED`

Pre-API validated execution bundle SHA256:
`cfd1541e3eb533af209ecd1254eacf21896b3564b6f3b1a3d44ca10dd67f2503`

This does NOT establish actual OpenAI literary-output quality, F08 surface effect, or Level-3 restoration.

## 4. Exact R70 state
`R70_STAGE_A_PASS__STAGE_B_R1_VALIDITY_HOLD__STAGE_B_R2_PREAPI_VIRTUAL_QUALIFIED__REAL_PROVIDER_HOLD__LIVE_R2_OUTPUTS_0`

Rules:
- do not reinterpret R1 as Treatment loss;
- do not reveal R2 mapping;
- do not regenerate R2 fresh inputs/payloads;
- do not tune R2 scientific runtime;
- when real provider access is restored, use ONLY the PREAPI_VALIDATED R2 bundle.

## 5. Next research while R70 real-provider trial is held
R71 is PLANNED, not started.

Candidate:
`R71 — F02 Visible-Action Causal Realization`

Question:
Can important state changes be causally bound to necessary screen-visible carriers rather than declarative dialogue/exposition?

Candidate carrier families:
- physical action;
- failed action;
- object transaction;
- blocking change;
- gaze/expression shift;
- silence/pause;
- approach/withdrawal;
- withholding.

Core planned tests:
- state-to-action binding;
- counterfactual removal;
- non-declarative substitution.

R71 must be architecture-level, API-independent, and causally isolated from R70.

After R71, candidate R72:
`F05 Adaptive Distribution / Count Pressure`

Goal:
sequence/scene count should emerge from obligation burden.
Human-authored distributions are calibration/metrology only, never fixed quotas.

## 6. Level-3 boundary
Component passes do not establish Level-3.

Later integrated requalification must include:
`State -> Episode -> Sequence -> Scene -> Surface >=35,000 chars -> Output-only Reverse Reconstruction -> Canonical State Commit -> >=3 Episode State Carry -> Fault Injection / Responsible-Ancestor Repair`

## 7. New-session exact resume procedure
1. Read this document first.
2. Load SYNC-R68 packages in canonical order.
3. Verify Trust Root and SHA256SUMS.
4. Verify C1 `LITERARY_OS_RUNTIME_SOURCE_CURRENT.zip` SHA256 equals exact R69 runtime SHA.
5. Confirm R70 R2 real provider outputs remain 0 and mapping remains hidden.
6. If API/Codex is still unavailable, begin only R71 preregistration.
7. If API/Codex is restored and developer chooses to resume R70, use only the PREAPI_VALIDATED bundle.
8. Do not start R72 before R71 adjudication.
9. Do not claim Level-3 restoration before integrated requalification.

Status token:
`SYNC_R68_SEALED__R70_PREAPI_VIRTUAL_QUALIFIED_REAL_PROVIDER_HOLD__R71_PLANNED_NOT_STARTED__NEW_SESSION_READY`
