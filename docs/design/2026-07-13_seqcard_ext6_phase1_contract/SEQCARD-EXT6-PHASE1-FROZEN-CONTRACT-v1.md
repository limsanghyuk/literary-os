# SeqCard EXT6 — Phase 1 Frozen Contract (P0: Cast Intelligence)

- Doc ID: SEQCARD-EXT6-PHASE1-CONTRACT-v1
- Date: 2026-07-13
- Status: **FROZEN** (양자 배포 기준. 변경은 v2 재발행으로만 — 파일럿 중 무단 스키마 변경 금지)
- Scope: **P0 3계약만** — EntityBridge · CastPresence · CharacterLoad. (CharacterVoice/Motif/Theme/Affect 등 나머지 EXT6 층은 이 계약 범위 밖 — 후속 Phase.)
- Authors of record: Claude(본 계약 저작) ↔ GPT(교차검토 합의 ARCHITECTURAL_CONSENSUS_REACHED, GPT-RESPONSE-v2)
- 목적: 클로드·GPT가 **동일 원본을 blind 독립 저작**한 뒤 diff·합의할 수 있도록, 정확 keyset·enum·grain·FK·파생식·게이트를 단일 스펙으로 고정한다.

---

## §0. 왜 frozen 계약이 선결인가

두 프론티어(Claude·GPT)가 비밀의숲을 각자 저작해 비교하려면, 두 산출이 **필드 단위로 정렬 가능(diffable)**해야 한다. 키 하나·enum 하나라도 어긋나면 불일치가 "계약 차이"인지 "판독 차이"인지 구분 불가 → inter-annotator agreement(κ) 신호가 오염된다. 따라서 저작 착수 전 계약을 얼려(freeze) 양측에 동일 배포한다.

---

## §1. 불변 전제 (합의 확정분)

1. **Stage01~04 = SSOT 불변.** EXT6은 기존 스키마를 수정하지 않는 **보강층**이다. SceneCard 9키(work_id·scene_no·heading·title·intent_gist·core·core2·skin·by)에 EXT 필드를 추가하지 않는다.
2. **새 공식 Stage 생성 금지.** 파일럿 산출은 **별도 sidecar 원장**으로만 존재한다.
3. **권위 3구분 명명:** `authored_` (인간/LLM 직접 판단) · `derived_` (무LLM 결정론 파생) · `advisory_` (가치증명 전 참고). Phase 1: CastPresence=authored, CharacterLoad=derived, EntityBridge=authored(projection).
4. **정본 승격 금지·전면 코퍼스 롤아웃 금지.** 앵커(비밀의숲→시크릿가든) Gate A/B/C 통과 전까지 파일럿 명명(EXT6-CAPTURE/DERIVE/…)만 사용.

---

## §2. 포착 시점 배치 (Phase 1 해당분)

| 계약 | 포착/생성 시점 | 근거 |
|---|---|---|
| CastPresence | **Stage01 quarter 직독 직후** (sidecar) | 씬별 등장인물은 정독 시점에만 신뢰 포착 가능 |
| EntityBridge | Stage01 인물 최초 등장 시 character_key 발급 | entity_id는 Page10 매핑까지 null |
| CharacterLoad | **Stage03 완료 후** 결정론 계산 | act_placement가 EpisodeArc.act_structure(Stage03 저작)를 참조 |

**quarter 내부 2-pass 규율:** (1) SceneCard 먼저 완성 → (2) 그 다음 CastPresence sidecar 포착. 포착이 정독 품질을 오염시키지 않게 한다.

---

## §3. 계약 P0-A — EntityBridgeRecord (9키)

Page10 Entity Registry로의 **read-only projection**. 정본(canonical) 복제·재정의 금지.
파일당 grain: `work_id × character_key` 정확 1행. 파일: `authored_bridge/<work>.bridge.jsonl`

| # | 키 | 타입 | 규칙 |
|---|---|---|---|
| 1 | work_id | str | 예 `비밀의숲` (시리즈 단위. 회차 아님) |
| 2 | character_key | str | 잠정 안정키 `<work_slug>:<canonical_name_slug>` 예 `비밀의숲:황시목` |
| 3 | canonical_name | str | 극중 표준 표기 |
| 4 | aliases | list[str] | 별칭·직함·약칭 (빈 리스트 허용) |
| 5 | entity_id | str \| null | Page10 FK. **매핑 전 null** |
| 6 | mapping_status | enum | `PROVISIONAL` \| `MAPPED` \| `CONFLICT` |
| 7 | source_registry_ref | str \| null | Page10 export 경로/식별자 (null=미연동) |
| 8 | source_registry_sha | str \| null | export 스냅샷 SHA256 (변조 감지) |
| 9 | by | str | 저작 주체 예 `cowork_opus` / `gpt5` |

