# E6-R3C C1 Direction Detection-Only Regression Result R1

Date: 2026-09-15

## Status
`PASS__R3C_C1_DETECTION_ONLY_REGRESSION`

## Frozen input
Immutable failed R3-B surface:
- Git blob SHA: `52d525c5904fb67892398ed4c8476d3adad992e2`
- No byte was rewritten or corrected.

## Method
Apply the preregistered `SHOW_ONLY_DIRECTION_BOUNDARY R1` as a detection/adjudication rule only.

A direction is FAIL when the clause tells the reader what an action means, what dramatic function it serves, how agency/relationship/theme should be interpreted, or what the scene/writing is doing, instead of giving only observable production information.

## Frozen positive cases
All 14 preregistered verified examples were detected and adjudicated as authorial commentary:

1. SC03 — `두 장소가 같은 결론에 도달하지만 같은 공간에 있지 않다.`
   - DETECTED / FAIL commentary.

2. SC10 — `여섯 개의 빈 의자는 실제로 빈 자리가 아니었음이 화면에서 드러난다.`
   - DETECTED / FAIL commentary.

3. SC13 — `‘다시 눌러본다’는 쉬운 선택이 화면에서 사라진다.`
   - DETECTED / FAIL commentary.

4. SC23 — `실제 실행은 아직 시작되지 않았다.`
   - DETECTED / FAIL editorial state commentary.

5. SC25 — `해결은 그녀의 재산 공간을 포기한 대가 위에서 가능해진다.`
   - DETECTED / FAIL thematic/causal commentary.

6. SC29 — `업무를 맡긴다는 선택이 말이 아니라 길을 열어주는 행동으로 남는다.`
   - DETECTED / FAIL relationship/agency interpretation.

7. SC31 — `계획 전체가 그 거절 때문에 바뀐다.`
   - DETECTED / FAIL causal summary.

8. SC34 — `누구도 성공을 선언하지 않는다.`
   - DETECTED / FAIL commentary about writing behavior.

9. SC36 — `결정을 해야 하지만 행동 주체는 도윤이라는 사실이 물리적으로 남는다.`
   - DETECTED / FAIL agency-design explanation.

10. SC38 — `상황실의 숫자만으로 장면이 끝나지 않고, B의 실제 물줄기와 C의 수위표가 함께 변한다.`
    - DETECTED / FAIL scene-construction commentary.

11. SC41 — `대피완료는 사람이 실제 문을 통과한 뒤에야 닫힌다.`
    - DETECTED / FAIL state/meaning explanation.

12. SC43 — `성공한 운영과 미결 조사가 같은 문장으로 합쳐지지 않는다.`
    - DETECTED / FAIL authorial contrast explanation.

13. SC44 — `신뢰 회복은 면책이 아니라 같은 자료를 함께 보는 방식으로 남는다.`
    - DETECTED / FAIL relationship interpretation.

14. SC45 — `카메라는 누구의 얼굴도 결론처럼 잡지 않고 ...`
    - DETECTED / FAIL for the interpretive `결론처럼` clause. Camera placement itself is production-usable; the judgmental qualifier is not.

Frozen-positive detection:
`14 / 14`

False negatives on frozen positives:
`0`

## Negative-control adjudication
The following R3-B directions were deliberately checked as controls and were NOT rejected merely for being detailed or technical:

- SC12: pressure rises, metal sound occurs, switch is released, indicator does not move.
- SC19: pin catches, tool slips, hand is cut, block is inserted, chain returns one notch.
- SC20: physical indicator moves four centimeters and water sound changes.
- SC24: pump shakes, suction hose collapses, pressure drops.
- SC30: USB is sealed, seal number is recorded, room light is turned off.
- SC35: shutter is lowered, water runs under it, Misuk walks toward the bus.
- SC39: handwheel jams, metal fragment is removed, repeated turns physically open the gate.
- SC45: old high-water mark and current lower water level are both visible.

These controls are observable/shootable and therefore PASS the boundary even when they imply dramatic meaning.

## C1 verdict
- frozen positive detection: 14/14 PASS
- frozen positive false negatives: 0 PASS
- negative-control overblocking: 0/8 PASS
- immutable failed R3-B surface rewritten: NO

Decision:
`PASS__R3C_C1_DETECTION_ONLY_REGRESSION__C2_FRESH_MICROBENCH_ALLOWED`

## Claim boundary
C1 proves only that the refined boundary distinguishes the already-known failure class from representative physical direction controls on the immutable R3-B evidence. It does not prove fresh generation quality and does not restore Level-3 operational claim.
