"""
SP-B.1 (V598) — Gate G53: LoRA 추론 게이트

Phase B 본안 보강 (ADR-058):
- LoRAInferenceGateway + LoRAModelRegistry 통합 검증
- G53-1: PROMOTED 아티팩트 존재 + ArtifactStage 무결성
- G53-2: 추론 레이턴시 ≤ 2000ms (stub 모드 포함)
- G53-3: 응답 길이 ≥ 100 chars
- G53-4: 3-tag 무결성 (seed_tag 정수 + commit_tag 7자 + dataset_sha_tag 32자 hex)
- G53-5: provider_name == 'lora_local'

LLM-0 원칙: 이 게이트는 외부 LLM API를 직접 호출하지 않음.
"""
from __future__ import annotations

from typing import Any, Dict


def _gate_lora_inference_g53() -> Dict[str, Any]:
    """
    Gate G53: LoRA 추론 게이트 (SP-B.1, V598, ADR-058).

    체크포인트:
        G53-1: LoRAModelRegistry + LoRAInferenceGateway 임포트 성공
        G53-2: PROMOTED 아티팩트 등록·승격 후 is_available() == True
        G53-3: stub 추론 latency_ms ≤ 2000
        G53-4: stub 추론 응답 길이 ≥ 100 chars
        G53-5: provider_name == 'lora_local'
        G53-6: 3-tag 무결성 (seed_tag int, commit_tag 7자, dataset_sha_tag 32자 hex)
        G53-7: ArtifactStage.CORRUPTED 시 추론 차단 (RuntimeError)
        G53-8: InferenceResult.passes_g53 latency+length 복합 조건
    """
    checks: Dict[str, bool] = {}
    errors = []

    # G53-1: 임포트
    try:
        from literary_system.finetune.lora_artifact import ArtifactStage, make_artifact
        from literary_system.finetune.lora_inference_gateway import (
            G53_LATENCY_LIMIT_MS,
            G53_MIN_LENGTH,
            LORA_PROVIDER_NAME,
            LoRAInferenceGateway,
        )
        from literary_system.finetune.lora_model_registry import (
            LoRAModelRegistry,
        )
        checks["G53-1"] = True
    except Exception as e:
        checks["G53-1"] = False
        errors.append(f"G53-1 import: {e}")
        return _build_result(checks, errors)

    # G53-2: PROMOTED 아티팩트 존재 + is_available()
    try:
        reg = LoRAModelRegistry()
        artifact = make_artifact(
            base_model="meta-llama/Llama-3.1-8B",
            lora_rank=16,
            seed_tag=42,
            commit_tag="abcdef1",
            dataset_sha_tag="a" * 32,
        )
        reg.register(artifact)
        reg.promote(artifact.artifact_id)   # CANDIDATE → VALIDATED
        reg.promote(artifact.artifact_id)   # VALIDATED → PROMOTED
        gw = LoRAInferenceGateway(registry=reg, stub_mode=True)
        assert gw.is_available(), "is_available() == False"
        checks["G53-2"] = True
    except Exception as e:
        checks["G53-2"] = False
        errors.append(f"G53-2 is_available: {e}")
        return _build_result(checks, errors)

    # G53-3: latency ≤ 2000ms
    try:
        result = gw.infer("드라마 장면을 생성하세요. 두 인물이 대화를 나누는 장면.")
        assert result.latency_ms <= G53_LATENCY_LIMIT_MS, (
            f"latency={result.latency_ms:.1f}ms > {G53_LATENCY_LIMIT_MS}ms"
        )
        checks["G53-3"] = True
    except Exception as e:
        checks["G53-3"] = False
        errors.append(f"G53-3 latency: {e}")

    # G53-4: 응답 길이 ≥ 100
    try:
        assert len(result.text) >= G53_MIN_LENGTH, (
            f"len={len(result.text)} < {G53_MIN_LENGTH}"
        )
        checks["G53-4"] = True
    except Exception as e:
        checks["G53-4"] = False
        errors.append(f"G53-4 length: {e}")

    # G53-5: provider_name
    try:
        assert gw.provider_name == LORA_PROVIDER_NAME, (
            f"provider_name={gw.provider_name!r} != {LORA_PROVIDER_NAME!r}"
        )
        checks["G53-5"] = True
    except Exception as e:
        checks["G53-5"] = False
        errors.append(f"G53-5 provider_name: {e}")

    # G53-6: 3-tag 무결성
    try:
        active = reg.get_active()
        assert active is not None, "PROMOTED 아티팩트 없음"
        assert isinstance(active.seed_tag, int), f"seed_tag not int: {type(active.seed_tag)}"
        assert len(active.commit_tag) >= 7, f"commit_tag len={len(active.commit_tag)} < 7"
        dsha = active.dataset_sha_tag
        assert len(dsha) == 32, f"dataset_sha_tag len={len(dsha)} != 32"
        assert all(c in "0123456789abcdefABCDEF" for c in dsha), "dataset_sha_tag not hex"
        checks["G53-6"] = True
    except Exception as e:
        checks["G53-6"] = False
        errors.append(f"G53-6 3-tag: {e}")

    # G53-7: CORRUPTED 시 추론 차단
    try:
        reg2 = LoRAModelRegistry()
        a2 = make_artifact("meta-llama/Llama-3.1-8B", 16, 42, "fff0000", "b" * 32)
        reg2.register(a2)
        reg2.promote(a2.artifact_id)
        reg2.promote(a2.artifact_id)
        reg2.mark_corrupted(a2.artifact_id)
        gw2 = LoRAInferenceGateway(registry=reg2, stub_mode=True)
        # CORRUPTED → get_active() returns None → RuntimeError
        try:
            gw2.infer("테스트")
            checks["G53-7"] = False
            errors.append("G53-7: CORRUPTED 아티팩트에서 추론이 차단되지 않음")
        except RuntimeError:
            checks["G53-7"] = True
    except Exception as e:
        checks["G53-7"] = False
        errors.append(f"G53-7 corrupted block: {e}")

    # G53-8: passes_g53 복합 조건
    try:
        result2 = gw.infer("복합 조건 테스트 장면.")
        assert result2.passes_g53, (
            f"passes_g53 failed: latency={result2.latency_ms}ms, len={len(result2.text)}"
        )
        checks["G53-8"] = True
    except Exception as e:
        checks["G53-8"] = False
        errors.append(f"G53-8 passes_g53: {e}")

    return _build_result(checks, errors)


def _build_result(checks: Dict[str, bool], errors: list) -> Dict[str, Any]:
    passed = all(checks.values())
    passed_count = sum(1 for v in checks.values() if v)
    total = len(checks)
    return {
        "gate_name":   "LoRA Inference Gate G53 — 추론 레이턴시·3-tag·PROMOTED 무결성 (ADR-058)",
        "pass":        passed,
        "gate":        "lora_inference_g53",
        "checkpoints": checks,
        "details":     f"LoRAInferenceGate {'PASS' if passed else 'FAIL'} — {passed_count}/{total} 체크포인트",
        "errors":      errors,
    }
