# R62 EXTERNAL JUDGE CUSTODY & RESULT MATRIX R1

Date: 2026-09-20
Status: `THREE_JUDGMENTS_RECEIVED__SCIENTIFIC_RESULT_CLOSED__CUSTODY_LIMITATIONS_EXPLICIT`

## Source custody

### J01
Delivery mode:
- user supplied complete JSON inline in coordinator conversation
- no separate original file attachment was supplied

Metadata:
- judge_id: J01
- model/config: GPT-5.6 Sol / High
- independence_attestation: true
- pairs: 12/12
- critical violations: 0

Raw winner sequence by pair C01..C12:
`B, A, B, A, B, A, A, B, B, A, A, A`

Original-file SHA256:
`UNAVAILABLE__INLINE_JSON_NOT_FILE_BYTES`

### J02
Delivery mode:
- user supplied complete JSON inline in coordinator conversation
- no separate original file attachment was supplied

Metadata:
- judge_id: J02
- model/config: GPT-5.6 Sol / High
- independence_attestation: true
- pairs: 12/12
- critical violations: 0

Raw winner sequence by pair C01..C12:
`A, B, B, B, A, B, B, B, B, A, A, A`

Original-file SHA256:
`UNAVAILABLE__INLINE_JSON_NOT_FILE_BYTES`

### J03
Delivery mode:
- exact JSON file attached by user
- filename:
  `J03_R62_F01_STAGE_GRAMMAR_BLIND_RESULT_R1.json`

Metadata:
- judge_id: J03
- model/config: GPT-5.6 Sol / High
- independence_attestation: true
- pairs: 12/12
- critical violations: 0

Raw winner sequence by pair C01..C12:
`TIE, A, A, B, A, A, A, A, B, B, B, A`

The conversation attachment is the original file custody source.
The current coordinator did not recompute a byte SHA because local container execution was in TransportTimeout state.

## Mapped Treatment arms

J01:
`C01=B C02=A C03=B C04=A C05=B C06=B C07=A C08=A C09=B C10=A C11=B C12=A`

J02:
`C01=A C02=B C03=B C04=B C05=A C06=A C07=B C08=A C09=B C10=A C11=B C12=A`

J03:
`C01=B C02=A C03=A C04=B C05=A C06=B C07=A C08=B C09=B C10=B C11=A C12=A`

Each mapping is exactly 6 A / 6 B.

Important custody note:
The sealed coordinator-secret ZIP could not be byte-extracted after all judgments because local container execution returned TransportTimeout. Treatment-arm mapping was reconstructed from treatment-only transaction-family signatures and checked against the preregistered 6A/6B balance. This limitation is disclosed and no judge result was altered.

## Mapped result matrix

- C01_PORT_LOCKOUT — Treatment WIN: J01 W / J02 W / J03 T
- C02_NEWSROOM_SOURCE — Treatment WIN: W / W / W
- C03_HOSPITAL_BLACKOUT — Treatment WIN: W / W / W
- C04_SCHOOL_AUDIT — Treatment WIN: W / W / W
- C05_INHERITANCE — Treatment WIN: W / W / W
- C06_FACTORY_STRIKE — Treatment LOSS: L / L / L
- C07_BOARDROOM — Treatment WIN: W / W / W
- C08_MOUNTAIN_RESCUE — Treatment LOSS: L / L / L
- C09_COURT_EVIDENCE — Treatment WIN: W / W / W
- C10_TEAM_FINAL — Treatment WIN: W / W / W
- C11_MUSEUM_THEFT — Treatment LOSS: L / L / L
- C12_DATACENTER_OUTAGE — Treatment WIN: W / W / W

Aggregate:
- wins 9/12
- ties 0/12
- losses 3/12
- wins+ties 9/12
- critical Treatment state-fidelity violations 0

Final scientific result:
`R62 = CLOSED_FAIL`

Canonical result:
`research/interventions/20260920/R62_F01_STAGE_GRAMMAR_DIVERSIFICATION_EXTERNAL_BLIND_RESULT_R1.md`

## Recovery rule
A new session must NOT rerun the three valid judgments merely because J01/J02 lacked separate file attachments or because the coordinator-secret ZIP could not be extracted during the runtime incident.

If stronger byte custody is desired later, preserve the original conversation/export as provenance and create a separate normalization receipt. Do not replace or re-score the valid judgments.

Status token:
`R62_JUDGE_CUSTODY_R1__3_OF_3_RECEIVED__J01_J02_INLINE__J03_FILE__R62_FAIL_IMMUTABLE__NO_RERUN`
