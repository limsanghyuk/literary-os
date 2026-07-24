# 개발자 인계서

## 권위

- Authority: `DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10`
- Version: `10.0.0`
- Status: `ACTIVE_SINGLE_AUTHORITY`
- Master: `DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10.md`

## 개발자 작업 순서

1. 루트 포인터가 V10을 가리키는지 확인
2. master와 manifest hash 확인
3. schema·validator contract drift 검사
4. acceptance suite 메타데이터 확인
5. 새 분석은 bootstrap 문서로 시작

## Acceptance suite

- 수호천사: 기존판 오염·미래 정보 혼입·Stage04 재저작
- 눈이 부시게 EP01: 번호 없는 물리 장면 누락과 부분 원본 차단
- 질투의 화신: 신규 완전 원본 선정, HWP 추출, 24부작 Stage01–04, DB 신규 편입, ZIP 호환

## 허브에 올리지 않는 것

- 원본 대본
- 전체 raw 의미 JSONL
- 장문 대사
- embedding·비밀키

## 변경 관리

의미 규칙을 바꾸면 master를 먼저 수정한다. 그다음 schema·tool·template·manifest·acceptance report 순으로 갱신한다. 사용자 승인 없이 CANONICAL로 승격하지 않는다.
