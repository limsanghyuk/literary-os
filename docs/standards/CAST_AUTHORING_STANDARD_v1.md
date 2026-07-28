---
doc_id: LOS-STD-CAST-AUTHORING-V1
title: CastPresenceRecord 직접독해 저작 표준 v1
status: ACTIVE
date: 2026-07-29
supersedes: (없음 — 신규)
depends_on: EXT6 P0-B CastPresenceRecord 계약 (FROZEN 2026-07-13), LOS-SPEC-CASTLAYER-V3.0
by: claude-opus-direct-reading
---

# CastPresenceRecord 직접독해 저작 표준 v1

## 0. 이 층이 존재하는 이유

SceneCard 9키(`work_id, scene_no, heading, title, intent_gist, core, core2, skin, by`)에는
**인물 필드가 없다.** 씬에 누가 나오고, 누가 행동하고, 누가 말하는지가 원장에 기록되지 않는다.

`intent_gist` 텍스트에서 인물명을 역추출하는 방식은 실제 등장의 45.5~67.8%만 포착한다.
결정론 씬 배치(표면형 매칭)의 천장은 골드 2작 실측 F1 0.43~0.70이며, 전 코퍼스 단일 규칙은 존재하지 않는다.

따라서 **이 층은 원문 직접 독해로만 저작한다.** 매칭·추출·추론 자동화로 대체할 수 없다.

## 1. 입자도와 키

- 입자도: **씬 × 인물 = 정확히 1행.** 같은 씬에 같은 인물이 두 행이면 게이트 위반(CAST-2).
- 10키 전체 필수:
  `work_id, episode_no, scene_no, character_key, entity_id, presence_mode, focality, speaking_status, evidence_ref, by`
- `character_key`: `<work_id>:<이름>` 형식. 이름은 해당 작품 `advisory_bridge`의 `canonical_name`과 **정확히 일치**시킨다.
  명부에 없는 인물이라도 실제 등장하면 기록하고, 명부 결함으로 별도 보고한다(등장을 누락시키지 않는다).
- `entity_id`: 저작 시점 `null`. 전역 엔티티 병합은 후속 패스.
- `by`: 저작 주체 문자열. 직접독해 저작물은 `claude-opus-direct-reading`.

## 2. presence_mode — 5값

| 값 | 정의 | 판정 기준 |
|---|---|---|
| `ONSCREEN` | 화면 안에 신체가 있음 | 지문에 등장·행동·표정이 서술됨 |
| `VOICE_ONLY` | 화면 밖에서 목소리만 | 문 너머 외침, 화면 밖 대사, 나레이션 주체 |
| `PHONE_OR_REMOTE` | 통화·영상통화·무전 등 원격 연결 | 통화 상대 |
| `ARCHIVAL_OR_MEMORY` | 사진·영정·TV·회상·환영·녹음 | 현재 시점의 실재가 아닌 매체·기억 속 존재 |
| `REFERENCED_ONLY` | 언급만 됨 | 특정 가능한 인물이 대사·지문에서 지칭됨 |

**경계 규칙 3종**

1. **들리지 않는 통화 상대도 기록한다.** 한쪽 대사만 있고 상대 대사가 없어도, 상대가 특정 가능하면 `PHONE_OR_REMOTE`로 1행. 특정 불가하면 기록하지 않는다.
2. **회상 속 대사는 `ARCHIVAL_OR_MEMORY` + `SPEAKING`.** 모드는 존재 방식, speaking_status는 발화 여부 — 두 축은 독립이다.
3. **`REFERENCED_ONLY`는 특정 가능한 인물에만.** "사람들이", "누가" 같은 불특정 지칭은 기록하지 않는다.

## 3. focality — 3값

| 값 | 정의 |
|---|---|
| `PRIMARY` | 그 씬의 사건을 끌고 가는 인물 |
| `SECONDARY` | 사건에 관여하나 주도하지 않음 |
| `PRESENT_ONLY` | 배경·군중·존재만 |

**핵심 규칙: 애매하면 낮춘다.** 3축 중 focality의 평가자간 일치도가 가장 낮다(κ=0.663 vs presence 0.942, speaking 0.941).
PRIMARY/SECONDARY 경계가 흔들리면 SECONDARY, SECONDARY/PRESENT_ONLY가 흔들리면 PRESENT_ONLY.
PRIMARY 과다 부여가 이 층의 가장 흔한 저작 오류다.

