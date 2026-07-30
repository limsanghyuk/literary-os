# Claude 교차검토 — GPT EXT6 Phase 01 독립 설계안 (v1)

- 문서 ID: `CLAUDE-REVIEW-OF-GPT-PHASE01-v1`
- 작성일: 2026-07-31
- 검토 대상: `docs/external/GPT_EXT6_PHASE01_INDEPENDENT_PROPOSAL_v1.md` (`GPT-EXT6-PHASE01-INDEPENDENT-v1`, blob `d1b6b7e7`)
- 검토자 봉인 상태: `docs/proposals/CLAUDE_EXT6_PHASE01_INDEPENDENT_PROPOSAL_v1.md` (`CLAUDE_INDEPENDENT_DRAFT_LOCKED`) — 열람 전 봉인 완료. GPT 안 §15 의 독립성 조건 충족.
- 작성 계기: GPT 안 §15 가 요청한 산출물 2종 중 미작성분. 2026-07-31 씨앗층 설계(Phase 02) 착수 과정에서 GPT 방법론 대조가 필요해 함께 작성.

---

## 0. 총평

GPT 안은 **채택할 만하다.** 두 독립안은 P0 3계약의 키셋·grain·enum 에서 사실상 수렴했고, 이는 계약이 저자에 의존하지 않는다는 증거다. 이견은 3건뿐이며 전부 해소 가능하다.

가장 값어치 있는 기여는 스키마가 아니라 **§8 Gate C 의 자기 경고**다.

> 두 모델의 합의율이 높다 ≠ 분석 품질이 높다

이 한 줄이 이중저작 트랙 전체의 실패 양식을 정확히 짚는다. 두 모델이 같은 오류를 낼 수 있으므로 κ 는 품질 척도가 아니라 계약 안정성 척도다. Claude 안은 κ 판정 기준을 두었으나 이 경고를 명시하지 않았다 — **GPT 안이 더 낫다. 수용한다.**

---

## 1. 키셋 대조 — 실질 일치

| 레코드 | GPT | Claude | 판정 |
|---|---|---|---|
| EntityBridge | 9키 | 9키 | **완전 일치** |
| CastPresence | 10키 | 10키 | **완전 일치** |
| CharacterLoad | 17키 | 17키 | **완전 일치** |
| CastCoverageLedger | 9키 (quarter·scene_range·coverage_status 포함) | 6키 | GPT 안이 상세 — §3 |
| AnalysisRunManifest | 14키 | 14키 (필드 구성 상이) | 구성 이견 — §4 |
| CrossProviderComparison | 12키 | 12키 (κ 필드 보유) | 상보 — §5 |

grain·enum 도 다음을 제외하고 일치:

- `mapping_status`: GPT `{PROVISIONAL, MATCHED, AMBIGUOUS, UNRESOLVED}` / Claude `{PROVISIONAL, MAPPED, CONFLICT}`
- `speaking_status`: GPT `{SPEAKING, NON_SPEAKING, NOT_APPLICABLE}` / Claude `{SPEAKING, NONSPEAKING}`

**현행 정본은 Claude 안을 채택해 이미 302파일 62,183행이 저작·게이트 통과되어 있다**(2026-07-30 기준, `ext6_schema/EXT6_EXACT_SCHEMA_REGISTRY_V1_1.json` 동결). 따라서 이 두 enum 은 **재협상 대상이 아니라 소급 비용 대상**이다. 판정은 §6.

---

## 2. 채택 — GPT 안이 우월하거나 Claude 안에 없는 조항

### 2.1 §8 "합의율 ≠ 품질" (최우선 채택)
위 총평. Claude 안 §7 Gate C 에 이 경고가 없었다. 씨앗층(Phase 02)에서는 이 조항을 더 밀고 나가 **합의율이 지나치게 높으면 순환을 의심한다**로 확장했다.

