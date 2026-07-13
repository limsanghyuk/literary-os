# CLAUDE — EXT6 Phase 01 독립 설계안 (v1)

- 저장소 트랙: `limsanghyuk/literary-os` (Claude 허브)
- 상태: `CLAUDE_INDEPENDENT_DRAFT_LOCKED`
- 독립성: 본 문서는 GPT의 `docs/external/GPT_EXT6_PHASE01_INDEPENDENT_PROPOSAL_v1.md`를 **열람하지 않은 상태**에서 작성·봉인되었습니다. 교차검토는 봉인 이후에만 수행합니다.
- 차별점: 본 안은 설계 초안이 아니라 **앵커 비밀의숲 ep01에서 결정론 Gate A + Gate B를 ERRORS 0으로 통과한 실증 계약**입니다.

---

## 0. 권위 경계 (변경 불가)

- Stage01~04 SSOT는 **한 바이트도 변경하지 않습니다.** EXT6는 `authored_*` / `derived_*` / `_ext6_audit` 사이드카 원장으로만 존재합니다.
- 파일럿 기간 중 **신규 공식 Stage를 만들지 않습니다.** 기능명만 사용: CAPTURE(포착) · DERIVE(파생) · FULL-SERIES-SYNTHESIS(종합) · VALUE-PROOF(가치증명).
- **정본 승격·전면 코퍼스 확장·허브 push는 사용자 승인 전까지 금지.**

## 1. EXT6 시점(Stage 매핑, 불변경)