## 4. speaking_status — 2값

`SPEAKING` / `NONSPEAKING`. 대사 슬롯 보유 여부.

- **입모양 대사도 SPEAKING**(예: 유리창 너머 "(입모양 보이도록)끝나고 먹어.").
- **지문에 인용된 발화도 SPEAKING**(예: 지문 안 "만세! 야호!" 환호).
- 대사 없이 표정·행동만이면 NONSPEAKING.

## 5. evidence_ref — 형식과 원칙

형식: `EP<NN>-S<NN> <원문 인용>`

- 인용은 **원문 축자**. 요약·의역·창작 금지.
- 모든 행에 비어 있지 않은 근거가 있어야 한다(CAST-4).
- 근거는 그 행의 3축 판정을 지지해야 한다. ARCHIVAL 행이면 사진·회상임이 인용에 드러나야 한다.

## 6. 무명·군중·명부 외 인물

- 이름 없는 인물은 기능 명칭으로 키를 만든다: `결혼정보회사커플매니저`, `두리두리이벤트직원`.
- **같은 라벨이 작품 내 서로 다른 인물을 가리키면 반드시 구분한다.**
  실사례: 3씬 몽타주의 `맞선녀01`~`맞선녀17` 계열과 38씬 호텔 맞선 상대가 `맞선녀1`로 충돌 → `호텔맞선녀`/`호텔맞선남`으로 분리.
- 특정 불가한 군중(`행인들`, `하객들`)은 기록하지 않는다. 씬에서 개별 행동·대사를 가지면 그때 기록한다.

## 7. 게이트 코드

`tools/castlayer_v3/gate_cast_authored.py <cast_dir> <authored_dir>`

| 코드 | 등급 | 조건 |
|---|---|---|
| CAST-1 | ERROR | 키셋이 10키와 불일치 |
| CAST-2 | ERROR | 씬×인물 중복 행 |
| CAST-3 | ERROR | enum 위반 |
| CAST-4 | ERROR | evidence_ref 공백 |
| CAST-5 | ERROR | scene_no가 SceneCard 원장에 없음 |
| CAST-W1 | WARN | 해당 회차에 PRIMARY가 0 |
| CAST-W2 | WARN | 인물 0인 씬이 10% 초과 |

푸시 조건: **ERRORS 0.** WARN은 사유를 회차 노트에 남긴다.

## 8. 기준편 벤치마크 (101번째프로포즈 01회)

| 지표 | 기준편 | 골드(돌아온일지매) |
|---|---|---|
| 행수 | 238 | — |
| 씬 | 57 (인물 있는 씬 54) | — |
| 씬당 평균 인물 | 4.18 (비어있지 않은 씬 4.41) | 2.95 |
| ONSCREEN / REFERENCED_ONLY / PHONE / ARCHIVAL / VOICE | 169 / 39 / 21 / 6 / 3 | REFERENCED_ONLY 2 |
| PRIMARY / SECONDARY / PRESENT_ONLY | 94 / 54 / 90 | — |
| SPEAKING / NONSPEAKING | 149 / 89 | — |

밀도 차이는 거의 전부 `REFERENCED_ONLY`에서 발생한다. 계약이 5모드를 정의하므로 **기록이 규격 준수**이며,
골드 2작은 향후 재저작 대상으로 표시한다.

## 9. 이 층이 여는 기획 게이트 v2 (기준편 실측, REFERENCED_ONLY 제외)

| 인물 | 씬수 | 비율 | 밴드 |
|---|---|---|---|
| 박달재 | 41 | 0.72 | DOMINANT |
| 한수정 | 26 | 0.46 | MAJOR |
| 박민재 | 17 | 0.30 | MAJOR |
| 박창만 | 13 | 0.23 | MAJOR |
| 장은임 | 12 | 0.21 | MAJOR |
| 한금정 | 8 | 0.14 | MINOR |
| 염선자 | 6 | 0.11 | MINOR |
| 준기 | 6 | 0.11 | MINOR |

밴드 분포 DOMINANT 1 / MAJOR 4 / MINOR 7 / CAMEO 50.
충족 하한: 주요인물 5 ≥ 3, 유효인물 12 ≥ 4, 주인공 부재율 0.28 ≥ 0.25.
**이 세 하한은 이 층 이전에는 계산 자체가 불가능했다.**