---

## §4. 계약 P0-B — CastPresenceRecord (10키)

**Grain: 씬 × 인물 정확 1행.** (한 씬에 인물 N명 → N행). 파일: `authored_cast/<work>_NN.cast.jsonl`

| # | 키 | 타입 | 규칙 |
|---|---|---|---|
| 1 | work_id | str | 회차 단위 예 `비밀의숲_01` |
| 2 | episode_no | int | |
| 3 | scene_no | int | SceneCard.scene_no와 FK 일치 (실재 씬만) |
| 4 | character_key | str | EntityBridge.character_key와 FK 일치 |
| 5 | entity_id | str \| null | Bridge에서 복사 (매핑 전 null) |
| 6 | presence_mode | enum | `ONSCREEN` \| `VOICE_ONLY` \| `PHONE_OR_REMOTE` \| `ARCHIVAL_OR_MEMORY` \| `REFERENCED_ONLY` |
| 7 | focality | enum | `PRIMARY` \| `SECONDARY` \| `PRESENT_ONLY` |
| 8 | speaking_status | enum | `SPEAKING` \| `NONSPEAKING` |
| 9 | evidence_ref | str | 씬 내 근거 위치 지시(대사/지문 offset·hash). **원문 장문 복사 금지** |
| 10 | by | str | 저작 주체 |

**정의 주석:**
- `presence_mode=REFERENCED_ONLY`는 인물이 화면에 없고 **언급만** 된 경우 — 등장 카운트에서 제외(§6 참조).
- `focality=PRIMARY`는 그 씬의 극적 초점을 이끄는 인물. 씬당 PRIMARY는 0~복수 가능(단독 강제 아님).

---

## §5. 계약 P0-C — CharacterLoadRecord (17키)

**Grain: 회차 × 인물 정확 1행.** 전량 §6 결정론 식으로 계산 (자기점수 금지). 파일: `derived_character_load/<work>_NN.load.jsonl`

| # | 키 | 타입 | 파생 근거 |
|---|---|---|---|
| 1 | work_id | str | |
| 2 | episode_no | int | |
| 3 | character_key | str | |
| 4 | entity_id | str \| null | |
| 5 | canonical_name | str | Bridge 조인 |
| 6 | present_scene_count | int | presence_mode ∈ {ONSCREEN,VOICE_ONLY,PHONE_OR_REMOTE,ARCHIVAL_OR_MEMORY} 인 씬 수 (REFERENCED_ONLY 제외) |
| 7 | focal_scene_count | int | focality=PRIMARY 씬 수 |
| 8 | speaking_scene_count | int | speaking_status=SPEAKING 씬 수 |
| 9 | present_sequence_count | int | 인물이 ≥1 member 씬에 존재하는 distinct seq_id 수 |
| 10 | scene_share | float | present_scene_count / episode_scene_count (반올림 4자리) |
| 11 | focal_share | float | focal_scene_count / episode_scene_count |
| 12 | scene_share_band | enum | §6 임계로 파생: `DOMINANT` \| `MAJOR` \| `MINOR` \| `CAMEO` |
| 13 | act_placement | dict[str,int] | act명→present_scene_count (scene→seq→act 조인) |
| 14 | first_scene_no | int | 최소 등장 scene_no |
| 15 | last_scene_no | int | 최대 등장 scene_no |
| 16 | max_absence_gap | int | [first,last] 내 연속 등장 씬 간 최대 scene_no 간극 |
| 17 | by | str | 예 `derived_deterministic` |

---

## §6. 결정론 파생 규칙 (무LLM, 재현 100%)

- **episode_scene_count** = 해당 회차 SceneCard 총 씬 수.
- **scene→seq 조인**: SequenceBlueprint.member_scene_nos 로 scene_no→seq_id.
- **seq→act 조인**: EpisodeArc.act_structure[].seq_span (seq_index 범위)로 seq→act명.
- **scene_share_band 임계(파일럿 고정, Gate C 후 재조정 가능):**
  - `DOMINANT` ≥ 0.50 · `MAJOR` 0.20–0.50 · `MINOR` 0.05–0.20 · `CAMEO` < 0.05
- **max_absence_gap**: 인물 등장 scene_no 오름차순 정렬 후 인접차의 최대값−1 (연속이면 0).
- 모든 float 소수 4자리 반올림. 카운트는 CastPresence에서만 집계(중복 계산 금지).

---

## §7. 물리 배치

```
seqcard_ko/
  authored_bridge/<work>.bridge.jsonl              # P0-A (시리즈 1파일)
  authored_cast/<work>_NN.cast.jsonl               # P0-B (회차별)
  derived_character_load/<work>_NN.load.jsonl      # P0-C (회차별, 무LLM 재생성 가능)
  _ext6_audit/<work>_NN.castcoverage.json          # QuarterAudit(§9)
```

