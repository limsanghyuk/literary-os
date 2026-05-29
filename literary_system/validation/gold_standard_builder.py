"""
V320: GoldStandardBuilder
Phase 1A — 인간 레이블 기반 Literary Quality 골드 스탠다드 구축.

핵심 원칙 (최고 프론티어 개발자 지적 반영):
  "비교 기준은 GPT critic이 아닌 인간 판단이어야 한다.
   두 개의 rule-based 시스템이 서로를 검증하는 것은
   상호 검증이 아니다. 두 개의 틀린 시계가 서로를
   정확하다고 확인해주는 상황이다."

구조:
  SceneLabel           — 단일 씬 레이블 데이터
  GoldStandardStore    — 레이블 저장 / 조회 / 통계
  GoldStandardBuilder  — 레이블링 워크플로우 관리
  InterRaterAgreement  — 아키텍트/컴파일러 교차 검증

LLM 0회. 완전 로컬.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class QualityLabel(str, Enum):
    GOOD     = "GOOD"      # 좋은 씬 — 로컬 판정이 통과시켜야 할 것
    BAD      = "BAD"       # 나쁜 씬 — 로컬 판정이 걸러내야 할 것
    MARGINAL = "MARGINAL"  # 경계 씬 — 측정에서 제외


class LabelSource(str, Enum):
    ARCHITECT  = "architect"   # 수석 아키텍트
    COMPILER   = "compiler"    # 수석 컴파일러
    CONSENSUS  = "consensus"   # 교차 검증 합의


@dataclass
class SceneLabel:
    """단일 씬 레이블."""
    scene_id: str
    scene_text: str
    label: QualityLabel
    source: LabelSource
    labeler_notes: str = ""
    genre: str = ""
    episode_no: int = 0
    # 보조 지표 (레이블러가 직관적으로 판단한 수치)
    perceived_reader_pull: float = 0.0   # [0, 1]
    perceived_pdi_compliance: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class InterRaterResult:
    """아키텍트 × 컴파일러 교차 검증 결과."""
    total_items: int
    agreed_items: int
    disagreed_items: int
    agreement_rate: float
    disagreed_scene_ids: list[str]
    consensus_labels: dict[str, QualityLabel]  # {scene_id: 합의된 레이블}
    passed_threshold: bool  # agreement_rate >= threshold


class GoldStandardStore:
    """
    골드 스탠다드 레이블 저장소.
    파일 기반 (JSON) 또는 메모리 기반으로 동작.
    """

    def __init__(self, store_path: str | Path | None = None):
        self.store_path = Path(store_path) if store_path else None
        self._labels: dict[str, SceneLabel] = {}
        if self.store_path and self.store_path.exists():
            self._load()

    def add(self, label: SceneLabel) -> None:
        self._labels[label.scene_id] = label
        if self.store_path:
            self._save()

    def get(self, scene_id: str) -> SceneLabel | None:
        return self._labels.get(scene_id)

    def list_by_source(self, source: LabelSource) -> list[SceneLabel]:
        return [l for l in self._labels.values() if l.source == source]

    def list_all(self) -> list[SceneLabel]:
        return list(self._labels.values())

    def count(self) -> dict[str, int]:
        counts = {q.value: 0 for q in QualityLabel}
        for lbl in self._labels.values():
            counts[lbl.label.value] += 1
        counts["total"] = len(self._labels)
        return counts

    def filter_for_validation(self) -> list[SceneLabel]:
        """MARGINAL 제외 — 판정 검증에 사용할 레이블만 반환."""
        return [l for l in self._labels.values()
                if l.label != QualityLabel.MARGINAL]

    def to_dict_list(self) -> list[dict]:
        return [
            {
                "scene_id": l.scene_id,
                "scene_text": l.scene_text[:200] + "..." if len(l.scene_text) > 200 else l.scene_text,
                "label": l.label.value,
                "source": l.source.value,
                "genre": l.genre,
                "notes": l.labeler_notes,
            }
            for l in self._labels.values()
        ]

    def _save(self) -> None:
        data = {sid: {
            "scene_id": l.scene_id,
            "scene_text": l.scene_text,
            "label": l.label.value,
            "source": l.source.value,
            "labeler_notes": l.labeler_notes,
            "genre": l.genre,
            "episode_no": l.episode_no,
            "perceived_reader_pull": l.perceived_reader_pull,
            "perceived_pdi_compliance": l.perceived_pdi_compliance,
            "created_at": l.created_at,
        } for sid, l in self._labels.items()}
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _load(self) -> None:
        try:
            data = json.loads(self.store_path.read_text())
            for sid, d in data.items():
                self._labels[sid] = SceneLabel(
                    scene_id=d["scene_id"],
                    scene_text=d["scene_text"],
                    label=QualityLabel(d["label"]),
                    source=LabelSource(d["source"]),
                    labeler_notes=d.get("labeler_notes", ""),
                    genre=d.get("genre", ""),
                    episode_no=d.get("episode_no", 0),
                    perceived_reader_pull=d.get("perceived_reader_pull", 0.0),
                    perceived_pdi_compliance=d.get("perceived_pdi_compliance", True),
                    created_at=d.get("created_at", ""),
                )
        except Exception:
            pass


class GoldStandardBuilder:
    """
    Phase 1A — 골드 스탠다드 구축 워크플로우.

    사용법:
      builder = GoldStandardBuilder(store)

      # 아키텍트 1차 레이블
      builder.label_scene(
          scene_text="그는 복도에서 파일을 발견했다...",
          label=QualityLabel.GOOD,
          source=LabelSource.ARCHITECT,
          notes="PDI 준수, 오브제 선명"
      )

      # 컴파일러 2차 교차 검토
      result = builder.cross_validate(
          architect_labels=[...],
          compiler_labels=[...]
      )
    """

    MINIMUM_LABELS = 20     # 최소 레이블 수
    TARGET_LABELS  = 50     # 목표 레이블 수
    AGREEMENT_THRESHOLD = 0.75  # 합격 기준 일치율

    def __init__(self, store: GoldStandardStore | None = None):
        self.store = store or GoldStandardStore()

    def label_scene(
        self,
        scene_text: str,
        label: QualityLabel,
        source: LabelSource,
        notes: str = "",
        genre: str = "",
        episode_no: int = 0,
        perceived_reader_pull: float = 0.0,
        perceived_pdi_compliance: bool = True,
        scene_id: str | None = None,
    ) -> SceneLabel:
        """씬에 레이블 부여."""
        sid = scene_id or f"scene_{uuid.uuid4().hex[:8]}"
        lbl = SceneLabel(
            scene_id=sid,
            scene_text=scene_text,
            label=label,
            source=source,
            labeler_notes=notes,
            genre=genre,
            episode_no=episode_no,
            perceived_reader_pull=perceived_reader_pull,
            perceived_pdi_compliance=perceived_pdi_compliance,
        )
        self.store.add(lbl)
        return lbl

    def cross_validate(
        self,
        architect_labels: list[SceneLabel],
        compiler_labels: list[SceneLabel],
    ) -> InterRaterResult:
        """
        아키텍트 × 컴파일러 교차 검증.
        동일 scene_id에 대한 레이블 일치율 계산.
        """
        arch_map  = {l.scene_id: l for l in architect_labels}
        comp_map  = {l.scene_id: l for l in compiler_labels}
        common_ids = set(arch_map.keys()) & set(comp_map.keys())

        agreed = 0
        disagreed_ids = []
        consensus: dict[str, QualityLabel] = {}

        for sid in common_ids:
            a_label = arch_map[sid].label
            c_label = comp_map[sid].label
            if a_label == c_label:
                agreed += 1
                consensus[sid] = a_label
            else:
                disagreed_ids.append(sid)

        total = len(common_ids)
        rate  = round(agreed / max(total, 1), 4)
        passed = rate >= self.AGREEMENT_THRESHOLD

        return InterRaterResult(
            total_items=total,
            agreed_items=agreed,
            disagreed_items=len(disagreed_ids),
            agreement_rate=rate,
            disagreed_scene_ids=disagreed_ids,
            consensus_labels=consensus,
            passed_threshold=passed,
        )

    def commit_consensus(
        self,
        consensus: dict[str, QualityLabel],
        original_labels: list[SceneLabel],
    ) -> int:
        """합의된 레이블을 store에 CONSENSUS 소스로 저장. 저장된 개수 반환."""
        label_map = {l.scene_id: l for l in original_labels}
        committed = 0
        for sid, label in consensus.items():
            orig = label_map.get(sid)
            if orig:
                consensus_lbl = SceneLabel(
                    scene_id=sid,
                    scene_text=orig.scene_text,
                    label=label,
                    source=LabelSource.CONSENSUS,
                    labeler_notes="교차 검증 합의",
                    genre=orig.genre,
                    episode_no=orig.episode_no,
                    perceived_reader_pull=orig.perceived_reader_pull,
                    perceived_pdi_compliance=orig.perceived_pdi_compliance,
                )
                self.store.add(consensus_lbl)
                committed += 1
        return committed

    def get_progress(self) -> dict[str, Any]:
        """구축 진행 상황 요약."""
        counts = self.store.count()
        consensus_count = len(self.store.list_by_source(LabelSource.CONSENSUS))
        validatable = len(self.store.filter_for_validation())
        return {
            "total_labels": counts["total"],
            "good_count": counts[QualityLabel.GOOD.value],
            "bad_count": counts[QualityLabel.BAD.value],
            "marginal_count": counts[QualityLabel.MARGINAL.value],
            "consensus_labels": consensus_count,
            "validatable_labels": validatable,
            "minimum_met": counts["total"] >= self.MINIMUM_LABELS,
            "target_met": counts["total"] >= self.TARGET_LABELS,
            "ready_for_phase1b": validatable >= self.MINIMUM_LABELS,
        }

    def load_from_gpt_outputs(
        self,
        scene_texts: list[str],
        auto_labels: list[QualityLabel] | None = None,
        genre: str = "korean_political_thriller",
    ) -> list[SceneLabel]:
        """
        GPT v1402 드라이브 출력물을 로드하는 헬퍼.
        auto_labels가 없으면 MARGINAL로 설정 (인간 검토 대기).
        """
        labels = auto_labels or [QualityLabel.MARGINAL] * len(scene_texts)
        result = []
        for i, (text, label) in enumerate(zip(scene_texts, labels)):
            lbl = self.label_scene(
                scene_text=text,
                label=label,
                source=LabelSource.ARCHITECT,
                notes="GPT v1402 드라이브 출력물",
                genre=genre,
                episode_no=i + 1,
            )
            result.append(lbl)
        return result
