"""
V423: ManuscriptImporter v2
텍스트 원고(txt/md) → 씬 단위 분리 → NKGGraphStore 저장 + SceneCorpusBuilder 연결.

ADR-001: L3 Orchestration 레이어 — SchemaMapper 경유 없이 literary_system 직접 접근 허용.
ADR-005: 기존 routers/io.py stub 인터페이스 완전 보존 (scene_count, imported_scene_ids).

연결 신경망:
  ImportRequest.content
  → SceneParser.split()        : 구분자(#씬/## 씬/---) 기반 분리
  → SceneNormalizer.normalize(): 메타데이터 추출 (episode, characters)
  → NKGGraphStore.add_node()   : SceneNode 저장
  → SceneCorpusBuilder.build() : SceneFeature 추출 (ManuscriptLearner 학습용)
"""
from __future__ import annotations

import re
import uuid
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ── literary_system 연결 ─────────────────────────────────────
try:
    from literary_system.nkg.graph_store import NKGGraphStore
    from literary_system.nkg.schema import SceneNode, NKGNodeType
    from literary_system.learning.scene_corpus_builder import SceneCorpusBuilder
    from literary_system.prose.surface_scorer import ReaderSurfaceScorer, SurfaceScore
    _CORE = True
except ImportError:
    _CORE = False

