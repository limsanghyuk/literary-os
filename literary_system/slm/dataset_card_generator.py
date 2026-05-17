"""
literary_system/slm/dataset_card_generator.py
V494: DatasetCardGenerator — HuggingFace DatasetCard 형식 메타데이터 자동 생성

SLM 수출 파이프라인 최종 단계에서 학습 데이터셋의 메타데이터 카드를 생성한다.
HuggingFace Hub DatasetCard YAML 형식을 따르며 라이선스·통계·샘플을 포함한다.

ADR-008 준수: 라이선스 및 데이터 출처 정보 의무 기재
"""
from __future__ import annotations

import datetime
import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── 메타데이터 타입 ───────────────────────────────────────────────────
@dataclass
class DatasetStats:
    """데이터셋 통계 요약."""
    total_records:   int
    train_count:     int
    val_count:       int
    test_count:      int
    avg_text_length: float
    min_text_length: int
    max_text_length: int
    avg_quality:     float
    tier_distribution: Dict[str, int] = field(default_factory=dict)
    pii_scrubbed:    int = 0
    dedup_removed:   int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_records":    self.total_records,
            "splits":           {"train": self.train_count, "val": self.val_count, "test": self.test_count},
            "text_length":      {"avg": round(self.avg_text_length, 1),
                                  "min": self.min_text_length, "max": self.max_text_length},
            "avg_quality_score": round(self.avg_quality, 3),
            "tier_distribution": self.tier_distribution,
            "pii_scrubbed":      self.pii_scrubbed,
            "dedup_removed":     self.dedup_removed,
        }


@dataclass
class DatasetCard:
    """HuggingFace DatasetCard 호환 메타데이터 카드."""
    dataset_name:   str
    version:        str
    description:    str
    language:       List[str]
    license:        str
    task_categories: List[str]
    stats:          DatasetStats
    source:         str = "Literary OS"
    created_at:     str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    authors:        List[str] = field(default_factory=list)
    tags:           List[str] = field(default_factory=list)
    samples:        List[Dict[str, Any]] = field(default_factory=list)  # 최대 3개 예시
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_yaml_header(self) -> str:
        """HuggingFace README.md YAML front-matter 형식."""
        lines = [
            "---",
            f"dataset_info:",
            f"  dataset_name: {self.dataset_name}",
            f"  version: {self.version}",
            f"language:",
        ]
        for lang in self.language:
            lines.append(f"  - {lang}")
        lines += [
            f"license: {self.license}",
            f"task_categories:",
        ]
        for cat in self.task_categories:
            lines.append(f"  - {cat}")
        lines += [
            f"tags:",
        ]
        for tag in self.tags:
            lines.append(f"  - {tag}")
        lines += [
            f"source: {self.source}",
            f"created_at: {self.created_at}",
            "---",
        ]
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """전체 DatasetCard 마크다운 문서."""
        stats_d = self.stats.to_dict()
        sample_block = ""
        if self.samples:
            sample_lines = ["## 데이터 샘플\n"]
            for i, s in enumerate(self.samples[:3], 1):
                text = str(s.get("text", ""))[:200]
                sample_lines.append(f"**샘플 {i}** (tier={s.get('tier','?')}, score={s.get('quality_score','?')})\n```\n{text}\n```\n")
            sample_block = "\n".join(sample_lines)

        return f"""{self.to_yaml_header()}

# {self.dataset_name} v{self.version}

{self.description}

## 데이터셋 정보

| 항목 | 값 |
|------|----|
| 총 레코드 | {stats_d['total_records']} |
| Train | {stats_d['splits']['train']} |
| Val | {stats_d['splits']['val']} |
| Test | {stats_d['splits']['test']} |
| 평균 텍스트 길이 | {stats_d['text_length']['avg']} 자 |
| 평균 품질 점수 | {stats_d['avg_quality_score']} |
| PII 스크럽 | {stats_d['pii_scrubbed']} 건 |
| 중복 제거 | {stats_d['dedup_removed']} 건 |

## 티어 분포

{chr(10).join(f'- **{k}**: {v}건' for k, v in stats_d['tier_distribution'].items())}

## 라이선스

{self.license}

{sample_block}
## 출처

{self.source}

생성일: {self.created_at}
"""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name":    self.dataset_name,
            "version":         self.version,
            "description":     self.description,
            "language":        self.language,
            "license":         self.license,
            "task_categories": self.task_categories,
            "stats":           self.stats.to_dict(),
            "source":          self.source,
            "created_at":      self.created_at,
            "authors":         self.authors,
            "tags":            self.tags,
            "samples_count":   len(self.samples),
        }


