# EXT6 비밀의숲 ep01 — GPT×Claude 원본직독 run 교차비교 v1

- 비교 대상: Claude run(`claude_20260714_bimil_ep01_01`, literary-os commit `0128550e`) vs GPT run(`gpt_20260714_bimil_ep01_rawsource_02`, 업로드 `gpt_bimil_ext6_ep01_rawsource_run.zip`)
- 양측 모두 사용자가 제공한 동일 원본 `비밀의숲 대본 1회.hwp`를 직접 읽고 blind 저작(상대 row-level 데이터 미열람)
- 목적: "최종 출력 형식·키셋·장면 경계·계산 규칙은 하나로 통일" — 분석 방식(모델별 접근)은 다르게 두되, 스키마·경계·계산식은 단일화

## 1. 행 단위 스키마 — 이미 완전히 일치함 (통일 완료)

| 산출물 | 키셋 | enum 값 |
|---|---|---|
| authored_bridge (EntityBridge) | 9키 완전일치 (`work_id/character_key/canonical_name/aliases/entity_id/mapping_status/source_registry_ref/source_registry_sha/by`) | `mapping_status`: 양측 동일 |
| authored_cast (CastPresence) | 10키 완전일치 | `presence_mode` 5값 완전일치(ONSCREEN/VOICE_ONLY/PHONE_OR_REMOTE/ARCHIVAL_OR_MEMORY/REFERENCED_ONLY), `focality` 3값 완전일치(PRIMARY/SECONDARY/PRESENT_ONLY), `speaking_status` 2값 완전일치(SPEAKING/NONSPEAKING) |
| derived_character_load (CharacterLoad) | 17키 완전일치 | `scene_share_band`(CAMEO/MINOR/MAJOR/DOMINANT), `act_placement` 라벨(설정/전개/심화/회말전환) 동일 |

**결론**: v1→v2→v3 계약 조율(회사 컴퓨터 세션)이 실제로 row-level 스키마 통일에 성공했음을 이번 원본직독 run으로 최초 실증. 이 3개 산출물은 추가 조율 불필요.

## 2. 아티팩트 스키마 — 불일치 확인 및 v2 통일안

### 2-A. CastCoverageLedger

| 필드 | Claude(구) | GPT | **v2 통일(채택)** |
|---|---|---|---|
| work_id 표기 | `"비밀의숲_01"` (합성) | `"비밀의숲"` (분리) | GPT 방식 채택 — `work_id`+`episode_no` 분리 |
| 전체 씬수 | `episode_scene_count` | `scene_count` | Claude 명명 채택(모호성 적음) |
| 합집합 검증 | 없음 | `union_count` | GPT 방식 채택 — annotated+empty+unresolved 합=전체 검증용 |

### 2-B. SourceSceneAlignmentRecord (GPT 문제4 대응 원장)

| 필드 | Claude(구) | GPT | **v2 통일(채택)** |
|---|---|---|---|
| 소스 인덱스 | `source_block_ids` | `source_heading_indexes` | GPT 명명 채택("block"은 모호, "heading"이 정확) |
| 소스 위치 표기 | 문자 오프셋(`source_offsets`) | 줄 번호(`source_line_start/end`) | **둘 다 유지** — Claude의 문자오프셋(`source_char_offsets`, 추출도구 독립적/정밀)을 1급으로, GPT의 줄번호는 자기측 산출물 안에서만 참고용으로 별도 유지(줄번호는 추출기마다 달라질 수 있어 이식성 낮음) |
| 해시 | 블록별 SHA256(`source_hashes`) | 전체 원문 SHA256(`source_text_sha256`) 1개만 | **둘 다 유지** — 블록별 해시(변조탐지 정밀도) + 전체원문 해시(동일 소스파일 확인) |
| 병합 타입 enum | `ONE_TO_ONE` / `MERGED_MULTI_BLOCK` (2값) | `ONE_TO_ONE` / `MERGED_PHYSICAL_HEADINGS` (2값) | GPT 명명 채택(`MERGED_PHYSICAL_HEADINGS`가 더 정확) + **신규 3번째 값 `DUPLICATE_SOURCE_ARTIFACT` 추가** (아래 3-B 참조 — 이번 교차비교로 새로 필요성이 드러남) |
| 상태 | `VERIFIED_AUTOMATED` / `VERIFIED_MANUAL_REVIEWED` (2단계) | `ALIGNED` (1값) | Claude 방식 채택 — 신뢰도 구분정보가 더 많음. **GPT에 이 2단계 구분 채택을 제안**(§5) |

