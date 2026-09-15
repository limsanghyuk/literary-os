# E6-R3B Internal Whole-Episode Dramaturgy Audit Result R1

Date: 2026-09-15

## Experiment
`P07-E6-R3B-FRESH-WHOLE-EPISODE-DRAMATURGY-REQUALIFICATION-R1`

## Frozen parent
- Historical physical authority: `SYNC-R52`
- Operational Level-3 claim: suspended pending dramaturgy requalification
- Parent R3-A: `PASS__R3A_DRAMATURGY_MICROBENCH__STAGE_B_FRESH_WHOLE_EPISODE_ALLOWED`
- R3-B prereg SHA (Git blob): `694762f2d1c11b3c39287a5c063eae20982a75c2`
- R3-B plan/contracts SHA (Git blob): `f781c4fc3f0e58d28dd5f1833e1b4ad3be7b31c9`

## Scientific surface output
- File: `E6_R3B_WHOLE_EPISODE_SURFACE_R1.md`
- Scientific output commit: `3283dc768102293d45b483b11db8586a5ea213af`
- Git blob SHA: `52d525c5904fb67892398ed4c8476d3adad992e2`
- 9 sequences / 45 named scenes are present in the sealed output.
- No post-output surface editing is permitted.

## What improved versus E6-R2
The R3-B output does NOT reproduce the old fixed `4 speaking characters / 6 utterances` template. The sealed planning topology is materially diverse and the surface actually uses low-dialogue scenes, two-person scenes, ensemble scenes, remote/cross-cut scenes, civilian refusal/choice scenes and multi-step crisis scenes.

Observed successful repairs include:
- SC06: Han Misuk directly refuses to evacuate without her father.
- SC08: Kang Seojin directly refuses unverified full bypass discharge.
- SC12-SC15: first gate-drive attempt fails visibly and simple retry is explicitly rejected by the responsible field actor.
- SC19-SC20: second attempt changes conditions, incurs hand injury and produces only a partial physical result.
- SC22/SC25: civilian economic loss and choice are enacted by Misuk rather than reported by staff.
- SC24-SC25-SC33: pump failure -> alternative access -> resident sacrifice -> second installation -> observable operation.
- SC29: Harin directly asks whether she will be removed from duty; Seojin directly answers, rather than another character summarizing the relationship change.
- SC31/SC34/SC41: evacuation is changed by resident/elder refusal and concludes with actual arrival, not only a numeric status report.
- SC37-SC40: irreversible manual-gate choice, first manual failure, obstacle removal, costly retry and observable water-level consequence are enacted.
- SC44-SC45: accountability remains open through new evidence rather than a state-summary speech.

## Critical internal finding
R3-B still violates the frozen R3 surface rule:

> direction is playable/shootable and does not explain dialogue meaning.

The problem is no longer the E6-R2 fixed dialogue template. It is `DRAMATURGICAL_COMMENTARY_LEAKAGE_IN_DIRECTION` — stage direction sometimes shifts from observable action into authorial interpretation of what the scene means.

### Verified examples from the immutable surface
1. SC03: `두 장소가 같은 결론에 도달하지만 같은 공간에 있지 않다.`
   - First half is interpretation of dramatic meaning, not an actor/camera action.

2. SC10: `여섯 개의 빈 의자는 실제로 빈 자리가 아니었음이 화면에서 드러난다.`
   - Explains the intended interpretation of the image.

3. SC13: `‘다시 눌러본다’는 쉬운 선택이 화면에서 사라진다.`
   - Explicit authorial commentary about option structure.

4. SC23: `실제 실행은 아직 시작되지 않았다.`
   - Editorial state explanation appended to otherwise playable blocking.

5. SC25: `해결은 그녀의 재산 공간을 포기한 대가 위에서 가능해진다.`
   - Explains theme/cost instead of showing only the physical consequence.

6. SC29: `업무를 맡긴다는 선택이 말이 아니라 길을 열어주는 행동으로 남는다.`
   - Explains the meaning of Seojin stepping aside.

7. SC31: `계획 전체가 그 거절 때문에 바뀐다.`
   - Causal summary rather than playable direction.

8. SC34: `누구도 성공을 선언하지 않는다.`
   - Meta description of what the writing avoids, not a shot/action.

9. SC36: `결정을 해야 하지만 행동 주체는 도윤이라는 사실이 물리적으로 남는다.`
   - Directly explains agency design.

10. SC38: `상황실의 숫자만으로 장면이 끝나지 않고, B의 실제 물줄기와 C의 수위표가 함께 변한다.`
    - Explains the intended dramaturgical construction.

11. SC41: `대피완료는 사람이 실제 문을 통과한 뒤에야 닫힌다.`
    - State/meaning explanation after the physical arrival already shows it.

12. SC43: `성공한 운영과 미결 조사가 같은 문장으로 합쳐지지 않는다.`
    - Authorial interpretation of file separation.

13. SC44: `신뢰 회복은 면책이 아니라 같은 자료를 함께 보는 방식으로 남는다.`
    - Relationship interpretation rather than action.

14. SC45: `카메라는 누구의 얼굴도 결론처럼 잡지 않고 ...`
    - Camera placement is shootable, but `결론처럼` is interpretive and carries authorial judgment.

This is not a single isolated sentence. The same failure mode appears across early/middle/late episode regions and therefore is treated as a systemic whole-episode direction-craft defect.

## Gate application
Frozen R3-B rules required:
- direction playable/shootable;
- direction must not explain dialogue meaning;
- internal whole-episode PASS before external blind release;
- SAFE_NO_COMMIT on any critical failure.

Decision:
`FAIL__R3B_SYSTEMIC_DRAMATURGICAL_COMMENTARY_LEAKAGE_IN_DIRECTION__SAFE_NO_COMMIT`

## Consequences
- State Commit: `0`
- External blind packet release: `PROHIBITED`
- External judgments: `0`
- The immutable R3-B surface must NOT be edited into a replacement PASS.
- Historical E6-R2 original-gate PASS remains preserved and claim-limited.
- Historical R52 Level-3 entry declaration remains preserved in lineage.
- Operational Level-3 claim remains suspended.

## Root-cause refinement
Old E6-R2 root cause:
`SEMANTIC_PLAN_LEAKAGE_IN_NATURAL_LANGUAGE + FIXED_4_PERSON_6_UTTERANCE_RENDERER`

R3-B demonstrates that the topology/dialogue-template portion is substantially repaired, but a narrower conversion defect remains:
`SEMANTIC_INTENT -> AUTHORIAL_DIRECTION_COMMENTARY`

The renderer understands the scene's dramatic purpose but occasionally writes that purpose as explanation after already showing the physical action.

## Successor recommendation
Open a fresh successor only after preregistering a `SHOW_ONLY_DIRECTION_BOUNDARY`:
- Direction may contain only observable environment, action, blocking, facial/breath/voice behavior, prop interaction, silence and camera-legible physical consequence.
- Direction may NOT name the dramatic function, agency ownership, causal lesson, relationship meaning, thematic cost, success/failure interpretation, or what the scene/writing is doing.
- A deterministic/manual validator must flag phrases of the form `~라는 사실`, `~로 남는다`, `~때문에 계획이 바뀐다`, `해결은 ~ 위에서 가능`, `장면이 ~`, `화면에서 드러난다`, `성공을 선언하지 않는다`, etc. as candidates for coordinator adjudication.
- The repair must be tested first on the immutable failed R3-B output as detection-only regression; it must NOT rewrite that evidence.
- Then use a fresh whole-episode sample for qualification. Do not reuse `물이 돌아오는 길` as the PASS sample.
