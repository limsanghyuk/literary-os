# 운영 런북

## 회차 체크포인트

1. source index와 SceneCard 수량 일치
2. JSON/JSONL parse
3. Sequence coverage·runtime
4. Arc trigger 참여자
5. LocalEdge target core
6. 독립 audit run 기록
7. `.tmp` → atomic rename
8. SHA·work_state·journal 갱신

## 중단 복구

- 마지막 `CHECKPOINT_LOCKED`를 찾는다.
- 사용자 보고가 아니라 실제 파일·SHA를 기준으로 상태를 판정한다.
- audit 미완료면 의미 PASS를 철회한다.
- 복구 원장에 유실 범위와 다음 포인터를 남긴다.

## ZIP 릴리스

- ASCII 최상위 폴더
- UTF-8 filename flag
- path traversal·symlink 0
- 내부 최장 경로 권장 180자 이하
- CRC PASS
- 새 빈 경로에 전량 해제
- 파일 수·SHA256SUMS·portable validator PASS

## DB 편입

- 실제 DB root와 작품 수 확인
- 신규 작품인지 기존 작품인지 분기
- 기존 파일 덮어쓰기 검사
- 전역 index 새 버전 생성
- 전체 JSON/JSONL parse
- 전역 count와 fresh extraction
