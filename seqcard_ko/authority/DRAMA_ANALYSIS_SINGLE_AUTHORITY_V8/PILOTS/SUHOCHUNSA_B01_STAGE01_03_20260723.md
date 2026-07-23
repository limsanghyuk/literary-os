# 수호천사 B01 EP01–08 Stage01–03 검증 메타데이터

- 권위: `DRAMA_ANALYSIS_SINGLE_AUTHORITY_V8`
- 범위: EP01–08
- 상태: `B01_STAGE01_03_PASS_CANDIDATE`
- Stage04: 미착수
- 데이터베이스 편입: 미착수

## 실행 원칙

각 회차를 첫 장면부터 마지막 장면까지 순서대로 직접 독해한 뒤 Stage01→Stage02→Stage03을 완결하고 다음 회차로 이동했다. Q1–Q4 분할은 사용하지 않았다. Python은 추출·직렬화·결정론적 재계산·검증·패키징에만 사용했다.

중단 복구 시 EP02–08의 동일 run source-grounded worksheet를 원문 line/hash에 재연결했다. 같은 작품의 구형 title·intent/action은 저작 입력에서 제외했다.

## 수량

- SceneCard: 556
- SequenceBlueprint: 85
- EpisodeArc: 8
- CharacterArc: 31
- RelationshipArc: 29
- LocalEdge: 34
- PayoffCandidate: 23

## 강검증

- exact schema·JSON parse: PASS
- Scene ordinal·Sequence coverage/partition/runtime/density: PASS
- EpisodeArc act tiling·turning point: PASS
- Character/Relationship trigger FK: PASS
- LocalEdge 동일 회차·target core·ID uniqueness: PASS
- 기존 수호천사 title exact match: 0
- 기존 수호천사 intent exact match: 0
- 원문 24자 이상 연속 복사: 0
- 구조 강검증: PASS
- 의미 강검증: PASS_AFTER_CORRECTION
- ZIP CRC·SHA256SUMS·fresh extraction·portable validator: PASS

## 의미 감사에서 적발·교정한 결함

최초 기계 PASS 뒤 EP06 SC068–081에 EP07의 기차 승차 결과가 앞당겨 섞인 것을 원문 재감사로 발견했다. EP06 실제 회말은 정다소가 플랫폼에 들어가고 하태웅은 개찰구 밖에 남은 상태에서 열차가 움직이기 시작하는 분리 위기다.

다음 항목을 EP06 raw source에서 재저작했다.

- SceneCard 14건
- SequenceBlueprint 3건
- EpisodeArc 1건
- CharacterArc 2건
- RelationshipArc 1건
- LocalEdge 3건

교정 후 구조·의미 강검증을 다시 실행해 오류·경고 0을 확인했다.

## 독립 패키지

- 파일명: `SUHOCHUNSA_V8_B01_STAGE01_03_PASS_CANDIDATE_20260723.zip`
- SHA-256: `ae3eea0edeb69125a9b2b98e4c7914ff0ff49e0b64856cb23ccac92861298d1a`
- 원문 대본과 raw JSONL은 허브에 적재하지 않았다.

## 다음 진입점

EP09 전체 원문 직접독해. EP09–16 Stage01–03과 전 시즌 Stage04가 끝나기 전에는 작품 전체 PASS 또는 데이터베이스 정본 편입으로 간주하지 않는다.
