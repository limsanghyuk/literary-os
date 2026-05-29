# CHANGELOG — V731 (v12.5.0)

## Summary
SP-D.4 착수: G86 API Completeness Gate 신설, DEFECT-2 수정

## Gates
- **G86** `api_completeness_g86` — API Completeness Gate A1~A6 (ADR-193) — 6/6 PASS
  - A1: Router 등록 검증 (6+ 라우터)
  - A2: 엔드포인트 파일 존재 검증 (5 router .py)
  - A3: Bearer 인증 미들웨어 검증
  - A4: 페이지네이션 패턴 검증 (limit/offset)
  - A5: 에러 응답 포맷 검증 (HTTPException/detail)
  - A6: Rate-limit 헤더 검증 (RateLimitBucket)

## ADRs
- **ADR-193**: G86 API Completeness Gate 신설 — DEFECT-2 수정 (docs/adr/ADR-193.md)

## Tests
- `tests/unit/test_v731_api_completeness.py` — 50 TC PASS (0.42s)
- TC count: 10,344 (10,294 + 50)

## DEFECT 수정
- DEFECT-2: G86 완전 부재 → api_completeness_gate.py 신설 + GATES 등록 완료

## Version
- v12.4.0 → v12.5.0
