"""
V383 — MotifResidueGraphBuilder
NKG 모티프 잔상 누적 그래프. residue_score = appearances × exp(-decay × episodes_since_last).
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List


_DECAY = 0.3          # 감쇠 계수
_ORPHAN_THRESHOLD = 0.1   # 잔상 점수 임계값
_MIN_APPEARANCES  = 2     # 잔상 경고 최소 등장 횟수


@dataclass
class MotifResidueNode:
    motif_id:           str
    appearances:        int
    last_seen_episode:  int
    residue_score:      float


@dataclass
class MotifOrphanWarning:
    motif_id:      str
    residue_score: float
    appearances:   int
    message:       str


@dataclass
class MotifResidueGraph:
    nodes:            Dict[str, MotifResidueNode] = field(default_factory=dict)
    orphan_warnings:  List[MotifOrphanWarning]    = field(default_factory=list)
    average_residue:  float = 0.0


class MotifResidueGraphBuilder:
    """에피소드별 모티프 잔상 그래프 빌드. 에피소드 단위 1회 빌드 후 캐시 권장."""

    def build(
        self,
        motif_appearances: Dict[str, int],   # motif_id → 총 등장 횟수
        motif_last_seen:   Dict[str, int],   # motif_id → 마지막 등장 에피소드 번호
        current_episode:   int = 0,
    ) -> MotifResidueGraph:
        if not motif_appearances:
            return MotifResidueGraph(average_residue=0.0)

        nodes: Dict[str, MotifResidueNode] = {}
        warnings: List[MotifOrphanWarning] = []

        for motif_id, count in motif_appearances.items():
            last = motif_last_seen.get(motif_id, current_episode)
            delta = max(0, current_episode - last)
            recency = math.exp(-_DECAY * delta)
            score   = min(1.0, count * recency / 10.0)  # 10회 등장 = 최대 잔상

            node = MotifResidueNode(
                motif_id          = motif_id,
                appearances       = count,
                last_seen_episode = last,
                residue_score     = score,
            )
            nodes[motif_id] = node

            # 잔상 없는 모티프 경고
            if score < _ORPHAN_THRESHOLD and count >= _MIN_APPEARANCES:
                warnings.append(MotifOrphanWarning(
                    motif_id      = motif_id,
                    residue_score = score,
                    appearances   = count,
                    message = (
                        f"Motif '{motif_id}' has {count} appearances "
                        f"but residue_score={score:.3f} < {_ORPHAN_THRESHOLD}. "
                        f"Last seen at episode {last}."
                    ),
                ))

        avg = sum(n.residue_score for n in nodes.values()) / len(nodes) if nodes else 0.0

        return MotifResidueGraph(
            nodes           = nodes,
            orphan_warnings = warnings,
            average_residue = avg,
        )
