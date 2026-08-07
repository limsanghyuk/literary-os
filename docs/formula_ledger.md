# Formula Lifecycle Ledger

| timestamp | formula_id | event | lifecycle | evidence_path |
|-----------|------------|-------|-----------|---------------|
| 2026-08-08 | sequence_planner.AVG_SEQUENCE_DURATION_MIN | recalibrate 11.0→7.26 | active | docs/measurement/SEQUENCE-PLANNER-RECALIBRATION-2026-08-08.md |
| 2026-08-08 | sequence_planner.SEQ_TYPE_BASE_SCENE_DUR | recalibrate mean 3.0→1.03 (×0.3437) | active | docs/measurement/SEQUENCE-PLANNER-RECALIBRATION-2026-08-08.md |
| 2026-08-08 | sequence_planner._calc_seq_count.clamp | widen [3,8]→[5,18] (정본 p1–p99) | active | docs/measurement/SEQUENCE-PLANNER-RECALIBRATION-2026-08-08.md |
| 2026-08-08 | sequence_planner._calc_scene_count.clamp | widen [2,8]→[2,14] (정본 p1–p99) | active | docs/measurement/SEQUENCE-PLANNER-RECALIBRATION-2026-08-08.md |
| 2026-08-08 | sequence_planner.docstring:실측한국드라마기준 | **retract** (출처불명·정본과 3배 괴리) | retracted | docs/measurement/SEQUENCE-PLANNER-RECALIBRATION-2026-08-08.md |
| 2026-08-08 | sequence_planner.SEQ_TYPE_DURATION_RANGE | no-op (정규화로 스케일 불변) | active | docs/measurement/SEQUENCE-PLANNER-RECALIBRATION-2026-08-08.md |