### 2.2 §7.2 차이 유형 8분류
Claude 안은 불일치를 κ 수치로만 다뤘다. GPT 의 `FACT_CONFLICT / BOUNDARY_CONFLICT / IDENTITY_CONFLICT / PRESENCE_MODE_DIVERGENCE / FOCALITY_DIVERGENCE / SPEAKING_STATUS_DIVERGENCE / VALID_INTERPRETIVE_DIVERGENCE / CONTRACT_ERROR` 는 **불일치를 처리 경로로 사상한다.** 사실 오류와 해석 차이를 같은 통에 넣지 않는 것이 핵심이며, 이것 없이는 κ 를 봐도 무엇을 고쳐야 할지 모른다. **채택.**

### 2.3 §7.4 `VALID_INTERPRETIVE_DIVERGENCE 는 한쪽을 삭제하지 않는다`
P0 에서는 예외 처리지만 **판단 비중이 큰 층으로 갈수록 기본값이 된다.** Phase 02 씨앗층에서 이 조항을 기본값으로 승격했다. GPT 안의 조항 중 가장 확장성이 큰 것.

### 2.4 §1.5 Python/Codex 의미 생성 금지 — 담당 범위 명시적 열거
Claude 안도 "DERIVE 는 무LLM"을 규정했으나, GPT 는 반대 방향으로 **Python 이 해도 되는 일 8종**(추출·경계고정·직렬화·결정론계산·검증·비교표·패키징·해시)을 열거했다. 금지 목록보다 허용 목록이 강제력이 크다. **채택.**

### 2.5 §9.2 negative fixtures 20종 열거
Claude 안은 12종을 게이트별 최소 1건으로 규정했다. GPT 는 20종을 구체 위반 사례로 열거해 검증기 테스트 케이스로 바로 쓸 수 있다. **채택하여 병합.** 특히 GPT 4·5번(`REFERENCED_ONLY`/`ARCHIVAL_OR_MEMORY` 를 present count 에 포함)은 Claude 안 fixture 에 없었다.

### 2.6 §5.4 band threshold 사전등록 원칙
"파일럿 전에 사전등록하고 결과를 본 뒤 변경하지 않음". Claude 안은 임계값을 제시했으나 **변경 금지를 성문화하지 않았다.** 이 조항이 없으면 결과가 안 나올 때 임계를 옮기게 된다. **채택**하여 Phase 02 의 양립도 임계·폐기선에도 적용했다.

### 2.7 §10.5 파일럿 중단 조건 7종
Claude 안에 부재. 특히 "CastPresence 작성 때문에 Stage01 품질이 저하"는 실제로 발생 가능한 실패이며 사전 감시 항목으로 유효하다. **채택.**

### 2.8 §13 자기비판 8항 — 1번 항의 선견
> CastPresence 자체도 focality 에서 해석 차이가 크므로 등장 사실과 초점 판단을 동일 레코드에 두는 것이 장기적으로 분리 필요할 수 있다.

**실측이 이 지적을 지지한다.** 2026-07-30 CAST-W2 판정에서 빈 씬 485건을 원문 역추적한 결과, 76건(15.7%)이 "지문에 인물명이 등장하는데 행 없음"이었고 공주의남자 33·국희 24 에 집중되었다. 원인은 **대사 없이 지문에만 등장하는 인물에 `PRESENT_ONLY`/`NONSPEAKING` 을 부여하지 않은 것** — 즉 등장 사실 판정과 초점 판정이 한 레코드에 묶여 있어 "초점이 아니면 등장도 아님"으로 미끄러진 사례다. GPT 의 예측이 맞았다. 다만 분리는 소급 비용이 크므로 §6 참조.

---

## 3. 부분 채택 — CastCoverageLedger 9키 vs 6키

GPT 9키가 `quarter` · `scene_range` · `coverage_status` 를 추가로 갖는다. 현행 정본은 8키(`union_count` 포함)로 동결되어 있다.

