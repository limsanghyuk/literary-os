# CHANGELOG V598 — Phase B SP-B.1 LoRAArtifact + LoRAModelRegistry + LoRAInferenceGateway

**버전**: v10.3.0  
**날짜**: 2026-05-21  
**커밋**: (pending)  
**Gates**: 52/52 PASS  
**Tests**: 6225+ PASS  

---

## 신규 파일

| 파일 | 설명 |
|------|------|
| `literary_system/finetune/lora_artifact.py` | LoRAArtifact 3-tag 아티팩트 계약 (B-M-03, ADR-058) |
| `literary_system/finetune/lora_model_registry.py` | LoRAModelRegistry 체크포인트 버전 관리 |
| `literary_system/finetune/lora_inference_gateway.py` | LoRAInferenceGateway LLMBridgeInterface 확장 |
| `literary_system/gates/lora_inference_gate.py` | Gate G53 (8체크포인트) |
| `docs/adr/ADR-058.md` | LoRA 추론 게이트웨이 계약 설계 결정 |
| `tests/unit/test_v598_lora_inference.py` | 14 TC PASS |

## 수정 파일

| 파일 | 변경 내용 |
|------|-----------|
| `literary_system/gates/release_gate.py` | Gate G53 등록 (52 Gates) |
| `literary_system/finetune/__init__.py` | V598 신규 심볼 export |
| `literary_system/finetune/lora_artifact.py` | verify_integrity(): 빈 artifact_path 처리 수정 |
| `pyproject.toml` | version 10.2.0 → 10.3.0 |
| `README.md` | 버전 배지 V598/v10.3.0/52 Gates 갱신 |

## 핵심 구현

### LoRAArtifact (B-M-03 3-tag)
- `ArtifactStage`: PENDING/CANDIDATE/VALIDATED/PROMOTED/RETIRED/CORRUPTED
- `LoRAArtifactContract`: 추상 계약 (seed_tag/commit_tag/dataset_sha_tag)
- `verify_integrity()`: sha256 체크섬 검증, 빈 경로 hex 형식 검증
- `save_manifest()` / `load_manifest()`: 무결성 자동 검증

### LoRAModelRegistry
- 5단계 수명주기: CANDIDATE → VALIDATED → PROMOTED (LLM-1 원칙)
- `promote()`: 기존 PROMOTED 자동 RETIRED 전환
- `RegisterConflictError` / `StageTransitionError`: 잘못된 전환 차단
- JSON 영속화 (`lora_model_registry.json`)

### LoRAInferenceGateway
- `LLMBridgeInterface` 확장: `provider_name = "lora_local"`
- `StubInferenceBackend`: HAS_TRANSFORMERS=False CI 환경 지원
- `InferenceResult.passes_g53`: latency_ms ≤ 2000 AND len(text) ≥ 100
- PROMOTED 없으면 `RuntimeError` (LLM-1 원칙 집행)

### Gate G53 (8체크포인트)
- G53-1: 임포트 성공
- G53-2: PROMOTED + is_available()
- G53-3: latency_ms ≤ 2000
- G53-4: len(text) ≥ 100
- G53-5: provider_name == "lora_local"
- G53-6: 3-tag 무결성
- G53-7: CORRUPTED 추론 차단
- G53-8: passes_g53 복합 조건

## 테스트

```
TC-A1~A3+A3b: LoRAArtifact 3-tag + sha256 + manifest roundtrip
TC-B1~B3+B3b: LoRAModelRegistry 수명주기 + JSON 영속화
TC-C1~C3+C3b: LoRAInferenceGateway stub 추론 + G53 합격
TC-D1~D2: Gate G53 통합 (8/8 PASS + release_gate 등록)
```

14 TC PASS (목표 11 TC 초과 달성)

## 다음 단계 (V599~V600)

- V599: PreTrainSafetyGate (Pre-train Safety 검증)
- V600: FinetuningGate (G54) + SP-B.1 Exit + Llama/EXAONE A/B 비교
