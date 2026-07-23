# V8 → V9 변경 요약 (비규범)

- Q1–Q4 필수 규칙 제거: 한 회차 전체가 의미 저작 단위, quarter는 선택적 읽기 보조.
- 45분 규칙을 20분 경고 / 25분 체크포인트 / 30분 무저장 하드스톱으로 강화.
- atomic write, RunJournal, stale-state, recovery contract 추가.
- SourceFormatAudit와 원본 완전성 상태 추가.
- author attestation과 independent manual audit 분리 강화.
- SameWorkLegacyLock과 구판-신판 품질 비교 계약 추가.
- 수호천사에서 발견한 미래 정보 혼입·자기감사·부분 DB 오인 반례를 acceptance test로 편입.
- 하나의 마스터 문서만 의미 권위로 고정.
