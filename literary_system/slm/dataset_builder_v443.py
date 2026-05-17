"""
V443 -- SLMDatasetBuilderV443
SLMDatasetBuilder 확장: ShareGPT 포맷 추가 + PIIScrubber 통합.

신규 기능:
  - build_sharegpt_dataset(): ShareGPT 포맷 (human/gpt 교대 대화 구조)
  - PIIScrubber 통합: 모든 build_* 메서드에 scrub_pii=True 옵션
  - PII 스크럽 통계를 메타데이터에 포함

하위호환:
  - SLMDatasetBuilder의 모든 메서드 그대로 상속
  - 기존 테스트 무변경
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from literary_system.slm.dataset_builder import SLMDatasetBuilder
from literary_system.slm.pii_scrubber import PIIScrubber
from literary_system.trace.trace_dataset_store import TraceRecord, PromotionTier


class SLMDatasetBuilderV443(SLMDatasetBuilder):
    """
    V443 확장: ShareGPT 포맷 + PII 마스킹.

    ShareGPT 포맷:
      {
        "conversations": [
          {"from": "human", "value": "..."},
          {"from": "gpt",   "value": "..."}
        ],
        "metadata": {...}
      }
    """

    def __init__(
        self,
        store,
        scrubber: Optional[PIIScrubber] = None,
    ) -> None:
        super().__init__(store)
        self._scrubber = scrubber or PIIScrubber()

    # --- ShareGPT ----------------------------------------------------------

    def build_sharegpt_dataset(
        self,
        out_path,
        max_L_total: float = 0.18,
        min_reader_pull: float = 0.30,
        max_ai_smell: float = 0.35,
        scrub_pii: bool = True,
        system_prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        ShareGPT 포맷 데이터셋 생성.
        LLaMA-Factory, axolotl 등 ShareGPT 포맷 지원 프레임워크와 호환.
        """
        if not system_prompt:
            system_prompt = (
                "당신은 한국 문학 창작 전문 AI입니다. "
                "주어진 조건에 따라 절제된 압박형 산문을 생성합니다."
            )
        records = self._filter_records(max_L_total, min_reader_pull, max_ai_smell)
        dataset = []
        pii_total = 0

        for r in records:
            entry = self._to_sharegpt(r, system_prompt, scrub_pii)
            if entry:
                pii_total += entry.pop("_pii_count", 0)
                dataset.append(entry)

        out_path = Path(out_path)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        return {
            "format":         "sharegpt",
            "total_records":  len(dataset),
            "output_path":    str(out_path),
            "pii_removed":    pii_total,
            "quality_summary": self._quality_summary(records),
        }

    # --- PII-aware Alpaca override -----------------------------------------

    def build_alpaca_dataset_scrubbed(
        self,
        out_path,
        max_L_total: float = 0.18,
        min_reader_pull: float = 0.30,
        max_ai_smell: float = 0.35,
    ) -> dict[str, Any]:
        """Alpaca 데이터셋 + PII 스크럽."""
        records = self._filter_records(max_L_total, min_reader_pull, max_ai_smell)
        dataset = []
        pii_total = 0

        for r in records:
            entry = self._to_alpaca(r)
            if entry:
                # scrub output
                clean_out, rep_out = self._scrubber.scrub(entry["output"])
                clean_inp, rep_inp = self._scrubber.scrub(entry["input"])
                entry["output"] = clean_out
                entry["input"] = clean_inp
                pii_total += rep_out.total_removed + rep_inp.total_removed
                dataset.append(entry)

        out_path = Path(out_path)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        return {
            "format": "alpaca_scrubbed",
            "total_records": len(dataset),
            "output_path": str(out_path),
            "pii_removed": pii_total,
        }

    # --- internal helpers --------------------------------------------------

    def _to_sharegpt(
        self,
        r: TraceRecord,
        system_prompt: str,
        scrub_pii: bool,
    ) -> Optional[dict[str, Any]]:
        """TraceRecord -> ShareGPT format."""
        # Bug-Fix: use double newline separator (chr(10)+chr(10)) consistent with alpaca/openai formats
        output_text = (chr(10) + chr(10)).join(
            "[" + sid + "]" + chr(10) + txt
            for sid, txt in r.render_output.items()
            if txt and txt.strip()
        )
        if not output_text.strip():
            return None

        human_msg = (
            "[장르] " + r.seed_contract.get("genre", "drama") + chr(10) +
            "[문체] " + r.style_dna_profile + chr(10) +
            "[의도] " + r.macroarc_intent + chr(10) +
            "[씨드] " + r.seed_contract.get("user_prompt", "")
        )

        pii_count = 0
        if scrub_pii:
            human_msg, r1 = self._scrubber.scrub(human_msg)
            output_text, r2 = self._scrubber.scrub(output_text)
            pii_count = r1.total_removed + r2.total_removed

        entry = {
            "conversations": [
                {"from": "system", "value": system_prompt},
                {"from": "human",  "value": human_msg},
                {"from": "gpt",    "value": output_text},
            ],
            "metadata": {
                "trace_id":   r.trace_id,
                "promotion":  r.promotion,
                "L_total":    r.loss_report.get("L_total", 1.0),
                "reader_pull": r.reader_estimate.get("reader_pull", 0.0),
                "pii_removed": pii_count,
            },
            "_pii_count": pii_count,
        }
        return entry
