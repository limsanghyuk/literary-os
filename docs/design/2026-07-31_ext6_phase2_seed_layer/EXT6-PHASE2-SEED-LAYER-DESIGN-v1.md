# EXT6 Phase 02 설계안 — 기획씨앗층 (DesignSeed Layer) v1

- 문서 ID: `CLAUDE-EXT6-PHASE02-SEED-v1`
- 상태: `CLAUDE_DESIGN_DRAFT` — 제안서. 정본 아님. 저작 착수 전 사용자 승인 필요.
- 작성일: 2026-07-31
- 작성 주체: Claude (Opus) 트랙
- 상위 계약: `docs/design/2026-07-13_seqcard_ext6_phase1_contract/SEQCARD-EXT6-PHASE1-FROZEN-CONTRACT-v1.md` (FROZEN)
- 대조 검토 대상: `docs/external/GPT_EXT6_PHASE01_INDEPENDENT_PROPOSAL_v1.md` (`GPT_INDEPENDENT_DRAFT_LOCKED`)
- 동반 문서: `docs/proposals/CLAUDE_REVIEW_OF_GPT_PHASE01_v1.md`

---

## 0. 왜 Phase 02 인가 — 계약 위치

Phase 01 계약은 **FROZEN** 이며 그 §0 은 범위를 이렇게 못박는다.

```text
Scope: P0 3계약만 — EntityBridge · CastPresence · CharacterLoad.
(CharacterVoice/Motif/Theme/Affect 등 나머지 EXT6 층은 이 계약 범위 밖 — 후속 Phase.)
Status: FROZEN — 변경은 v2 재발행으로만.
```

따라서 씨앗층은 **Phase 01 계약을 수정해서 끼워 넣을 수 없다.** Phase 01 이 이미 예고한 "후속 Phase" 자리에 **새 계약 문서**로 들어간다. Phase 01 의 비타협 원칙 — Stage01~04 SSOT 불변, SceneCard 9키 확장 금지, 사이드카 전용, 권위 3구분(`authored_`/`derived_`/`advisory_`), Gate 통과 전 정본 승격 금지 — 은 **그대로 상속한다.**

## 0.1 이 층이 존재해야 하는 이유

현재 DB 는 **완성된 구조를 기술한다.** SceneCard 104,578 · LocalEdge 20,635 · PayoffCandidate 8,593 · CharArc 10,731 · RelArc 9,078 · CastPresence 62,183. 전부 "이 작품은 이렇게 되어 있다"이다.

생성 시스템에 필요한 것은 그 앞 단계다. **무엇으로부터 이 구조가 나왔는가.** 로그라인, 인물 구도의 초기 배치, 세계의 제약, 작가가 미리 정한 결말 방향 — 구조가 도출되어 나온 씨앗. 씨앗→구조의 사상(map)이 없으면 시스템은 구조를 복제할 수 있을 뿐 설계할 수 없다.

**설계 목표는 씨앗을 기록하는 것이 아니라 씨앗→구조 사상을 학습 가능하게 만드는 것이다.** 이 구분이 이하 모든 설계 결정을 지배한다.

---

## 1. 치명적 위험 — 순환성 (Circularity)

완성작을 읽고 뽑은 씨앗은 **원인이 아니라 요약이다.**

```text
완성된 구조 → (역추출) → "씨앗" → (학습) → 구조
```

이 고리로 학습한 모델은 설계를 배우지 않는다. **복호화를 배운다.** 씨앗 필드에 이미 정답 구조가 인코딩되어 있으므로 예측이 성립하지만, 새 씨앗을 받으면 아무것도 못한다. 데이터 누설(leakage)의 교과서적 형태이며, 층 전체를 무가치하게 만든다.

이 위험은 EXT6 P0(CastPresence 등)에는 존재하지 않는다. "이 씬에 누가 있는가"는 원문에 실재하는 사실이고 행 대조로 검증된다. **씨앗층은 우리 검증 문화가 처음으로 깨지는 지점이다.** 씨앗은 원문에 축자적으로 존재하지 않으므로 `verify2.py` 식 행 대조가 원리적으로 불가능하다.

### 1.1 왜 이 경고를 실측 근거 위에서 하는가

2026-07-30 FULLDB V19 편입 검증에서 확인된 결함: **원문 본문이 통째로 비어 있는 씬 343건에 Stage01 이 그럴듯한 `intent_gist` 를 써 넣었다.** (굿캐스팅 EP03 은 빈 씬 22건 중 20건이 이 경우 — 헤딩 `환풍구 안 (낮)` 다음이 공백인데 "미순은 숨을 참으며 좁은 덕트 안에서 소리 없이 대기한다"가 기록됨.)

