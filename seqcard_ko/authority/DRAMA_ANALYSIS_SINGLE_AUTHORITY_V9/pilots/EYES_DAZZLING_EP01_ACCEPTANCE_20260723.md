# 〈눈이 부시게〉 EP01 V9 권위 수용 파일럿

- 권위: `DRAMA_ANALYSIS_SINGLE_AUTHORITY_V9`
- 작품 분류: `NEW_ANALYSIS`
- 범위: EP01 Stage01–03 only
- 상태: `EP01_STAGE01_03_PASS_CANDIDATE_SOURCE_PARTIAL`
- 전 시즌 상태: 원본 완전성 미확인으로 EP02 확대·Stage04·FullSeriesArc 차단

## 실측 수량

- SceneCard: 64
  - 번호 장면: 56
  - 번호 없는 물리 전환·외경 장면: 8
- SequenceBlueprint: 10
- EpisodeArc: 1
- CharacterArc: 3
- RelationshipArc: 3
- LocalEdge: 8
- PayoffCandidate: 5

## 최초 실패와 교정

최초 인덱서는 숫자가 있는 `씬/NN`만 장면으로 잠가 56장면을 만들었다. 저작 실행과 분리된 독립 원문 감사에서 `거리전경`, `혜자집 외경`, `산 또는 바다 전경` 등 번호 없는 물리 표제 8개가 앞 장면에 합쳐진 사실을 발견했다.

이를 ordinal만 고치는 결정론적 보정으로 처리하지 않고 SourceIndex·SourceLock·Stage01·EpisodeMeta·Stage02·Stage03의 모든 종속 참조를 새 author run으로 다시 잠갔다.

## 실행 분리

- author run: `eyes-dazzling-v9-author-correction-20260723`
- audit run: `eyes-dazzling-v9-independent-audit-20260723`
- source reopened: true
- scene review: 64/64

## 검증

- STRUCTURAL_CONTRACT_PASS: PASS
- SEMANTIC_MECHANICAL_PASS: PASS
- SOURCE_GROUNDED_MANUAL_PASS: PASS
- PACKAGE_FRESH_EXTRACTION_PASS: PASS
- 원문 24자 이상 연속 복사: 0
- title·intent exact duplicate: 0
- Sequence coverage·partition 오류: 0
- trigger·edge FK 오류: 0
- 고정 수량 Arc: 없음
- Stage04 미실행: 원본 완전성 차단에 따른 정상 동작

## 권위 acceptance 판정

V9는 파일럿 첫 시도를 그대로 승인하지 않았다. SourceFormatAudit와 독립 감사가 실제 장면 경계 누락을 찾아 fail-closed로 중단했고, 종속 계층 전부를 재저작한 뒤에만 EP01 PASS_CANDIDATE를 허용했다.

이 파일럿은 다음 규칙의 실행 증거다.

1. 물리 장면 경계는 숫자 마커만으로 확정하지 않는다.
2. 저작과 감사는 다른 run이어야 한다.
3. 구조 PASS 뒤에도 원문 의미 감사가 실패를 발견할 수 있다.
4. 부분 원본은 회차 파일럿만 허용하고 Stage04·FullSeriesArc를 차단한다.
5. 권위 문서는 규칙 선언이 아니라 실제 실패를 차단해야 한다.

독립 파일럿 ZIP: `EYES_DAZZLING_V9_EP01_STAGE01_03_ACCEPTANCE_PILOT_20260723.zip`  
SHA-256: `e05d492d5d175d61d990700d61e89de3d924660d80efec0f61f60d9869b60c30`