---

## §8. Gate A — 계약 검사 (ERRORS 0 필수, 결정론)

1. **Exact keyset**: 각 레코드 키 집합이 계약과 정확 일치(누락·잉여 0).
2. **Enum 유효성**: presence_mode·focality·speaking_status·mapping_status·scene_share_band 모두 허용값.
3. **Type 검사**: int/float/str/list/dict 타입 일치. null 허용 필드 외 null 금지.
4. **Grain uniqueness**: CastPresence (work_id,scene_no,character_key) 유일 · Load (work_id,episode_no,character_key) 유일 · Bridge (work_id,character_key) 유일.
5. **FK 무결성**: CastPresence.scene_no ∈ SceneCard · character_key ∈ Bridge · Load.character_key ∈ Bridge.
6. **COUNT 정합**: Load 카운트 6~9 = CastPresence 재집계와 정확 일치.
7. **재계산 정합**: scene_share/focal_share/band/act_placement/max_absence_gap 를 원장에서 재계산해 저장값과 일치.

## §9. Gate B — 근거·반게이밍 검사 (ERRORS 0 필수)

1. **씬 실재**: 모든 CastPresence.scene_no가 원본 SceneCard에 실재.
2. **인물 실등장**: evidence_ref가 해당 씬 텍스트 범위를 실제로 가리킴(placeholder·상수 금지).
3. **evidence 원문 비저장**: evidence_ref는 offset/hash/짧은 지시어만 — 원문 장문 복사 탐지 시 FAIL.
4. **고정 골격 금지**: 전 회차 동일 인물집합 붙여넣기(회차 변별력 0) 탐지 시 FAIL.
5. **placeholder 금지**: "TBD"/"미상"/빈 evidence 등.
6. **CastCoverageLedger(QuarterAudit)**: 각 회차 `annotated_scene_nos` / `empty_cast_scene_nos`(인물 없는 외경·인서트) / `unresolved_scene_nos`(판독 보류) 를 명시 → **인물 없는 씬 vs 분석 누락**을 구별. 세 집합의 합집합 = 전체 씬집합(누락 0 불변식).

---

## §10. 이중저작 비교 → 합의 프로토콜 (5단)

1. **양측 Gate A/B ERRORS 0** 각각 통과(통과 못한 산출은 비교 대상 제외).
2. **정렬·일치율 측정**: (work_id,scene_no,character_key) 기준 조인 →
   - CastPresence: presence_mode·focality·speaking_status **셀 단위 일치율** + Cohen κ / PABAK.
   - CharacterLoad: scene_share_band·act_placement 일치율.
   - 인물집합 자체 불일치(한쪽만 태깅한 인물) = **커버리지 diff**로 별도 집계.
3. **불일치 목록화**: 씬·인물별로 어느 쪽이 누락/과탐/등급차인지 표.
4. **규칙 정정**: 불일치 유형을 계약/판독지침 개정으로 환원(예 presence_mode 경계 모호 → 정의 보강).
5. **reconciled gold 산출**: 합의된 단일 정답판 = **Gate C 앵커**. 이후 대량 분석의 기준이 됨.

**κ 판정(advisory)**: κ<0.4 → 계약/지침 결함 우선 의심. 0.4≤κ<0.6 → 부분정정. κ≥0.6 → 계약 안정, 불일치는 개별 판독차로 처리.

---

## §11. blind 독립성 · 파일럿 규율

- 두 저작이 **완료·잠금되기 전 상호 산출 열람 금지**(합의 오염 방지). 잠근 뒤에만 §10 개시.
- 파일럿 명명: `EXT6-CAPTURE`(CastPresence) · `EXT6-DERIVE`(CharacterLoad) · `EXT6-VALUE-PROOF`(Gate C). 비밀의숲·시크릿가든 A/B/C 통과 후에만 공식 **"Stage05 — Literary Interpretation & Cast Intelligence"** 승격.
- 앵커 순서: 1차 비밀의숲(다인물 수사극) · 2차 시크릿가든(로맨스 대비) · 3차 베토벤바이러스(군상).
- **금지 유지**: 전면 코퍼스, 새 공식 Stage, 정본 승격, 무단 허브 push.

---

## §12. 착수 지시 (양자 공통)

동일 원본(seqcard_ko/authored/비밀의숲_01~16)에 대해, 본 계약대로:
1. Stage01 quarter 정독 직후 CastPresence 포착(2-pass 규율).
2. EntityBridge character_key 발급(entity_id=null).
3. Stage03 완료 확인 후 CharacterLoad 결정론 계산.
4. 자체 Gate A/B 실행 → ERRORS 0 → 잠금.
5. 잠금 완료 통지 후에만 §10 비교 개시.