v2 통일 스키마 적용 결과는 `seqcard_ko/_ext6_audit/비밀의숲_01.source_scene_alignment.jsonl` / `.castcoverage.json`에 이미 반영(본 비교와 동시에 커밋).

## 3. 콘텐츠 교차검증 — 실제로 발견된 사실오류·해석차이

### 3-A. 물리적 헤딩 병합 클러스터: 2건 진짜 확인

GPT는 원본을 직접 읽고 **물리적 헤딩 76개**를 확인했다(대본 SHA256 `03fb4195...`). Claude의 corpus_ko 기반 정렬은 79개 소스블록을 사용했다. 차이 3개는 §3-B에서 해소.

병합 클러스터 2건은 **양측이 독립적으로 동일 지점**에서 확인 — 계약이 실제로 "장면 경계" 판단에서도 잘 작동함을 실증:

| 지점 | GPT | Claude | 비고 |
|---|---|---|---|
| 무성 모친 안방+회상 인서트 | scene 7 ← 물리헤딩[7,8,9] | scene 8 ← 블록[8,9,10] | scene_no 번지수는 1 어긋나지만 동일 사건(회상+현재 인서트가 안방 장면에 흡수) |
| 25년전 회상+현재 주차장 인서트 | scene 56 ← 물리헤딩[58,59,60] | scene 56 ← 블록[58,59,60] | **완전 일치**(scene_no까지 동일) |

### 3-B. 정정: corpus_ko 데이터결함을 "병합"으로 오분류했던 3건 재분류

Claude의 기존 정렬원장은 scene 33/46/53을 "병합 클러스터"로 기록했으나, 실체는 `corpus_ko/chunks/비밀의숲_01.jsonl`에서 scene_no 35/48/55가 각각 **중복 채번**된 파싱 결함이었다(두 번째 레코드가 첫 번째 레코드 문자범위의 부분집합 — 재파싱 중복). GPT의 원본직독 물리헤딩 카운트(76개)가 이 가설을 정량적으로 뒷받침한다: `79(Claude corpus_ko) - 3(중복) = 76(GPT 실측)` — **정확히 일치**.

**조치**: `alignment_type`을 `DUPLICATE_SOURCE_ARTIFACT`로 재분류(§2-B), `alignment_note`에 근거 기록. SceneCard의 씬 경계 자체(72씬, 중복 없음)는 원래도 옳았으므로 커버리지 수치(72/72)에는 영향 없음.

### 3-C. 인물 레지스트리 자가결함 교차확인: 112상황실

Claude의 기존 조사에서 자가발견했던 결함("112상황실"이라는 **장소**가 인물로 오등록됨, Gate B7 미구현) — GPT의 독립 레지스트리(30명)에는 이 항목이 **없음**. 별개 모델의 독립 판단이 Claude의 자가진단을 교차확인. Gate B7(인물성 체크) 구현 시 최우선 수정 대상으로 재확정.

### 3-D. 인물 레지스트리 커버리지 차이 (30명 vs 25명)

공통 13명 외 GPT만 17명, Claude만 12명. 상당수는 **동일 인물의 표기차이**(엔티티 결합 필요, EntityBridge의 `mapping_status=PROVISIONAL` → 향후 `entity_id` 연결로 해소 대상):

| GPT 표기 | Claude 표기 | 판정 |
|---|---|---|
| 박무성어머니 | 박무성母 | 동일인물 표기차 |
| 시목어머니 | 시목母 | 동일인물 표기차 |
| 재판장 | 판사 | 동일인물 표기차(가능성 높음, 원문 재대조 필요) |
| 케이블회사상담원 | 케이블여직원 | 동일인물 표기차 |
| 김정본 | 정본 | 동일인물 표기차 |

