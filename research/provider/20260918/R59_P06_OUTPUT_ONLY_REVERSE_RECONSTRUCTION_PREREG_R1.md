# R59 — P06 Output-Only Reverse Reconstruction (출력물 전용 역재구성) Preregistration R1

Date: 2026-09-18
Status: `PREREGISTERED__FRESH_EVALUATOR_REQUIRED__NO_RESULT_YET`
Parent physical authority: `SYNC-R58 / ADAPTIVE_UL16`
Production/control: `ENG:R47 / LEGACY_R53`
Runtime DB authority: `DB59 frozen`
Formal scored count impact: `NONE`
Candidate code impact: `NONE`

## 1. Numbering rule
Research numbering proceeds monotonically and sequentially:
`R58 -> R59 -> R60 -> R61 ...`

No `R59-0`, `R59-1`, or other sub-number is used as a separate research transaction.
R59 is exclusively the Output-Only Reverse Reconstruction (출력물 전용 역재구성) study.

## 2. Purpose
Test whether the completed P06 screenplay itself carries enough information for an independent evaluator to reconstruct the narrative state that the upper-layer architecture intended to realize.

Core distinction:
`Structure Contract Satisfied (구조 계약 충족) != Dramatic / Textual State Recoverability (극적·텍스트 상태 복원 가능성)`

R59 does NOT evaluate whether the screenplay is human-level overall.
It evaluates whether the screenplay, without architecture disclosure, makes its major narrative state legible and recoverable.

## 3. Frozen input
Evaluator packet:
`SYNC_R58_P06_OUTPUT_ONLY_RECONSTRUCTION_PACKET_R1.zip`

Packet bytes: `29182`
Packet SHA256: `26cb904b69ae446d6d2d08e8e6b4e6735376efe33d18ffc4c5a83320122ff515`

Contained screenplay:
- SHA256: `88e74a280be7c657eb241309144475be4fcc702f1052646f31b8fe608e25d653`
- UTF-8 bytes: `84,722`
- 11 sequences / 55 scenes
- completed Provider (제공자) screenplay only

The packet contains:
- `SCREENPLAY_ONLY.txt`
- `EVALUATOR_INSTRUCTIONS.md`
- `MANIFEST.json`

It MUST NOT contain the original P06 architecture, mapping, prior audit conclusions, handoff conclusions, or current coordinator findings.

## 4. Independence gate
The evaluator must be fresh with respect to P06 architecture.

The evaluator must:
1. read only the frozen screenplay-only packet;
2. not search Literary OS, SYNC-R58, P06, GitHub, prior evaluations, mappings, or handoffs;
3. not request or infer the original architecture before sealing its result;
4. mark unsupported states `NOT RECOVERABLE (복원 불가)` instead of guessing;
5. seal the reconstruction result before any architecture disclosure.

The current coordinator is NOT eligible because it has already seen the P06 architecture and prior audit.

If evaluator independence cannot be established:
`R59 = HOLD__INDEPENDENT_EVALUATOR_UNAVAILABLE`

## 5. Required reconstruction output
The sealed evaluator result must reconstruct, from screenplay evidence only:

1. Episode Premise (회차 전제)
2. Major Threads (주요 서사선)
3. Sequence Functions (시퀀스 기능)
4. Major Scene Transactions (주요 장면 거래)
5. Relationship Deltas (관계 변화)
6. Information Deltas (정보 변화)
7. Social / Institutional Deltas (사회·제도 변화)
8. Due-now Items Apparently Resolved (현재 해결된 것으로 보이는 의무)
9. Deferred / Open Obligations (유예·열린 의무)
10. Final Next-Episode State (다음 회차로 넘길 최종 상태)

For every major item:
- scene evidence;
- confidence `HIGH / MEDIUM / LOW`;
- evidence mode `EXPLICIT / BEHAVIORALLY_INFERABLE / WEAKLY_IMPLIED / NOT_RECOVERABLE`.

