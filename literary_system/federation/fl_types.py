"""FL 공통 타입 정의 — V732 (ADR-194)"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import time


@dataclass
class FLClientState:
    """연합 학습 클라이언트 상태."""
    client_id: str
    round_num: int
    num_samples: int
    local_loss: float
    weights: Dict[str, List[float]] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def is_valid(self) -> bool:
        return (
            bool(self.client_id)
            and self.round_num >= 0
            and self.num_samples > 0
            and self.local_loss >= 0.0
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "round_num": self.round_num,
            "num_samples": self.num_samples,
            "local_loss": self.local_loss,
            "weights_keys": list(self.weights.keys()),
            "timestamp": self.timestamp,
        }


@dataclass
class FLGlobalModel:
    """연합 학습 글로벌 모델 상태."""
    round_num: int
    global_weights: Dict[str, List[float]] = field(default_factory=dict)
    aggregated_from: int = 0           # 집계에 참여한 클라이언트 수
    global_loss: float = 0.0
    converged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "aggregated_from": self.aggregated_from,
            "global_loss": self.global_loss,
            "converged": self.converged,
            "weights_keys": list(self.global_weights.keys()),
        }


@dataclass
class FLRound:
    """하나의 연합 학습 라운드 기록."""
    round_num: int
    participants: List[str] = field(default_factory=list)
    client_states: List[FLClientState] = field(default_factory=list)
    global_model: Optional[FLGlobalModel] = None
    status: str = "pending"   # pending / aggregating / done / failed

    def summary(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "participants": len(self.participants),
            "status": self.status,
            "global_loss": self.global_model.global_loss if self.global_model else None,
        }