# ── 씬 구분자 패턴 ────────────────────────────────────────────
_SCENE_DELIMITERS = [
    re.compile(r"^#{1,3}\s*씬\s*\d*", re.MULTILINE),   # # 씬 1, ## 씬, ### 씬3
    re.compile(r"^#{1,3}\s*Scene\s*\d*", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^---+\s*$", re.MULTILINE),              # --- 구분선
    re.compile(r"^\*\*\*+\s*$", re.MULTILINE),           # *** 구분선
    re.compile(r"^\[씬\s*\d+\]", re.MULTILINE),          # [씬 1]
]

# ── 캐릭터명 추출 패턴 (대화 화자) ────────────────────────────
_CHARACTER_PATTERN = re.compile(
    r'^([가-힣A-Za-z]{2,10})\s*[:：]\s*["""\'"\'「]',
    re.MULTILINE,
)


@dataclass
class ParsedScene:
    """단일 씬 파싱 결과."""
    scene_id: str
    episode: int
    content: str
    characters: list[str] = field(default_factory=list)
    word_count: int = 0
    char_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class SceneParser:
    """텍스트 → ParsedScene 목록 분리."""

    def split(self, text: str, series_id: str, base_episode: int = 1) -> list[ParsedScene]:
        """구분자 기반 씬 분리. 구분자 미발견 시 단락 기반 분리."""
        # 최적 구분자 선택
        best_pattern = None
        best_count = 0
        for pat in _SCENE_DELIMITERS:
            count = len(pat.findall(text))
            if count > best_count:
                best_count = count
                best_pattern = pat

        if best_pattern and best_count >= 2:
            raw_scenes = best_pattern.split(text)
        else:
            # fallback: 빈 줄 2개 이상으로 단락 분리
            raw_scenes = re.split(r"\n{2,}", text)

        scenes = []
        for i, raw in enumerate(raw_scenes):
            raw = raw.strip()
            if len(raw) < 20:  # 너무 짧은 단편 스킵
                continue

            chars = sorted(set(_CHARACTER_PATTERN.findall(raw)))
            scene = ParsedScene(
                scene_id=f"{series_id}_ep{base_episode:02d}_sc{i+1:04d}",
                episode=base_episode,
                content=raw,
                characters=chars,
                word_count=len(raw.split()),
                char_count=len(raw),
                metadata={"source_index": i},
            )
            scenes.append(scene)

        return scenes


class SceneNormalizer:
    """ParsedScene → NKG SceneNode 변환 준비."""

    def to_scene_dict(self, scene: ParsedScene) -> dict[str, Any]:
        """
        SceneCorpusBuilder.build() 입력 형식으로 변환.
        텍스트 비저장 원칙(ADR-001 L2): prose_report만 포함, raw text 제외.
        """
        # 간이 표면 스코어 (실제 ReaderSurfaceScorer 미실행 시 기본값)
        prose_report: dict[str, float] = {
            "anti_llm":    min(1.0, scene.word_count / 200),
            "emotion":     0.5,
            "sensory":     0.5,
            "rhythm":      min(1.0, len(scene.characters) / 3 + 0.3),
            "consistency": 0.6,
            "structure":   0.6,
        }

        if _CORE:
            try:
                scorer = ReaderSurfaceScorer()
                score = scorer.score(scene.content)
                prose_report = score.report()
            except Exception:
                pass  # 기본값 유지

        return {
            "scene_id": scene.scene_id,
            "episode": scene.episode,
            "character_count": len(scene.characters),
            "word_count": scene.word_count,
            "prose_report": prose_report,
            "conflict_intensity": 0.5,
            "scene_energy_ratio": min(1.0, scene.word_count / 500),
            "motif_residue_score": 0.4,
            "curiosity_gradient": 0.5,
            "reader_uncertainty": 0.5,
            "reader_pull": 0.5,
            "reader_afterimage": 0.4,
        }


class ManuscriptImporter:
    """
    V423 ManuscriptImporter v2.
    routers/io.py의 stub을 교체하는 실제 임포터.

    파이프라인:
      content (str) → SceneParser → [ParsedScene]
                    → SceneNormalizer → scene_dicts
                    → NKGGraphStore (선택적 저장)
                    → SceneCorpusBuilder → SceneFeatures (학습용)
    """

    def __init__(
        self,
        store: Any | None = None,
        enable_learning: bool = False,
    ) -> None:
        self._parser = SceneParser()
        self._normalizer = SceneNormalizer()
        self._store = store
        self._enable_learning = enable_learning
        self._corpus_builder = None

        if _CORE and enable_learning:
            try:
                from literary_system.learning.scene_corpus_builder import SceneCorpusBuilder
                self._corpus_builder = SceneCorpusBuilder()
            except Exception:
                pass

    def parse(
        self,
        content: str,
        series_id: str,
        format: str = "txt",
        base_episode: int = 1,
    ) -> dict[str, Any]:
        """
        원고 텍스트 파싱 → ImportResponse 형식 반환.
        routers/io.py에서 직접 호출.
        """
        try:
            scenes = self._parser.split(content, series_id, base_episode)

            if not scenes:
                return {
                    "series_id": series_id,
                    "format": format,
                    "scene_count": 0,
                    "imported_scene_ids": [],
                    "characters": [],
                    "warnings": ["씬 구분자를 찾을 수 없어 분리 실패"],
                }

            scene_dicts = [self._normalizer.to_scene_dict(s) for s in scenes]
            imported_ids = [s.scene_id for s in scenes]

            # NKGGraphStore 저장 (store 주입 시)
            if _CORE and self._store is not None:
                self._store_scenes(scenes)

            # SceneCorpusBuilder 연결 (학습 활성화 시)
            features_count = 0
            if self._corpus_builder is not None:
                try:
                    features = self._corpus_builder.build(scene_dicts)
                    features_count = len(features)
                except Exception as exc:
                    logger.warning("SceneCorpusBuilder 연결 실패 (degraded): %s", exc)

            # 등장인물 전체 집계
            all_chars: set[str] = set()
            for s in scenes:
                all_chars.update(s.characters)

            warnings = []
            if features_count == 0 and self._enable_learning:
                warnings.append("SceneFeature 추출 실패 — 학습 데이터 생성 안 됨")

            return {
                "series_id": series_id,
                "format": format,
                "scene_count": len(scenes),
                "imported_scene_ids": imported_ids,
                "characters": sorted(all_chars),
                "warnings": warnings,
                "features_extracted": features_count,
            }

        except Exception as exc:
            logger.error("ManuscriptImporter.parse() 오류: %s", exc)
            return {
                "series_id": series_id,
                "format": format,
                "scene_count": 0,
                "imported_scene_ids": [],
                "characters": [],
                "warnings": [f"파싱 오류 (degraded): {exc}"],
            }

    def _store_scenes(self, scenes: list[ParsedScene]) -> None:
        """NKGGraphStore에 SceneNode 저장."""
        try:
            for scene in scenes:
                node = SceneNode(
                    node_id=scene.scene_id,
                    node_type=NKGNodeType.SCENE,
                    series_id=scene.scene_id.split("_ep")[0],
                    episode_index=scene.episode,
                )
                self._store.add_node(node)
        except Exception as exc:
            logger.warning("NKGGraphStore 저장 실패: %s", exc)
