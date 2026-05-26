# CHANGELOG — V641 (v11.12.0)

**릴리즈일**: 2026-05-26
**태그**: v11.12.0
**ADR**: ADR-101

## 개요
SP-C.1 MetaLearner 4사이클 중 1차.
Constitution v2.0 §A1: R(scene)≥0.78, Krippendorff α≥0.70.

## 신규 모듈
- `literary_system/constitution/krippendorff_alpha.py` — KrippendorffAlpha (coincidence matrix)
- `literary_system/constitution/meta_learner_cycle.py` — MetaLearnerCycle 4사이클 래퍼

## 신규 문서
- `docs/adr/ADR-101.md`

## 신규 테스트
- `tests/unit/test_v641_meta_learner_cycle.py` — 33 TC (33/33 PASS)

## test_inventory
7610 TC (+33)