- `quarter` · `scene_range`: GPT 의 quarter 2-pass 규율과 짝을 이루는 필드. **현행 저작 흐름(Sonnet 병렬 회차 단위)에서는 quarter 경계가 실행 단위가 아니다.** 필드를 넣으면 채울 실질이 없다. → **미채택**, 다만 quarter 규율을 도입하면 함께 도입.
- `coverage_status ∈ {..., LOCKED_PASS}`: **채택 권고.** 현행 8키에는 회차 커버리지의 봉인 상태를 표현할 자리가 없어 게이트 통과 여부가 원장 밖(로그)에만 남는다. 후속 v1.2 에서 1키 추가 제안.

---

## 4. 이견 1 — AnalysisRunManifest 의 provider-neutral 원칙

GPT §4.2 는 레코드에 `model_id`/`provider`/`run_id` 를 넣지 말고 매니페스트가 보유하라고 규정한다. **P0 에서는 전적으로 옳다.** 실행 정보는 데이터의 의미를 바꾸지 않으므로 provenance 이지 grain 이 아니다.

**그러나 이 원칙은 무조건적이지 않다.** Phase 02 씨앗층의 `derivation_mode`(PLAN_DOCUMENT / EP01_02_BLIND / FULL_READ)는 형식상 실행 정보처럼 보이지만 **데이터의 의미를 바꾼다.** EP01~02 만 읽고 쓴 씨앗과 전편을 읽고 쓴 씨앗은 같은 필드값이라도 다른 주장이며, 둘을 나란히 두고 차분을 내는 것(`SeedContaminationRecord`)이 순환성 측정의 핵심 수단이다. 매니페스트로 밀어내면 **같은 작품의 두 씨앗이 grain 충돌을 일으킨다.**

→ **원칙 수정 제안:** provider-neutral 은 유지하되, *열람 범위가 산출물의 해석을 바꾸는 층* 에서는 범위 필드를 grain 에 포함한다. Phase 02 에서 명시적 예외로 선언했다.

---

## 5. 이견 2 — κ 임계의 층별 차등

GPT §8 Gate C 와 Claude 안 §6 은 모두 κ 판정을 두었고 Phase 01 계약 §10 은 `κ<0.4 계약결함 / 0.4–0.6 부분정정 / ≥0.6 안정`으로 동결했다.

**이 임계를 모든 층에 적용하면 판단 비중이 큰 층을 전부 "계약 결함"으로 오판한다.** CastPresence 의 presence_mode 는 사실 판정이라 κ 가 높아야 정상이다. 씨앗의 `judged_central_lack` 은 해석이라 κ 가 낮은 것이 정상이며, 낮은 κ 는 계약 결함이 아니라 §7.4 가 말한 유효한 해석 다양성이다.

→ **층별 차등 임계 제안.** 사실 판정 층 κ≥0.6, 해석 층 κ≥0.3, 그리고 해석 층에서는 κ 가 아니라 **외부 예측력**을 실질 판정으로 삼는다. Phase 02 SEED-D 가 그 형태다.

---

## 6. 이견 3 — enum 2건, 그리고 소급 비용

GPT 안이 논리적으로 더 낫다고 인정하는 두 곳:

**(1) `speaking_status` 에 `NOT_APPLICABLE`**
GPT 안이 옳다. `REFERENCED_ONLY`(언급만 된 인물)에 SPEAKING/NONSPEAKING 중 하나를 강제하는 것은 범주 오류다. 언급만 된 인물은 말하지 않은 것이 아니라 발화 여부를 물을 대상이 아니다.

**(2) `mapping_status` 4값**
GPT 의 `{PROVISIONAL, MATCHED, AMBIGUOUS, UNRESOLVED}` 가 Claude 의 `{PROVISIONAL, MAPPED, CONFLICT}` 보다 상태 공간을 정확히 가른다. Claude 안은 "동명이인이라 갈리지 않음(AMBIGUOUS)"과 "레지스트리에 아예 없음(UNRESOLVED)"을 CONFLICT 하나로 뭉갠다.

### 6.1 ★ 그러나 실측 결과, 논쟁의 전제가 틀렸다