이것이 잡힌 유일한 이유는 **원문이 옆에 있었기 때문**이다. 근거 공백에 그럴듯한 텍스트를 채우는 것은 우발적 실수가 아니라 LLM 저작의 기본 실패 양식이다. 씨앗층은 층 전체가 근거 공백 위에 놓인다. 아무 장치 없이 저작하면 **343건짜리 결함이 90작 전체 규모로 재현된다.**

### 1.2 두 번째 실측 근거 — 게이트를 만들어도 돌리지 않으면 표류한다

본 설계 과정에서 추가로 확인한 결함(2026-07-31 실측): `authored_bridge` 2,147행 중 **1,534행(71.45%)이 Phase 01 동결 enum `mapping_status ∈ {PROVISIONAL, MAPPED, CONFLICT}` 를 위반**하고 있다. 실사용은 미선언 5값(`PROVISIONAL_ROLE` 922 · `PROVISIONAL` 613 · `RESOLVED_LOCAL` 474 · `RESOLVED_CANONICAL` 110 · `CONFIRMED` 28)이며 `MAPPED`·`CONFLICT` 는 0회다.

원인은 계약도 도구도 아니다. `_ext6_tools/ext6_gate_ab.py:22` 가 이 enum 을 정확히 강제하도록 구현되어 있으나 **정본 검증 절차의 실행 목록에서 빠져 있었다.** 상세는 `docs/proposals/CLAUDE_REVIEW_OF_GPT_PHASE01_v1.md` §6.1~6.3.

씨앗층 설계에 주는 교훈: **게이트를 정의하는 것과 게이트가 도는 것은 다른 일이다.** 씨앗층은 판단부가 커서 표류하면 되돌리기 어렵다. 그러므로 §5 의 SEED-A/B/C 는 정의만 두지 않고 **층별 게이트-실행 대응표에 등재하고 매 저작 라운드마다 실행을 강제한다.** 실행되지 않은 게이트는 존재하지 않는 게이트다.

그러므로 이 설계의 절반은 스키마가 아니라 **오염 통제 장치**다.


---

## 2. 씨앗의 판별식 — 다대일

씨앗은 **다대일이어야 한다.** 하나의 씨앗에서 서로 다른 여러 구조가 나올 수 있어야 씨앗이다. 씨앗과 구조가 1:1 로 대응하면 그것은 구조를 다른 말로 옮겨 적은 것이다.

같은 항목이 입자도에 따라 씨앗도 되고 오염도 된다.

| 기술 | 판정 | 이유 |
|---|---|---|
| "목표를 이루되 대가를 치른다" | 씨앗 | 수백 가지 구조를 허용 |
| "주인공은 형이 범인임을 알게 된다" | 경계 | 사건은 특정하나 시점·경로 미정 |
| "14화에서 A가 B의 정체를 안다" | 구조 | 회차·인물·사건이 고정 — 씨앗 아님 |
| "사람이 무언가를 원한다" | 무내용 | 모든 작품을 허용 — 예측력 0 |

**실패 모드가 양쪽에 있다.** 너무 구체적이면 순환(TOO_SPECIFIC), 너무 추상적이면 무내용(TOO_VAGUE). 씨앗은 그 사이 좁은 대역에만 존재한다.

### 2.1 ★ 판별식의 조작적 정의 — 코퍼스 양립도

"다대일"을 문장으로 두면 판정이 주관에 빠진다. **90작 코퍼스 자체를 자로 쓴다.**

```text
씨앗 S 에 대해
  C(S) = { w ∈ 코퍼스 90작 | S 가 w 의 씨앗이었어도 모순 없음 }
  |C(S)| = 양립 작품 수

|C(S)| = 1        → TOO_SPECIFIC  (자기 자신만 허용 = 구조를 옮겨 적음)
2 ≤ |C(S)| ≤ 10   → ADMISSIBLE    (씨앗 대역)
|C(S)| > 30       → TOO_VAGUE     (무내용)
11 ≤ |C(S)| ≤ 30  → REVIEW        (개별 판정)
```

임계 1/10/30 은 **파일럿 착수 전 사전등록**하며 결과를 본 뒤 변경하지 않는다(GPT 안 §5.4 band threshold 원칙을 그대로 차용).

