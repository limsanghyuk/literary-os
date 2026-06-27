# corpus_ko 재분할 → 정본 승격 (2026-06-27)

class4 그라인드(205편 무손실 재분할) 종료 후, 재분할 경계를 corpus_ko 6-스토어
정본으로 승격하기 위한 CPU-완결 스테이징 + 집(GPU/API) 적용 도구 일습.

## 한 줄 요약
재분할 205편을 corpus_ko 정본으로 올리는 전 과정 중 **CPU 가능 단계 전부를
무손실·패리티 검증까지 끝내 STAGING 적재**. 남은 단일 게이트는 임베딩
(text-embedding-3-small, OpenAI) = 집/API 단계. 정본 corpus_ko는 이 세션에서
일절 미변경(무결성 인증 보존).

## 실측 (205/205 PASS, 실패 0)
- 씬: 5,340 → 15,493 (x2.90)
- 재임베딩 필요(신규 씬 chunk): 10,774
- 폐기(stale 씬 id): 3,550 / 재사용(불변 씬 id): 5,357
- **slide 임베딩 100% 불변** — 재분할은 nospace-무손실이고 승격은 바이트-정확
  원본 전체본문에 경계를 재매핑하므로 `"".join(scene.text)`가 바이트 동일.
  slide chunk는 전체본문 char-offset 슬라이딩 → 경계 이동 무관.

## 파일
- `promote_stage.py` — STAGING 빌더(경계 재매핑 + chunk 재생성, 무손실 게이트 내장). CPU.
- `promote_apply.py` — 집 적용 오케스트레이터: backup / swap / prune / verify.
- `glue_split.py`, `residual_split.py` — END-GLUED 영화/잔여 메가블록용 char-offset 분할기.
- `class4_disposition.json` — 203 적용 + 8 처분(=211 class4 전수) 사유 기록.
- `resplit_verification_summary.json` — 재분할 무손실 검증 요약.
- `PROMOTION-HANDOFF-v1.md` — 6-스토어 의존성 사슬 + 집 실행 순서 + 롤백/안전.
- `RESPLIT-PIPELINE-DESIGN-v1.md` — 재분할 파이프라인 설계.

## 집 실행 순서 (PROMOTION-HANDOFF-v1.md 참조)
backup → swap → embed.py(증분, 신규 씬 id만) → prune(stale 제거) →
features.py → nkg.py → rebuild_chroma_local.py → verify(MISSING=0, ORPHAN=0).

주의: **swap → embed 순서 엄수**(embed는 swap된 chunks에서 신규 id 선별).
정본 무결성 인증은 재임베딩 완료 시점에 복원되며, 그 전엔 STAGING만 존재.

## 비-푸시 산출물 (C:\claude 로컬 보관)
`scenes_resplit/*.resplit.jsonl`(205, 6.4M)·`promotion_staging/{scenes,chunks}`은
코퍼스 대용량 데이터로 허브 미적재(허브는 corpus 벌크 미보유, 집 재빌드 원칙).
