# 새 세션 부트스트랩

## 1. 처음 읽을 파일

- `DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10.md`
- `AUTHORITY_MANIFEST.json`
- 이 문서

## 2. 대상 작품 시작 전

- 최신 DB 작품 목록과 후보 대조
- 전 회차·최종회 존재 확인
- 원본 파일 SHA와 추출 텍스트 SHA 생성
- 회차별 길이·장면 수 이상치 확인
- 중복 최종고와 수정 조각 분리
- 삭제·삽입·번호 없는 장면 감사
- SourceLock과 canonical scene map 생성
- 기존 작품이면 SameWorkLegacyLock 활성화

## 3. 회차 실행

```text
원본 전체 순차 독해
→ Stage01
→ EpisodeMeta
→ Stage02
→ Stage03
→ 경량 검사
→ 독립 원문 감사
→ 체크포인트
```

20분 준비, 25분 저장, 30분 무저장 하드스톱.

## 4. 블록과 전 시즌

- 최대 8회차 블록 강검증
- 전 회차 Stage01–03 잠금 뒤 Stage04
- 후보 100% 처분
- 보수적인 CrossEpisodeEdge
- FullSeriesArc
- 독립 ZIP과 fresh extraction
- DB 신규 추가 또는 작품 단위 교체

## 5. 금지

- Python 의미 생성
- 기존 대상 작품 의미문 선열람
- 자동 회차 경계 bridge
- 복합 인물 관계 엔터티
- 최종회 집결만으로 장거리 회수 승격
- 파일 미저장 상태를 완료로 보고
