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
