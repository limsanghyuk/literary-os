"""
V316: SLMDatasetBuilder
Trace Dataset → SLM Instruction-Tuning 학습 데이터 변환기.

핵심 역할:
  누적된 canonical/candidate trace를
  Sovereign SLM 파인튜닝용 데이터셋으로 변환.

출력 포맷:
  - Alpaca 스타일 (instruction/input/output)
  - OpenAI fine-tuning 스타일 (messages)
  - 품질 필터링 (L_total, reader_pull, ai_smell)

이것이 V316의 핵심:
  "좋은 씬의 생성 조건 전체를 instruction으로,
   생성 결과를 output으로 — 그것이 문학 SLM 학습 데이터다"

LLM 0회.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from literary_system.trace.trace_dataset_store import PromotionTier, TraceDatasetStore, TraceRecord


class SLMDatasetBuilder:
    """
    TraceDatasetStore → SLM 학습 데이터셋 변환기.
    """

    def __init__(self, store: TraceDatasetStore):
        self.store = store

    def build_alpaca_dataset(
        self,
        out_path: str | Path,
        max_L_total: float = 0.18,
        min_reader_pull: float = 0.30,
        max_ai_smell: float = 0.35,
    ) -> dict[str, Any]:
        """
        Alpaca 스타일 학습 데이터셋 생성.
        {instruction, input, output} 형태.
        """
        records = self._filter_records(max_L_total, min_reader_pull, max_ai_smell)
        dataset = []

        for r in records:
            entry = self._to_alpaca(r)
            if entry:
                dataset.append(entry)

        out_path = Path(out_path)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        return {
            "format":       "alpaca",
            "total_records": len(dataset),
            "output_path":  str(out_path),
            "quality_summary": self._quality_summary(records),
        }

    def build_openai_dataset(
        self,
        out_path: str | Path,
        max_L_total: float = 0.18,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        OpenAI fine-tuning 스타일 (messages 형식) 데이터셋.
        """
        if not system_prompt:
            system_prompt = (
                "당신은 한국 문학 창작 전문 시스템입니다. "
                "주어진 장르, 문체 DNA, 서사 의도, Literary State에 따라 "
                "절제된 압박형 산문을 생성합니다. "
                "감정 직설 표현 금지. 오브제/행동으로 감정을 대체합니다."
            )

        records = self._filter_records(max_L_total)
        dataset = []

        for r in records:
            messages = self._to_openai_messages(r, system_prompt)
            if messages:
                dataset.append({"messages": messages})

        out_path = Path(out_path)
        with open(out_path, "w", encoding="utf-8") as f:
            for entry in dataset:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return {
            "format":       "openai_jsonl",
            "total_records": len(dataset),
            "output_path":  str(out_path),
        }

    def build_quality_report(self, out_path: str | Path) -> dict[str, Any]:
        """
        데이터셋 품질 리포트.
        "어떤 씬이 왜 canonical이 됐는가"를 분석.
        """
        stats = self.store.statistics()
        all_records = list(self.store._index.values())

        # 장르별 평균 품질
        genre_quality: dict[str, list[float]] = {}
        for r in all_records:
            genre = r.seed_contract.get("genre", "unknown")
            genre_quality.setdefault(genre, []).append(r.loss_report.get("L_total", 1.0))

        genre_avg = {
            g: round(sum(ls) / len(ls), 4)
            for g, ls in genre_quality.items()
        }

        # 스타일 프로파일별 평균
        profile_quality: dict[str, list[float]] = {}
        for r in all_records:
            profile_quality.setdefault(r.style_dna_profile, []).append(
                r.loss_report.get("L_total", 1.0)
            )
        profile_avg = {
            p: round(sum(ls) / len(ls), 4)
            for p, ls in profile_quality.items()
        }

        # repair 효과 분석
        repaired = [r for r in all_records if r.repair_applied]
        repair_promotion = {}
        for r in repaired:
            repair_promotion[r.promotion] = repair_promotion.get(r.promotion, 0) + 1

        report = {
            "overview": stats,
            "genre_avg_L_total": genre_avg,
            "profile_avg_L_total": profile_avg,
            "repair_analysis": {
                "total_repaired": len(repaired),
                "repaired_by_tier": repair_promotion,
                "repair_success_rate": round(
                    sum(1 for r in repaired if r.promotion != PromotionTier.ARCHIVE)
                    / max(len(repaired), 1), 3
                ),
            },
            "knowledge_pressure_analysis": {
                "avg_pressure": round(
                    sum(r.knowledge_pressure for r in all_records)
                    / max(len(all_records), 1), 3
                ),
                "high_pressure_scenes": sum(
                    1 for r in all_records if r.knowledge_pressure > 0.6
                ),
            },
        }

        out_path = Path(out_path)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report

    # ── 내부 헬퍼 ─────────────────────────────────────────
    def _filter_records(
        self,
        max_L_total: float = 0.20,
        min_reader_pull: float = 0.0,
        max_ai_smell: float = 1.0,
    ) -> list[TraceRecord]:
        records = [
            r for r in self.store._index.values()
            if r.loss_report.get("L_total", 1.0) <= max_L_total
            and r.promotion != PromotionTier.ARCHIVE
            and r.reader_estimate.get("reader_pull", 0.0) >= min_reader_pull
            and r.reader_estimate.get("ai_smell_score", 1.0) <= max_ai_smell
        ]
        return sorted(records, key=lambda r: r.loss_report.get("L_total", 1.0))

    def _to_alpaca(self, r: TraceRecord) -> dict[str, Any] | None:
        """TraceRecord → Alpaca 형식."""
        output_text = "\n\n".join(
            f"[{sid}]\n{txt}"
            for sid, txt in r.render_output.items()
            if txt and txt.strip()
        )
        if not output_text.strip():
            return None

        instruction = (
            "다음 조건에 맞는 드라마/소설 장면을 생성하라. "
            "감정 직설 금지. 행동/오브제로 감정을 대체하라."
        )

        input_text = (
            f"장르: {r.seed_contract.get('genre', 'drama')}\n"
            f"문체: {r.style_dna_profile}\n"
            f"서사 의도: {r.macroarc_intent}\n"
            f"Literary State — SP:{r.literary_state_before.get('SP', 0):.2f} "
            f"RU:{r.literary_state_before.get('RU', 0):.2f} "
            f"ET:{r.literary_state_before.get('ET', 0):.2f}\n"
            f"씨드: {r.seed_contract.get('user_prompt', '')}\n"
            f"Promotion: {r.promotion} (L_total={r.loss_report.get('L_total', 0):.3f})"
        )

        return {
            "instruction": instruction,
            "input":       input_text,
            "output":      output_text,
            "metadata": {
                "trace_id":   r.trace_id,
                "promotion":  r.promotion,
                "L_total":    r.loss_report.get("L_total", 1.0),
                "reader_pull": r.reader_estimate.get("reader_pull", 0.0),
            },
        }

    def _to_openai_messages(
        self, r: TraceRecord, system_prompt: str
    ) -> list[dict] | None:
        """TraceRecord → OpenAI messages 형식."""
        output_text = "\n\n".join(
            f"[{sid}]\n{txt}"
            for sid, txt in r.render_output.items()
            if txt and txt.strip()
        )
        if not output_text.strip():
            return None

        user_msg = (
            f"[장르] {r.seed_contract.get('genre', 'drama')}\n"
            f"[문체] {r.style_dna_profile}\n"
            f"[의도] {r.macroarc_intent}\n"
            f"[State] SP={r.literary_state_before.get('SP', 0):.2f} "
            f"RU={r.literary_state_before.get('RU', 0):.2f}\n"
            f"[씨드] {r.seed_contract.get('user_prompt', '')}"
        )

        return [
            {"role": "system",    "content": system_prompt},
            {"role": "user",      "content": user_msg},
            {"role": "assistant", "content": output_text},
        ]

    def _quality_summary(self, records: list[TraceRecord]) -> dict[str, Any]:
        if not records:
            return {}
        l_totals = [r.loss_report.get("L_total", 1.0) for r in records]
        pulls    = [r.reader_estimate.get("reader_pull", 0.0) for r in records]
        return {
            "count":        len(records),
            "avg_L_total":  round(sum(l_totals) / len(l_totals), 4),
            "avg_reader_pull": round(sum(pulls) / len(pulls), 4),
            "best_L_total": round(min(l_totals), 4),
        }
