"""
V653 — AgentSafetyGuard (SP-C.2 Multi-Agent Ensemble).
앙상블 파이프라인 진입 전(pre_check)·후(post_check) 안전 검증.
4축: 자해/혐오/PII/저작권 (C-M-09 §SafetyV2, ADR-113).
LLM-0: 외부 API 직접 호출 없음.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────
# 안전 축 레이블
# ────────────────────────────────────────────────────────────────
SAFETY_AXES = ["self_harm", "hate_speech", "pii", "copyright"]


# ────────────────────────────────────────────────────────────────
# 결과 dataclass
# ────────────────────────────────────────────────────────────────

@dataclass
class AgentSafetyCheckResult:
    """단일 안전 검사 결과."""
    passed:        bool
    axis_results:  Dict[str, bool]          = field(default_factory=dict)
    violations:    List[str]                = field(default_factory=list)
    severity:      str                      = "none"   # none / low / medium / high
    note:          str                      = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed":       self.passed,
            "axis_results": dict(self.axis_results),
            "violations":   list(self.violations),
            "severity":     self.severity,
            "note":         self.note,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentSafetyCheckResult":
        return cls(
            passed       = bool(d.get("passed", True)),
            axis_results = dict(d.get("axis_results", {})),
            violations   = list(d.get("violations", [])),
            severity     = str(d.get("severity", "none")),
            note         = str(d.get("note", "")),
        )

    @classmethod
    def ok(cls) -> "AgentSafetyCheckResult":
        return cls(
            passed       = True,
            axis_results = {ax: True for ax in SAFETY_AXES},
            violations   = [],
            severity     = "none",
            note         = "all clear",
        )


# ────────────────────────────────────────────────────────────────
# 패턴 정의 (규칙 기반 — LLM-0 준수)
# ────────────────────────────────────────────────────────────────

_SELF_HARM_RE = re.compile(
    r"\b(자살|자해|스스로.*목숨|kill\s+myself|suicide\s+method|self[-\s]?harm|slit\s+wrist|"
    r"약.*과다복용|overdose\s+on)\b",
    re.IGNORECASE,
)

_HATE_RE = re.compile(
    r"\b(ethnic\s+cleansing|genocide|racial\s+slur|holocaust\s+denial|"
    r"inferior\s+race|kill\s+all\s+\w+s)\b",
    re.IGNORECASE,
)

_PII_RE = re.compile(
    r"(?:"
    r"\b\d{3}-\d{2}-\d{4}\b"          # SSN
    r"|\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"  # 신용카드
    r"|\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"  # 이메일
    r"|\b01[0-9]-\d{3,4}-\d{4}\b"      # 한국 휴대폰
    r")"
)

_COPYRIGHT_RE = re.compile(
    r"(?:"
    r"©\s*\d{4}|"
    r"all\s+rights\s+reserved|"
    r"copyright\s+\d{4}|"
    r"licensed\s+under\s+(cc|mit|apache|gpl)"
    r")",
    re.IGNORECASE,
)

_SEVERITY_MAP = {
    "self_harm":  "high",
    "hate_speech": "high",
    "pii":        "medium",
    "copyright":  "low",
}


# ────────────────────────────────────────────────────────────────
# AgentSafetyGuard
# ────────────────────────────────────────────────────────────────

class AgentSafetyGuard:
    """
    앙상블 파이프라인 진입 전·후 안전 검증기.

    pre_check(blueprint_dict)  — 청사진(입력) 안전 검사
    post_check(result_dict)    — 출력 텍스트 안전 검사
    check_text(text)           — 임의 텍스트 직접 검사
    """

    # 검사 활성화 플래그 (테스트 목업용 오버라이드 가능)
    ENABLED_AXES: Tuple[str, ...] = tuple(SAFETY_AXES)

    def __init__(self, enabled_axes: Optional[List[str]] = None) -> None:
        if enabled_axes is not None:
            self.ENABLED_AXES = tuple(enabled_axes)

    # ── 공개 API ────────────────────────────────────────────────

    def pre_check(self, blueprint_dict: Dict[str, Any]) -> AgentSafetyCheckResult:
        """청사진 딕셔너리의 텍스트 필드 전체를 안전 검사."""
        text = self._extract_text(blueprint_dict)
        return self.check_text(text, context="pre_check")

    def post_check(self, result_dict: Dict[str, Any]) -> AgentSafetyCheckResult:
        """CoordinatorResult / EnsembleEvalResult 딕셔너리 안전 검사."""
        text = result_dict.get("final_text", "") or result_dict.get("selected_text", "")
        if not isinstance(text, str):
            text = str(text)
        return self.check_text(text, context="post_check")

    def check_text(self, text: str, *, context: str = "direct") -> AgentSafetyCheckResult:
        """
        임의 텍스트를 4축으로 검사한다.
        활성화된 축(ENABLED_AXES)만 실행.
        """
        if not isinstance(text, str):
            text = str(text)

        axis_results: Dict[str, bool] = {}
        violations:   List[str]       = []
        max_severity  = "none"

        for axis in SAFETY_AXES:
            if axis not in self.ENABLED_AXES:
                axis_results[axis] = True   # 비활성 → 통과
                continue
            ok, detail = self._check_axis(axis, text)
            axis_results[axis] = ok
            if not ok:
                violations.append(f"{axis}: {detail}")
                sev = _SEVERITY_MAP.get(axis, "low")
                max_severity = self._max_severity(max_severity, sev)

        passed = len(violations) == 0
        return AgentSafetyCheckResult(
            passed       = passed,
            axis_results = axis_results,
            violations   = violations,
            severity     = max_severity if not passed else "none",
            note         = f"context={context}",
        )

    # ── 내부 헬퍼 ───────────────────────────────────────────────

    def _check_axis(self, axis: str, text: str) -> Tuple[bool, str]:
        """(ok, detail) 반환."""
        if axis == "self_harm":
            m = _SELF_HARM_RE.search(text)
            return (True, "") if m is None else (False, m.group(0))
        if axis == "hate_speech":
            m = _HATE_RE.search(text)
            return (True, "") if m is None else (False, m.group(0))
        if axis == "pii":
            m = _PII_RE.search(text)
            return (True, "") if m is None else (False, m.group(0)[:20] + "…")
        if axis == "copyright":
            m = _COPYRIGHT_RE.search(text)
            return (True, "") if m is None else (False, m.group(0))
        return (True, "")  # 알 수 없는 축 → 통과

    @staticmethod
    def _extract_text(d: Dict[str, Any]) -> str:
        """딕셔너리에서 텍스트 관련 필드를 모아 단일 문자열로 반환."""
        parts: List[str] = []
        for key in ("text", "content", "description", "title", "premise",
                    "genre", "theme", "notes", "scene_context"):
            val = d.get(key)
            if isinstance(val, str):
                parts.append(val)
            elif isinstance(val, list):
                parts.extend(str(v) for v in val)
            elif isinstance(val, dict):
                parts.append(" ".join(str(v) for v in val.values()))
        return " ".join(parts)

    @staticmethod
    def _max_severity(current: str, new: str) -> str:
        order = {"none": 0, "low": 1, "medium": 2, "high": 3}
        return new if order.get(new, 0) > order.get(current, 0) else current
