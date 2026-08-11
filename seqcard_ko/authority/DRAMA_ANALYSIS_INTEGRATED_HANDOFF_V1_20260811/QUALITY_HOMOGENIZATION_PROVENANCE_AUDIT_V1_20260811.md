# 품질 균질화 + Provenance + 감사 증거 실행 규약 V1

문서 ID: `QUALITY_HOMOGENIZATION_PROVENANCE_AUDIT_V1_20260811`  
목적: 작품/회차/블록에 따라 분석 품질이 얕아지거나, 구조 검증만 통과한 가짜 의미 데이터가 정본화되는 것을 방지한다.

## 1. 왜 필요한가

실제 작업에서 다음 결함이 발견됐다.

1. **가을동화 grain collapse** — EP01은 충분한 의미 깊이였지만 이후 회차가 schema minimum 위주로 얕아져 old validator는 PASS했음.
2. **궁 초기 THICK 후보** — event 174/174가 Stage02 exact copy, scene_notes 1089/1089가 Stage01 exact copy, cast/info가 scene-note 재기술 중심이라 독립 THICK 저작성이 부족했음. 후보 폐기 후 직접독해 재저작.
3. **legacy R5 debt 결함** — 장기 열린 thread가 있는데 unresolved/subplot/character debt가 시즌 내내 비어 있는 작품이 있었음.
4. **stale runtime 결함** — THICK가 수정돼도 old Runtime/manifest/work_state가 active면 제거된 의미가 downstream에 남음.
5. **패키징 evidence skew** — 최종 ZIP 수정 뒤 validation/checksum을 재실행하지 않으면 보고서가 artifact와 다른 revision을 가리킬 수 있음.

따라서 품질은 `schema pass`가 아니라 **source-grounded semantic depth + provenance + downstream closure + frozen artifact evidence**로 정의한다.

## 2. 균질화의 기준

### 필수 동일성

모든 회차에 동일하게 적용:

- full episode direct read
- 4-quarter attention pass
- all human sequences reread
- source refs
- exact schema
- episode light audit
- independent source audit

블록은 의미 compression 단위가 아니다.

### 금지

- 첫 회차만 깊게 쓰고 나머지를 template fill
- proposition 수를 목표로 padding
- diversity 점수만 올리기 위해 정상 정보를 다른 말로 억지 변형
- 빈 info/payoff를 강제로 채움

## 3. THICK quality signals

### main operational gate

현재 12작에서 사용한 main diversity operational floor: `0.748`.

### auxiliary diagnostics

- template/cliche
- cast restatement
- payoff restatement
- proposition restatement
- title quote
- payoff/info coverage
- event/cast/info diversity

auxiliary는 **진단·위치 찾기용**이다. 단독 hard gate로 승격하지 않는다.

### semantic review triggers

- event가 기존 sequence_intent와 대량 exact copy
- scene_notes가 Stage01 intent_gist와 대량 exact copy
- cast function이 scene note/sequence summary와 과도 중복
- info before/after가 실제 contradictory state가 아님
- 동일 work에서 thread semantics가 끊기거나 ID가 episode-local dump
- 3 consecutive eps: ≥90% scenes exactly one proposition
- source line range/evidence density 급락

## 4. Provenance exact floor

THICK의 six hash roles:

1. baseline_artifact_sha256
2. source_text_sha256
3. scene_card_file_sha256
4. sequence_blueprint_file_sha256
5. episode_arc_file_sha256
6. source_lock_sha256

모든 값은 lowercase 64 hex.

SOURCE evidence는 실제 source file과 line range로 resolve되어야 한다.

현재 12작 reference result:

- source refs: 27,197
- exact line refs: 27,197
- actual provenance hash checks: 8,975
- errors: 0

## 5. R5 quality

R5는 형식적으로 14키만 맞아도 PASS가 아니다.

검사:

- EP01 empty boundary
- EP02+ source_episode == N-1
- thread through/available_through <= N-1
- duplicate character/relation state 0
- 실제 open thread 존재 시 unresolved/debt가 합리적으로 carry-over
- target/future episode semantic leakage 0
- previous EpisodeArc hash match

장기작에서 시즌 전체 debt가 mechanically empty면 FAIL/REVIEW.

## 6. R8 quality

R8은 의미 독립성 점수를 부여하지 않는다. deterministic parity만 검사한다.

- records == SceneCard scenes
- one scene exactly once
- seq membership exact
- cast/event/info/payoff/proposition parity mismatch 0
- source refs preserved

## 7. independent audit evidence

저작자 selfcheck와 독립 감사 evidence를 분리 저장한다.

권장 파일:

```text
validation/<work>/episode/<ep>/selfcheck.json
validation/<work>/episode/<ep>/independent_source_audit.json
validation/<work>/blocks/<block>/strong_audit.json
validation/<work>/final/semantic_quality_audit.json
validation/<work>/final/exact_schema_validation.json
validation/<work>/final/provenance_validation.json
validation/<work>/final/planner_runtime_validation.json
validation/<work>/final/non_target_immutability.json
validation/<work>/final/fresh_extraction_validation.json
```

파일명은 active package convention에 맞춰도 되지만 **역할 분리는 유지**한다.

## 8. 패키징 순서

잘못된 순서:

`validate → checksum → ZIP mutate → release`

정상 순서:

`semantic freeze → final artifact freeze → fresh extract → validators → authority/hash integrity → non-target immutability → builder reproduction → release gate → checksums`

ZIP을 수정한 뒤 이전 validation report를 그대로 재사용하지 않는다.

## 9. 현재 reference work quality

| 작품 | main diversity |
|---|---:|
| 경성스캔들 | 0.799 |
| 결혼못하는남자 | 0.779 |
| 공주가돌아왔다 | 0.766 |
| 내이름은김삼순 | 0.761 |
| 내여자친구는구미호 | 0.759 |
| 난폭한로맨스 | 0.749 |
| 강남엄마따라잡기 | 0.826 |
| 너의목소리가들려 | 0.814 |
| 개와늑대의시간 | 0.816 |
| 101번째프로포즈 | 0.782 |
| 가을동화 | 0.758 |
| 궁 | 0.783 |

새 작품은 이 문장들을 흉내 내지 않는다. **분포/직접독해 discipline을 품질 앵커로 사용**한다.
