"""
Gate 13: SubPhase 3 SLM Export 핵심 모듈 생존 검증 (V446 신설)

검증 모듈:
  1. PIIScrubber          — PII 마스킹 파이프라인
  2. SLMDatasetBuilderV443 — ShareGPT + 스크럽 포맷
  3. TraceQualityFilter   — MinHash dedup + stratified split
  4. DatasetCardGenerator — HF 카드 생성
  5. TrainingDataRegistry — ADR-008 버전/동의/삭제 추적
  6. SyntheticAugmentor   — DRSE 기반 증강기
"""
from __future__ import annotations


def _gate_slm_subphase3_survival() -> dict:
    """SubPhase 3 SLM Export 핵심 모듈 생존 검증."""
    try:
        # 1. PIIScrubber
        from literary_system.slm.pii_scrubber import PIIScrubber
        scrubber = PIIScrubber()
        clean, report = scrubber.scrub("연락처 010-1234-5678")
        assert "[PHONE]" in clean, "PIIScrubber 전화번호 마스킹 실패"

        # 2. SLMDatasetBuilderV443
        from literary_system.slm.dataset_builder_v443 import SLMDatasetBuilderV443
        from literary_system.trace.trace_dataset_store import TraceDatasetStore, make_trace_record
        import tempfile, os
        tmpdir = tempfile.mkdtemp()
        store = TraceDatasetStore(tmpdir)
        rec = make_trace_record(
            project_id="gate13", episode_no=1, scene_id="sc01",
            seed_contract={"genre": "drama", "user_prompt": "씬"},
            style_dna_profile="압박형", macroarc_intent="갈등",
            literary_state_before={"SP": 0.4},
            literary_state_after={"SP": 0.5},
            render_output={"sc01": "씬 내용 텍스트"},
            loss_report={"L_total": 0.10},
            reader_estimate={"reader_pull": 0.6, "ai_smell_score": 0.1},
            trajectory_deviation=0.05, critic_findings=[],
            repair_applied=False, hitl_recommended=False,
            knowledge_pressure=0.3,
        )
        store.commit(rec)
        builder = SLMDatasetBuilderV443(store)
        out_sg = os.path.join(tmpdir, "test.json")
        result = builder.build_sharegpt_dataset(out_sg)
        assert result["total_records"] >= 1, "SLMDatasetBuilderV443 출력 0개"

        # 3. TraceQualityFilter
        from literary_system.slm.trace_quality_filter import TraceQualityFilter
        flt = TraceQualityFilter()
        records = list(store._index.values())
        kept, removed = flt.filter_by_tier(records)
        assert kept, "TraceQualityFilter: 모든 레코드 제거됨"

        # 4. DatasetCardGenerator
        from literary_system.slm.dataset_card_registry import DatasetCardGenerator
        gen = DatasetCardGenerator("gate13_ds", "v1.0")
        card_result = gen.generate_card(records)
        assert "card_text" in card_result, "DatasetCardGenerator 카드 없음"

        # 5. TrainingDataRegistry
        from literary_system.slm.dataset_card_registry import TrainingDataRegistry
        reg = TrainingDataRegistry()
        v = reg.register_version("v1.0", "gate13_ds", [r.trace_id for r in records], {})
        assert v.version_tag == "v1.0", "TrainingDataRegistry 버전 등록 실패"

        # 6. SyntheticAugmentor
        from literary_system.slm.synthetic_augmentor import SyntheticAugmentor
        augmentor = SyntheticAugmentor(threshold=0.15)
        aug_result = augmentor.augment(records)
        assert aug_result.source_count >= 1, "SyntheticAugmentor 후보 0개"

        return {
            "pass": True,
            "modules_verified": 6,
            "summary": (
                "SubPhase3 Gate13 PASS: "
                "PIIScrubber/SLMDatasetBuilderV443/TraceQualityFilter/"
                "DatasetCardGenerator/TrainingDataRegistry/SyntheticAugmentor"
            ),
        }

    except Exception as e:
        return {"pass": False, "reason": str(e)}