이 검사는 **90작 정본 DB 가 있어야만 성립한다.** 단일 작품 분석으로는 다대일 여부를 판정할 방법이 아예 없다. 코퍼스가 판별기가 되는 구조이며, 우리 DB 의 고유 자산이다.

---

## 3. 스키마 — 근거 가능부 / 판단부 이분

씨앗층 스키마의 최상위 설계 결정: **필드를 증거 요건에 따라 두 블록으로 물리적으로 가른다.** 이 구분을 안 해두면 §1.1 의 Stage01 결함이 층 전체에서 반복된다.

```text
EVIDENCED 블록 = EP01(~02) 원문에서 축자 인용 가능 → 행 대조 강제 (SEED-B)
JUDGED   블록 = 원문에 축자로 존재하지 않음 → 행 대조 면제, 모드 격리·양립도로 통제 (SEED-C)
```

**JUDGED 블록에 `evidence_ref` 를 요구하지 않는다.** 요구하면 저자는 없는 근거를 만들어 낸다. 근거를 못 대는 필드에 근거를 요구하는 것이 바로 343건 결함의 발생 조건이다. 대신 판단부는 **전량 판단임을 스키마가 선언**하고, 다른 장치로 통제한다.

### 3.1 DesignSeedRecord — 정확히 14키

경로: `seqcard_ko/advisory_seed/<work>.<derivation_mode>.seed.json`
grain: **(work_id, derivation_mode) = 1 레코드**

```text
work_id
derivation_mode
read_span
evidenced_initial_configuration
evidenced_world_constraints
evidenced_opening_disturbance
judged_logline
judged_central_lack
judged_governing_question
judged_central_opposition_axis
judged_ending_direction
judged_cost_structure
contract_version
by
```

#### EVIDENCED 블록 (3필드 — 전 항목 `evidence_ref` 필수)

- **`evidenced_initial_configuration`** — 초기 인물 배치.
  `[{character_key, initial_position, initial_relation_axis, evidence_ref}]`
  `character_key` 는 EntityBridge FK(Phase 01 §5.1 재사용). EP01 CastPresence 의 PRIMARY/SECONDARY 집합에서 부분적으로 기계 유도 가능.
- **`evidenced_world_constraints`** — 세계가 부과하는 규칙.
  `[{rule, scope, evidence_ref}]` 예: "힐러는 신원을 드러낼 수 없다", "왕의 딸은 사가로 시집갈 수 없다".
- **`evidenced_opening_disturbance`** — 최초 균형 파괴.
  `{summary, scene_no, evidence_ref}`

`evidence_ref` 규약은 CAST 층 v1.2 를 그대로 승계한다: `EPnn-Snn Lnn <원문 인용>`. 기존 `verify2.py`(±3행 창, 정규화 말미 12자, 8자 미만 제외)가 **수정 없이 재사용된다.**

#### JUDGED 블록 (6필드 — `evidence_ref` 없음)

- **`judged_logline`** — 1문장. 고유명사 금지, 회차 번호 금지.
- **`judged_central_lack`** — 중심 결핍. 주인공에게 없는 것.
- **`judged_governing_question`** — 전편을 지탱하는 질문. Yes/No 로 답할 수 있어야 함.
- **`judged_central_opposition_axis`** — `{pole_a, pole_b}`. 인물명이 아니라 **가치·힘의 축**으로 기술.
- **`judged_ending_direction`** — 작가가 미리 정한 결말 **방향**. `{direction, cost_paid}`.
  `direction ∈ {ACHIEVE, ACHIEVE_WITH_COST, FAIL, FAIL_BUT_TRANSFORM, REFUSE, AMBIGUOUS}`.
  **구체 사건 기술 금지** — "누가 죽는다"는 구조이지 방향이 아니다.
- **`judged_cost_structure`** — 목표 달성 시 치르는 대가의 종류.

#### 메타 (5필드)

- **`derivation_mode` ∈ {PLAN_DOCUMENT, EP01_02_BLIND, FULL_READ}** — §4.
- **`read_span`** — 저작 시 실제 열람한 회차 범위. 모드와 정합해야 함(SEED-A6).
- `contract_version` · `by` · (`work_id`)

### 3.2 SeedAdmissibilityRecord — 정확히 7키

경로: `seqcard_ko/advisory_seed_admissibility/<work>.<mode>.adm.json`
grain: (work_id, derivation_mode)

