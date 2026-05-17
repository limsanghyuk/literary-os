"""SceneNecessityTheorem — V395. LLM 0 calls.
장면이 최소 2개 이상의 상태 차원을 변화시키는지 검증.
여백 장면은 atmosphere_function / emotional_residue_function으로 보호.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class SceneFunctionType(str, Enum):
    NARRATIVE = "NARRATIVE"           # 서사 전진
    ATMOSPHERE = "ATMOSPHERE"         # 분위기/여백
    EMOTIONAL_RESIDUE = "EMOTIONAL_RESIDUE"  # 감정 잔상


@dataclass
class StateDelta:
    """장면 전후 상태 변화량 (0이면 변화 없음)."""
    belief: float = 0.0
    emotion: float = 0.0
    relationship: float = 0.0
    reveal: float = 0.0
    conflict: float = 0.0
    motif: float = 0.0
    agency: float = 0.0
    curiosity: float = 0.0

    THRESHOLD = 0.05   # 이 값 이상이면 '변화 있음'으로 간주

    @property
    def changed_dimensions(self) -> int:
        dims = [self.belief, self.emotion, self.relationship, self.reveal,
                self.conflict, self.motif, self.agency, self.curiosity]
        return sum(1 for v in dims if abs(v) >= self.THRESHOLD)


@dataclass
class NecessityResult:
    scene_id: str
    changed_dimensions: int
    scene_function_type: SceneFunctionType
    action: str                      # keep / revise / merge / remove
    necessity_score: float

    @property
    def is_necessary(self) -> bool:
        return self.changed_dimensions >= 2 or \
               self.scene_function_type != SceneFunctionType.NARRATIVE

    @property
    def is_removable(self) -> bool:
        return self.changed_dimensions < 1 and \
               self.scene_function_type == SceneFunctionType.NARRATIVE


@dataclass
class NecessityReport:
    results: List[NecessityResult] = field(default_factory=list)
    weak_scene_ratio: float = 0.0
    removable_scenes: List[str] = field(default_factory=list)
    revision_candidates: List[str] = field(default_factory=list)
    repeated_pattern_warnings: List[str] = field(default_factory=list)

    @property
    def pass_gate(self) -> bool:
        return self.weak_scene_ratio < 0.15


class SceneNecessityChecker:
    """V395 — 장면 필요성 검증기."""

    WEAK_THRESHOLD = 2   # changed_dims < WEAK_THRESHOLD → weak

    def check_scene(
        self,
        scene_id: str,
        delta: StateDelta,
        function_type: SceneFunctionType = SceneFunctionType.NARRATIVE,
    ) -> NecessityResult:
        changed = delta.changed_dimensions
        score = changed / 8.0  # 0~1 정규화
        if changed >= self.WEAK_THRESHOLD or function_type != SceneFunctionType.NARRATIVE:
            action = "keep"
        elif changed == 1:
            action = "revise"
        elif changed == 0:
            action = "merge_or_remove"
        else:
            action = "keep"

        return NecessityResult(
            scene_id=scene_id,
            changed_dimensions=changed,
            scene_function_type=function_type,
            action=action,
            necessity_score=round(score, 4),
        )

    def analyze(self, scene_deltas: Dict[str, StateDelta],
                scene_functions: Dict[str, SceneFunctionType] = None) -> NecessityReport:
        if scene_functions is None:
            scene_functions = {}
        results = []
        for sid, delta in scene_deltas.items():
            ft = scene_functions.get(sid, SceneFunctionType.NARRATIVE)
            results.append(self.check_scene(sid, delta, ft))

        narrative_results = [r for r in results if
                              r.scene_function_type == SceneFunctionType.NARRATIVE]
        n_narrative = max(1, len(narrative_results))
        weak_count = sum(1 for r in narrative_results if r.changed_dimensions < self.WEAK_THRESHOLD)
        weak_ratio = weak_count / n_narrative

        removable = [r.scene_id for r in results if r.is_removable]
        revision = [r.scene_id for r in results if r.action == "revise"]

        # 반복 패턴 감지: 같은 action이 3회 이상 연속
        warnings = []
        if len(results) >= 3:
            for i in range(len(results) - 2):
                if results[i].action == results[i+1].action == results[i+2].action == "merge_or_remove":
                    warnings.append(f"repeated_removable_pattern at {results[i].scene_id}")

        return NecessityReport(
            results=results,
            weak_scene_ratio=round(weak_ratio, 4),
            removable_scenes=removable,
            revision_candidates=revision,
            repeated_pattern_warnings=warnings,
        )
