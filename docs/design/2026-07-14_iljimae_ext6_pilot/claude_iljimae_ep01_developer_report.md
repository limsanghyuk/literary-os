# Claude EXT6 Phase1 — 돌아온일지매 EP01 원본 직접독해 run

- Run ID: `claude_20260714_iljimae_ep01_01`
- 원본: 사용자 제공 `한국드라마04/돌아온일지매.zip` → `01.txt`(cp949, MBC 2009 방영본 대본)
- 원본 직접독해: **TRUE** (전문을 직접 읽고 58씬 전량 저작)
- GPT 산출물 열람: **FALSE** (blind — 2026-07-14 시점 GPT는 아직 결과물 미제출)
- Canonical: **FALSE**

## 결과 수량

| 산출물 | 행수 |
|---|---|
| Stage01 SceneCard | 58씬 (1~58 전수, 결번·중복 없음) |
| EntityBridge | 24명 |
| CastPresence | 104행 |
| CastCoverageLedger | 50씬 배치 / 8씬 empty(군중·내레이션 전용 씬) |
| SourceSceneAlignment | 58행, 전량 ONE_TO_ONE(원본 헤딩 1~58과 SceneCard 1:1 완전 대응 — 비밀의숲 hwp 파싱 때와 달리 원본이 이미 정제된 텍스트 대본이라 중복/병합 없음) |
| CharacterLoad | 24명 |

## 검증 결과 (자체 Gate A/B 상당 점검)

- exact_keyset / enum / grain_uniqueness / foreign_keys / coverage_union / character_load_recomputation / placeholder_zero: **ERRORS 0**
- WARNINGS 6건: 뇌물양반·기생1·기생2·남자1·경찰1·포졸 — 실명이 아닌 역할라벨 인물. 장소/사물 오등록은 아니나(112상황실류 결함과는 다름) Gate B7 인물성 재검토 후보로 명시 플래그.

## 방법론 메모 (비밀의숲 ep01과의 차이)

- **원본 형식**: 비밀의숲은 `.hwp`(바이너리, 커스텀 파서 필요)였으나 돌아온일지매는 이미 `.txt`(cp949) 대본이라 재추출 파서 불필요, `source_scene_alignment`도 훨씬 단순(병합/중복 케이스 0건).
- **CharacterLoad의 `act_placement`/`present_sequence_count`**: 이 작품은 아직 Stage02(SequenceBlueprint+EpisodeArc)가 없는 신규 파일럿이므로, 합의문서가 명시한 "Stage03 완료 후 CharacterLoad 파생" 순서를 따르지 못했다. 대신 임시 근사치를 사용했음을 투명하게 표기한다: act_placement는 씬번호 1~15/16~31/32~48/49~58 4분위 근사, present_sequence_count는 8개 서사 비트 경계(장면 뭉치)의 임시 구간화다. `by` 필드를 `derived_deterministic_pilot`으로 표기해 정식 EpisodeArc 기반 산출과 구분함.
- **서사 구조상 특이점**: ep01은 주인공 일지매의 등장 비중이 낮다(17/58씬, scene_share 0.293, MAJOR band — DOMINANT 아님). 현대 프레임(월희)과 조선시대 도입부(백매/구자명/배선달)에 상당 분량을 할애하는 앙상블적 파일럿 구조로, 이는 저작 오류가 아니라 원작의 실제 씬 배분을 반영한 결과임.

## 권위 경계

- 이 run은 사용자가 "새 EXT6 5계층을 신규 작품에 즉시 적용"을 승인한 정책(2026-07-14) 하에서 진행된 **Claude 독립 파일럿**이다.
- Stage02(SequenceBlueprint+EpisodeArc)·Stage04(FullSeriesArc)·구식 Stage03(LocalEdge 등)은 미저작 — 따라서 이 작품은 45편 "완주" 코퍼스에 아직 편입되지 않는다(ep01 SceneCard + EXT6 사이드카만 존재).
- GPT의 동일 작품 결과물을 열람하지 않은 상태에서 봉인 — 추후 GPT 결과물 수령 시 blind 비교(κ 산정) 가능.
- 정본 승격 아님, ep02~24 확장은 사용자 지시 전까지 보류.

---
_by: Claude(Opus) · 근거: 사용자 제공 원본 텍스트(01.txt) 직접독해 · 2026-07-14_