```text
work_id
derivation_mode
compatible_work_ids
compatibility_count
alternative_structures
specificity_violations
verdict
```

- `compatible_work_ids` — §2.1 의 C(S). 코퍼스 90작 중 이 씨앗과 모순 없는 작품 목록.
- `alternative_structures` — 이 씨앗이 허용하는 **대안 구조 스케치 최소 3개**. `[{sketch, divergence_point}]`. 하나도 못 쓰면 그 씨앗은 구조의 다른 이름이다.
- `specificity_violations` — 씨앗 필드에 등장한 회차 번호·씬 번호·고유명사·특정 사건명 목록. 비어 있지 않으면 SEED-C ERROR.
- `verdict ∈ {ADMISSIBLE, TOO_SPECIFIC, TOO_VAGUE, REVIEW}`

### 3.3 SeedStructurePredictionRecord — 정확히 9키 (결정론 파생, 무LLM)

경로: `seqcard_ko/derived_seed_prediction/<work>.pred.jsonl`
grain: (work_id, derivation_mode, indicator)

```text
work_id
derivation_mode
indicator
predicted_value
observed_value
observation_source
match
corpus_prior
by
```

**사전등록 지표 5종** (N=90 에서 다중검정을 견디기 위해 5개로 제한, Bonferroni α=0.01):

| indicator | 씨앗의 어느 필드에서 예측 | 실측 출처 (기존 층) |
|---|---|---|
| `center_count` | `evidenced_initial_configuration` PRIMARY 수 | CharacterLoad `scene_share_band` DOMINANT+MAJOR 수 |
| `opposition_persistence` | `judged_central_opposition_axis` | RelArc 대립 관계 지속률 |
| `conflict_persist` | `judged_central_lack` 유형 | `_ALL_series_arc.json` `CONFLICT_persist` |
| `ending_direction` | `judged_ending_direction.direction` | CharArc 종단 state_label + Stage04 FullSeriesArc |
| `cost_realized` | `judged_cost_structure` | PayoffCandidate 처분 중 LOSS 계열 비율 |

`corpus_prior` = 90작 주변분포에서의 우연 적중 확률. **비교 기준은 정확도가 아니라 사전분포 초과분이다.**

### 3.4 SeedContaminationRecord — 정확히 8키 (결정론 파생, 무LLM)

경로: `seqcard_ko/derived_seed_contamination/<work>.contam.json`

```text
work_id
mode_b_ref
mode_c_ref
field_level_diff
diverged_fields
mode_b_prediction_accuracy
mode_c_prediction_accuracy
leakage_estimate
```

**순환성을 논증이 아니라 숫자로 만드는 레코드다.**

```text
leakage_estimate = mode_c_prediction_accuracy − mode_b_prediction_accuracy
```

FULL_READ 씨앗이 EP01_02_BLIND 씨앗보다 구조 지표를 훨씬 잘 맞힌다면, 그 초과분은 씨앗의 설계력이 아니라 **정답을 이미 본 데서 온 누설**이다. 누설량이 크면 FULL_READ 산출물은 학습에서 배제한다.

---

## 4. derivation_mode — 오염 통제의 핵심

| mode | 열람 범위 | 순환 위험 | 학습 사용 |
|---|---|---|---|
| `PLAN_DOCUMENT` | 기획의도·기획안·인물소개·시놉시스 실물 | **없음** — 결과 이전에 존재한 문서 | 최우선 |
| `EP01_02_BLIND` | EP01~02 원문만. EP03+ 및 자기 하위층 열람 금지 | 낮음 (§9 약점2 참조) | 주 사용 |
| `FULL_READ` | 전편 정독 | **높음** | 대조군 전용. 기본 배제 |

### 4.1 ★ 실측 — PLAN_DOCUMENT 는 현재 코퍼스에 존재하지 않는다

설계 전 실측했다(로컬 정본, 2026-07-31 기준).

```text
original_extracted 87작 EP01 파일 중
  "기획의도" 본문 보유            0작
  ("기획의도" 문자열 4작 검출 — 전부 방송사 웹페이지 내비게이션 잔여물,
    "기획의도연출진등장인물미리보기 다시보기 대본보기 시청자의견")
  "등장인물" 소개부 보유          3작 / 87작
```

**즉 순환 없는 유일한 근거원이 현재 0/90 이다.** 이 사실을 설계 전제로 명시한다. 결과:

