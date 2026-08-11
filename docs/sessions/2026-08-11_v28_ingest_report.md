# 편입 원장 — DB98(GPT Stage04, 98작) 병합 (2026-08-05, 집 Fable)
- 소스: DB98_STAGE04_98WORKS_EXT6_34_PHASE02_16_WINDOWS_SAFE_20260805.zip (개발자 제공, GPT 분석)
- 방식: **append-only** (덮어쓰기 0건 — 로컬 기존 파일 무손상), NFC 정규화 대조, 양방향 차분 보충
- 신규 작품 4: 1프로의어떤것(26화/1,259씬)·가을동화(16화/914씬)·난폭한로맨스(16화/1,350씬)·연애말고결혼(16화/956씬) — 전 계층(seqcard·seq·arc·chararc·relarc·edges·원문·감사) 완비, JSON 파싱 오류 0
- 오버레이 차분: EXT6 통합 11→21·레지스트리 28→35, Phase02 인가 9→16, derived_character_load 598→732, validation 810→1,149, history 0→38 등
- 결과: **98작 / 1,814회차 / 씬카드 114,371(인덱스 기준)** · 총 26,859파일 · 업로드 인덱스 사본=AUTHORED_WORK_INDEX_V24_DB98_98WORKS.json
- 배포본: C:\claude\SEQCARD_KO_FULLDB_98WORKS_MERGED_20260805.zip (124MB, 정본과 파일 단위 완전 일치 검증)

---
# 증보 — V28 FULL 편입 (2026-08-11, 집 Fable)
- 소스: SEQCARD_KO_FULLDB_V28_FULL_20260811.zip (98작 유지, 28,788파일)
- **reinforcement_v1 = V28 정본 승계**(append-only 아님 — 재저작 반영 필수): 후판 **9작 147회차 1,283시퀀스** 파싱 0오류. 강남엄마따라잡기 재저작판(0.594→0.857)·경성스캔들·내이름은김삼순·너의목소리가들려 등 4작 신규 + runtime_scene_projection 147·planner_input 147·validation 281·source_read_evidence 10(신층). 로컬 구판 578파일 = `_superseded_local/reinforcement_pre_V28/` 백업.
- 나머지 트리: 신규 파일만 추가(tools 1) + 루트 갱신 1건(구판 백업). 로컬은 V28의 슈퍼셋 유지.
- 개발자 고지: **추가 보강 추후 제공 예정** — 차기 편입 시 본 절차(reinforcement=승계, 기타=append) 재사용.
