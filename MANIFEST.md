# MANIFEST — Literary OS V604

버전: 10.11.0
릴리즈일: 2026-05-22
빌드 타입: Phase B SP-B.2 완료 — CanonicalBridgeV2 + Gate G56 + G57 (V606, ADR-066)

## 테스트 결과

| 항목 | 값 |
|------|----|
| PASS | 6,382+ |
| FAIL | 0 |
| SKIP | 2 (REAL LLM — API 키 없을 시) |
| 릴리즈 게이트 | **56/56 PASS** |
| Phase A 기준 대비 신규 | +200 (V595.2 기준 6,182 + 46) |

## 릴리즈 게이트 현황

| Gate | 검증 항목 | 버전 | 상태 |
|------|-----------|------|------|
| G01~G46 | 기존 V581~V587 게이트 | — | ✅ PASS |
| G47 | QueryInterface + Qdrant | V588 | ✅ PASS |
| G48 | BackendHealthMonitor + HybridRetrieverV2 | V589 | ✅ PASS |
| G49 | GPUAdapterContract + CostSLO | V590 | ✅ PASS |
| G50 | EquivalenceTester 5축 + 골든셋20 | V591 | ✅ PASS |
| G51 | LOSConstitution v1.0 (5축 가중합) | V594 | ✅ PASS |
| G52 | Phase A Exit Gate (EA-1~EA-6) | V595 | ✅ PASS |
| G53 | LoRA Inference Gate (레이턴시≤2초 + 100자+) | V598 | ✅ PASS |
| G54 | Fine-tuning Pipeline Gate (7CP 수직 통합) | V600 | ✅ PASS |
| G55 | PPO Stability Gate (KL≤0.08 + ConstraintGuard + PPOResult) | V604 | ✅ PASS |
| G56 | RLHF Reward Gate (mean_reward≥0.75, delta≥0.05) | V606 | ✅ PASS |
| G57 | Constitution Axis Gate (5축 Pearson≥0.80) | V606 | ✅ PASS |
| **합계** | | | **56/56 ALL PASS** |

## Phase B SP-B.1 산출물 (V596~V599)

### V596 — LoRA Dataset Pipeline + Governance (ADR-056)
| 파일 | 설명 |
|------|------|
| `literary_system/finetune/lora_dataset_builder.py` | Alpaca JSONL 빌더 + sha256 |
| `literary_system/finetune/dataset_splitter.py` | 8:1:1, seed=42 |
| `literary_system/finetune/dataset_registry.py` | DVC + sha256 검증 |
| `literary_system/governance/provenance_ledger.py` | sha256 체인 immutable |
| `literary_system/governance/dsr_handler.py` | GDPR/PIPA 30일 SLA |
| `docs/adr/ADR-056.md` | LoRA 데이터셋 포맷 결정 |

### V597 — LoRA Training Config + Job Runner + TrainPlane Helm (ADR-057)
| 파일 | 설명 |
|------|------|
| `literary_system/finetune/lora_training_config.py` | rank=16, alpha=32, q/k/v/o_proj |
| `literary_system/finetune/lora_job_runner.py` | 격주 $48 + 주간 $48 = 월 $96 SLO |
| `deploy/helm/train_plane/` | TrainPlane Helm 격리 |
| `docs/adr/ADR-057.md` | LoRA 학습 설정 + GPU 격리 |

### V598 — LoRAArtifact + Registry + Inference Gateway + Gate G53 (ADR-058)
| 파일 | 설명 |
|------|------|
| `literary_system/finetune/lora_artifact.py` | safetensors 3-tag + sha256 |
| `literary_system/finetune/lora_model_registry.py` | CANDIDATE→VALIDATED→PROMOTED |
| `literary_system/finetune/lora_inference_gateway.py` | LLM-1 PROMOTED 전용 서빙 |
| `literary_system/gates/lora_inference_gate.py` | Gate G53 (8체크포인트) |
| `docs/adr/ADR-058.md` | LoRA 추론 게이트웨이 계약 |

### V599 — PreTrainSafety + FineTuneEvalPipeline + LongContextStrategy (ADR-059)
| 파일 | 설명 |
|------|------|
| `literary_system/finetune/pre_train_safety.py` | PII/Toxic/Copyright/Quality 4축 |
| `literary_system/finetune/finetune_eval_pipeline.py` | BERTScore + LLM-judge + Style + BLEU + Equiv |
| `literary_system/finetune/long_context_strategy.py` | 100K청크 + 16K오버랩 + NKG RAG |
| `docs/adr/ADR-059.md` | 파인튜닝 평가 기준선 |

## Phase A 완료 기준선 (V595.2 고정)

| 항목 | 값 |
|------|----|
| 버전 | v10.0.2 (V595.2) |
| Gates | 51/51 PASS |
| Tests | 6,182 collected |
| SHA256 | 932 files, 0 mismatch |
| ADR | ADR-001~055 |
| CI | GREEN |

## 아키텍처 제약 (영구)

| 원칙 | 내용 |
|------|------|
| LLM-0 | corpus/, constitution/, finetune/ 외부 LLM 직접 호출 금지 (ADR-031) |
| LLM-1 | LoRA 학습 모델: finetune/ 내부 + PROMOTED 단계만 서빙 허용 (ADR-058) |
| DEV_MODE | 항상 "false" 기본 (ADR-034) |
| Preflight | 매 버전 진입 전 15단계 필수 |


### V601 — RewardModel v1.0 + ADR-061 (SP-B.2 시작)
- `literary_system/rlhf/reward_model.py`: MARKER_WEIGHT_CAP=0.20, 적대적 시드 5종, quality_correlation()
- `tests/unit/test_v601_reward_model.py`: 8 TC PASS
- 테스트 6,390+ PASS

### V600 — Gate G54 + ADR-060 + finetune_ci.yml (SP-B.1 완료)
| 파일 | 설명 |
|------|------|
| `literary_system/gates/lora_finetuning_gate.py` | Gate G54 (7체크포인트 수직 통합) |
| `.github/workflows/finetune_ci.yml` | 격주 파인튜닝 CI (B-M-06) |
| `docs/adr/ADR-060.md` | Fine-tuning Pipeline Gate + 모델 적합성 확정 |


## SP-B.1 완료 선언 ✅

| 조건 | 상태 |
|------|------|
| Gate G53 PASS (추론 레이턴시 + 100자+) | ✅ V598 |
| Gate G54 PASS (7CP 수직 통합) | ✅ V600 |
| 테스트 6,382+ PASS (V595.2 기준 +200) | ✅ V600 |
| LoRAArtifact 3-tag sha256 무결성 | ✅ ADR-058 |
| 월 GPU SLO $96 정책 확립 | ✅ ADR-057 |
| 베이스 모델 3종 호환성 확인 | ✅ ADR-060 |

**SP-B.2 (V601~, RLHF 루프) 진입 가능.**

