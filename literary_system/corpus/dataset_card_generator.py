"""
SP-A.6 (V593) — CorpusDatasetCardGenerator: HuggingFace 표준 Dataset README

기존 literary_system/slm/dataset_card_generator.py (DatasetCard/DatasetCardGenerator)와 별도.
코퍼스 수집 후 HuggingFace 데이터셋 카드 생성 — 코퍼스 전용.

ADR-053 참조.
LLM-0 준수: 외부 LLM 호출 없음.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from literary_system.corpus.corpus_ingestor import CorpusEntry
    from literary_system.corpus.corpus_validator import CorpusEntryValidationReport


# ---------------------------------------------------------------------------
# CorpusDatasetCard — HuggingFace 표준 카드 구조
# (기존 slm/DatasetCard와 별도 — 코퍼스 전용)
# ---------------------------------------------------------------------------

@dataclass
class CorpusDatasetCard:
    """
    HuggingFace 표준 Dataset README 구조.
    (기존 slm/dataset_card_generator.py DatasetCard와 별도 — 코퍼스 전용)

    Attributes:
        dataset_name:   데이터셋 이름
        language:       ["ko"]
        license:        라이선스 집합
        task_categories: 태스크 목록
        size_category:  HF 크기 범주
        total_entries:  총 항목 수
        passed_entries: 검증 통과 항목 수
        pass_rate:      검증 통과율
        by_source:      소스 유형별 통계
        created_at:     생성 시각 (ISO8601 UTC)
        description:    데이터셋 설명
        citation:       인용 정보
    """
    dataset_name:    str
    language:        List[str] = field(default_factory=lambda: ["ko"])
    license:         List[str] = field(default_factory=list)
    task_categories: List[str] = field(default_factory=lambda: [
        "text-generation", "text2text-generation"
    ])
    size_category:   str = "1K<n<10K"
    total_entries:   int = 0
    passed_entries:  int = 0
    pass_rate:       float = 0.0
    by_source:       dict = field(default_factory=dict)
    created_at:      str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    description:     str = ""
    citation:        str = ""

    # ── YAML 헤더 ──────────────────────────────────────────

    def to_yaml_header(self) -> str:
        """HuggingFace YAML front-matter 생성."""
        lines = ["---"]
        lines.append(f"dataset_name: {self.dataset_name}")
        lines.append("language:")
        for lang in self.language:
            lines.append(f"  - {lang}")
        lines.append("license:")
        for lic in sorted(set(self.license)):
            lines.append(f"  - {lic}")
        lines.append("task_categories:")
        for task in self.task_categories:
            lines.append(f"  - {task}")
        lines.append("size_categories:")
        lines.append(f"  - {self.size_category}")
        lines.append("---")
        return "\n".join(lines)

    # ── Markdown 본문 ───────────────────────────────────────

    def to_markdown(self) -> str:
        """HuggingFace 표준 README 마크다운 생성."""
        lines = [
            self.to_yaml_header(),
            "",
            f"# {self.dataset_name}",
            "",
            "> **Literary OS** 코퍼스 데이터셋 (ADR-053 CorpusGovernance)",
            "",
            "## 설명",
            "",
            self.description or "한국 드라마·소설 장면 텍스트 코퍼스.",
            "",
            "## 통계",
            "",
            "| 항목 | 값 |",
            "|------|-----|",
            f"| 총 항목 수 | {self.total_entries:,} |",
            f"| 검증 통과 | {self.passed_entries:,} |",
            f"| 통과율 | {self.pass_rate:.1%} |",
            f"| 생성일시 | {self.created_at[:10]} |",
            "",
            "### 소스 유형별 분포",
            "",
        ]
        if self.by_source:
            lines.append("| 소스 유형 | 항목 수 |")
            lines.append("|-----------|---------|")
            for k, v in sorted(self.by_source.items()):
                lines.append(f"| {k} | {v:,} |")
        lines += [
            "",
            "## 라이선스",
            "",
            ", ".join(sorted(set(self.license))) or "mixed",
            "",
            "## 인용",
            "",
            self.citation or "Literary OS Project (2026). Korean Drama/Novel Corpus.",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "dataset_name":    self.dataset_name,
            "language":        self.language,
            "license":         self.license,
            "task_categories": self.task_categories,
            "size_category":   self.size_category,
            "total_entries":   self.total_entries,
            "passed_entries":  self.passed_entries,
            "pass_rate":       self.pass_rate,
            "by_source":       self.by_source,
            "created_at":      self.created_at,
            "description":     self.description,
            "citation":        self.citation,
        }


# ---------------------------------------------------------------------------
# CorpusDatasetCardGenerator
# (기존 slm/DatasetCardGenerator와 별도 — 코퍼스 전용)
# ---------------------------------------------------------------------------

def _hf_size_category(n: int) -> str:
    """HuggingFace size_categories 변환."""
    if n < 1_000:
        return "n<1K"
    elif n < 10_000:
        return "1K<n<10K"
    elif n < 100_000:
        return "10K<n<100K"
    elif n < 1_000_000:
        return "100K<n<1M"
    return "1M<n<10M"


class CorpusDatasetCardGenerator:
    """
    HuggingFace 표준 Dataset README(CorpusDatasetCard) 생성기.
    (기존 slm/DatasetCardGenerator와 별도 — 코퍼스 전용)

    LLM-0 준수: 외부 LLM 호출 없음.

    Usage::

        gen = CorpusDatasetCardGenerator("los-corpus-v1")
        card = gen.generate(entries, validation_report)
        gen.save(card, "README.md")
    """

    def __init__(
        self,
        dataset_name: str = "los-corpus",
        description: str = "",
        citation: str = "",
    ) -> None:
        self._name = dataset_name
        self._desc = description
        self._cite = citation

    def generate(
        self,
        entries: List["CorpusEntry"],
        validation_report: Optional["CorpusEntryValidationReport"] = None,
    ) -> CorpusDatasetCard:
        """
        CorpusEntry 목록과 검증 보고서로 CorpusDatasetCard 생성.

        Args:
            entries:            CorpusEntry 목록
            validation_report:  CorpusEntryValidationReport (optional)

        Returns:
            CorpusDatasetCard
        """
        # 소스 유형별 통계
        by_source: dict = {}
        licenses: List[str] = []
        for e in entries:
            by_source[e.source_type] = by_source.get(e.source_type, 0) + 1
            if e.license and e.license not in licenses:
                licenses.append(e.license)

        total   = len(entries)
        passed  = validation_report.passed if validation_report else total
        p_rate  = validation_report.pass_rate if validation_report else 1.0

        return CorpusDatasetCard(
            dataset_name    = self._name,
            license         = licenses,
            size_category   = _hf_size_category(total),
            total_entries   = total,
            passed_entries  = passed,
            pass_rate       = p_rate,
            by_source       = by_source,
            description     = self._desc or f"Literary OS 한국어 코퍼스 — {total:,}개 장면",
            citation        = self._cite,
        )

    def save(self, card: CorpusDatasetCard, path: str) -> None:
        """CorpusDatasetCard를 markdown 파일로 저장."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(card.to_markdown())
