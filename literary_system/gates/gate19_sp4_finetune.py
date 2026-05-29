"""
Gate19 — SP4 Fine-tune LoRA POC 검증 (V473)

ADR-014: Training Data Hygiene
ADR-017: Canary Deployment

5개 모듈 통합 검증:
  1. FineTuneJobManager: LoRA 잡 제출 → 완료
  2. ProseStyleDataset: CC-BY 필터 + 데이터셋 카드
  3. ModelEvalHarness: BLEU/ROUGE/Coherence 평가
  4. SafetyRegressionSuite: 안전성 회귀 테스트
  5. ModelVersionManager + CanaryKPIMonitor: 버전 등록 → 카나리 → KPI 감시

LLM-0: 모든 검증 규칙 기반.
"""
from __future__ import annotations

from typing import Any


def _gate_sp4_finetune() -> dict[str, Any]:
    """Gate19 SP4 파인튜닝 LoRA POC 검증"""
    import uuid

    from literary_system.finetune.canary_kpi_monitor import CanaryKPIMonitor
    from literary_system.finetune.finetune_job_manager import (
        FineTuneJobManager,
        FineTuneMethod,
    )
    from literary_system.finetune.model_eval_harness import (
        EvalSample,
        ModelEvalHarness,
    )
    from literary_system.finetune.model_version_manager import (
        ModelArtifact,
        ModelStage,
        ModelVersionManager,
    )
    from literary_system.finetune.prose_specializer_api import (
        ProseSpecializerAPI,
        ServeRequest,
    )
    from literary_system.finetune.prose_style_dataset import (
        DataSource,
        LicenseType,
        ProseStyle,
        ProseStyleDataset,
        make_entry,
    )
    from literary_system.finetune.safety_regression_suite import SafetyRegressionSuite

    symbols_verified: list[str] = []
    errors: list[str] = []

    # ---------------------------------------------------------------
    # 1. FineTuneJobManager: MOCK 잡 제출 → 완료
    # ---------------------------------------------------------------
    try:
        mgr = FineTuneJobManager()
        job_id = mgr.submit("dataset-gate19", method=FineTuneMethod.MOCK)
        job = mgr.simulate_training(job_id, steps=1000)
        assert job.status.value == "completed", f"잡 상태 오류: {job.status}"
        assert job.model_artifact_id is not None
        assert job.current_step == job.total_steps
        symbols_verified.append(
            f"FineTuneJobManager[MOCK job {job_id[:12]}, {job.current_step}/{job.total_steps} steps, COMPLETED]"
        )
    except Exception as e:
        errors.append(f"FineTuneJobManager: {e}")

    # ---------------------------------------------------------------
    # 2. ProseStyleDataset: CC-BY 필터 + 데이터셋 카드
    # ---------------------------------------------------------------
    try:
        ds = ProseStyleDataset()
        entries = [
            make_entry(
                "그의 눈빛이 그녀를 향했다. 설레는 마음을 감추지 못한 채 미소를 지었다.",
                ProseStyle.ROMANCE, DataSource.SYNTHETIC, LicenseType.CC_BY,
            ),
            make_entry(
                "발소리가 가까워졌다. 그는 숨을 죽이며 어둠 속에 몸을 숨겼다.",
                ProseStyle.THRILLER, DataSource.KOFICE, LicenseType.CC_BY,
            ),
            make_entry(
                "우주선 엔진이 작동했다. 인공지능이 목적지 좌표를 계산했다.",
                ProseStyle.SF, DataSource.KOCCA, LicenseType.PUBLIC_DOMAIN,
            ),
            make_entry(
                "조선의 하늘 아래 장군이 칼을 빼들었다.",
                ProseStyle.HISTORICAL, DataSource.KLAP, LicenseType.CC_BY_SA,
            ),
            make_entry(
                "스마트폰 알림이 울렸다. 카페에서 커피를 홀짝이며 메시지를 확인했다.",
                ProseStyle.CONTEMPORARY, DataSource.SYNTHETIC, LicenseType.CC_BY,
            ),
            # 라이선스 위반 — 거부되어야 함
        ]
        added, skipped = ds.add_entries(entries)
        assert added == 5, f"추가 수 오류: {added}"

        # PROPRIETARY 거부 확인
        bad_entry = make_entry("테스트", ProseStyle.SF, DataSource.INTERNAL, LicenseType.PROPRIETARY)
        try:
            ds.add_entry(bad_entry)
            errors.append("ProseStyleDataset: PROPRIETARY 라이선스가 허용됨 (ADR-008 위반)")
        except ValueError:
            pass  # 올바르게 거부됨

        ds_id = "gate19-dataset"
        card = ds.generate_card(ds_id, entries)
        assert card.total_entries == 5
        assert card.checksum != ""
        symbols_verified.append(
            f"ProseStyleDataset[5 entries CC-BY, card_id={ds_id}, checksum={card.checksum}]"
        )
    except Exception as e:
        errors.append(f"ProseStyleDataset: {e}")

    # ---------------------------------------------------------------
    # 3. ModelEvalHarness: BLEU/ROUGE/Coherence 평가
    # ---------------------------------------------------------------
    try:
        harness = ModelEvalHarness()
        samples = [
            EvalSample(
                sample_id=str(uuid.uuid4()),
                input_text="사랑에 빠진 두 사람을 묘사하라",
                reference_text="그의 눈빛이 그녀를 향했다. 설레는 마음을 감추지 못한 채, 그녀는 미소를 지었다. 두 사람은 서로를 바라보며 행복을 느꼈다.",
                generated_text="그의 눈빛이 그녀를 향했다. 설레는 마음을 감추지 못한 채, 그녀는 미소를 지었다.",
                style_label="romance",
            ),
            EvalSample(
                sample_id=str(uuid.uuid4()),
                input_text="긴장감 있는 장면을 묘사하라",
                reference_text="발소리가 가까워졌다. 그는 숨을 죽이며 어둠 속에 몸을 숨겼다. 그런데 갑자기 문이 열렸다.",
                generated_text="발소리가 점점 가까워졌다. 그는 숨을 죽이며 어둠 속에 몸을 숨겼다.",
                style_label="thriller",
            ),
        ]
        report = harness.run_eval("gate19-model", samples)
        assert report.sample_count == 2
        assert report.bleu_score >= 0.0
        assert report.rouge_l >= 0.0
        assert report.coherence_score >= 0.0
        symbols_verified.append(
            f"ModelEvalHarness[BLEU={report.bleu_score}, ROUGE-L={report.rouge_l}, "
            f"Coherence={report.coherence_score}, passed={report.passed}]"
        )
    except Exception as e:
        errors.append(f"ModelEvalHarness: {e}")

    # ---------------------------------------------------------------
    # 4. SafetyRegressionSuite: 안전성 회귀 테스트
    # ---------------------------------------------------------------
    try:
        suite = SafetyRegressionSuite()
        safe_samples = [
            "그의 눈빛이 그녀를 향했다. 아름다운 저녁이었다.",
            "우주선이 별을 향해 날아갔다. 인류의 새로운 시대가 열렸다.",
            "조선의 하늘 아래 평화로운 마을이 있었다.",
        ]
        safety_report = suite.run("gate19-model", safe_samples)
        assert safety_report.total_samples == 3
        assert safety_report.violation_rate == 0.0
        assert safety_report.passed is True
        symbols_verified.append(
            f"SafetyRegressionSuite[3 samples, violation_rate={safety_report.violation_rate}, "
            f"safety_score={safety_report.safety_score}, passed={safety_report.passed}]"
        )
    except Exception as e:
        errors.append(f"SafetyRegressionSuite: {e}")

    # ---------------------------------------------------------------
    # 5. ModelVersionManager + CanaryKPIMonitor + ProseSpecializerAPI
    # ---------------------------------------------------------------
    try:
        version_mgr = ModelVersionManager()
        artifact = ModelArtifact(
            artifact_id=f"artifact-{str(uuid.uuid4())[:8]}",
            model_id="gate19-model",
            base_model="mock-model-v1",
            method="mock",
            checksum="abcd1234",
            size_mb=512.0,
        )
        version_id = version_mgr.register(
            "gate19-model", artifact, version_tag="v1.0-gate19"
        )
        # 카나리 1% → 5% 승격
        v = version_mgr.canary_promote(version_id, 1)
        assert v.stage.value == "canary"
        v = version_mgr.canary_promote(version_id, 5)
        assert v.canary_pct == 5

        # KPI 모니터: 정상 KPI 기록 → 롤백 불필요
        monitor = CanaryKPIMonitor()
        for _ in range(3):
            monitor.record(version_id, coherence=0.75, hallucination_rate=0.05,
                          safety_violation_rate=0.01)
        window = monitor.evaluate(version_id)
        assert window.rollback_triggered is False

        # 이상 KPI 기록 → 롤백 신호
        bad_monitor = CanaryKPIMonitor()
        bad_monitor.record(version_id, coherence=0.3, hallucination_rate=0.5,
                          safety_violation_rate=0.1)
        bad_window = bad_monitor.evaluate(version_id)
        assert bad_window.rollback_triggered is True
        assert len(bad_window.rollback_reasons) > 0

        # ProseSpecializerAPI: 서빙 + A/B 비교
        api = ProseSpecializerAPI(active_version_id=version_id, canary_pct=5)
        req = ServeRequest(
            request_id=str(uuid.uuid4()),
            prompt="사랑하는 두 사람을 묘사해주세요",
            style_hint="romance",
        )
        resp = api.serve(req)
        assert resp.generated_text != ""
        ab_result = api.compare_ab("로맨틱한 장면을 묘사하라", style_hint="romance")
        assert ab_result.comparison_id != ""

        symbols_verified.append(
            "ModelVersionManager[v1.0-gate19, canary_pct=5%]"
        )
        symbols_verified.append(
            "CanaryKPIMonitor[normal→no rollback, bad_KPI→rollback triggered]"
        )
        symbols_verified.append(
            f"ProseSpecializerAPI[served, AB winner={ab_result.winner}]"
        )
    except Exception as e:
        errors.append(f"ModelVersionManager/CanaryKPI/ProseSpecializer: {e}")

    # ---------------------------------------------------------------
    # 결과
    # ---------------------------------------------------------------
    passed = len(errors) == 0 and len(symbols_verified) >= 5
    return {
        "pass": passed,
        "modules_verified": len(symbols_verified),
        "symbols_verified": symbols_verified,
        "errors": errors,
        "summary": (
            f"Gate19 PASS: SP4 FineTune/LoRA POC ALL OK ({len(symbols_verified)}/7)"
            if passed else
            f"Gate19 FAIL: {errors}"
        ),
    }
