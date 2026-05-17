"""
literary_system/schemas/tree_node.py
V482 — TreeNode JSON 스키마 v1

FractalPlotTree와 EpisodeStructure를 연결하는 범용 트리 노드.

계층 구조:
  SERIES → EPISODE → MICROPLOT → SCENE → BEAT

인터페이스:
  TreeNode.from_scene_slot(slot) → TreeNode
  TreeNode.to_dict() → dict (JSON 직렬화)
  TreeNode.add_child(child) → None
  TreeNodeBuilder.build_episode_tree(structure) → TreeNode
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ── 노드 타입 ────────────────────────────────────────────────────

class TreeNodeType(str, Enum):
    SERIES    = "series"
    EPISODE   = "episode"
    MICROPLOT = "microplot"
    SCENE     = "scene"
    BEAT      = "beat"

    @property
    def depth(self) -> int:
        return {
            "series": 0,
            "episode": 1,
            "microplot": 2,
            "scene": 3,
            "beat": 4,
        }[self.value]


# ── TreeNode ─────────────────────────────────────────────────────

@dataclass
class TreeNode:
    """
    V482 범용 서사 트리 노드.

    - node_id: 고유 식별자 (UUID4 hex)
    - node_type: 계층 유형 (SERIES/EPISODE/MICROPLOT/SCENE/BEAT)
    - label: 사람이 읽을 수 있는 레이블
    - metadata: 임의 추가 데이터 (씬 슬롯, 필요성 판정 등)
    - children: 자식 노드 목록 (재귀 구조)
    """
    node_id: str
    node_type: TreeNodeType
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List["TreeNode"] = field(default_factory=list)
    parent_id: Optional[str] = None

    # ── 팩토리 메서드 ────────────────────────────────────────────

    @classmethod
    def new(
        cls,
        node_type: TreeNodeType,
        label: str,
        metadata: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
    ) -> "TreeNode":
        return cls(
            node_id=uuid.uuid4().hex[:12],
            node_type=node_type,
            label=label,
            metadata=metadata or {},
            parent_id=parent_id,
        )

    @classmethod
    def from_scene_slot(cls, slot, parent_id: Optional[str] = None) -> "TreeNode":
        """SceneSlot → TreeNode 변환."""
        return cls.new(
            node_type=TreeNodeType.SCENE,
            label=f"S{slot.scene_idx:03d}:{slot.role.value}:{slot.slot_function}",
            metadata={
                "scene_idx": slot.scene_idx,
                "microplot_idx": slot.microplot_idx,
                "start_min": round(slot.start_min, 2),
                "end_min": round(slot.end_min, 2),
                "duration_min": round(slot.duration_min, 2),
                "role": slot.role.value,
                "act_position": slot.act_position.value,
                "slot_function": slot.slot_function,
                "reveal_budget": slot.reveal_budget,
                "emotional_target": slot.emotional_target,
                "conflict_weight": slot.conflict_weight,
                "is_critical": slot.is_critical,
            },
            parent_id=parent_id,
        )

    # ── 트리 조작 ────────────────────────────────────────────────

    def add_child(self, child: "TreeNode") -> None:
        """자식 노드 추가. child.parent_id를 자동 설정."""
        child.parent_id = self.node_id
        self.children.append(child)

    def depth(self) -> int:
        return self.node_type.depth

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def child_count(self) -> int:
        return len(self.children)

    def all_descendants(self) -> List["TreeNode"]:
        """BFS로 모든 후손 노드 반환."""
        result: List["TreeNode"] = []
        queue = list(self.children)
        while queue:
            node = queue.pop(0)
            result.append(node)
            queue.extend(node.children)
        return result

    def find_by_type(self, node_type: TreeNodeType) -> List["TreeNode"]:
        """특정 타입의 모든 노드 반환 (자신 포함)."""
        result = []
        if self.node_type == node_type:
            result.append(self)
        for desc in self.all_descendants():
            if desc.node_type == node_type:
                result.append(desc)
        return result

    # ── 직렬화 ───────────────────────────────────────────────────

    def to_dict(self, include_children: bool = True) -> dict:
        d = {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
        }
        if include_children:
            d["children"] = [c.to_dict() for c in self.children]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TreeNode":
        """to_dict() 역직렬화."""
        node = cls(
            node_id=d["node_id"],
            node_type=TreeNodeType(d["node_type"]),
            label=d["label"],
            metadata=d.get("metadata", {}),
            parent_id=d.get("parent_id"),
        )
        for child_d in d.get("children", []):
            node.children.append(cls.from_dict(child_d))
        return node

    def __repr__(self) -> str:
        return (
            f"TreeNode(type={self.node_type.value}, "
            f"label={self.label!r}, children={len(self.children)})"
        )


# ── TreeNodeBuilder ───────────────────────────────────────────────

class TreeNodeBuilder:
    """
    EpisodeStructure → TreeNode 계층 변환 빌더.

    EPISODE
      └─ MICROPLOT (K개)
           └─ SCENE (각 MP 내 씬)
    """

    def build_episode_tree(self, structure) -> TreeNode:
        """
        EpisodeStructure → TreeNode 트리 구성.
        EPISODE 루트 아래 MICROPLOT별로 SCENE을 그룹핑.
        """
        ep_node = TreeNode.new(
            node_type=TreeNodeType.EPISODE,
            label=f"EP{structure.episode_idx:02d}:{structure.runtime_min:.0f}min",
            metadata={
                "episode_idx": structure.episode_idx,
                "runtime_min": structure.runtime_min,
                "microplot_count": structure.microplot_count,
                "total_scene_count": structure.total_scene_count,
                "pass_60min_constraint": structure.pass_60min_constraint,
            },
        )

        # 미시 플롯별 그룹핑
        mp_map: Dict[int, TreeNode] = {}

        for scene in structure.scenes:
            mp_idx = scene.microplot_idx

            # 콜드 오픈 / 예고편은 특수 MP
            if mp_idx == -1:
                mp_key = "cold_open"
            elif mp_idx == -2:
                mp_key = "preview"
            else:
                mp_key = str(mp_idx)

            if mp_key not in mp_map:
                if mp_idx == -1:
                    label = "COLD_OPEN"
                    ntype = TreeNodeType.MICROPLOT
                elif mp_idx == -2:
                    label = "PREVIEW"
                    ntype = TreeNodeType.MICROPLOT
                else:
                    label = f"MP{mp_idx:02d}"
                    ntype = TreeNodeType.MICROPLOT
                mp_node = TreeNode.new(
                    node_type=ntype,
                    label=label,
                    metadata={"microplot_idx": mp_idx},
                )
                ep_node.add_child(mp_node)
                mp_map[mp_key] = mp_node

            scene_node = TreeNode.from_scene_slot(scene, parent_id=mp_map[mp_key].node_id)
            mp_map[mp_key].add_child(scene_node)

        return ep_node

    def build_series_tree(self, episode_structures: list) -> TreeNode:
        """복수 EpisodeStructure → SERIES 루트 트리."""
        series_node = TreeNode.new(
            node_type=TreeNodeType.SERIES,
            label=f"SERIES:{len(episode_structures)}ep",
            metadata={"total_episodes": len(episode_structures)},
        )
        for structure in episode_structures:
            ep_tree = self.build_episode_tree(structure)
            series_node.add_child(ep_tree)
        return series_node