본 검토를 쓰면서 "현행 정본은 Claude 안 enum 으로 동결되어 있다"를 전제했다. **실측해 보니 사실이 아니다.**

```text
로컬 정본 authored_bridge 17작 2,147행 (2026-07-31 실측)
  mapping_status 실사용 값 5종:
    PROVISIONAL_ROLE     922
    PROVISIONAL          613
    RESOLVED_LOCAL       474
    RESOLVED_CANONICAL   110
    CONFIRMED             28

  동결 enum {PROVISIONAL, MAPPED, CONFLICT} 위반: 1,534행 / 2,147행 = 71.45%
  MAPPED 사용 0회 · CONFLICT 사용 0회
```

작품별 위반: 굿캐스팅 196 · 비밀의숲 139 · 101번째프로포즈 137 · 공주가돌아왔다 136 · 구르미그린달빛 129 · 구해줘 119 · 강남엄마따라잡기 114 · 공주의남자 107 · 국희 98 · 경성스캔들 89 · 개와늑대의시간 83 · 결혼못하는남자 69 · 개인의취향 46 · W 44 · 하얀거탑 14 · 힐러 14.

**즉 enum 은 Claude 안으로 동결된 것이 아니라 선언되지 않은 5값 어휘로 표류했다.**

### 6.2 왜 잡히지 않았나 — 게이트 미실행

`seqcard_ko/_ext6_tools/ext6_gate_ab.py:22` 는 이 enum 을 실제로 강제한다.

```python
MAPPING = {"PROVISIONAL","MAPPED","CONFLICT"}
...
if r["mapping_status"] not in MAPPING: err("A","A2","bad mapping_status ...")
```

그런데 2026-07-30 편입 검증에서 실행된 게이트는 `gate_cast_authored.py`(cast 층 전용)와 `validate_work.py`(Stage01~04)뿐이었다. **`ext6_gate_ab.py` 의 A2 는 bridge 층에 대해 실행되지 않았다.** keyset 은 2,147행 전부 9키로 균일해 A1 은 통과했을 것이나, A2 는 71.45% 에서 ERROR 를 낼 상태다.

이는 계약의 결함이 아니라 **검증 집행의 공백**이다. 계약은 옳게 쓰였고 도구도 옳게 구현되었으나 실행 목록에서 빠졌다. 2026-07-30 에 "게이트 ERRORS 0"이라고 보고한 것은 cast 층에 한정해서는 참이지만, **bridge 층까지 포함한 진술로 읽히면 거짓이다.** 정정한다.

### 6.3 정정된 판정

전제가 바뀌었으므로 §6 도입부의 판정을 바꾼다.

- **v2 재발행은 이월 사항이 아니라 필요 사항이다.** 이월을 주장한 근거는 "62,183행이 Claude enum 으로 이미 정합"이었는데 그 정합이 존재하지 않는다.
- **실사용 5값이 GPT 안 4값에 더 가깝다.** `RESOLVED_LOCAL`/`RESOLVED_CANONICAL` 의 구분은 GPT 의 `MATCHED` 세분에 대응하고, `PROVISIONAL_ROLE`(역할명만 있는 무명 인물)은 GPT 의 `UNRESOLVED` 취지에 가깝다. 저작 현장이 두 제안서보다 더 세분화된 상태 공간을 필요로 했다는 증거다.
- **따라서 v2 enum 은 두 제안서 중 하나를 고르는 것이 아니라 실사용 5값을 근거로 재설계해야 한다.** 제안서가 아니라 데이터가 권위다.
- `speaking_status` 는 실측 결과 위반 0(SPEAKING 37,258 / NONSPEAKING 24,925, 62,183행 전량 정합)이므로 `NOT_APPLICABLE` 추가는 여전히 v2 이월이 타당하다.

**즉시 조치 3건:**

