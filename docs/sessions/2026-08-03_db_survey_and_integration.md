# C:\claude·db 전수 조사 + 신규 자료 편입 보고 (2026-08-03)

## 1. 작업 공간 전수 조사 (8/3 시점)
- **db/seqcard_ko**: 이미 **V24 FULLDB(93작)** 로 갱신되어 있었음(8/3 오후 추출, 신 레이아웃: ext6_authority/integration/manifests/registry/schema·ext6_phase02_authorization(9건)·stage04·source_index·source_text·semantic_audits·derived_seed_* 등 계층 대폭 확장). 회차 1,724 → 조사 시점 확인.
- 루트: literary-os-v795.zip(8/3 신규), 감사 산출물(delivery/LAYER_VALUE_AUDIT 계열)은 회사 트랙 문서로 확인. corpus_ko·4070_oneclick·harvest_pairs(25,500쌍 V4) 불변.
- Phase02 신층 확인: _ext6_packages/PHASE02_V1_0_x(구미호·김삼순·너목들 등) — cast 위에 맥락 공개(context disclosure) 강화층.

## 2. 편입 실행 (append-only, 매니페스트 규약 준수)
| 패키지 | 내용 | 결과 |
|---|---|---|
| 대장금 EXT6 v1.2.2+Phase02 v1.0.2 (8/3) | 327 files | **cast 54/54회 신설** |
| 돌아온일지매 동형 (8/3) | 170 files | cast 24회 — 구판 v1 → **v1.2.2 갱신** |
| 더킹투하츠 동형 (8/3) | 162 files | **cast 20/20 신설** |
| 대물 동형 (8/3) | 172 files | **cast 24/24 신설** |
| **건빵선생과별사탕** Stage01~04 (BISCUITTEACHER, 8/2) | 341 files | **신규 작품 편입 — 16회** |
| (drive-download 잔여 3종: 검사프린세스·닥터챔프·38사기동대) | — | V24에 기포함 확인, 편입 불요 |

## 3. 편입 후 정본 상태
- **94작 / 1,740회차** (93+건빵선생과별사탕). EXT6 cast 보유 작품: 기존 확산분 + 금회 4작(대장금·대물·더킹투하츠·일지매 v1.2.2).
- 무결성: 각 패키지 SHA256SUMS 동봉본 기준 append-only 적용, Stage01~04 비변경(매니페스트 stage01_04_modified=false 확인). BT 루트 매니페스트는 _stage04_packages/로 격리(DB 루트 오인 방지).
- 후속 기회: 대장금 EXT6 정렬 기록 도착 → 기존 부분 수확(2,960/3,630)의 잔여 670장 해소 후보. 더킹투하츠(85/1,110 부분)도 동일.

**문서 ID**: LOS-DB-SURVEY-INTEGRATE-V1.0-2026-08-03
