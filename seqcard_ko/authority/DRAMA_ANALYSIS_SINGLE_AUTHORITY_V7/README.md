# DRAMA ANALYSIS SINGLE AUTHORITY V7

상태: **ACTIVE / SOLE EXECUTION AUTHORITY**  
버전: 7.0.0  
기준일: 2026-07-23

이 디렉터리는 한국 드라마 대본을 직접 독해하고 Stage 01–04 산출물을 저작·검사·패키징하는 단일 권위다.

## 읽기 순서
1. `01_EXECUTION_PROTOCOL.md`
2. `02_SCHEMA_CONTRACTS.md`
3. `03_VALIDATION_AND_RELEASE.md`
4. `04_NEW_SESSION_BOOTSTRAP.md`
5. `AUTHORITY_MANIFEST.json`

## 절대 원칙
- 대본을 직접 읽고 이해한 뒤 저작한다. 줄거리 사이트·기존 산출물·다른 작품의 수량 패턴을 대체 근거로 사용하지 않는다.
- 전체 회차를 최대 8회 단위의 연속 블록으로 나누어 앞 블록부터 순서대로 처리한다.
- Stage01→Stage02→Stage03은 회차별로 누적 저작하고, Stage04는 전 블록 완료 후 전 시즌 후보·인과·아크를 다시 감사해 저작한다.
- 자동 검사 PASS, 원문 근거 PASS, 패키지 재현 PASS를 분리한다.
- 고정 수량을 목표로 하지 않는다. 모든 수량은 원문이 결정한다.

이 패키지와 과거 문서·검사기·예시가 충돌하면 이 패키지가 우선한다. 실제 데이터가 이 계약과 다르면 자동 변환하지 말고 `MIGRATION_REQUIRED`로 판정한다.
