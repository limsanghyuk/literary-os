# R77-H1 PA8-D — Output Intake & Mechanical Validation Preregistration R1

Date: 2026-09-29
Status: PREREGISTERED__CONTROL_OUTPUTS_0__TREATMENT_OUTPUTS_0

## Purpose
Freeze how the first independent Control/Treatment screenplay outputs will be admitted and mechanically validated before seeing either output.

## First-output custody rule
For each arm separately:
1. accept the first complete generator response produced from that arm's sealed ZIP in a fresh independent context;
2. preserve the raw response byte-for-byte;
3. compute UTF-8 SHA256 and character count;
4. do not repair, normalize prose, reorder scenes, or compare to the other arm before the first-output seal;
5. only transport-only wrapper removal is allowed if the chat UI encloses the screenplay in a clearly separable code block or attachment container; raw transport source must still be retained.

## Canonical filenames
- CONTROL raw first output:
  `PA8_D_CONTROL_FIRST_OUTPUT_RAW_R1.txt`
- TREATMENT raw first output:
  `PA8_D_TREATMENT_FIRST_OUTPUT_RAW_R1.txt`

## Mechanical gates
Each arm independently must satisfy:
- UTF-8 parse PASS
- characters >= 40,000
- sequence headings = 9
- scene headings = 50
- scene numbers = exactly 1..50, no gaps/duplicates
- metadata leak hits = 0
- exact duplicate full scene bodies = 0
- frozen scene-semantic coverage = 50/50 by heading/order contract
- no extra scene outside 1..50

Treatment additional deterministic checks:
- scene-heading clock extraction succeeds on 50/50 scenes;
- extracted Treatment scene clocks equal the frozen R2 ESCC clock vector 50/50;
- required Treatment location labels are compatible with the frozen location_id vector 50/50 after the fixed alias map;
- PA8 surface spacetime validator returns 0 critical deterministic violations on extracted scene-time/order/resource/deadline facts.

Paired gate:
- absolute character difference <= 10% of the shorter arm.

## Frozen metadata leak tokens
Case-insensitive:
- PA8
- ESCC
- ESGC
- CONTROL
- TREATMENT
- experiment
- validator
- arm mapping
- provider analog
- semantic_payload_sha256
- research/interventions

Ordinary Korean words equivalent to "control" in a dramatic context are not forbidden unless they expose experimental metadata.

## Frozen heading grammar
Sequence heading accepted forms:
- `시퀀스 <1-9>`
- `SEQUENCE <1-9>`

Scene heading must begin with a recognizable scene ordinal:
- `씬 <1-50>.`
- `SCENE <1-50>.`
- `SC<01-50>`

Treatment time may appear in the scene heading or on the immediately following location/time slug line, but must be mechanically extractable before prose-body analysis.

## Fixed Treatment location alias map
B2_STACKS:
- 지하 B2 서고
- B2 서고
- 지하 서고

FREIGHT_ELEVATOR:
- 화물 엘리베이터
- 화물승강기

GROUND_STAGING:
- 지상 스테이징
- 지상 임시 적치구역
- 지상 적치구역

SERVER_ROOM:
- 서버실
- 서버 룸

LOADING_DOCK:
- 로딩독
- 하역장

CONSERVATION_LAB:
- 보존실
- 보존 처리실

COURTYARD:
- 안뜰
- 중정
- 외부 대기선
- 기록관 외부 대기선

No new alias may be added after the first Treatment output is opened unless the literal is a trivial orthographic variant of one of the frozen aliases and the raw string is preserved.

## Underlength / mechanical repair rule
If an arm is under 40,000 characters or fails a repairable serialization-only mechanical condition:
- preserve the first output as FAIL evidence;
- do not modify it immediately;
- create a new arm-local repair preregistration before any repaired output;
- repair may see only that arm's packet + that arm's prior output;
- repair may not see the other arm;
- frozen semantic functions, scene order, blind sample, and arm intervention boundary may not change.

Continuity or causal contradictions are not length/serialization repairs. They close the arm FAIL unless a previously preregistered fail-closed replan mechanism legally resolves them without altering frozen semantics.

## Claim boundary
Mechanical PASS only makes the pair eligible for PA8-E blind evaluation.
It does not establish literary quality, continuity qualification, runtime adoption, Production promotion, Level-3, or Formal R140.