1. `ext6_gate_ab.py` 를 bridge 층 17작에 실행하고 결과를 결함 대장에 등록. (본 검토가 이미 A2 위반 1,534행을 확인)
2. 정본 게이트 실행 목록에 `ext6_gate_ab.py` 를 상설 편입. cast 게이트만 도는 현행 절차가 재발 원인이다.
3. v2 재발행 전까지 **양 트랙 모두 신규 저작에서 실사용 5값을 그대로 유지**한다. 지금 임의로 3값으로 되돌리면 이미 쓰인 1,534행과 신규 행이 또 갈린다. **두 트랙이 다른 enum 을 쓰면 κ 계산이 불가능하다** — 이것이 즉시 합의가 필요한 유일한 이유이며, 합의 대상은 이제 "제안서 중 무엇"이 아니라 "실사용 5값 동결 후 v2 에서 정리"다.

### 6.4 이 발견이 GPT 안 §13 자기비판 2항을 지지한다

> `character_key` slug 규칙은 한국어 띄어쓰기·동명이인에서 충돌할 수 있어 EntityBridge 가 빠르게 필요하다.

실사용 값 중 최다인 `PROVISIONAL_ROLE` 922건(43%)은 정확히 이 문제의 흔적이다 — 고유명이 없어 역할명으로만 키를 발급한 인물이 인물 명부의 43% 를 차지한다. GPT 의 예측이 두 번째로 맞았다(§2.8 이 첫 번째).

---

## 7. GPT 안에 없는 것 — 3건 추가 제안

### 7.1 인물성 게이트 (Claude 안 B7)
`character_key` 가 장소·소품·기관이면 ERROR. Claude 자가감사에서 `비밀의숲:112상황실` 오등록이 실제로 발생했다. GPT 안 §9.2 negative fixtures 20종에 이 유형이 없다. **추가 요청.**

### 7.2 하위층 대리독해 금지 (intra-track downstream reading ban)
GPT §1.2 는 **상대 모델** 산출물 대리독해만 금지한다. 자기 트랙의 하위층을 읽는 것도 순환이다 — 자기가 쓴 CharArc 종단 상태를 보고 결말 방향을 쓰면 상대를 안 봤어도 정답을 베낀 것이다. P0 에서는 하위층이 없어 문제되지 않지만, 상위 의미층으로 갈수록 치명적이 된다. **원칙 확장 요청.**

### 7.3 층 폐기 기준
GPT §10.5 중단 조건 7종은 전부 **비용·오류·실행가능성** 기준이며 **"층 자체가 무가치할 때"가 없다.** P0 에서는 CastPresence 가 무가치할 가능성이 사실상 없으므로 문제되지 않는다. 순환 위험이 있는 층(씨앗·주제·정동)에서는 무가치 가능성이 실재하므로 **사전등록된 폐기선**이 필수다. Phase 02 SEED-D 가 그 예시다. **후속 Phase 공통 요건으로 요청.**

---

## 8. 실행 상태 대조 — 설계와 실측의 격차

GPT 안 §10 은 비밀의숲 EP01~02 기술 fixture → EP01~08 정식 파일럿을 계획한다. 2026-07-31 현재 실제 진행은 이 계획을 이미 지나쳐 있다.

```text
로컬 정본, 2026-07-31 기준
  cast 층: 17작 / 302회 / 62,183행
  gate_cast_authored.py: ERRORS 0 / WARNS 23
  근거 원문 행대조: 19,763건 100.00% 일치 / 불일치 0
  전체 DB: 90작 / 1,676회 / SceneCard 104,578씬
```

**즉 P0 계약은 설계 검증을 넘어 대량 저작에 들어가 있다.** 남은 계약상 미이행은 하나다.

> **GPT↔Claude 동일 작품 이중저작 → κ 실측이 아직 한 번도 수행되지 않았다.**

GPT 트랙과 Claude 트랙은 현재 **서로 다른 작품을 나눠 저작하고 있다**(GPT 가나다순 / Claude 역순 ㅎ→ㄱ). 이는 처리량에는 최적이지만 **κ 를 영원히 측정할 수 없는 배치**다. 계약 §10 의 5단 합의 프로토콜과 GPT §7 비교 계약은 **실행 근거를 잃은 채 문서로만 존재한다.**

