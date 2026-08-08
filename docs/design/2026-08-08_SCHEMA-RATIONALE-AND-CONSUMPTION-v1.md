# 스키마 설계 근거 조사 · 연결 소비 방향
`LOS-SCHEMA-RATIONALE-V1.0` · 2026-08-08 · 조사 4개 병렬 에이전트 실측

전제: 이 문서는 폐기 권고가 아니다. 개발자 지시 "각각의 스키마를 왜 설계했는지
조사하고 검토하고 연결하여 소비하는 방향을 모색하라"에 대한 응답이다.

---

## §1. 조사 결과 — 층은 세 갈래 다른 동기에서 태어났다

층을 한 덩어리로 보면 답이 안 나온다. 문서 원문을 복원하니 출신이 셋으로 갈린다.

### (가) 생성 사슬을 잇기 위해 만든 층 — 소비자 **선언 있음**

| 층 | 선언된 소비자 | 근거 |
|---|---|---|
| Stage01 SceneBlueprint (`authored/` 1,814) | LLM-2 거시 플래너의 학습 기질(substrate) | `2026-07-01_SEQCARD-VALUE-REPORT.md:12` |
| Stage02 SequenceBlueprint (`authored_seq/` 1,814) | 렌더러 주입 — 상위 의도를 씬 예산으로 번역 | `2026-07-04_DESIGN-4LAYER-REVERSE-FILL-v1.md:29,30` |
| EXT6 CharacterLoad (`derived_character_load/` 712) | SequenceBlueprint 인물배분 예산의 실측 근거 | `..._v2_무결성복구.md:109` |

Stage02 는 특히 분명하다. 원문이 "SequenceBlueprint는 이번에 신설되는 층이며,
상위 의도를 씬 예산으로 번역하는 유일한 층 = top-down의 실제 병목"이라 적었다.
분석 욕구가 아니라 끊긴 마디를 이으려고 만든 층이다.

Stage01 의 프로덕션 미연결은 **사고가 아니라 명시적 유보**다 — 같은 보고서 :105 가
"인간 블라인드 κ≥0.6 통과 전엔 분석/PoC 위상 유지, prior 주입 금지"라 못박았다.

### (나) 가짜 산출물을 잡기 위해 만든 층 — 소비자 **미선언**

`_AUTHORING_BRIEF_3LAYER.md:152` 가 출신을 자백한다. GPT가 원문 미독해로 통계만 맞춘
산출물을 낸 사건의 분류 결과가 곧 층 목록이 됐다. CausalSpine/Plant-Payoff/HookChain은
채택되어 LocalEdge·PayoffCandidate가 되고, CharacterArc/RelationshipArc는 신규 채택됐다.

해당 층: `authored_edges/` (local_edges 1,814 · payoff_candidates 1,814),
`authored_chararc/` 1,814, `authored_relarc/` 1,814, cross_episode_edges 98,
candidate_disposition_ledger 98.

이들의 하류로 문서가 지목한 유일한 대상은 `functional_holdout` 게이트인데
(`_VALIDATION_ADOPTION_v1.md:15`), 그 하네스는 **미구현**이다.
즉 이 층들은 "생성에 무엇을 공급할지"가 아니라 "가짜를 어떻게 잡을지"에서 태어났고,
그 유일한 하류마저 없다.

### (다) 하류를 **일부러 차단**하려고 만든 층 — DesignSeed

`EXT6_V1_2_PHASE02_DESIGNSEED_SINGLE_AUTHORITY_V1_0.md` 의 골자는 소비가 아니라 차단이다.
`downstream_layers_blocked` · `downstream_blocklist` · `cross_provider_outputs_blocked`
(:165-166), 그리고 :291 "no retroactive claim that a completed-work summary was a
pre-writing plan".

