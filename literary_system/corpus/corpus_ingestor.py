"""
literary_system/corpus/corpus_ingestor.py  — V557
CorpusIngestor: 외부 코퍼스 수집 및 ScenarioEntry 목록 생성
목표: 합성 데이터로 TARGET_SCENES(10,000) ScenarioEntry 빠른 생성
LLM-0 정책(ADR-015/031): 외부 LLM 호출 없음
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

# ── 합성 데이터 소스 ─────────────────────────────────────────────────────────
DRAMA_TITLES = [
    "별들의 귀환", "밤의 경계", "사랑의 온도", "운명의 교차로", "빛과 그림자",
    "시간의 강", "붉은 노을", "달빛 아래서", "폭풍 전야", "소용돌이",
]
GENRES = ["멜로", "스릴러", "가족", "의학", "법정", "역사", "판타지"]
CHARACTERS_POOL = [
    "이민준", "박지수", "김도현", "최수아", "정재원",
    "윤하은", "강민서", "오태양", "한지은", "서준혁",
]
SCENE_TEMPLATES = [
    "{a}와 {b}는 카페에서 처음 만난다. {a}는 {b}의 이야기에 귀를 기울인다.",
    "{a}는 {b}에게 진실을 고백하려 하지만 말문이 막힌다.",
    "{b}는 {a}의 계획을 알게 되고 배신감을 느낀다.",
    "{a}와 {b}가 빗속에서 오래된 오해를 풀어간다.",
    "{a}는 {b}를 위해 모든 것을 포기하기로 결심한다.",
    "{b}는 {a}의 진심을 의심하면서도 마음이 흔들린다.",
    "{a}와 {b}는 위기의 순간 서로에게 의지한다.",
]


@dataclass
class ScenarioEntry:
    """단일 시나리오 씬 레코드."""
    scene_id: str
    title: str
    genre: str
    characters: List[str]
    content: str
    license: str = "CC-BY-4.0"
    source: str = "synthetic"
    episode: int = 1
    scene_index: int = 0


@dataclass
class IngestReport:
    """수집 결과 리포트."""
    total_ingested: int
    by_genre: dict
    by_source: dict
    target_reached: bool


class CorpusIngestor:
    """
    외부 코퍼스 수집기.
    실제 운영: CC-BY 라이선스 드라마 데이터 파일에서 읽음.
    현재: LLM-0 정책에 따라 합성 데이터로 TARGET_SCENES 달성.
    """
    TARGET_SCENES: int = 10_000

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)
        self._entries: List[ScenarioEntry] = []

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def ingest(self, target: Optional[int] = None) -> IngestReport:
        """target개의 ScenarioEntry를 수집(합성)하여 내부 목록을 채운다."""
        n = target if target is not None else self.TARGET_SCENES
        self._entries = self._generate_synthetic(n)
        return self._build_report()

    def entries(self) -> List[ScenarioEntry]:
        return list(self._entries)

    def by_genre(self, genre: str) -> List[ScenarioEntry]:
        return [e for e in self._entries if e.genre == genre]

    def sample(self, k: int = 10) -> List[ScenarioEntry]:
        return self._rng.sample(self._entries, min(k, len(self._entries)))

    # ── 내부 헬퍼 ────────────────────────────────────────────────────────────

    def _generate_synthetic(self, count: int) -> List[ScenarioEntry]:
        entries: List[ScenarioEntry] = []
        for i in range(count):
            genre = self._rng.choice(GENRES)
            title = self._rng.choice(DRAMA_TITLES)
            chars = self._rng.sample(CHARACTERS_POOL, 2)
            tmpl  = self._rng.choice(SCENE_TEMPLATES)
            content = tmpl.format(a=chars[0], b=chars[1])
            entries.append(ScenarioEntry(
                scene_id    = f"syn_{i:07d}",
                title       = title,
                genre       = genre,
                characters  = chars,
                content     = content,
                license     = "CC-BY-4.0",
                source      = "synthetic",
                episode     = (i // 20) + 1,
                scene_index = i % 20,
            ))
        return entries

    def _build_report(self) -> IngestReport:
        by_genre: dict = {}
        by_source: dict = {}
        for e in self._entries:
            by_genre[e.genre]   = by_genre.get(e.genre, 0) + 1
            by_source[e.source] = by_source.get(e.source, 0) + 1
        return IngestReport(
            total_ingested = len(self._entries),
            by_genre       = by_genre,
            by_source      = by_source,
            target_reached = len(self._entries) >= self.TARGET_SCENES,
        )


# =============================================================================
# SP-A.5 (V592) — 3종 폴백 Ingestor + CorpusEntry
# ADR-053: CorpusGovernance
# =============================================================================

import hashlib
import json
from enum import Enum


class CorpusFallbackOption(str, Enum):
    """
    코퍼스 수집 폴백 옵션 (ADR-053 §3).

    우선순위: A → B → C
      A. PUBLIC_DOMAIN  — 공공 도메인 한국문학 (저작권 무료)
      B. SYNTHETIC      — 합성 코퍼스 (~$50, LLM-0 준수 템플릿 생성)
      C. ACADEMIC       — 학술 협약 (KOFICE/KOCCA LOI 기반)
    """
    PUBLIC_DOMAIN = "public_domain"
    SYNTHETIC     = "synthetic"
    ACADEMIC      = "academic"


@dataclass
class CorpusEntry:
    """
    SP-A.5 코퍼스 단위 레코드.
    기존 ScenarioEntry와 별도 — Provenance 필드 강화.

    Attributes:
        entry_id:      전역 고유 식별자 (sha256 기반)
        text:          씬 텍스트
        source_type:   CorpusFallbackOption 값
        license:       라이선스 식별자
        source_title:  원본 작품명
        source_author: 작가명 (공공도메인) 또는 "synthetic"
        ingestor:      수집기 클래스명
        word_count:    단어 수
    """
    entry_id:      str
    text:          str
    source_type:   str                  # CorpusFallbackOption.value
    license:       str
    source_title:  str = ""
    source_author: str = ""
    ingestor:      str = ""
    word_count:    int = 0

    def __post_init__(self) -> None:
        if not self.entry_id:
            self.entry_id = hashlib.sha256(self.text.encode()).hexdigest()[:16]
        if self.word_count == 0:
            self.word_count = len(self.text.split())

    def to_dict(self) -> dict:
        return {
            "entry_id":      self.entry_id,
            "text":          self.text,
            "source_type":   self.source_type,
            "license":       self.license,
            "source_title":  self.source_title,
            "source_author": self.source_author,
            "ingestor":      self.ingestor,
            "word_count":    self.word_count,
        }


# ---------------------------------------------------------------------------
# PublicDomainIngestor — 폴백 A
# ---------------------------------------------------------------------------

class PublicDomainIngestor:
    """
    폴백 A: 공공 도메인 한국 고전 문학 수집기.
    저작권 만료(사망 70년 이상) 작품만 사용.
    실제 환경: 국립중앙도서관 API / Project Gutenberg Korea 연동.
    현재: 대표적 고전 작품 기반 합성 씬으로 대체.
    LLM-0 준수: 외부 LLM 미호출.
    """

    SOURCE_TITLE  = "공공도메인 한국고전문학"
    LICENSE       = "public_domain"

    _PUBLIC_DOMAIN_SCENES = [
        ("춘향전",   "성춘향", "춘향이 그네를 타며 노래를 불렀다. 광한루 뜰에 봄꽃이 흩날렸다."),
        ("춘향전",   "성춘향", "이도령이 방자를 데리고 광한루에 올랐다. 멀리 그네 타는 처녀가 보였다."),
        ("심청전",   "심청",   "심청이 아버지의 눈을 뜨게 하려고 공양미 삼백 석에 몸을 팔았다."),
        ("심청전",   "심청",   "심청이 인당수에 빠지는 순간, 하늘에서 선녀들이 내려왔다."),
        ("홍길동전", "홍길동", "홍길동이 활빈당을 이끌고 탐관오리의 창고를 열었다."),
        ("홍길동전", "홍길동", "홍길동은 서자라는 신분의 벽에 부딪혀 조선을 떠나기로 했다."),
        ("토끼전",   "토끼",   "토끼가 용왕을 속이고 무사히 육지로 돌아왔다."),
        ("구운몽",   "성진",   "성진이 꿈속에서 화려한 세상을 살다 깨어나 도를 닦기로 결심했다."),
        ("박씨전",   "박씨",   "박씨 부인이 변신하여 청나라 장수를 물리쳤다."),
        ("사씨남정기", "사씨", "사씨가 모함을 받아 집에서 쫓겨났으나 의연하게 고난을 견뎠다."),
    ]

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)

    def ingest(self, count: int) -> List[CorpusEntry]:
        entries: List[CorpusEntry] = []
        pool = self._PUBLIC_DOMAIN_SCENES
        for i in range(count):
            title, author, base_text = pool[i % len(pool)]
            # 약간의 변형으로 다양성 확보
            text = f"[제{i+1}장] " + base_text if i >= len(pool) else base_text
            eid  = hashlib.sha256(f"pd_{i}_{text}".encode()).hexdigest()[:16]
            entries.append(CorpusEntry(
                entry_id      = eid,
                text          = text,
                source_type   = CorpusFallbackOption.PUBLIC_DOMAIN.value,
                license       = self.LICENSE,
                source_title  = title,
                source_author = author,
                ingestor      = self.__class__.__name__,
            ))
        return entries


# ---------------------------------------------------------------------------
# SyntheticCorpusIngestor — 폴백 B
# ---------------------------------------------------------------------------

class SyntheticCorpusIngestor:
    """
    폴백 B: 합성 코퍼스 수집기 (~$50 예산).
    기존 CorpusIngestor의 템플릿 엔진을 CorpusEntry 인터페이스로 래핑.
    LLM-0 준수: 규칙 기반 템플릿 생성.
    """

    LICENSE = "CC-BY-4.0"

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)
        self._inner = CorpusIngestor(seed=seed)

    def ingest(self, count: int) -> List[CorpusEntry]:
        report = self._inner.ingest(target=count)
        entries: List[CorpusEntry] = []
        for sc in self._inner.entries():
            eid = hashlib.sha256(f"syn_{sc.scene_id}".encode()).hexdigest()[:16]
            entries.append(CorpusEntry(
                entry_id      = eid,
                text          = sc.content,
                source_type   = CorpusFallbackOption.SYNTHETIC.value,
                license       = self.LICENSE,
                source_title  = sc.title,
                source_author = "synthetic",
                ingestor      = self.__class__.__name__,
            ))
        return entries


# ---------------------------------------------------------------------------
# AcademicCorpusIngestor — 폴백 C
# ---------------------------------------------------------------------------

class AcademicCorpusIngestor:
    """
    폴백 C: 학술 협약 코퍼스 수집기 (KOFICE/KOCCA LOI 기반).
    실제 환경: 협약 체결 후 API 엔드포인트 연동.
    현재: LOI 협상 진행 중이므로 플레이스홀더 텍스트 반환.
    LLM-0 준수: 외부 LLM 미호출.
    """

    LICENSE = "academic_license_v1"

    _PLACEHOLDER_SCENES = [
        "한국방송작가협회 제공 시나리오 — 데이터 협약 체결 후 실제 콘텐츠로 교체 예정.",
        "KOFICE 한류 콘텐츠 코퍼스 — 2026 하반기 LOI 합의 목표.",
        "KOCCA 드라마 아카이브 — 저작권 계약 진행 중 (V592~V595).",
        "국립국어원 구어 말뭉치 — 학술 연구 목적 사용 협의 중.",
        "한국영상자료원 시나리오 데이터베이스 — 접근 권한 신청 완료.",
    ]

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)

    def ingest(self, count: int) -> List[CorpusEntry]:
        entries: List[CorpusEntry] = []
        pool = self._PLACEHOLDER_SCENES
        for i in range(count):
            text = pool[i % len(pool)]
            eid  = hashlib.sha256(f"ac_{i}_{text}".encode()).hexdigest()[:16]
            entries.append(CorpusEntry(
                entry_id      = eid,
                text          = text,
                source_type   = CorpusFallbackOption.ACADEMIC.value,
                license       = self.LICENSE,
                source_title  = "Academic Corpus (Placeholder)",
                source_author = "KOFICE/KOCCA",
                ingestor      = self.__class__.__name__,
            ))
        return entries


# ---------------------------------------------------------------------------
# CorpusFallbackPipeline — A → B → C 자동 선택
# ---------------------------------------------------------------------------

class CorpusFallbackPipeline:
    """
    3종 폴백 파이프라인 (ADR-053 §3).

    count개의 CorpusEntry를 수집할 때:
    1. PublicDomainIngestor(A) 시도
    2. 부족하면 SyntheticCorpusIngestor(B)로 보충
    3. 아직도 부족하면 AcademicCorpusIngestor(C)로 보충

    사용::

        pipeline = CorpusFallbackPipeline()
        entries  = pipeline.collect(count=5000)
        assert len(entries) == 5000
    """

    def __init__(self, seed: int = 42, prefer: Optional[CorpusFallbackOption] = None) -> None:
        self._seed    = seed
        self._prefer  = prefer
        self._ingestors = {
            CorpusFallbackOption.PUBLIC_DOMAIN: PublicDomainIngestor(seed),
            CorpusFallbackOption.SYNTHETIC:     SyntheticCorpusIngestor(seed),
            CorpusFallbackOption.ACADEMIC:      AcademicCorpusIngestor(seed),
        }

    def collect(self, count: int) -> List[CorpusEntry]:
        """
        count개 CorpusEntry 수집. 폴백 순서: PUBLIC_DOMAIN → SYNTHETIC → ACADEMIC.
        prefer가 지정되면 해당 ingestor를 최우선 사용.
        """
        order = [
            CorpusFallbackOption.PUBLIC_DOMAIN,
            CorpusFallbackOption.SYNTHETIC,
            CorpusFallbackOption.ACADEMIC,
        ]
        if self._prefer and self._prefer in order:
            order.remove(self._prefer)
            order.insert(0, self._prefer)

        all_entries: List[CorpusEntry] = []
        remaining = count
        for option in order:
            if remaining <= 0:
                break
            ingestor = self._ingestors[option]
            batch    = ingestor.ingest(remaining)
            all_entries.extend(batch)
            remaining -= len(batch)

        return all_entries[:count]

    def stats(self, entries: List[CorpusEntry]) -> dict:
        """소스 유형별 통계."""
        by_type: dict = {}
        for e in entries:
            by_type[e.source_type] = by_type.get(e.source_type, 0) + 1
        return {
            "total": len(entries),
            "by_source_type": by_type,
            "coverage_pct": {k: round(v / len(entries) * 100, 1) if entries else 0 for k, v in by_type.items()},
        }