1. Phase 02 파일럿은 **`EP01_02_BLIND` 로만 착수한다.** `PLAN_DOCUMENT` 는 스키마에 정의만 하고 미사용.
2. 신규 작품 편입 시 **기획안·시놉시스 동반 확보를 편입 권고 조건**에 추가한다. 대본만 모으면 이 층의 상한이 영구히 mode B 에 묶인다.
3. 이는 층의 약점이며 숨기지 않는다.

### 4.2 저작 순서 강제 — 역전 금지

```text
mode B 전량 저작 → 봉인 → 그 다음에만 mode C 저작
```

같은 저자가 mode C 를 먼저 쓰면 mode B 를 쓸 때 이미 오염되어 있다. 순서 역전은 SEED-C ERROR. 이상적으로는 **다른 실행(run)이 mode B 와 mode C 를 나눠 맡는다.**

---

## 5. 게이트

### SEED-A — 계약 무결성 (하드, ERRORS 0)

- A1 exact keyset (14/7/9/8키 정확 일치)
- A2 enum 유효 (`derivation_mode`, `direction`, `verdict`)
- A3 타입
- A4 grain 유일 — (work_id, derivation_mode)
- A5 FK — `character_key` ∈ EntityBridge · `scene_no` ∈ SceneCard
- A6 **모드↔범위 정합** — `read_span` 이 `derivation_mode` 허용 범위를 초과하면 ERROR
- A7 `compatible_work_ids` 전원이 코퍼스 실재 work_id

### SEED-B — 근거 대조 (하드, ERRORS 0, **EVIDENCED 블록에 한정**)

- B1 EVIDENCED 3필드 전 항목 `evidence_ref` 비어있지 않음
- B2 `evidence_ref` 규약 `EPnn-Snn Lnn <인용>` 준수
- B3 **원문 행 대조** — 기존 `verify2.py` 그대로. 불일치 0
- B4 인용 대상 회차가 `read_span` 내부
- B5 placeholder 금지
- **B6 JUDGED 블록에 evidence_ref 가 있으면 ERROR** — 판단부에 근거를 붙이는 것 자체가 위반이다. 없는 근거를 만들어 낸 흔적이기 때문이다.

### SEED-C — 반순환 (하드, ERRORS 0)

- C1 `specificity_violations` 비어 있음 (회차 번호·씬 번호·고유명사·특정 사건명 0건)
- C2 `alternative_structures` ≥ 3
- C3 `verdict == ADMISSIBLE` (TOO_SPECIFIC / TOO_VAGUE 는 저작 반려)
- C4 **하위층 미열람 선언** — CharArc 종단 상태·FullSeriesArc·Stage04 Disposition 을 mode B 저작 전 열람하지 않았음
- C5 **모드 순서 준수** — mode C 레코드는 대응 mode B 레코드가 봉인된 뒤에만 존재 가능
- C6 상대 provider 산출물 미열람 선언 (Phase 01 §11 승계)

### SEED-D — 가치 증명 (advisory, 사전등록된 폐기선 보유)

```text
사전등록 판정:
  5개 지표 중 3개 이상에서 mode B 예측이 corpus_prior 를 유의하게 초과 (이항검정, Bonferroni α=0.01)
    → PROMOTE : 90작 전량 확대
  1~2개만 초과
    → REVISE  : 지표·스키마 재설계 후 재검정 1회
  0개 초과
    → REJECT  : 층 폐기. 확대하지 않는다.
  leakage_estimate 중앙값 > 0.30
    → FULL_READ 산출물 학습 영구 배제
```

**폐기선을 사전에 못박는 것이 이 층 설계의 필수 조건이다.** 순환성 때문에 이 층은 실제로 무가치할 가능성이 있고, 그 경우 싸게 버릴 수 있어야 한다. 파일럿 10작 기준 폐기 비용은 90작 확대 비용의 1/9 이다.

---

## 6. 물리 배치

```text
seqcard_ko/
  advisory_seed/<work>.<mode>.seed.json                    # 판단 포함 — advisory_
  advisory_seed_admissibility/<work>.<mode>.adm.json       # 양립도·대안구조
  derived_seed_prediction/<work>.pred.jsonl                # 무LLM 결정론
  derived_seed_contamination/<work>.contam.json            # 무LLM 결정론
  _seed_audit/<work>.seedcoverage.json                     # 필드 커버리지·미판정 목록
  ext6_schema/SEED_LAYER_EXACT_SCHEMA_REGISTRY_V0_1.json   # 키셋 레지스트리
```