완성작을 다 읽고 쓴 씨앗은 기획이 아니라 결말의 요약이다. 그걸로 생성기를 학습시키면
"씨앗→구조" 예측이 맞는 게 당연해지고 유용성 증거가 위조된다. DesignSeed 는 그 위조를
막는 장치이며, `leakage_estimate = mode_c 정확도 − mode_b 정확도` 로 위조량을 재고
중앙값 >0.30 이면 FULL_READ 를 학습에서 영구 배제한다(:230).
실측 28작 중앙값 0.20 — 배제는 발동 안 했으나 눈금이 0.2 단위라 해상도가 1지표뿐이다.

**따라서 DesignSeed 가 소비되지 않는 것은 결함이 아니라 설계대로다.**

### (라) 저작된 적이 없는 층

EXT6 원설계 6종 중 CharacterVoice · ThematicSpine · MotifLedger · EmotionalBeat ·
Tone/Pacing 다섯은 **정본 트리에 디렉터리조차 없다**. 실존하는 EXT6 산출은 ⑥ CharacterLoad
계열뿐이다. Phase02 는 계획(Voice 파일럿)을 건너뛰고 DesignSeed로 갈아끼워졌다.

---

## §2. ★진짜 원인 — 배선이 끊긴 게 아니라 계약이 협상된 적이 없다

이게 이번 조사에서 나온 가장 아픈 사실이다.

허브 `docs/design/` 전체에서 SeqCard·cast·CharArc·RelArc·thick·DesignSeed·EXT6 를
**언급이라도 하는 파일이 6개**뿐이고, 그중 5개가 단일 클러스터
(`2026-07-03_sceneblueprint_vertical_slice/`)다. LLM-2 본선 설계도 전부 —
SYNOPSIS-ASSEMBLER · ORCHESTRATOR · WIRING-ORCHESTRATOR · CAPACITY-DIVISION ·
BLANK-SLOTS · PLANNER-CURRICULUM · PLC-A1 · BLUEPRINT-MASTER · LLM-LADDER · PHASE-F ·
P0-PAIRING — **0건**이다.

설계도들이 선언한 입력 원천은 셋뿐이다: 사람이 준 시드, 결정론 엔진 산출,
NarrativeStateTensor 스칼라 버스. 파이프라인 최초 입력은
`SeedCompiler.compile(seed_text)` — **자연어 한 줄**이다
(`DESIGN-LLM2-WIRING-ORCHESTRATOR-v1.md:96`).
코퍼스는 κ 캘리브레이션 앵커 · RAG · 지도라벨 · ablation 하네스로만 등장한다.
**계측·학습 자산으로 선언됐지 런타임 입력으로 선언된 적이 없다.**

부수 확인:
- `PlannerInputRecord` · `RuntimeSceneProjection` — 전 트리 grep **0건. 존재하지 않는다.**
- 이름 충돌: 구현 `SceneBlueprint`(6필드) ≠ 설계 `SceneBlueprint`(23필드). 동명이물이라
  배선하려 해도 계약이 충돌한다.
- 씬 층 23필드 대응 판정은 이미 존재한다 — ✅9 / 🔶6 / ❌8
  (`DESIGN-SCENEBLUEPRINT-SCHEMA-v1.md:44-70`). 미대응 8종에 dramatic_conflict,
  plant/payoff_operations, information_reveal, subtext_target 이 포함된다.
  즉 **CT-07R 에서 우위가 확인된 info·link 에 대응하는 수용 슬롯이 코드에 0개**다.
- `SequencePlan.goal` 은 있으나 `_pick_goal()` 이 고정 풀을 `idx % len` 으로 순환한다
  (`orchestrators/sequence_planner.py:454-456`) — 형식만 goal 이고 내용이 없다.

결론: 이건 배선 누락이 아니다. **나는 층을 생산자 관점에서만 설계했고 소비 계약을 한 번도
상대와 협상하지 않았다.** 2달의 저작이 소비되지 않은 원인의 이름은 이것이다.

---

## §3. 직전 답변의 정정 — 검색은 필드를 골라 쓴다

