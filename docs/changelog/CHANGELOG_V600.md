# CHANGELOG V600 — v10.5.0

**버전**: v10.5.0 | **날짜**: 2026-05-22 | **Phase**: B SP-B.1 완료

## 🎯 SP-B.1 완료 선언 (V596~V600)

Gate G53 + G54 PASS, 53/53 Gates, 6,382+ PASS — SP-B.2 진입 가능.

---

## 신규 모듈 (3종)

### `literary_system/gates/lora_finetuning_gate.py`
- `gate_lora_finetuning()` — Gate G54 7체크포인트 수직 통합 (ADR-060)
  - G54-1: PreTrainSafety 4축 차단 검증
  - G54-2: LoRADatasetBuilder JSONL + sha256
  - G54-3: DatasetSplitter 8:1:1 seed=42 재현성
  - G54-4: ProvenanceLedger sha256 체인 무결성
  - G54-5: LoRAJobRunner dry_run() JobRunRecord
  - G54-6: LoRAArtifact 3-tag tag_string 포맷
  - G54-7: FineTuneEvalPipeline 5축 임계 PASS

### `.github/workflows/finetune_ci.yml`
- 격주 월요일 02:00 KST 자동 실행 (B-M-06)
- Gate G54 포함 + SP-B.1 단위 테스트 일괄 실행
- `workflow_dispatch` 수동 트리거 지원

### `docs/adr/ADR-060.md`
- Fine-tuning Pipeline Gate G54 설계 결정
- 베이스 모델 3종 적합성 확정
- SP-B.1 완료 조건 6항목 명시

---

## 모델 적합성 갱신 (V600)

### `literary_system/finetune/lora_training_config.py`
- `LLAMA32_LITE_MODEL` 상수 추가: `meta-llama/Llama-3.2-3B-Instruct`
- `llama32_lite()` classmethod 추가: rank=8, NF4, VRAM≤8GB 환경용
- 호환성 요구사항 명시: transformers≥4.44, peft≥0.12, trl≥0.9, bitsandbytes≥0.43
- `exaone_candidate()` docstring 갱신

### `pyproject.toml`
- `[finetune]` optional-deps 그룹 추가
  - transformers≥4.44.0, peft≥0.12.0, trl≥0.9.0, bitsandbytes≥0.43.0
  - datasets≥2.18.0, accelerate≥0.30.0, safetensors≥0.4.2, sentencepiece≥0.2.0

---

## 문서 일치화 (V598~V599 누락 수정)

| 항목 | 수정 전 | 수정 후 |
|------|---------|---------|
| README H1 | V596 | V600 |
| README version badge | 10.2.0 | 10.5.0 |
| README Gates badge | 51/51 | 53/53 |
| README Tests badge | 6225 | 6382 |
| pyproject description | V598 / 52 Gates | V600 / 53 Gates |
| MANIFEST version | 10.0.3 | 10.5.0 |
| MANIFEST Gates | 51/51 | 53/53 |
| RELEASE_INFO | V597 / 10.2.0 | V600 / 10.5.0 |
| CHANGELOG latest | 10.2.0 | 10.5.0 |

---

## ADR
- `docs/adr/ADR-060.md` — Fine-tuning Pipeline Gate + 베이스 모델 3종 적합성

## 테스트
- `tests/unit/test_v600_finetuning_gate.py` — 21 TC (TC-A~F)
- 누적: 6,382+ PASS (V595.2 기준 +200 달성)

## Gate
- Gate G54: 7/7 체크포인트 PASS
- 누적 53/53 PASS (release_gate.py 등록 완료)

## 릴리즈
- v10.5.0 / V600 / SP-B.1 완료
- 다음: SP-B.2 (V601~, RLHF 루프 — RewardModel + PPOTrainer + Gate G55)
