---
doc_id: LOS-HANDOFF-CASTLAYER-87W
title: 인물 등장층(CastPresenceRecord) 87작 직접독해 저작 — 재개 RUNBOOK
status: ACTIVE
date: 2026-07-29
by: claude-opus-direct-reading
---

# 인물 등장층 87작 저작 — 재개 RUNBOOK

**어느 컴퓨터에서든 이 문서 하나로 이어받는다.**

## 1. 지금 어디까지 왔나

진행 상태의 단일 출처: `tools/castlayer_v3/cast_progress_ledger.json`
(`doc_id: LOS-LEDGER-CASTLAYER-AUTHORED-87W`, 입자도 = 작품 × 회차, 순서 = 가나다)

| 항목 | 값 |
|---|---|
| 전체 | 87작 / 1,640회 / 102,417씬 |
| 완료 회차 | 26 |
| 남은 회차 | 1,614 |

상태 3값: `DONE`(전 회차 완료) / `PARTIAL`(일부 완료) / `TODO`(미착수)

현재 비-TODO 작품:

| 작품 | 상태 | 완료/전체 |
|---|---|---|
| 101번째프로포즈 | PARTIAL | 1/15 |
| 돌아온일지매 | DONE | 24/24 |
| 비밀의숲 | PARTIAL | 1/16 |

## 2. 재개 절차 (5단계)

```bash
# 1) 허브 clone (읽기 토큰 불요)
git clone https://github.com/limsanghyuk/literary-os.git

# 2) 진행대장에서 다음 대상 확인
python3 -c "import json;d=json.load(open('literary-os/tools/castlayer_v3/cast_progress_ledger.json'));\
print([w['work_id'] for w in d['works'] if w['status']!='DONE'][:5])"

# 3) 표준 정독
#    docs/standards/CAST_AUTHORING_STANDARD_v1.md
#    tools/castlayer_v3/samples/author_101번째프로포즈_ep01.py  (기준편 저작 스크립트)
#    seqcard_ko/authored_cast/101번째프로포즈_01.cast.jsonl     (기준편 산출물)

# 4) 원문 직접 독해 → 저작
#    원문: <로컬 정본>/seqcard_ko/original_extracted/<작품>/<작품>_NN.txt
#    산출: seqcard_ko/authored_cast/<작품>_NN.cast.jsonl

# 5) 게이트
python3 literary-os/tools/castlayer_v3/gate_cast_authored.py <cast_dir> <authored_dir>
# ERRORS 0 이어야 진행
```

**원문 텍스트는 허브에 커밋하지 않는다.** 원문은 로컬 정본 DB에만 둔다.

## 3. 저작 방식 — 자동화 금지 조항

이 층은 **원문 직접 독해로만** 저작한다. 이름 매칭·정규식 추출·LLM 추론으로 대체하지 않는다.
근거: 결정론 씬 배치 천장 F1 0.43~0.70 (골드 2작 실측), `intent_gist` 역추출 포착률 45.5~67.8%.

병렬 저작 시 각 에이전트는 회차 단위로 독립 배정하되, 반드시
`CAST_AUTHORING_STANDARD_v1.md` + 기준편 산출물을 참조 샘플로 함께 받는다.

## 4. 작품 1편 완성 시 인계 프로토콜 (필수)

한 **작품**(회차가 아님)의 전 회차가 게이트 ERRORS 0으로 통과하면 다음 4단계를 즉시 수행한다.

| 단계 | 산출물 | 위치 |
|---|---|---|
| 1. 게이트 전작 재실행 | `<작품>_gate.txt` | 배포 번들 내 |
| 2. 번들 생성 | `<작품>_cast_v1.zip` (전 회차 `.cast.jsonl` + `MANIFEST.json` + 게이트 리포트) | `castlayer_v3/delivery/` |
| 3. 개발자 인계 | 위 zip을 작업 폴더로 복사 후 사용자에게 파일 링크 제시 | 사용자 작업 폴더 |
| 4. 허브 반영 | `seqcard_ko/authored_cast/<작품>_*.cast.jsonl` + 갱신된 `cast_progress_ledger.json` 커밋·푸시 | 허브 |

`MANIFEST.json` 필수 필드:
`work_id, episodes, scenes, rows, files[{name, rows, sha256}], gate{errors, warns}, standard_doc_id, generated_at, by`

**중간 상태도 유실되지 않게 한다.** 작품이 미완성이라도 회차 저작이 끝날 때마다
`cast_progress_ledger.json`의 `cast_done_eps`를 갱신하고 허브에 푸시한다.

## 5. 알려진 결함 (인계 대상)

1. **돌아온일지매_12 원장 씬수 트리 간 불일치 (ERROR급)** — 로컬 정본 43씬 / 허브 48씬. 24회 중 이 회차만 갈린다(나머지 23회 완전 일치, 총 1,382 vs 1,387). 원문 대조로 어느 쪽이 옳은지 확정 후 한쪽을 폐기해야 한다. cast 게이트 CAST-5는 cast와 원장을 교차 트리로 붙이면 발생하므로, **게이트는 반드시 같은 트리 안에서 실행한다.**
2. **돌아온일지매 cast는 이중저작 파일럿 산출물이며 두 판본이 병존한다.**
   - 로컬 = `gpt-5.6-thinking-direct-reading`, 24회 4,622행
   - 허브 = `opus_reading`, 24회 3,608행
   두 판본이 κ 측정(presence 0.942 / speaking 0.941 / focality 0.663)의 원천이다. 결함이 아니라 설계된 blind 이중저작(허브 커밋 66a0058). **정본 1판을 확정하기 전까지 이 작품은 다른 작품의 밀도 기준선으로 쓰지 않는다.**
3. **골드 판본 간 REFERENCED_ONLY 기록 편차** — opus 판본은 REFERENCED_ONLY를 0건, gpt 판본은 33건(ep12 기준) 기록한다. 기준편은 39건. 계약이 5모드를 정의하므로 **기록이 규격 준수**이며, opus 판본이 과소기록이다.
4. **돌아온일지매_01 CAST-W2** — 인물 0인 씬 8/58 (13.8%).
5. **명부(advisory_bridge) 커버리지 결함** — 101번째프로포즈 01회에서 `찬혁`, `정만수`, `준기`가 실질 등장하나 명부에 없음(명부에는 `찬혁모`만 존재). 그들이사는세상 `준호` 사례와 동일 패턴. Stage03 CharacterArc 결함이며 인물층 결함이 아니다.
6. **잠정 키 병합 대기** — `수정모`/`수정부`는 명부의 `정순`/`한태성`과 후속 대조 필요.

## 6. 가나다 순 다음 대상

101번째프로포즈(02~15회) → W(16) → 강남엄마따라잡기(18) → 개와늑대의시간(16) → 개인의취향(15)
→ 결혼못하는남자(16) → 경성스캔들(16) → 공주가돌아왔다(16) → ...

`비밀의숲`은 02~16회 미저작, `돌아온일지매`는 완료.