내가 어제 "검색은 시퀀스 덩어리를 통째로 쓰지 필드를 골라 쓰지 않는다"고 말했다.
실측으로 검증했고 **절반 틀렸다.**

필터 필드로 성립하는 것 (전부 실측, 2026-08-08):

| 필드 | 채움률 | distinct | 비고 |
|---|---|---|---|
| `core` (씬 114,371) | 100% | 16 | CONFLICT 17,064 … INTRO 1,235, 균형 분포 |
| `turn_class` (시퀀스 16,233) | 100% | 16 | 상위 4종이 99.3% |
| `scene_budget` | 100% | 24 | 7:3,115 · 6:2,954 · 8:2,374 |
| `presence_mode` (cast 133,299) | 100% | 5 | ONSCREEN 116,441 … |
| `focality` | 100% | 3 | PRIMARY/SECONDARY/PRESENT_ONLY |
| `speaking_status` | 100% | 2 | |
| plant 유무 | 48.19% | 2 | |

4필드 합성 필터 후 잔존 후보:

| 조건 | 잔존 / 16,233 | 작품 |
|---|---|---|
| REVEAL & CONFLICT & plant≥1 & budget 5–8 | 807 (4.97%) | 95 |
| FALL & LOSS & plant≥1 & budget≥8 | 451 (2.78%) | 75 |
| RISE & PERIL & plant≥1 & seq_index≤3 | 239 (1.47%) | 65 |
| STALL & BOND & plant=0 & budget≤4 | 70 (0.43%) | 35 |

4원 교차표 비어있지 않은 셀 69개, 중앙값 142건. **조건부 검색은 데이터상 성립한다.**

내 주장이 맞았던 부분: 자유서술 필드는 필터가 못 된다.
`sequence_intent` 16,232/16,233 · `goal` 15,921 · `obstacle` 15,874 · `value_shift` 15,673 ·
`state_label` 10,402/11,654 · `relation_state` 9,086/9,880 — distinct/행 비율이 90~100%다.
**chararc·relarc 층 전체가 필터 조건으로는 무가치하다** (임베딩 대상은 될 수 있다).
`turn_type` 은 distinct 308 중 상위 16 enum 이 96.6%, 꼬리 292값이 자유서술 오염이다.

### 내 오독 정정
내가 "pov_char 15,796행 전부 단일값"이라고 옮겨 적었는데, **원 관찰(2026-08-05)을 내가 잘못
읽은 것**이다. 원문의 "전부 단일 문자열"은 *한 행이 배열이 아니라 문자열 하나*라는 뜻이고
그건 맞다. 실측: 전역 distinct 4,103, 회차별 단일값은 82회차(4.5%)뿐, 최대 21값.
즉 pov_char 는 값이 다양하다 — 다만 고카디널리티라 단독 필터로는 부적합하다.

---

## §4. ★진짜 병목은 카디널리티가 아니라 커버리지 3종

| 결손 | 실측 |
|---|---|
| chroma 가 다른 코퍼스를 본다 | `ko_scenes` 2,040 + `ko_slides` 1,478. 임베딩된 작품 14종은 영화 위주이고 **정본 98작과 교집합 1작(신사의품격)**. 97작은 임베딩 0개 |
| 메타데이터 키 0종 | `embedding_metadata` 사용자 키 **0**. 빌더 `rebuild_chroma_local.py:57` 이 `metadatas=` 인자 없이 호출. 넣는 코드(`store_chroma.py:25-31`)는 있으나 미실행이고 그마저 `work_id` 1개 |
| 필터 호출 코드 0건 | 코퍼스 전체에 `.query(...where=...)` **0건**. 지금은 "눈먼 최근접이웃"조차 아니고 소비자 자체가 없다 |
| cast 층 범위 | 35/98작(35.7%). 시퀀스 16,233 중 인물수를 붙일 수 있는 것 6,352개(39.13%) |

