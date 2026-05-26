# CHANGELOG V637 — ConstitutionEvalV2 (2026-05-26)

## 버전: v11.7.0

## 신규
- `literary_system/constitution/constitution_eval_v2.py` (274줄)
  - EvalDimension, EvalScore, EvalResult dataclass
  - ConstitutionEvalV2: 5축 멀티 채점 + JSONL 영속화
  - EVAL_THRESHOLD = 0.70, DEFAULT_DIMENSION_NAMES 5축
  - evaluate() / batch_evaluate() / history() / pass_rate()
- `tests/unit/test_v637_constitution_eval_v2.py` (321줄, 33/33 PASS)
- `docs/adr/ADR-079.md`

## 보강
- `literary_system/finetune/lora_artifact.py`: constitution_weights_version 필드 추가 (C-M-06)
- `literary_system/constitution/__init__.py`: ConstitutionEvalV2 API 공개

## 지표
- Gates: 61/61 PASS
- Tests: 7,445 total