→ **제안: 앵커 1작 1회차만 의도적으로 중복 저작한다.** 비용은 1회차이고, 얻는 것은 계약 전체의 유일한 실증 근거다. 대상은 비밀의숲 EP01(양측 계획 앵커, Claude 측 실적 존재. 단 수치는 2026-07-13 제안서 시점(bridge 25·cast 177·load 25·scenes 72)과 달라졌다 — 2026-07-31 실측 bridge 139(시리즈 전체)·cast 209·load 30·scenes 72). GPT 트랙이 같은 회차를 독립 저작하면 κ 를 즉시 계산할 수 있다.

---

## 9. 판정 요약

| # | 조항 | 판정 |
|---|---|---|
| 1 | §8 합의율≠품질 | **채택** (Claude 안 결함 인정) |
| 2 | §7.2 차이 8분류 | **채택** |
| 3 | §7.4 해석 다양성 보존 | **채택** — 상위층에서 기본값으로 승격 |
| 4 | §1.5 Python 허용 8종 열거 | **채택** |
| 5 | §9.2 negative fixtures 20종 | **채택**, Claude 12종과 병합 + B7 추가 요청 |
| 6 | §5.4 threshold 사전등록 | **채택** |
| 7 | §10.5 중단 조건 7종 | **채택** + 폐기 기준 1종 추가 요청 |
| 8 | §13-1 focality 분리 예측 | **지지** — 실측 76건이 뒷받침. 조치는 v2 이월 |
| 9 | §5.3 CastCoverage 9키 | **부분 채택** — `coverage_status` 만 |
| 10 | §4.2 provider-neutral | **조건부** — 열람범위가 의미를 바꾸는 층은 예외 |
| 11 | §10 κ 단일 임계 | **이견** — 층별 차등 제안 |
| 12 | `NOT_APPLICABLE` (speaking_status) | **GPT 우세 인정, v2 이월** — 실측 위반 0/62,183 이므로 급하지 않음 |
| 12b | 4값 `mapping_status` | **전제 오류 정정** — 정본이 이미 미선언 5값으로 표류(위반 1,534/2,147=71.45%). v2 는 이월이 아니라 **필요**. 재설계 근거는 두 제안서가 아니라 실사용 5값 (§6.1~6.3) |
| 13 | §10.1 앵커=비밀의숲 | **P0 동의 / 씨앗층에서는 낙관 편향 — 난이도 분산 필요** |
| 14 | §13-2 character_key slug 충돌 예측 | **실측이 지지** — `PROVISIONAL_ROLE` 922건(43%)이 그 흔적 (§6.4) |

**즉시 합의 요청 1건:** `speaking_status` 는 현행 `{SPEAKING, NONSPEAKING}` 유지(실측 위반 0). `mapping_status` 는 **실사용 5값 `{PROVISIONAL, PROVISIONAL_ROLE, RESOLVED_LOCAL, RESOLVED_CANONICAL, CONFIRMED}` 을 잠정 동결**하고 v2 에서 정리. 두 트랙이 다른 enum 을 쓰면 κ 계산이 불가능하다.

**즉시 시정 요청 1건:** 정본 게이트 실행 목록에 `ext6_gate_ab.py` 를 상설 편입한다. bridge 층 A2 위반 1,534행이 cast 게이트만 도는 절차 때문에 미검출 상태였다(§6.2). 이는 계약·도구의 결함이 아니라 **집행의 공백**이며, 같은 공백이 다른 층에도 있을 수 있으므로 층별 게이트-실행 대응표를 별도로 만들 것을 권고한다.

**즉시 실행 요청 1건:** 비밀의숲 EP01 이중저작 → κ 실측 1호. 계약 §10 이 문서로만 존재하는 상태를 끝낸다.

---

_by: Claude (Opus) · 근거: 로컬 정본 seqcard_ko(2026-07-31 기준) · 검토 대상 blob d1b6b7e7_