## 6. Sealing rule
Before architecture disclosure, seal:
- evaluator identifier;
- evaluation timestamp;
- complete reconstruction text or JSON;
- SHA256 of the result artifact;
- declaration that the evaluator had not seen the original P06 architecture.

No post-disclosure edits are allowed to the sealed reconstruction.
Any correction after disclosure must be stored separately as a post-unblind annotation and cannot alter the blind result.

## 7. Post-seal comparison taxonomy
Only after sealing, compare reconstruction against the frozen P06 architecture using these labels:

- `RECOVERED_EXACT_OR_EQUIVALENT (정확·동등 복원)`
- `RECOVERED_PARTIAL (부분 복원)`
- `NOT_RECOVERED (미복원)`
- `INVENTED_CLOSURE (근거 없는 종결 추정)`
- `INVENTED_STATE (근거 없는 상태 추정)`
- `HIDDEN_STATE_DEPENDENCE (숨은 상태 의존)`
- `SURFACE_DRIFT (표면 이탈)`
- `ARCHITECTURE_ONLY_STATE (구조에만 존재하는 상태)`

## 8. Primary gate
R59 is a State-Carry eligibility gate, not a literary-quality score competition.

### PASS
`R59 = PASS__TEXT_STATE_RECOVERABILITY_SUFFICIENT_FOR_STATE_CARRY_VALIDATION`
only if all of the following hold:
1. all six P06 due-now resolution states are at least `RECOVERED_PARTIAL`;
2. no due-now item is `INVENTED_CLOSURE`;
3. every state proposed for next-episode commit is supported by screenplay evidence;
4. no critical next-episode state depends only on architecture-hidden information;
5. deferred/open obligations are either recoverable from text or explicitly withheld from automatic commit.

### HOLD
`R59 = HOLD__TEXT_STATE_RECOVERABILITY_INCOMPLETE`
if any critical next-episode state is `NOT_RECOVERED`, `HIDDEN_STATE_DEPENDENCE`, or `ARCHITECTURE_ONLY_STATE`, or if an apparently resolved due-now item is an invented closure.

R59 has no FAIL state for literary quality. A HOLD means the State Carry (상태 이월) loop is not yet safe to close.

## 9. Secondary diagnostics
Measure but do not use as a standalone pass criterion:
- thread recall;
- sequence-function recoverability;
- relationship-delta recoverability;
- information-delta recoverability;
- social/institutional-delta recoverability;
- due-now resolution recoverability;
- deferred/open obligation recoverability;
- confidence calibration;
- number of invented states/closures.

## 10. Prohibited actions during R59
- Do not rerun Provider (제공자).
- Do not regenerate the screenplay.
- Do not rerun Architecture-Only Blind (구조 전용 블라인드).
- Do not modify Candidate (후보 엔진) code.
- Do not change DB59 authority.
- Do not use DB64 as runtime authority.
- Do not start R60 before R59 blind reconstruction is sealed and compared.

## 11. Authority impact
R59 is research-only.

`CURRENT_PHYSICAL_AUTHORITY = SYNC-R58`
`CANDIDATE_ROUTE = ADAPTIVE_UL16`
`PRODUCTION = ENG:R47 / LEGACY_R53`
`RUNTIME_DB = DB59 frozen`

## 12. Next research after R59
If R59 closes:
`R60 = Text-Derived State Carry Closure (대본 기반 상태 이월 폐쇄)`

R60 must consume the sealed R59 result, not the original architecture alone.

Status token:
`R59__OUTPUT_ONLY_REVERSE_RECONSTRUCTION__PREREGISTERED__SCREENPLAY_ONLY_SHA_LOCKED__FRESH_EVALUATOR_REQUIRED__SEAL_BEFORE_ARCHITECTURE_DISCLOSURE__NO_ENGINE_CHANGE__SYNC_R58_CURRENT`