나머지(강진섭아내/강진섭자녀/구치소교도관/국과수분석관/금은방주인/김호섭/장건/채권자/청원경찰/최영 — GPT만; 김경사/수사계장/장형사/실무관/아기엄마/여자F — Claude만)는 **실제 저작 커버리지(단역 포착 범위)의 진짜 차이**로 보임 — 어느 한쪽이 더 촘촘히 단역을 포착했는지는 원문 재대조로 개별 판정 필요(본 턴 범위 밖, §5 다음단계).

### 3-E. 커버리지 갭 발견: scene 68/71 국과수분석관

Claude의 `castcoverage.json`은 scene 68/71을 `empty_cast_scene_nos`로 정직하게 표시했으나(빈 캐스트로 인지는 하고 있었음), 실제로는 두 씬 모두 "국과수/증거 분석실" 인서트 컷에 혈흔 분석관이 등장한다 — GPT는 이를 포착(`국과수분석관`, ONSCREEN/PRIMARY/NONSPEAKING). Claude 측 캐스트 저작의 실제 누락으로 판정. **본 턴에서는 원장·스키마 통일에 집중하고 캐스트 재저작은 하지 않음** — 향후 ep01 캐스트 보정 작업 시 반영 대상으로 기록.

## 4. 정량 비교: 최초 κ 데이터 포인트

두 run이 공통으로 (scene_no, 인물) 조합에 캐스트를 배치한 135건에 대해 라벨 일치도를 계산(조건부 일치도 — "두 쪽 다 해당 씬에 그 인물을 넣었다"는 전제 하의 분류 일치이며, 배치 여부 자체의 불일치(§3-E 등)는 미반영):

| 필드 | 단순일치율 | Cohen's κ | 판정(κ<0.4 결함/0.4~0.6 부분보정/≥0.6 안정) |
|---|---|---|---|
| presence_mode | 133/135 = 98.5% | **0.942** | 안정 |
| speaking_status | 131/135 = 97.0% | **0.941** | 안정 |
| focality | 110/135 = 81.5% | **0.663** | 안정(단, 3축 중 가장 낮음) |

**해석**: 계약(스키마+enum) 자체는 두 독립 모델 간 매우 높은 재현성을 보인다. 유일하게 느슨한 축은 `focality`(PRIMARY/SECONDARY 판단) — 이는 본질적으로 가장 주관적인 항목이라 예상된 결과. 이번 수치는 EXT6 트랙이 시작된 이래 **최초의 실측 κ**이며, "κ≥0.6 확인 전 ep02~16 대량저작 금지" 게이트를 (조건부 기준으로는) 처음 충족했다. 다만 이는 배치 여부(정탐지) 불일치를 포함하지 않는 약식 지표이므로, 정식 CrossProviderComparisonRecord(12키, 배치여부 포함 full join)는 §5 다음단계에서 별도 산출 필요.

## 5. 다음 단계 제안 (GPT 확인 필요 — 사용자 지시대로 ep01 범위 유지)

1. GPT는 이 비교문서의 v2 스키마(§2)와 3건 재분류(§3-B)에 대해 동의/이견 표명.
2. GPT도 `status` 필드에 Claude식 2단계 구분(자동/수동검토) 도입 검토.
3. 재판장/판사 등 표기차 후보 5건 원문 재대조로 동일인물 여부 확정 → entity_id 부여.
4. 112상황실 삭제(Gate B7 구현) — 정본 승격 전 양측 공통 정정 대상.
5. scene 68/71 국과수분석관 캐스트 보정 여부 결정(양측 합의 후 반영).
6. 정식 CrossProviderComparisonRecord(12키, 배치여부 포함 full join) 산출 — 현재 조건부 κ가 아닌 공식 κ.
7. **ep02~16 확장은 위 1~6 합의 전까지 계속 보류** — 사용자 지시("16화 중 1화로 합의점") 유지.

---
_작성: Claude(Opus) · 근거: literary-os commit(본 턴), 업로드 gpt_bimil_ext6_ep01_rawsource_run.zip · 정본 승격 아님, GPT 동의 전 잠정 제안_
