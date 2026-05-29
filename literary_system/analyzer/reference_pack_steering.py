"""V328 Task16: ReferencePackSteering — 레퍼런스 팩 기반 분석 조향 (단절 I)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SteeringResult:
    applied: bool   = False
    signals: list   = None
    def __post_init__(self):
        if self.signals is None: self.signals = []

class ReferencePackSteering:
    def __init__(self, reference_pack=None):
        self._pack = reference_pack

    def steer(self, analysis_result: Any) -> Any:
        if self._pack is None or analysis_result is None:
            return analysis_result
        try:
            signals = []
            if hasattr(self._pack, "get_signals"):
                signals = self._pack.get_signals() or []
            if hasattr(analysis_result, "steering_signals"):
                analysis_result.steering_signals = signals
            elif isinstance(analysis_result, dict):
                analysis_result["steering_signals"] = signals
        except Exception:
            pass
        return analysis_result