**`advisory_` 접두를 쓴다.** Phase 01 §1 의 권위 3구분에서 advisory 는 "가치증명 전 참고"다. 씨앗층은 SEED-D 를 통과하기 전까지 정본 권위를 갖지 않는다. 통과 시 `authored_seed` 로 승격을 **제안**하며, 승격은 사용자 승인 사항이다.

규모: grain 이 작품이므로 **N=90.** 104,578 씬 grain 대비 1,162배 작다. **지금까지 만든 층 중 가장 작고, 가장 되돌리기 쉽다.** 이 점이 착수를 정당화한다 — 틀렸을 때 싸게 버릴 수 있다.

---

## 7. GPT 안 대조 검토

전문 검토는 `docs/proposals/CLAUDE_REVIEW_OF_GPT_PHASE01_v1.md`. 요약:

### 7.1 채택 (씨앗층에 그대로 상속)

| GPT 안 | 조항 | 씨앗층 적용 |
|---|---|---|
| §1.1 권위 3구분 | authored/derived/advisory | 씨앗층은 `advisory_` 로 진입, SEED-D 후 승격 제안 |
| §1.4 자동 병합 금지 | 다수결·평균·union·우선덮어쓰기 금지 | 판단부 비중이 커 P0 보다 더 강하게 적용 |
| §1.5 Python 의미생성 금지 | 결정론 계산만 | prediction·contamination 두 레코드는 100% 무LLM |
| §5.4 threshold 사전등록 | 결과 보고 변경 금지 | 양립도 임계 1/10/30, SEED-D 폐기선 모두 사전등록 |
| §7.2 차이 유형 분류 | VALID_INTERPRETIVE_DIVERGENCE | 씨앗층 **기본값**으로 승격 (§7.3) |
| §8 Gate C 경고 | "합의율 높다 ≠ 품질 높다" | 씨앗층에서 결정적 — §7.3 |
| §9.2 negative fixtures | 20종 열거 방식 | 씨앗층 전용 12종으로 재작성 (§8) |
| §6 provider 독립 | 상호 미열람 후 봉인 | SEED-C6 로 승계 |

### 7.2 수정 — GPT 안을 씨앗층에 그대로 적용할 수 없는 4곳

**(1) evidence 정책이 성립하지 않는다.**
GPT §5.2: "`evidence_ref` 는 SourceLock scene ref 또는 hash". 씨앗의 판단부는 **가리킬 씬이 없다.** 이 정책을 그대로 적용하면 저자는 형식을 맞추기 위해 임의의 씬을 가리키게 되고, 그 순간 근거는 장식이 된다. → **EVIDENCED/JUDGED 이분과 필드별 증거 요건 분리**로 대체(§3). SEED-B6(판단부에 evidence 붙이면 ERROR)이 이 대체의 강제 장치다.

**(2) quarter 2-pass 포착 규율이 무의미하다.**
GPT §3.2 의 `SceneCard 저작 → 짧은 재확인 → CastPresence 포착` 2-pass 는 grain 이 씬일 때 성립한다. 씨앗은 grain 이 **작품**이라 회차 내부 포착 시점이라는 개념 자체가 없다. → 그 자리를 **`read_span` 격리**(§4)가 대신한다. 시점 규율이 범위 규율로 치환된다.

**(3) 독립성 원칙이 부족하다 — 확장 제안.**
GPT §1.2 는 "원문 직접독해 필수 / 상대 모델 산출물 대리독해 금지"만 규정한다. 씨앗층에서는 이것으로 부족하다. **자기 트랙의 하위층을 읽는 것도 순환이다.** 자기가 쓴 CharArc 종단 상태를 보고 `judged_ending_direction` 을 쓰면 상대 모델을 안 봤어도 정답을 베낀 것이다.
→ 원칙 확장: **intra-track downstream reading ban.** SEED-C4 로 성문화. GPT 안에 이 조항이 없는 것은 P0 에서는 하위층이 없어서지 원칙의 한계는 아니다 — Phase 01 재발행 시 반영을 권고한다.

**(4) 앵커 선정이 씨앗층에서는 낙관 편향을 낳는다.**
GPT §10.1 은 비밀의숲을 1차 앵커로 삼는다(다인물·복잡 focality). P0 에서는 타당하다. 그러나 씨앗층에서 비밀의숲은 **EP01 에 세계 제약과 결핍이 이례적으로 선명하게 드러나는 작품**이다(감정 결여라는 결핍이 프롤로그에 명시됨). 이 작품으로 mode B 재구성이 쉽다는 결론을 얻으면 90작 확대에서 무너진다.
→ 씨앗층 파일럿은 **난이도 분산 표본**이 필요(§8.1).