그래서 "인물 3명 & REVEAL & plant≥1" 은 잔존 45건(19작)으로 무너진다.
붕괴 원인은 필드 설계가 아니라 **cast 가 35작뿐**이라서다.

---

## §5. 전략 3안 비교

### 안 A — 스키마 직접 주입 (schema-conditioned)
후판 5필드를 플래너 출력 스펙으로 확정하고 렌더러에 주입. CT-07R/CT-08A 노선.

장점: 층이 곧 산출물이라 해석이 명확. 단점: 5필드 외 층은 여전히 미사용.
리스크: 이미 두 번 시험했고 CT-07R 은 계측기 미검증(D-54), CT-08A 는 무효(D-53).
비용: 98작 저작 — 되돌릴 수 없다. **가장 비합리적.**

### 안 B — 검색 전면 (retrieval-only)
정본 위에 임베딩을 다시 세우고 유사 시퀀스를 통째로 예시로 준다.

장점: 배선 1개로 층 전량이 즉시 소비. 단점: 예시 통째 주입은 원문 유출 경계에 걸리고
(허브 원문 노출 미해결 건과 같은 문제), "왜 좋은지"는 학습되지 않는다.
리스크: chroma 커버리지 1/98. 비용: 재색인 중간.

### 안 C — 소비 계약 우선 + 조건부 검색 (선택)
1. `PlannerInputRecord` 를 **실제로 정의**한다 (지금 없다). 층을 바꾸지 않고 어댑터 한 겹으로 투영.
2. 정본 98작 위에 `ko_sequences` 컬렉션을 세우고 `core / turn_class / plant / scene_budget`
   4종을 메타데이터로 색인.
3. cast 35→98작 확장 (인물수 필터를 살리는 유일한 길).
4. 그 다음에야 예시조건부 vs 스키마조건부 대결 실험.

장점: 기존 층을 하나도 버리지 않고 각각에 역할이 생긴다 —
스키마 필드는 **후보를 좁히고**, 임베딩은 **그 안에서 고르고**, 후판 5필드는 **선택된 예시를
변형하는 지시**가 된다. 세 층위가 배타가 아니다.
단점: 3단계 커버리지 확장 비용이 실질적. 리스크: 계약을 확정해도 효용은 여전히 미측정.
비용: 안 A 의 98작 저작보다 훨씬 싸고 되돌릴 수 있다.

**선택 = 안 C.** 이유: 안 A 는 계측기가 서 있지 않은 상태에서 되돌릴 수 없는 비용을 치른다.
안 B 는 배선은 빠르나 층 대부분을 여전히 안 쓴다. 안 C 만이 (가)(나)(라) 층 전부에 정의된
자리를 준다 — (가)는 생성 입력, (나)는 필터·재랭킹 조건, (다) DesignSeed 는 설계대로 격리 유지.

---

## §6. 자기 논리 점검 (약점)

1. **안 C 도 효용을 증명하지 않는다.** 배선은 공정이고 효용은 별개 신호다.
   `feedback_escape_to_verifiable_work` 가 경고한 그대로 — 배선 PASS 를 효용 증거로 쓰면 안 된다.
2. **계측기가 아직 없다.** D-53(요소 문법 미정합) · D-54(기저율 부풀림)가 미해결이라
   대결 실험을 지금 돌려도 또 무효가 날 수 있다. 계측기 수리가 선행되어야 한다.
   대안으로 **결정성**(같은 스펙 N회 재생성 분산)은 사람도 AI 판정도 필요 없는 무료 신호다.
3. **`turn_class` 4종 편중**(상위 4가 99.3%)은 필터 해상도를 실제보다 낮춘다.
   교차표 셀 중앙값 142는 `core` 16종이 떠받친 값이다.
4. **커버리지 확장은 GPT 저작 의존**이다. cast 63작 추가는 이 모드가 직접 못 한다(역할 분담).
5. 조사는 허브 스냅샷 `literary-os-v795` 기준이다. 그 이후 커밋은 반영되지 않았다.
