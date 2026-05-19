"""
ProseStyleDataset — 한국 문학 스타일 레이블링 데이터셋 (V470)

ADR-008: Training Data Hygiene (CC-BY 라이선스 필터, PII 마스킹)
ADR-014: Fine-tune Lifecycle (데이터셋 카드 자동 생성)

설계:
  - CC-BY 라이선스 필터 (KOFICE/KOCCA 공공 도메인 허용)
  - 스타일 레이블: 로맨스/스릴러/SF/역사소설/현대소설 5종
  - SLM TrainingDataRegistry 연동
  - LLM-0: 규칙 기반 필터·분할 (외부 LLM 없음)
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class ProseStyle(str, Enum):
    ROMANCE = "romance"           # 로맨스
    THRILLER = "thriller"         # 스릴러/미스터리
    SF = "sf"                     # SF/판타지
    HISTORICAL = "historical"     # 역사소설
    CONTEMPORARY = "contemporary" # 현대소설
    UNKNOWN = "unknown"


class DatasetLicenseType(str, Enum):
    CC_BY = "cc-by"               # CC Attribution — 허용
    CC_BY_SA = "cc-by-sa"         # CC Attribution-ShareAlike — 허용
    CC_BY_NC = "cc-by-nc"         # NonCommercial — 비상업적만 허용
    PUBLIC_DOMAIN = "public_domain" # 공개 도메인 — 허용
    PROPRIETARY = "proprietary"   # 독점 — 금지
    UNKNOWN = "unknown"           # 미확인 — 금지 (안전 기본값)


class DataSource(str, Enum):
    KOFICE = "kofice"             # 한국문화예술위원회
    KOCCA = "kocca"               # 한국콘텐츠진흥원
    KLAP = "klap"                 # 한국문학번역원
    SYNTHETIC = "synthetic"       # 합성 데이터
    INTERNAL = "internal"         # 내부 생성 데이터


# ---------------------------------------------------------------------------
# 허용 라이선스
# ---------------------------------------------------------------------------

ALLOWED_LICENSES = {
    DatasetLicenseType.CC_BY,
    DatasetLicenseType.CC_BY_SA,
    DatasetLicenseType.PUBLIC_DOMAIN,
}

ALLOWED_SOURCES = {
    DataSource.KOFICE,
    DataSource.KOCCA,
    DataSource.KLAP,
    DataSource.SYNTHETIC,
    DataSource.INTERNAL,
}


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class ProseEntry:
    """단일 산문 샘플"""
    entry_id: str
    text: str
    style: ProseStyle
    source: DataSource
    license_type: DatasetLicenseType
    author: str = ""
    title: str = ""
    year: int | None = None
    language: str = "ko"
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.token_count == 0:
            # 간단한 한국어 토큰 추정 (공백 기준 × 1.5)
            self.token_count = int(len(self.text.split()) * 1.5)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "style": self.style.value,
            "source": self.source.value,
            "license_type": self.license_type.value,
            "author": self.author,
            "title": self.title,
            "year": self.year,
            "language": self.language,
            "token_count": self.token_count,
            "created_at": self.created_at,
        }


@dataclass
class DatasetSplit:
    train: list[ProseEntry]
    validation: list[ProseEntry]
    test: list[ProseEntry]

    @property
    def total(self) -> int:
        return len(self.train) + len(self.validation) + len(self.test)

    def to_dict(self) -> dict[str, Any]:
        return {
            "train_count": len(self.train),
            "validation_count": len(self.validation),
            "test_count": len(self.test),
            "total": self.total,
        }


@dataclass
class ProseDatasetCard:
    dataset_id: str
    name: str
    description: str
    license_types: list[str]
    sources: list[str]
    style_distribution: dict[str, int]
    total_entries: int
    total_tokens: int
    split_info: dict[str, int]
    created_at: str
    checksum: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "description": self.description,
            "license_types": self.license_types,
            "sources": self.sources,
            "style_distribution": self.style_distribution,
            "total_entries": self.total_entries,
            "total_tokens": self.total_tokens,
            "split_info": self.split_info,
            "created_at": self.created_at,
            "checksum": self.checksum,
        }


# ---------------------------------------------------------------------------
# ProseStyleDataset
# ---------------------------------------------------------------------------

class ProseStyleDataset:
    """
    ADR-008/014 한국 문학 스타일 파인튜닝 데이터셋.

    load(filters) → list[ProseEntry]
    license_check(entry) → bool
    split(entries, train_ratio, val_ratio) → DatasetSplit
    generate_card(dataset_id, entries) → ProseDatasetCard

    LLM-0: 필터·분할·카드 생성 모두 규칙 기반.
    """

    DEFAULT_TRAIN_RATIO = 0.8
    DEFAULT_VAL_RATIO = 0.1
    # test_ratio = 1.0 - train - val = 0.1

    def __init__(self) -> None:
        self._registry: list[ProseEntry] = []
        self._datasets: dict[str, ProseDatasetCard] = {}

    # ------------------------------------------------------------------
    # 데이터 등록
    # ------------------------------------------------------------------

    def add_entry(self, entry: ProseEntry) -> None:
        """샘플 등록 (라이선스 필터 통과 필요)"""
        if not self.license_check(entry):
            raise ValueError(
                f"ADR-008 위반: 허용되지 않는 라이선스 {entry.license_type.value} "
                f"(entry_id={entry.entry_id})"
            )
        self._registry.append(entry)

    def add_entries(self, entries: list[ProseEntry]) -> tuple[int, int]:
        """
        복수 샘플 등록. 라이선스 위반 건은 건너뜀.
        Returns: (added_count, skipped_count)
        """
        added = 0
        skipped = 0
        for entry in entries:
            if self.license_check(entry):
                self._registry.append(entry)
                added += 1
            else:
                skipped += 1
        return added, skipped

    # ------------------------------------------------------------------
    # 라이선스 검증
    # ------------------------------------------------------------------

    def license_check(self, entry: ProseEntry) -> bool:
        """
        ADR-008: CC-BY / CC-BY-SA / PUBLIC_DOMAIN만 허용.
        PROPRIETARY / UNKNOWN = 거부 (안전 기본값).
        """
        return entry.license_type in ALLOWED_LICENSES

    # ------------------------------------------------------------------
    # 로드 / 필터
    # ------------------------------------------------------------------

    def load(
        self,
        style: ProseStyle | None = None,
        source: DataSource | None = None,
        license_type: DatasetLicenseType | None = None,
        min_tokens: int = 0,
        max_tokens: int | None = None,
        language: str | None = None,
        limit: int | None = None,
    ) -> list[ProseEntry]:
        """
        필터 조합으로 샘플 로드.
        license_check() 통과 항목만 반환.
        """
        results = [e for e in self._registry if self.license_check(e)]

        if style is not None:
            results = [e for e in results if e.style == style]
        if source is not None:
            results = [e for e in results if e.source == source]
        if license_type is not None:
            results = [e for e in results if e.license_type == license_type]
        if min_tokens > 0:
            results = [e for e in results if e.token_count >= min_tokens]
        if max_tokens is not None:
            results = [e for e in results if e.token_count <= max_tokens]
        if language is not None:
            results = [e for e in results if e.language == language]
        if limit is not None:
            results = results[:limit]

        return results

    # ------------------------------------------------------------------
    # 데이터셋 분할
    # ------------------------------------------------------------------

    def split(
        self,
        entries: list[ProseEntry],
        train_ratio: float = DEFAULT_TRAIN_RATIO,
        val_ratio: float = DEFAULT_VAL_RATIO,
    ) -> DatasetSplit:
        """
        Stratified split — 스타일별 비율 유지.
        train + val + test = 1.0
        """
        if train_ratio + val_ratio >= 1.0:
            raise ValueError("train_ratio + val_ratio < 1.0 이어야 합니다.")

        # 스타일별 그룹
        by_style: dict[str, list[ProseEntry]] = {}
        for e in entries:
            by_style.setdefault(e.style.value, []).append(e)

        train_list: list[ProseEntry] = []
        val_list: list[ProseEntry] = []
        test_list: list[ProseEntry] = []

        for style_entries in by_style.values():
            n = len(style_entries)
            n_train = max(1, int(n * train_ratio))
            n_val = max(1, int(n * val_ratio)) if n > 2 else 0
            n_test = n - n_train - n_val

            train_list.extend(style_entries[:n_train])
            val_list.extend(style_entries[n_train:n_train + n_val])
            test_list.extend(style_entries[n_train + n_val:])

        return DatasetSplit(
            train=train_list,
            validation=val_list,
            test=test_list,
        )

    # ------------------------------------------------------------------
    # 데이터셋 카드 생성 (ADR-014)
    # ------------------------------------------------------------------

    def generate_card(
        self,
        dataset_id: str,
        entries: list[ProseEntry],
        name: str = "ProseStyleDataset",
        description: str = "한국 문학 스타일 파인튜닝 데이터셋",
    ) -> ProseDatasetCard:
        """ADR-014: 데이터셋 카드 자동 생성"""
        style_dist: dict[str, int] = {}
        total_tokens = 0
        licenses: set[str] = set()
        sources_set: set[str] = set()

        for e in entries:
            style_dist[e.style.value] = style_dist.get(e.style.value, 0) + 1
            total_tokens += e.token_count
            licenses.add(e.license_type.value)
            sources_set.add(e.source.value)

        # 데이터셋 분할 정보
        split = self.split(entries)
        split_info = split.to_dict()

        # 체크섬 (entry_id 목록 해시)
        ids_str = ",".join(sorted(e.entry_id for e in entries))
        checksum = hashlib.sha256(ids_str.encode()).hexdigest()[:16]

        card = ProseDatasetCard(
            dataset_id=dataset_id,
            name=name,
            description=description,
            license_types=sorted(licenses),
            sources=sorted(sources_set),
            style_distribution=style_dist,
            total_entries=len(entries),
            total_tokens=total_tokens,
            split_info=split_info,
            created_at=datetime.now(timezone.utc).isoformat(),
            checksum=checksum,
        )
        self._datasets[dataset_id] = card
        return card

    def get_card(self, dataset_id: str) -> ProseDatasetCard | None:
        return self._datasets.get(dataset_id)

    # ------------------------------------------------------------------
    # 통계
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        entries = self._registry
        style_dist: dict[str, int] = {}
        license_dist: dict[str, int] = {}
        for e in entries:
            style_dist[e.style.value] = style_dist.get(e.style.value, 0) + 1
            license_dist[e.license_type.value] = license_dist.get(e.license_type.value, 0) + 1
        return {
            "total_entries": len(entries),
            "style_distribution": style_dist,
            "license_distribution": license_dist,
            "total_tokens": sum(e.token_count for e in entries),
            "datasets_registered": len(self._datasets),
        }


# ---------------------------------------------------------------------------
# 편의 팩토리 함수
# ---------------------------------------------------------------------------

def make_entry(
    text: str,
    style: ProseStyle,
    source: DataSource = DataSource.SYNTHETIC,
    license_type: DatasetLicenseType = DatasetLicenseType.CC_BY,
    **kwargs: Any,
) -> ProseEntry:
    """ProseEntry 빠른 생성 헬퍼"""
    return ProseEntry(
        entry_id=str(uuid.uuid4()),
        text=text,
        style=style,
        source=source,
        license_type=license_type,
        **kwargs,
    )


LicenseType = DatasetLicenseType  # V579 backward-compat alias

DatasetCard = ProseDatasetCard  # V579 backward-compat alias