### 7.3 ★ GPT 안의 한 조항이 씨앗층에서 P0 보다 중요해진다

GPT §7.4: `VALID_INTERPRETIVE_DIVERGENCE 는 반드시 한쪽을 삭제하지 않는다.`

P0 에서 이것은 예외 처리다. 씨앗층에서는 **기본값**이다. 같은 작품에서 두 저자가 서로 다른 중심 결핍을 읽는 것은 오류가 아니라 **씨앗이 다대일이라는 증거**다. 두 씨앗이 모두 §2.1 양립도 검사를 통과하면 둘 다 보존한다.

따라서 씨앗층 κ 임계를 P0(κ≥0.6)와 같이 두면 안 된다. **씨앗층은 낮은 κ 를 계약 결함으로 판정하지 않는다.** 사전등록 임계: κ≥0.3 이면 계약 안정으로 간주하고, 대신 SEED-D 예측력이 실질 판정을 맡는다. 일치율이 아니라 **예측력**이 이 층의 품질 척도다.

이는 GPT §8 의 자기 경고 — "두 모델의 합의율이 높다 ≠ 분석 품질이 높다" — 를 씨앗층에서 끝까지 밀고 간 결과다. 씨앗층에서는 오히려 **합의율이 지나치게 높으면 순환을 의심해야 한다.** 두 모델이 같은 완성작을 읽고 같은 요약을 썼다는 뜻일 수 있기 때문이다.

### 7.4 GPT 안의 누락 — 폐기 기준

GPT §10.5 는 파일럿 중단 조건 7개를 열거하지만 전부 **비용·오류·실행 가능성** 기준이다. **"층 자체가 무가치할 때"가 없다.** P0 에서는 CastPresence 가 무가치할 가능성이 사실상 없으므로 문제되지 않는다. 씨앗층은 순환성 때문에 무가치할 가능성이 실재한다. → SEED-D 의 사전등록 폐기선(§5)이 이 공백을 메운다.

---

## 8. 파일럿

### 8.1 표본 10작 — 난이도 분산

| 구분 | 작품 | 선정 이유 |
|---|---|---|
| 골드·용이 | 비밀의숲 | 세계제약 EP01 명시. 상한 측정 |
| 골드 | 커피프린스 | causal 신호 금본위. 로맨스 대비 |
| 골드 | 배가본드 | 장르 이식성 |
| 다중심 | 하얀거탑 | 단일 주인공 부재. center_count 검정 |
| 다중심 | 공주의남자 | 24부 사극. 장편 |
| 장르 | 힐러 | 정체 은폐 = 세계제약 명시형 |
| 장르 | 구르미그린달빛 | 사극 로맨스 |
| 난이도·어려움 | 강남엄마따라잡기 | 사회물. 결핍 불선명 |
| 난이도·어려움 | 굿캐스팅 | 원문 공백 다수 — 최악 조건 |
| 대조 | 결혼못하는남자 | 시트콤형. 결말 방향 약함 |

**용이 3 / 중간 4 / 어려움 3.** 쉬운 표본만 쓰면 SEED-D 가 통과하고 90작에서 무너진다.

### 8.2 순서

```text
1. 스키마 레지스트리 + 게이트 도구 동결 (임계 사전등록)
2. mode B 10작 저작 (EP01~02 열람만, 하위층 차단)
3. SEED-A/B/C 실행 → ERRORS 0 → 봉인
4. 양립도 C(S) 계산 (90작 대조)
5. mode C 10작 저작 (별도 run 권장)
6. derived_seed_prediction · derived_seed_contamination 결정론 계산
7. SEED-D 판정 → PROMOTE / REVISE / REJECT
8. PROMOTE 시에만 사용자 승인 → 90작 확대
```

**7 이전에 90작 확대 금지.** Phase 01 §11 "전면 코퍼스 금지" 승계.

### 8.3 Negative fixtures (12종)