# ── 핵심 클래스 ───────────────────────────────────────────────────────
class DatasetCardGenerator:
    """
    SLM 학습 데이터셋에 대한 DatasetCard 자동 생성기.

    입력: train/val/test dict 리스트 + 메타데이터 파라미터
    출력: DatasetCard (마크다운 / YAML / JSON 직렬화 가능)

    ADR-008 준수: ALLOWED_LICENSES에 포함되지 않은 라이선스는 ValueError 발생
    """

    DEFAULT_LANGUAGE       = ["ko"]
    DEFAULT_LICENSE        = "cc-by-sa-4.0"
    DEFAULT_TASK_CATEGORIES = ["text-generation", "conditional-text-generation"]
    DEFAULT_TAGS           = ["korean-drama", "literary-os", "slm-export"]

    # ADR-008: 허용 라이선스 목록 (독점·비공개 라이선스 차단)
    ALLOWED_LICENSES: set = {
        "cc-by-4.0", "cc-by-sa-4.0", "cc-by-nc-4.0", "cc-by-nc-sa-4.0",
        "cc0-1.0", "public-domain",
        "apache-2.0", "mit", "gpl-3.0", "lgpl-3.0",
        "internal",          # 내부 사용 허가
        "cc-by", "cc-by-sa", # 단축형 허용
    }

    def __init__(
        self,
        dataset_name:    str = "literary-os-drama-slm",
        version:         str = "1.0.0",
        description:     str = "Literary OS SLM 수출 드라마 씬 데이터셋",
        language:        Optional[List[str]] = None,
        license:         str = "cc-by-sa-4.0",
        task_categories: Optional[List[str]] = None,
        tags:            Optional[List[str]] = None,
        authors:         Optional[List[str]] = None,
        source:          str = "Literary OS",
        n_samples:       int = 3,
    ) -> None:
        self._name        = dataset_name
        self._version     = version
        self._description = description
        self._language    = language or self.DEFAULT_LANGUAGE
        self._license     = license
        self._task_cats   = task_categories or self.DEFAULT_TASK_CATEGORIES
        self._tags        = tags or self.DEFAULT_TAGS
        self._authors     = authors or []
        self._source      = source
        self._n_samples   = n_samples

    def _compute_stats(
        self,
        train: List[Dict], val: List[Dict], test: List[Dict],
        pii_scrubbed: int = 0, dedup_removed: int = 0,
    ) -> DatasetStats:
        all_records = train + val + test
        texts = [str(r.get("text", "")) for r in all_records]
        lengths = [len(t) for t in texts] if texts else [0]
        qualities = [float(r.get("quality_score", 1.0)) for r in all_records]
        tier_dist: Dict[str, int] = {}
        for r in all_records:
            t = str(r.get("tier", "A"))
            tier_dist[t] = tier_dist.get(t, 0) + 1

        return DatasetStats(
            total_records   = len(all_records),
            train_count     = len(train),
            val_count       = len(val),
            test_count      = len(test),
            avg_text_length = sum(lengths) / len(lengths) if lengths else 0.0,
            min_text_length = min(lengths) if lengths else 0,
            max_text_length = max(lengths) if lengths else 0,
            avg_quality     = sum(qualities) / len(qualities) if qualities else 0.0,
            tier_distribution = tier_dist,
            pii_scrubbed    = pii_scrubbed,
            dedup_removed   = dedup_removed,
        )

    def generate(
        self,
        train: List[Dict[str, Any]],
        val:   List[Dict[str, Any]],
        test:  List[Dict[str, Any]],
        pii_scrubbed: int = 0,
        dedup_removed: int = 0,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> DatasetCard:
        """DatasetCard 생성.

        ADR-008: ALLOWED_LICENSES에 없는 라이선스는 ValueError 발생.
        """
        # ADR-008 라이선스 검증
        if self._license not in self.ALLOWED_LICENSES:
            raise ValueError(
                f"ADR-008 위반: 허용되지 않는 라이선스 '{self._license}'. "
                f"허용 목록: {sorted(self.ALLOWED_LICENSES)}"
            )
        stats = self._compute_stats(train, val, test, pii_scrubbed, dedup_removed)
        # 샘플: train에서 최대 n_samples개 선택
        samples = [r for r in train[:self._n_samples]]

        return DatasetCard(
            dataset_name    = self._name,
            version         = self._version,
            description     = self._description,
            language        = self._language,
            license         = self._license,
            task_categories = self._task_cats,
            stats           = stats,
            source          = self._source,
            authors         = self._authors,
            tags            = self._tags,
            samples         = samples,
            extra_metadata  = extra_metadata or {},
        )

    def save(
        self,
        card: DatasetCard,
        output_dir: str,
        filename: str = "README.md",
    ) -> Dict[str, str]:
        """DatasetCard를 마크다운 + JSON으로 저장."""
        out = pathlib.Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        md_path   = out / filename
        json_path = out / "dataset_card.json"
        md_path.write_text(card.to_markdown(), encoding="utf-8")
        json_path.write_text(
            json.dumps(card.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"markdown": str(md_path), "json": str(json_path)}
