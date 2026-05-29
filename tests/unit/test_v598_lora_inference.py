"""
V598 — LoRA Inference: LoRAArtifact + LoRAModelRegistry + LoRAInferenceGateway 단위 테스트 (11 TC)

TC-A1~A3: LoRAArtifact 3-tag 무결성 및 sha256 검증
TC-B1~B3: LoRAModelRegistry 등록·승격·퇴역 수명주기
TC-C1~C3: LoRAInferenceGateway stub 추론 + G53 합격
TC-D1~D2: Gate G53 8체크포인트 통합 검증
"""
from __future__ import annotations

import json
import tempfile
import warnings
from pathlib import Path

import pytest

from literary_system.finetune.lora_artifact import (
    ArtifactStage,
    LoRAArtifact,
    LoRAArtifactContract,
    compute_sha256,
    make_artifact,
)
from literary_system.finetune.lora_model_registry import (
    ArtifactNotFoundError,
    LoRAModelRegistry,
    RegisterConflictError,
    StageTransitionError,
)
from literary_system.finetune.lora_inference_gateway import (
    G53_LATENCY_LIMIT_MS,
    G53_MIN_LENGTH,
    LORA_PROVIDER_NAME,
    InferenceResult,
    LoRAInferenceGateway,
    StubInferenceBackend,
)


# ===========================================================================
# TC-A: LoRAArtifact
# ===========================================================================

class TestLoRAArtifact:
    """TC-A1~A3: 3-tag 무결성 및 sha256 검증."""

    def test_a1_3tag_contract(self):
        """TC-A1: make_artifact() 3-tag (B-M-03) 필드가 올바르게 설정되어야 한다."""
        artifact = make_artifact(
            base_model="meta-llama/Llama-3.1-8B",
            lora_rank=16,
            seed_tag=42,
            commit_tag="abcdef1",
            dataset_sha_tag="a" * 32,
        )
        assert artifact.seed_tag == 42
        assert artifact.commit_tag == "abcdef1"
        assert artifact.dataset_sha_tag == "a" * 32
        assert artifact.lora_rank == 16
        assert artifact.stage == ArtifactStage.CANDIDATE
        assert artifact.artifact_id.startswith("lora-abcdef1")

    def test_a2_tag_string_format(self):
        """TC-A2: tag_string이 'seed=N|commit=7자|dataset=8자' 형식이어야 한다."""
        artifact = make_artifact(
            base_model="meta-llama/Llama-3.1-8B",
            lora_rank=16,
            seed_tag=42,
            commit_tag="abc1234",
            dataset_sha_tag="01234567" + "0" * 24,
        )
        ts = artifact.tag_string
        assert ts.startswith("seed=42|commit=abc1234|dataset=01234567"), (
            f"tag_string format error: {ts}"
        )

    def test_a3_verify_integrity_no_file(self):
        """TC-A3: 파일 없이 64자 hex sha256 형식만 있으면 무결성 통과."""
        artifact = make_artifact(
            base_model="meta-llama/Llama-3.1-8B",
            lora_rank=16,
            seed_tag=42,
            commit_tag="abc1234",
            dataset_sha_tag="0" * 32,
            sha256="a" * 64,
        )
        # 파일 없이 sha256 hex 형식 검증
        assert artifact.verify_integrity() is True

    def test_a3b_save_load_manifest_roundtrip(self, tmp_path):
        """TC-A3b: save_manifest → load_manifest 라운드트립 (sha256 재계산)."""
        artifact = make_artifact(
            base_model="meta-llama/Llama-3.1-8B",
            lora_rank=16,
            seed_tag=42,
            commit_tag="abc1234",
            dataset_sha_tag="0" * 32,
        )
        manifest_path = artifact.save_manifest(str(tmp_path))
        # sha256 업데이트 (manifest 파일 기반)
        artifact.sha256 = compute_sha256(manifest_path)
        artifact.save_manifest(str(tmp_path))

        loaded = LoRAArtifact.load_manifest(manifest_path)
        assert loaded.artifact_id == artifact.artifact_id
        assert loaded.seed_tag == 42
        assert loaded.commit_tag == "abc1234"


# ===========================================================================
# TC-B: LoRAModelRegistry
# ===========================================================================

