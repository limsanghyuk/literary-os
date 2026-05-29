"""
V448: HallucinationDetector + SafetyGate
허상 탐지 및 안전 게이트 모듈.

원칙:
  - HallucinationDetector: 사실 확인 불가 구문, 단정적 허위 주장 탐지
  - SafetyGate: 유해·금지 콘텐츠 차단 (성인/폭력/혐오/개인정보)
  - LLM 0회 — 규칙 기반 + injectable check_fn / gate_fn
  - 탐지 결과는 불변 레코드로 관리
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─────────────────────────────────────────────
# HallucinationDetector
# ─────────────────────────────────────────────

_HALLUCINATION_PATTERNS = [
    (r"\b(무조건|반드시|절대로|100%|항상|절대)\s*(그렇다|맞다|틀리다|아니다)", "absolute_claim"),
    (r"\b(연구에\s*따르면|과학적으로\s*증명|전문가들이\s*모두)", "false_authority"),
    (r"\b(실제로\s*존재하지\s*않는|가상의|허구의)\s*[가-힣]+(?:이|가|은|는)", "fictional_fact"),
    (r"[0-9]{4}년\s*[0-9]{1,2}월\s*[0-9]{1,2}일.*?(?:사망|태어났|출생)", "unverifiable_date"),
    (r"\b(전\s*세계\s*[0-9]+억|전\s*인류의\s*[0-9]+%)", "inflated_statistic"),
]

_COMPILED_HALLUCINATION = [
    (re.compile(p, re.UNICODE), label)
    for p, label in _HALLUCINATION_PATTERNS
]


@dataclass(frozen=True)
class HallucinationFlag:
    """단일 허상 탐지 결과 (불변)."""
    flag_id:   str
    trace_id:  str
    pattern:   str
    matched:   str
    position:  int
    severity:  str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "flag_id":   self.flag_id,
            "trace_id":  self.trace_id,
            "pattern":   self.pattern,
            "matched":   self.matched,
            "position":  self.position,
            "severity":  self.severity,
            "timestamp": self.timestamp,
        }


@dataclass
class HallucinationReport:
    """HallucinationDetector.detect() 반환값."""
    trace_id:   str
    text:       str
    flags:      list
    flagged:    bool
    severity:   str
    checked_by: str

    def to_dict(self) -> dict:
        return {
            "trace_id":   self.trace_id,
            "flagged":    self.flagged,
            "severity":   self.severity,
            "flag_count": len(self.flags),
            "flags":      [f.to_dict() for f in self.flags],
            "checked_by": self.checked_by,
        }


def _default_hallucination_check(text: str) -> list:
    """
    규칙 기반 허상 탐지.
    반환: list of (pattern_label, matched_str, position, severity)
    """
    results = []
    for regex, label in _COMPILED_HALLUCINATION:
        for m in regex.finditer(text):
            severity = "high" if label in ("false_authority", "fictional_fact") else "medium"
            results.append((label, m.group(), m.start(), severity))
    return results


class HallucinationDetector:
    """
    규칙 기반 허상 탐지기.

    check_fn 주입으로 LLM 기반 탐지로 교체 가능.
    check_fn signature: (text: str) -> list of (pattern, matched, position, severity)
    """

    SEVERITY_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}

    def __init__(
        self,
        check_fn: Callable = None,
        min_severity: str = "low",
    ):
        self.check_fn     = check_fn if check_fn is not None else _default_hallucination_check
        self.min_severity = min_severity
        self._reports: list = []

    def detect(self, trace_id: str, text: str) -> HallucinationReport:
        """텍스트에서 허상 패턴 탐지."""
        raw_flags = self.check_fn(text)
        flags     = []
        min_rank  = self.SEVERITY_RANK.get(self.min_severity, 1)

        for pattern, matched, position, severity in raw_flags:
            if self.SEVERITY_RANK.get(severity, 0) >= min_rank:
                flags.append(HallucinationFlag(
                    flag_id=str(uuid.uuid4()),
                    trace_id=trace_id,
                    pattern=pattern,
                    matched=matched,
                    position=position,
                    severity=severity,
                    timestamp=_now_iso(),
                ))

        max_severity = "none"
        for f in flags:
            if self.SEVERITY_RANK[f.severity] > self.SEVERITY_RANK[max_severity]:
                max_severity = f.severity

        checked_by = "custom" if self.check_fn is not _default_hallucination_check else "rule_based"

        report = HallucinationReport(
            trace_id=trace_id,
            text=text,
            flags=flags,
            flagged=len(flags) > 0,
            severity=max_severity,
            checked_by=checked_by,
        )
        self._reports.append(report)
        return report

    def detect_batch(self, records: list) -> list:
        """TraceRecord 목록을 일괄 탐지."""
        results = []
        for rec in records:
            combined = " ".join(str(v) for v in rec.render_output.values())
            report = self.detect(rec.trace_id, combined)
            results.append(report)
        return results

    def flagged_reports(self) -> list:
        return [r for r in self._reports if r.flagged]

    def stats(self) -> dict:
        total   = len(self._reports)
        flagged = len(self.flagged_reports())
        severity_counts = {"none": 0, "low": 0, "medium": 0, "high": 0}
        for r in self._reports:
            severity_counts[r.severity] = severity_counts.get(r.severity, 0) + 1
        return {
            "total_checked": total,
            "flagged_count": flagged,
            "pass_rate":     round((total - flagged) / total, 4) if total > 0 else 1.0,
            "severity_dist": severity_counts,
        }


# ─────────────────────────────────────────────
# SafetyGate
# ─────────────────────────────────────────────

_SAFETY_PATTERNS = {
    "adult":    [r"\b(성인\s*콘텐츠|음란|포르노|성관계|야동)", r"\b(nude|pornograph|explicit\s*sexual)"],
    "violence": [r"\b(살인|폭행|고문|학대|자살\s*방법)", r"\b(murder|torture|abuse\s*method)"],
    "hate":     [r"\b(혐오\s*표현|차별|인종\s*비하)", r"\b(hate\s*speech|discriminat|racial\s*slur)"],
    "pii":      [r"\b\d{6}-[1-4]\d{6}\b", r"\b01[016789]-\d{3,4}-\d{4}\b"],
    "weapons":  [r"\b(폭탄\s*제조|총기\s*밀수|독약\s*제조)", r"\b(bomb\s*mak|weapon\s*smuggl|poison\s*synth)"],
}

_COMPILED_SAFETY: dict = {
    category: [re.compile(p, re.IGNORECASE | re.UNICODE) for p in patterns]
    for category, patterns in _SAFETY_PATTERNS.items()
}


@dataclass(frozen=True)
class SafetyViolation:
    """단일 안전 위반 탐지 결과 (불변)."""
    violation_id: str
    trace_id:     str
    category:     str
    matched:      str
    position:     int
    action:       str
    timestamp:    str

    def to_dict(self) -> dict:
        return {
            "violation_id": self.violation_id,
            "trace_id":     self.trace_id,
            "category":     self.category,
            "matched":      self.matched,
            "position":     self.position,
            "action":       self.action,
            "timestamp":    self.timestamp,
        }


@dataclass
class SafetyResult:
    """SafetyGate.check() 반환값."""
    trace_id:   str
    text:       str
    violations: list
    blocked:    bool
    warned:     bool
    action:     str
    checked_by: str

    def to_dict(self) -> dict:
        return {
            "trace_id":        self.trace_id,
            "blocked":         self.blocked,
            "warned":          self.warned,
            "action":          self.action,
            "violation_count": len(self.violations),
            "violations":      [v.to_dict() for v in self.violations],
            "checked_by":      self.checked_by,
        }


def _default_safety_check(text: str) -> list:
    """
    규칙 기반 안전 검사.
    반환: list of (category, matched_str, position)
    """
    results = []
    for category, regexes in _COMPILED_SAFETY.items():
        for regex in regexes:
            for m in regex.finditer(text):
                results.append((category, m.group(), m.start()))
    return results


class SafetyGate:
    """
    콘텐츠 안전 게이트.

    gate_fn 주입으로 커스텀 안전 검사로 교체 가능.
    gate_fn signature: (text: str) -> list of (category, matched, position)
    """

    BLOCKED_CATEGORIES = frozenset({"adult", "violence", "hate", "pii", "weapons"})
    WARNED_CATEGORIES  = frozenset({"adult_mild", "violence_mild"})

    def __init__(
        self,
        gate_fn:            Callable = None,
        blocked_categories: set      = None,
        warned_categories:  set      = None,
    ):
        self.gate_fn            = gate_fn if gate_fn is not None else _default_safety_check
        self.blocked_categories = frozenset(blocked_categories) if blocked_categories else self.BLOCKED_CATEGORIES
        self.warned_categories  = frozenset(warned_categories)  if warned_categories  else self.WARNED_CATEGORIES
        self._results: list     = []

    def check(self, trace_id: str, text: str) -> SafetyResult:
        """텍스트 안전 검사."""
        raw       = self.gate_fn(text)
        violations = []
        has_block  = False
        has_warn   = False

        for category, matched, position in raw:
            if category in self.blocked_categories:
                action    = "block"
                has_block = True
            elif category in self.warned_categories:
                action   = "warn"
                has_warn = True
            else:
                action = "pass"

            violations.append(SafetyViolation(
                violation_id=str(uuid.uuid4()),
                trace_id=trace_id,
                category=category,
                matched=matched,
                position=position,
                action=action,
                timestamp=_now_iso(),
            ))

        final_action = "block" if has_block else ("warn" if has_warn else "pass")
        checked_by   = "custom" if self.gate_fn is not _default_safety_check else "rule_based"

        result = SafetyResult(
            trace_id=trace_id,
            text=text,
            violations=violations,
            blocked=has_block,
            warned=has_warn,
            action=final_action,
            checked_by=checked_by,
        )
        self._results.append(result)
        return result

    def check_batch(self, records: list) -> list:
        """TraceRecord 목록 일괄 검사."""
        results = []
        for rec in records:
            combined = " ".join(str(v) for v in rec.render_output.values())
            result   = self.check(rec.trace_id, combined)
            results.append(result)
        return results

    def blocked_results(self) -> list:
        return [r for r in self._results if r.blocked]

    def stats(self) -> dict:
        total   = len(self._results)
        blocked = len(self.blocked_results())
        warned  = sum(1 for r in self._results if r.warned and not r.blocked)
        return {
            "total_checked": total,
            "blocked_count": blocked,
            "warned_count":  warned,
            "pass_count":    total - blocked - warned,
            "block_rate":    round(blocked / total, 4) if total > 0 else 0.0,
        }
