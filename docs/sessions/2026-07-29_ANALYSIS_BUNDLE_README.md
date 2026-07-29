# seqcard_ko 전체 분석 데이터베이스 — 개발자 배포본 (2026-07-29)

기준: 로컬 정본 `seqcard_ko`, 2026-07-29.

## 1. 이 배포본이 담는 것

| 지표 | 값 |
|---|---|
| 작품 | 90 |
| 회차 | 1,676 |
| SceneCard 씬 | 104,578 |
| 시퀀스 | 15,034 |
| CharArc / RelArc | 10,731 / 9,078 |
| LocalEdge / Payoff | 20,635 / 8,593 |
| CastPresenceRecord (인물등장층) | 41,303 (11작 192회) |
| 인물부하 / 인물명부 | 6,019 / 1,362 |

인물등장층 보유 11작: 101번째프로포즈(15), W(16), 강남엄마따라잡기(18), 개와늑대의시간(16),
개인의취향(15), 결혼못하는남자(16), 경성스캔들(16), 돌아온일지매(24), 비밀의숲(16), 하얀거탑(20), 힐러(20).
잔여 1,484회.

## 2. 이 배포본이 담지 않는 것 — 원문 전면 제외

허브 정책 `hub_boundary: "No raw scripts, source scripts, or full authored JSONL"` 에 따라
**원문 대본을 전부 제거**했다.

| 제외 경로 | 내용 | 규모 |
|---|---|---|
| `seqcard_ko/original_extracted/` | 87작 원문 대본 | 1,644파일 / 97MB |
| `seqcard_ko/source_text/` | 한성별곡 EP01-08 원문 | 8파일 / 0.6MB |
| `seqcard_ko/upgrade_audit/**/incoming_package/original_extracted/` | 수신 패키지 동봉 원문 (오나의귀신님·파리의연인·풍문으로들었소) | 51파일 |

원문은 **집 PC 로컬 전용**이며 이 배포본·허브 어느 쪽에도 실리지 않는다.
원문 대조가 필요한 검증(`verify2.py` 근거 행대조)은 로컬에서만 재현 가능하다.

원문 없이도 재현 가능한 검증: `validate_work.py`, `validate_semantic_quality_v2.py`,
`gate_cast_authored.py` (스키마·그레인·enum·대장 정합).

## 3. 무결성

- `SHA256SUMS_ANALYSIS.txt` — 이 아카이브에 실린 16,062개 파일의 sha256 전건. 아카이브 루트 기준 상대경로.
  - 검증: 압축 해제 후 루트에서 `sha256sum -c SHA256SUMS_ANALYSIS.txt`
- `seqcard_ko/SHA256SUMS.txt` — **원문 포함 로컬 정본 전체 트리**(18,557행)의 매니페스트다.
  이 배포본에는 원문이 없으므로 이 파일로 검증하면 원문 항목이 실패한다. 대조용 참고자료로만 둔다.

## 4. 상태 대장

- `seqcard_ko/DRAMA_ANALYSIS_DATABASE_STATUS_2026-07-29_V18.json` — 90작 전건 회차·씬·인물등장층 보유 현황
- `release_state/package_checkpoint_v18_fulldb_20260729.json` — 이번 릴리스 게이트 결과 전문

## 5. 이번 릴리스 게이트 결과 (전건 통과)

| 게이트 | 대상 | 결과 |
|---|---|---|
| `validate_work.py` | 한성별곡 | PASS 오류 0 / 경고 0 |
| `validate_semantic_quality_v2.py` | 한성별곡 | PASS (경고 1 `CROSS_TARGET_CONCENTRATION_REVIEW:4`) |
| `validate_work.py` | 경성스캔들 | PASS 오류 0 |
| `gate_cast_authored.py` | 인물등장층 전건 192파일 41,303행 | ERRORS 0 / WARNS 1 |
| `verify2.py` 근거 원문 행대조 | 경성스캔들 4,077행 | 행일치 100.00% |

유일한 경고 `CAST-W2 힐러_01 인물없는씬 24/101` 은 Stage01 결함(S70~S90 이 EP02 씬의 중복 등재)에서
비롯된 것으로 저작 품질 문제가 아니다. 미결 정정 대상으로 등록돼 있다.

## 6. 미결 정정 대상 (Stage01)

1. `힐러_01` SceneCard S70~S90 (21건) — EP02 씬의 중복 등재. 정정 시 EP01 실제 씬 101→80
2. `하얀거탑_12` SceneCard 헤딩 S2~S68 — 원문 헤딩이 아니라 줄거리 요약. EP02·06·07·08·15 동종
3. `하얀거탑` EP07 S16 — 원문상 EP08 소재. 회차 분할 오류
4. `authored_chararc` 인명 오기 — 하얀거탑 강동일→염동일, 박민승→함민승. 타 작품 동종 결함 미조사
5. `돌아온일지매_12` 43 vs 48 씬 분기 (장기 미결)

## 7. 압축 해제 후 검증 순서

```
sha256sum -c SHA256SUMS_ANALYSIS.txt
python3 seqcard_ko/tools/current/validate_work.py --root <root> --work <작품>
python3 gate_cast_authored.py seqcard_ko/authored_cast seqcard_ko/authored
```