class TestLoRAModelRegistry:
    """TC-B1~B3: 등록·승격·퇴역 수명주기."""

    def _make_reg_with_artifact(self) -> tuple[LoRAModelRegistry, LoRAArtifact]:
        reg = LoRAModelRegistry()
        a = make_artifact("meta-llama/Llama-3.1-8B", 16, 42, "abc1234", "0" * 32)
        reg.register(a)
        return reg, a

    def test_b1_register_and_stage(self):
        """TC-B1: register() 후 CANDIDATE, 중복 등록 시 RegisterConflictError."""
        reg, a = self._make_reg_with_artifact()
        assert a.stage == ArtifactStage.CANDIDATE
        assert a.artifact_id in reg

        # 중복 등록
        with pytest.raises(RegisterConflictError):
            reg.register(a)

    def test_b2_promote_lifecycle(self):
        """TC-B2: CANDIDATE → VALIDATED → PROMOTED 순서, PROMOTED 중복 시 기존 → RETIRED."""
        reg, a = self._make_reg_with_artifact()

        s1 = reg.promote(a.artifact_id)
        assert s1 == ArtifactStage.VALIDATED

        s2 = reg.promote(a.artifact_id)
        assert s2 == ArtifactStage.PROMOTED

        # 두 번째 PROMOTED 아티팩트 → 기존 RETIRED로
        a2 = make_artifact("meta-llama/Llama-3.1-8B", 16, 42, "def5678", "0" * 32)
        reg.register(a2)
        reg.promote(a2.artifact_id)  # CANDIDATE → VALIDATED
        reg.promote(a2.artifact_id)  # VALIDATED → PROMOTED (a 는 RETIRED)

        assert reg.get(a.artifact_id).stage == ArtifactStage.RETIRED
        assert reg.get(a2.artifact_id).stage == ArtifactStage.PROMOTED
        assert reg.get_active().artifact_id == a2.artifact_id

    def test_b3_retire_and_corrupted(self):
        """TC-B3: retire() PROMOTED→RETIRED, mark_corrupted(), 잘못된 전환 StageTransitionError."""
        reg, a = self._make_reg_with_artifact()
        reg.promote(a.artifact_id)
        reg.promote(a.artifact_id)

        # PROMOTED → RETIRED
        reg.retire(a.artifact_id)
        assert reg.get(a.artifact_id).stage == ArtifactStage.RETIRED
        assert reg.get_active() is None

        # retire() 재호출 (RETIRED는 PROMOTED가 아님)
        with pytest.raises(StageTransitionError):
            reg.retire(a.artifact_id)

        # mark_corrupted
        reg.mark_corrupted(a.artifact_id)
        assert reg.get(a.artifact_id).stage == ArtifactStage.CORRUPTED

    def test_b3b_persistence(self, tmp_path):
        """TC-B3b: save/load JSON 영속화 라운드트립."""
        reg = LoRAModelRegistry(registry_dir=str(tmp_path))
        a = make_artifact("meta-llama/Llama-3.1-8B", 16, 42, "abc1234", "0" * 32)
        reg.register(a)
        reg.promote(a.artifact_id)

        # 새 인스턴스로 로드
        reg2 = LoRAModelRegistry.load(str(tmp_path))
        assert a.artifact_id in reg2
        assert reg2.get(a.artifact_id).stage == ArtifactStage.VALIDATED


# ===========================================================================
# TC-C: LoRAInferenceGateway
# ===========================================================================

class TestLoRAInferenceGateway:
    """TC-C1~C3: stub 추론 + G53 합격."""

    def _make_gateway(self) -> LoRAInferenceGateway:
        reg = LoRAModelRegistry()
        a = make_artifact("meta-llama/Llama-3.1-8B", 16, 42, "abc1234", "0" * 32)
        reg.register(a)
        reg.promote(a.artifact_id)  # CANDIDATE → VALIDATED
        reg.promote(a.artifact_id)  # VALIDATED → PROMOTED
        return LoRAInferenceGateway(registry=reg, stub_mode=True)

    def test_c1_provider_name_and_availability(self):
        """TC-C1: provider_name == 'lora_local', PROMOTED 시 is_available() == True."""
        gw = self._make_gateway()
        assert gw.provider_name == LORA_PROVIDER_NAME
        assert gw.is_available() is True

    def test_c2_stub_infer_passes_g53(self):
        """TC-C2: stub 추론 결과가 G53 기준(≤2000ms, ≥100chars)을 만족해야 한다."""
        gw = self._make_gateway()
        result = gw.infer("두 인물이 병원 복도에서 마주치는 장면을 작성하라.")

        assert isinstance(result, InferenceResult)
        assert result.latency_ms <= G53_LATENCY_LIMIT_MS, (
            f"latency={result.latency_ms}ms > {G53_LATENCY_LIMIT_MS}ms"
        )
        assert len(result.text) >= G53_MIN_LENGTH, (
            f"len={len(result.text)} < {G53_MIN_LENGTH}"
        )
        assert result.passes_g53 is True
        assert result.backend == "stub"
        assert result.artifact_id != ""

    def test_c3_no_promoted_raises(self):
        """TC-C3: PROMOTED 아티팩트 없으면 RuntimeError."""
        empty_reg = LoRAModelRegistry()
        gw = LoRAInferenceGateway(registry=empty_reg, stub_mode=True)
        assert gw.is_available() is False

        with pytest.raises(RuntimeError, match="PROMOTED"):
            gw.generate("테스트 프롬프트")

    def test_c3b_generate_with_response(self):
        """TC-C3b: generate_with_response() → LLMResponse(latency_ms 포함)."""
        gw = self._make_gateway()
        resp = gw.generate_with_response("드라마 장면을 생성하라.")
        assert hasattr(resp, "latency_ms")
        assert resp.provider_id == LORA_PROVIDER_NAME
        assert len(resp.text) >= G53_MIN_LENGTH


# ===========================================================================
# TC-D: Gate G53 통합
# ===========================================================================

class TestGateG53:
    """TC-D1~D2: Gate G53 8체크포인트 통합 검증."""

    def test_d1_gate_all_pass(self):
        """TC-D1: Gate G53 전체 실행 — 8/8 체크포인트 PASS."""
        from literary_system.gates.lora_inference_gate import _gate_lora_inference_g53

        result = _gate_lora_inference_g53()
        assert result["pass"] is True, (
            f"Gate G53 FAIL: {result['errors']}"
        )
        assert result["gate"] == "lora_inference_g53"
        passed_count = sum(1 for v in result["checkpoints"].values() if v)
        assert passed_count == 8, (
            f"Gate G53: {passed_count}/8 체크포인트만 통과"
        )

    def test_d2_release_gate_includes_g53(self):
        """TC-D2: release_gate.py GATES 목록에 lora_inference_g53 포함."""
        from literary_system.gates.release_gate import GATES

        gate_ids = [g[0] for g in GATES]
        assert "lora_inference_g53" in gate_ids, (
            f"lora_inference_g53 not in GATES: {gate_ids}"
        )
        assert len(GATES) >= 52, f"GATES count={len(GATES)} < 52"
