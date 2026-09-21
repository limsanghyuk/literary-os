# R70 Stage B R2 Fresh Input and Execution Seal R1

Date: 2026-09-21
Status: `FRESH_12_SEALED__PROVIDER_EXECUTION_SEALED_BEFORE_OUTPUTS__LIVE_OUTPUTS_0`

## Source freeze
Implementation Freeze commit:
`f8e4de42db9904e77dcac3345ad23fd9e668344b`

Frozen R2 Runtime SHA256:
`34476d35f365a27e7e8e773b05c2951c4febc72bde8104e29f68e1e6d754d31d`

## Fresh Stage B R2 inputs
Fresh case count:
`12`

Input JSON SHA256:
`2d16692cc970e3d54ce66b4dd318c83dcee08170fb2445739095f7750985c56e`

Paired Payload JSON SHA256:
`bf0426e1c02c262a328c4691560048bcf737d7f4b3399ad1e0101b17a4e0ed76`

Hidden Mapping SHA256:
`c3340b146c3901b4e652b2b947ae76eb9a846fcbaad21a2bd17dda6b0e9cec17`

Mapping balance:
`Treatment=A 6 / Treatment=B 6`

Pre-output request hash file SHA256:
`15fbb71a9796a51541f164d9afde7a3630282f309b00c5db156039800ff50409`

Shared R2 renderer instructions SHA256:
`bac59b7b71c715994ceee5b20a2206734f2946ec02cb798699b42e1b5cd0050b`

## Provider Execution Seal
Status:
`SEALED_BEFORE_OUTPUTS`

Execution Seal SHA256:
`0c8a9781fbf27a78e2a583f45d2d23afb244991cbd052872ac3759fb0b6735b7`

Settings:
- provider: OpenAI
- API: Responses
- model: gpt-5.6-sol
- reasoning: high
- max_output_tokens: 12000
- timeout: 600 seconds
- max attempts per arm: 2
- no quality-motivated retry
- no fallback/template evidence

Live Runner SHA256:
`a0befe3e7fd3c030261207177ff37b8032a03f83fa5d3cef27b28909a4f2f838`

Post-run Audit SHA256:
`107ca360a518e9f146cb4d4ba9f28f350a8746ecc1bfbf36c0b11cb7e1bc4b19`

Windows Launcher SHA256:
`0dfda600445a149dbe5cc51ab99b9145990272c3754ccabdeb5ca19434e629e3`

Codex Execution Bundle SHA256:
`fadab523c4cc82b6244a046ff245fa59de7e248c05ecad00a8098cb8e7f978bd`

## No-key preflight
PASS.

With OPENAI_API_KEY absent:
- exit before first provider call;
- message: `OPENAI_API_KEY not available; no provider calls made`;
- no live output directory created.

## Validity rule
Literary judging is forbidden unless:
- valid arms = 24/24;
- valid pairs = 12/12.

If not:
`R70_STAGE_B_R2_VALIDITY_HOLD__NO_QUALITY_VERDICT`

If yes:
seal outputs -> J01/J02/J03 independent blind -> mapping reveal -> unchanged quality gate.

## Authority
Unchanged:
- Physical Authority: SYNC-R67
- Active Qualified Candidate: R69/R68/R67/R66
- Production: ENG:R47 / LEGACY_R53
- R70: research-only, not promoted

Status token:
`R70_STAGE_B_R2_FRESH_12_AND_EXECUTION_SEALED__OUTPUTS_0__READY_FOR_CODEX_LIVE_EXECUTION`
