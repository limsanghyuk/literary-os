# MANIFEST V634

## 산출물

| 항목 | 값 |
|------|-----|
| 버전 | v11.4.0 |
| Commit | (pending) |
| Gates | 60/60 PASS |
| Tests | 7,346 total |
| ADR | ADR-076 |

## 신규 구현물

### RetrainingScheduler
- `schedule()` — drift 확인 후 재학습 스케줄 등록
- `should_retrain(current_f1, baseline_f1)` → (bool, reason)
- `history()` / `last_scheduled()` / `count()` / `clear()`
- `DRIFT_THRESHOLD = 0.03`, `MIN_INTERVAL_DAYS = 7`
- JSONL 영속화 + 메모리 모드(`:memory:`)
- `force=True` 강제 스케줄 옵션