| 기능 | 입력(읽기 전용) | 산출(사이드카) | LLM 사용 |
|---|---|---|---|
| CAPTURE | authored/*.seqcard.jsonl(SSOT) + corpus 원문(증거) | authored_cast, authored_bridge | 예(프런티어 저작) |
| DERIVE | cast + bridge + authored_seq + authored_arc | derived_character_load | **아니오(100% 결정론)** |
| AUDIT | seqcard scene_no 집합 | _ext6_audit/*.castcoverage.json | 아니오 |
| SYNTHESIS(후속 Phase) | 회차별 load 누적 | derived_series_load | 아니오 |

## 2. 계약 P0 — 3 핵심 레코드 (frozen, ep01 실증)

### 2.1 EntityBridgeRecord (9키)
```
work_id, character_key, canonical_name, aliases, entity_id,
mapping_status, source_registry_ref, source_registry_sha, by
```
- `character_key` = `<work_slug>:<canonical_name_slug>` — 잠정 로컬 안정키.
- `entity_id` = Page10 Entity Registry FK, 매핑 전 `null`.
- `mapping_status` ∈ {PROVISIONAL, MAPPED, CONFLICT}.
- grain = 작품×인물 1행.

### 2.2 CastPresenceRecord (10키) — grain = 씬×인물 1행
```
work_id, episode_no, scene_no, character_key, entity_id,
presence_mode, focality, speaking_status, evidence_ref, by
```
- `presence_mode` ∈ {ONSCREEN, VOICE_ONLY, PHONE_OR_REMOTE, ARCHIVAL_OR_MEMORY, REFERENCED_ONLY}.
- `focality` ∈ {PRIMARY, SECONDARY, PRESENT_ONLY}.
- `speaking_status` ∈ {SPEAKING, NONSPEAKING}.
- `evidence_ref` = 참조 토큰(≤240자, 원문 덤프 금지).
- REFERENCED_ONLY은 present 집계에서 제외.

### 2.3 CharacterLoadRecord (17키) — 100% 결정론 파생(§5/§6)
```
work_id, episode_no, character_key, entity_id, canonical_name,
present_scene_count, focal_scene_count, speaking_scene_count,
present_sequence_count, scene_share, focal_share, scene_share_band,
act_placement, first_scene_no, last_scene_no, max_absence_gap, by
```
- `scene_share` = present_scene_count / episode_scene_count (소수 4자리).
- band: DOMINANT ≥0.50 · MAJOR 0.20–0.50 · MINOR 0.05–0.20 · CAMEO <0.05.
- `present_sequence_count` = member_scene_nos로 매핑된 seq_index 수.
- `act_placement` = act_structure seq_span 기준 act별 present 씬 수(dict).
- `max_absence_gap` = 연속 present scene_no 간 최대 공백.

## 3. CastCoverageLedger (감사 원장)
```
work_id, episode_scene_count, annotated_scene_nos,
empty_cast_scene_nos, unresolved_scene_nos, by
```
- 불변식: `annotated ∪ empty ∪ unresolved == 전체 scene_no 집합` (I-COVER).
- `annotated ∩ empty == ∅`.
- freeze 시 `unresolved == []` (I-COMPLETE).
- annotated 씬은 실제 cast 행을 가져야 함.

## 4. AnalysisRunManifest (독립 제안 — 실행 출처 증명)
비교의 재현성을 위해 각 provider 실행을 다음으로 봉인합니다.
```
run_id, work_id, episode_no, provider, model_id,
contract_version, input_seqcard_sha, input_corpus_sha,
cast_row_count, bridge_row_count, load_row_count,
gate_a_errors, gate_b_errors, sealed_at
```
- gate_a_errors == gate_b_errors == 0 이어야 봉인 유효.

## 5. 독립 실행 경로 (blind)
```
provider=Claude: 원문 → Sonnet N-병렬 CastPresence → Opus fan-in 정규화(bridge) → 결정론 load → Gate A/B
provider=GPT:    동일 계약으로 독립 저작 (Claude 산출 미열람)
```
- 두 provider가 각자 봉인할 때까지 상호 산출 비열람.

## 6. CrossProviderComparisonRecord (독립 제안 — κ 비교 출력)
```
work_id, episode_no, grain, compared_field,
n_units, n_agree, po, pe, kappa,
provider_a, provider_b, resolved_gold_ref
```
- 대상 필드: presence_mode, focality, speaking_status(씬×인물 grain) + scene_share_band(인물 grain).
- 판정: κ<0.4 = 계약 결함 → 재설계 / 0.4–0.6 = 부분보정 / ≥0.6 = 안정.
- 대상 union = 두 provider가 공통으로 등장시킨 인물의 공통 present 씬.

## 7. Gate A / B / C
- **Gate A(§8, 하드 ERRORS 0)**: A1 정확 keyset · A2 enum 도메인 · A3 타입 · A4 grain 유일성(scene_no,character_key) · A5 FK(cast/load char_key∈bridge, cast scene_no∈seqcard) · A6 COUNT 패리티(load 행수 == present-mode 인물키 distinct) · A7 재파생 대조(cast에서 load 전 필드 재계산 diff).
- **Gate B(§9, 하드 ERRORS 0)**: B2 증거 비어있지 않음 · B3 증거 ≤240자(원문덤프 아님) · B4 고정 스켈레톤 금지(전 씬 동일 cast 불가) · B5 placeholder 토큰 금지 · B6 CoverageLedger union 완전성 · **B7(신규 제안) 인물성 — character_key가 장소/소품/기관이면 ERROR**(자가감사 발견: `비밀의숲:112상황실` 오등록 차단).
- **Gate C(가치증명, advisory)**: band 분포의 극작 타당성, 회차간 load 궤적, κ 대조.

## 8. Fixtures
- positive: ep01 실 산출(bridge 25 · cast 177 · load 25 · scenes 72) → Gate A/B ERRORS 0.
- negative(각 게이트 최소 1건): keyset 누락 / bad enum / grain 중복 / dangling FK / COUNT 불일치 / recalc 불일치 / empty evidence / 240자 초과 / 고정 스켈레톤 / placeholder / union 결손 / 장소-인물(B7).

## 9. 앵커 계획
1. **비밀의숲**(앵커 1, ep01 완료·ERRORS 0) → κ 대조 1호 단위.
2. **시크릿가든**(앵커 2) → 계약 이식성 검증.
3. **베토벤바이러스**(앵커 3) → 군상극 부하 분포 검증.
- ep01 κ≥0.6 확인 **전에는** ep02–16 대량 저작 금지.

## 10. 비교·합의·승인 절차
```
Claude 독립안 봉인(본 문서)
→ GPT Phase01 문서 열람
→ 계약 keyset·enum·grain·게이트 diff 매트릭스
→ 합의/이견 원장 + κ 실측(ep01)
→ 사용자 승인 → 최종 동결 계약
→ (승인 시에만) ep02–16 확장 / 정본 승격 / 허브 push
```

## 11. 자가 논리점검(self-audit)
- **약점 1**: character_key 잠정키가 provider간 표기 변이(강진섭/김진섭 등)로 κ 대상 정렬을 깨뜨릴 수 있음 → 정렬은 entity_id 부재 시 canonical_name+aliases 정규화 후 수행(비교 전처리 규정 필요).
- **약점 2**: seqcard(72씬, SSOT) vs corpus(76씬, 원문) 씬수 불일치 → scene_no는 seqcard를 권위로, corpus는 증거로만 사용(ep01에서 채택·검증).
- **약점 3**: B7 인물성 판정 자체가 경계사례(예: "112상황실 형사들" 집합 인물)를 낳음 → 집합 인물은 별도 `is_collective` 플래그 후속 제안, 파일럿에서는 개별 인물만.
- **개선 최종안**: 위 3항을 비교 전처리·B7·후속 플래그로 분리 수용. 3 P0 계약과 게이트는 ep01 실증으로 확정 유지.

---
_by: Claude (Opus) · 근거: seqcard_ko/{authored_bridge,authored_cast,derived_character_load,_ext6_audit}/비밀의숲* · Gate: ext6_gate_ab.py ERRORS 0_
