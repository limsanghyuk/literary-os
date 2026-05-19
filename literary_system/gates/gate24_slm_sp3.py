"""
literary_system/gates/gate24_slm_sp3.py
Gate 24: SP3 SLM 수출 레이어 생존 게이트

V497 릴리즈 게이트.
SP3 4개 모듈의 심볼 및 인터페이스 계약을 검증한다.

검증 대상 (총 24개 심볼):
  TraceQualityFilterSP3 — SP3Record, DedupReport, SP3FilterResult, TraceQualityFilterSP3 (4)
  PIIScrubberSP3        — ScrubDetailSP3, DatasetScrubReport, PIIScrubberSP3 (3)
  DatasetCardGenerator  — DatasetStats, DatasetCard, DatasetCardGenerator (3)
  SyntheticAugmentorSP3 — AugmentedRecord, AugmentResultSP3, SyntheticAugmentorSP3,
                          SUPPORTED_STRATEGIES (4)
  인터페이스 계약 (10가지 메서드/속성 시그니처)

ADR-008 준수 검증:
  - synthetic=True 플래그 의무 부착 확인
  - PII 스크럽 카테고리 통계 확인
  - DatasetCard 라이선스 필드 확인
"""
from __future__ import annotations
import logging

from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _gate_slm_sp3_survival() -> Dict[str, Any]:
    """SP3 4개 모듈 생존 + 인터페이스 계약 검증."""
    errors: List[str] = []
    verified: List[str] = []
    adr_checks: List[str] = []

    # ── 1. TraceQualityFilterSP3 ──────────────────────────────────────
    try:
        from literary_system.slm.trace_quality_filter_sp3 import (
            SP3Record,
            DedupReport,
            SP3FilterResult,
            TraceQualityFilterSP3,
        )
        verified += ["SP3Record", "DedupReport", "SP3FilterResult", "TraceQualityFilterSP3"]

        # 인터페이스: from_dict / run / export_jsonl
        assert hasattr(SP3Record, "from_dict"), "SP3Record.from_dict 없음"
        assert hasattr(SP3Record, "to_dict"), "SP3Record.to_dict 없음"
        verified += ["SP3Record.from_dict", "SP3Record.to_dict"]

        filt = TraceQualityFilterSP3()
        assert callable(getattr(filt, "run", None)), "TraceQualityFilterSP3.run 없음"
        assert callable(getattr(filt, "export_jsonl", None)), "TraceQualityFilterSP3.export_jsonl 없음"
        verified += ["TraceQualityFilterSP3.run", "TraceQualityFilterSP3.export_jsonl"]

        # 실행 검증: 빈 입력
        result = filt.run([])
        assert isinstance(result, SP3FilterResult), "run([]) 반환 타입 오류"
        verified.append("TraceQualityFilterSP3.run(empty)")

    except Exception as e:
        errors.append(f"TraceQualityFilterSP3: {e}")

    # ── 2. PIIScrubberSP3 ─────────────────────────────────────────────
    try:
        from literary_system.slm.pii_scrubber_sp3 import (
            ScrubDetailSP3,
            DatasetScrubReport,
            PIIScrubberSP3,
        )
        verified += ["ScrubDetailSP3", "DatasetScrubReport", "PIIScrubberSP3"]

        scrubber = PIIScrubberSP3()
        assert callable(getattr(scrubber, "scrub", None)), "PIIScrubberSP3.scrub 없음"
        assert callable(getattr(scrubber, "scrub_batch", None)), "PIIScrubberSP3.scrub_batch 없음"
        assert callable(getattr(scrubber, "scrub_dataset", None)), "PIIScrubberSP3.scrub_dataset 없음"
        verified += ["PIIScrubberSP3.scrub", "PIIScrubberSP3.scrub_batch", "PIIScrubberSP3.scrub_dataset"]

        # ADR-008: PII 카테고리 통계 확인
        detail = scrubber.scrub("전화: 010-1234-5678")
        assert hasattr(detail, "removed_by_category"), "ScrubDetailSP3.removed_by_category 없음"
        assert isinstance(detail.removed_by_category, dict), "removed_by_category 타입 오류"
        adr_checks.append("ADR-008: PII category stats present")

        # DatasetScrubReport 계약
        _, report = scrubber.scrub_dataset([{"text": "010-1234-5678"}])
        assert hasattr(report, "scrub_rate"), "DatasetScrubReport.scrub_rate 없음"
        assert hasattr(report, "summary"), "DatasetScrubReport.summary 없음"
        verified.append("DatasetScrubReport.scrub_rate+summary")

    except Exception as e:
        errors.append(f"PIIScrubberSP3: {e}")

    # ── 3. DatasetCardGenerator ───────────────────────────────────────
    try:
        from literary_system.slm.dataset_card_generator import (
            DatasetStats,
            DatasetCard,
            DatasetCardGenerator,
        )
        verified += ["DatasetStats", "DatasetCard", "DatasetCardGenerator"]

        gen = DatasetCardGenerator()
        assert callable(getattr(gen, "generate", None)), "DatasetCardGenerator.generate 없음"
        assert callable(getattr(gen, "save", None)), "DatasetCardGenerator.save 없음"
        verified += ["DatasetCardGenerator.generate", "DatasetCardGenerator.save"]

        # 실행 검증
        card = gen.generate(
            train=[{"id": "t0", "text": "드라마 씬", "quality_score": 0.8, "tier": "A"}],
            val=[],
            test=[],
        )
        assert isinstance(card, DatasetCard), "generate() 반환 타입 오류"
        assert hasattr(card, "to_yaml_header"), "DatasetCard.to_yaml_header 없음"
        assert hasattr(card, "to_markdown"), "DatasetCard.to_markdown 없음"
        verified += ["DatasetCard.to_yaml_header", "DatasetCard.to_markdown"]

        # ADR-008: 라이선스 필드 확인
        assert card.license, "DatasetCard.license 비어 있음"
        adr_checks.append("ADR-008: DatasetCard license field present")

        # YAML front-matter 형식 검증
        yaml = card.to_yaml_header()
        assert yaml.startswith("---"), "YAML header 형식 오류"
        verified.append("DatasetCard.to_yaml_header format")

    except Exception as e:
        errors.append(f"DatasetCardGenerator: {e}")

    # ── 4. SyntheticAugmentorSP3 ──────────────────────────────────────
    try:
        from literary_system.slm.synthetic_augmentor_sp3 import (
            AugmentedRecord,
            AugmentResultSP3,
            SyntheticAugmentorSP3,
            SUPPORTED_STRATEGIES,
        )
        verified += ["AugmentedRecord", "AugmentResultSP3",
                     "SyntheticAugmentorSP3", "SUPPORTED_STRATEGIES"]

        # 전략 3종 확인
        assert len(SUPPORTED_STRATEGIES) == 3, f"전략 수 오류: {SUPPORTED_STRATEGIES}"
        for s in ("paraphrase", "back_translation", "style_transfer"):
            assert s in SUPPORTED_STRATEGIES, f"전략 누락: {s}"
        verified.append("SUPPORTED_STRATEGIES(3종)")

        augmentor = SyntheticAugmentorSP3(seed=42)
        assert callable(getattr(augmentor, "augment", None)), "SyntheticAugmentorSP3.augment 없음"
        assert callable(getattr(augmentor, "select_candidates", None)), "select_candidates 없음"
        verified += ["SyntheticAugmentorSP3.augment", "SyntheticAugmentorSP3.select_candidates"]

        # 실행 검증 + ADR-008: synthetic=True 확인
        record = {"id": "r0", "text": "드라마 씬 텍스트", "quality_score": 0.8, "tier": "A"}
        result = augmentor.augment([record], strategy="paraphrase")
        assert isinstance(result, AugmentResultSP3), "augment() 반환 타입 오류"
        assert len(result.augmented) > 0, "augmented 결과 없음"
        aug_rec = result.augmented[0]
        assert aug_rec.synthetic is True, "ADR-008: synthetic 플래그 누락"
        adr_checks.append("ADR-008: synthetic=True flag verified")
        verified.append("AugmentedRecord.synthetic=True")

        # target_count 검증
        result2 = augmentor.augment([record] * 3, target_count=10)
        assert len(result2.augmented) == 7, f"target_count 오류: {len(result2.augmented)}"
        verified.append("augment(target_count) correct")

    except Exception as e:
        errors.append(f"SyntheticAugmentorSP3: {e}")

    symbols_passed = len(verified)
    return {
        "pass": len(errors) == 0,
        "symbols_verified": verified,
        "symbols_checked": symbols_passed,   # G2: 명세 통일 (count 별칭)
        "symbols_passed": symbols_passed,    # G2: 명세 통일
        "count": symbols_passed,
        "errors": errors,
        "adr": adr_checks,
    }


def run_gate24() -> Dict[str, Any]:
    """Gate 24 공개 진입점."""
    result = _gate_slm_sp3_survival()
    result["gate"] = "Gate 24 — SP3 SLM 수출 생존"
    return result


if __name__ == "__main__":
    import json
    r = run_gate24()
    logger.debug(json.dumps(r, ensure_ascii=False, indent=2))
    if not r["pass"]:
        raise SystemExit(1)
