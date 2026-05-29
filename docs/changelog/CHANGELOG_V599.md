# CHANGELOG V599 — v10.4.0

**버전**: v10.4.0 | **날짜**: 2026-05-21 | **커밋**: TBD

## 신규 모듈 (3종)

### `literary_system/finetune/pre_train_safety.py`
- `PreTrainSafety` — 4축 학습 전 데이터 안전성 검사 (B-M-09)
  - Axis-1 PII: 주민등록번호·전화·이메일·계좌·여권 정규식 탐지
  - Axis-2 Toxic: 혐오·욕설·위험 키워드 패턴 차단
  - Axis-3 Copyright: verbatim 50자 이상 구절 비율 검사 (≤30%)
  - Axis-4 Quality: 최소 50자 / 반복비율≤0.40 / 공백비율≤0.60
- `filter_safe()` — 배치 필터링, `summary()` — 통계 리포트

### `literary_system/finetune/finetune_eval_pipeline.py`
- `FineTuneEvalPipeline` — 5축 평가 파이프라인 (B-M-07)
  - BERTScore F1 ≥ 0.85 (n-gram 근사, LLM-0 준수)
  - LLM-judge ≥ 4.0 (다양성·키워드 스텁)
  - Style ≥ 0.80 (문장 길이 분포 + TTR)
  - BLEU-4 ≥ 0.30 (smoothing)
  - Equiv rate ≥ 0.95 (EquivalenceTester 근사)
- `compute_krippendorff_alpha()` — Krippendorff α ≥ 0.70 (B-M-08)

### `literary_system/finetune/long_context_strategy.py`
- `LongContextStrategy` — 100K 청크 + 16K 오버랩 (B-M-11)
  - 자연 경계 정렬 (단락 → 개행 → 문장 부호)
  - NKG RAG 컨텍스트 주입 지원
  - `iter_chunks()` 제너레이터 + `summary()` 통계

## ADR
- `docs/adr/ADR-059.md` — 파인튜닝 평가 기준선 + 안전성 + 장문 전략

## 테스트
- `tests/unit/test_v599_pretrain_safety.py` — 17 TC PASS

## 수치
- 테스트: 6,228+ PASS (V598 기준 6,211 + 17 신규)
- Gate: 52/52 유지
- 버전: v10.3.0 → v10.4.0
