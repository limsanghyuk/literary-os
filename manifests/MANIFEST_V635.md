# MANIFEST V635

| 항목 | 값 |
|------|-----|
| 버전 | v11.5.0 |
| Gates | 61/61 PASS (G62 신규) |
| Tests | 7,379 total |
| ADR | ADR-077 |

## AutoPromotionGate G62
- `evaluate(scene_scores, rollback_count)` → GateResult
- `R_THRESHOLD=0.78`, `MAX_ROLLBACKS=0`
- JSONL 영속화 + 메모리 모드
- `history()` / `last_result()` / `count()` / `clear()`