1. `judged_logline` 에 고유명사 포함
2. `judged_ending_direction` 에 구체 사건 기술 ("형이 죽는다")
3. JUDGED 필드에 `evidence_ref` 부착 (B6)
4. EVIDENCED 필드에 `evidence_ref` 누락 (B1)
5. `evidence_ref` 가 `read_span` 밖 회차 인용 (B4)
6. `evidence_ref` 원문 행 불일치 (B3)
7. `derivation_mode=EP01_02_BLIND` 인데 `read_span` 이 EP01~16 (A6)
8. `alternative_structures` 2개 이하 (C2)
9. `compatibility_count` = 1 인데 `verdict=ADMISSIBLE` (C3)
10. mode B 레코드 없이 mode C 레코드 존재 (C5)
11. `character_key` 가 EntityBridge 에 없음 (A5)
12. 전 작품 `judged_logline` 동일 (고정 골격 — Phase 01 §9.4 승계)

---

## 9. 자가 논리점검 (self-audit)

**약점 1 — 순환 없는 근거원이 현재 0/90.**
§4.1 실측. `PLAN_DOCUMENT` 는 정의만 존재하고 사용할 수 없다. 이 층은 출발부터 차선(mode B)에서 시작한다. → 숨기지 않고 설계 전제로 명시. 완화: 신규 편입 시 기획안 동반 확보를 권고 조건에 추가.

**약점 2 — mode B 도 완전 무오염이 아니다.**
EP01~02 는 **작가가 이미 결말을 알고 쓴 텍스트**다. 도입부에는 회수될 설치가 이미 심겨 있다. 따라서 mode B 가 제거하는 것은 **분석자의 순환**이지 **저자의 순환**이 아니다. 후자는 원리적으로 제거 불가능하다. → 제거 대신 **측정**한다(SeedContaminationRecord). 이 층은 오염을 없앤다고 주장하지 않는다. 줄이고 계량한다고 주장한다.

**약점 3 — N=90 은 다중검정을 견디지 못한다.**
지표를 늘리면 우연 유의가 나온다. → 사전등록 지표를 **5종으로 상한**, Bonferroni α=0.01, 지표 추가는 v2 재발행으로만.

**약점 4 — 양립도 C(S) 판정 자체가 판단이다.**
"S 가 w 의 씨앗이었어도 모순 없음"의 판정에 LLM 이 개입한다. 완전 결정론이 아니다. → 판정 로그를 `compatible_work_ids` 에 남기고, 파일럿에서 두 provider 의 C(S) 교집합/합집합 비율을 측정한다. 비율이 낮으면 조작적 정의가 실패한 것이고, 임계를 고치는 것이 아니라 **정의를 재설계**한다.

**약점 5 — 씨앗은 집필 중 변한다.**
실제 작가의 씨앗은 집필 과정에서 변형된다. 어떤 재구성도 "사후에 정돈된 출발점"을 복원할 뿐 실제 출발점을 복원하지 못한다. → 이 층은 "작가의 실제 씨앗"을 주장하지 않는다. **"이 구조를 산출할 수 있는 최소 사전조건"을 주장한다.** 생성 시스템에 필요한 것도 후자다. 문서 전체에서 용어를 이 의미로 고정한다.

### 개선 최종안

위 5개 약점을 반영해 초안에서 다음을 변경했다.

1. `PLAN_DOCUMENT` 를 파일럿 필수에서 **정의만 유지·미사용**으로 강등 (약점 1)
2. `SeedContaminationRecord` 를 **신설** — 오염 제거 주장을 오염 측정으로 대체 (약점 2)
3. 예측 지표를 무제한에서 **5종 상한 + Bonferroni** 로 축소 (약점 3)
4. 다대일 판별을 문장 정의에서 **코퍼스 양립도 |C(S)| 조작적 정의**로 교체 (약점 4의 부분 대응 + §2.1 의 근거)
5. 층의 주장을 "작가의 씨앗 복원"에서 **"구조 산출의 최소 사전조건"**으로 재정의 (약점 5)

---

## 10. 상태 · 금지

```text
CLAUDE_DESIGN_DRAFT
NO_AUTHORING_BEFORE_USER_APPROVAL
NO_CORPUS_ROLLOUT_BEFORE_SEED-D
NO_CANONICAL_PROMOTION
STAGE01_04_SSOT_UNCHANGED
```

Stage01~04 정본은 한 바이트도 변경하지 않는다. 본 문서는 사이드카 신설 제안이며, 승인 전 어떤 파일도 저작하지 않는다.

---

_by: Claude (Opus) · 근거: 로컬 정본 seqcard_ko 90작/1,676회/104,578씬(2026-07-31 기준) · 대조: GPT-EXT6-PHASE01-INDEPENDENT-v1, SEQCARD-EXT6-PHASE1-FROZEN-CONTRACT-v1_
