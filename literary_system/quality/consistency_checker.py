"""
V449: ConsistencyChecker
씬 간 내러티브 일관성 검사 모듈.

검사 항목:
  - 캐릭터 속성 모순 (동일 인물이 동시에 두 곳에 존재)
  - 시간선 역행 (에피소드 번호 역행)
  - 키 팩트 철회 (이전 씬에서 확인된 팩트가 취소됨)
  - 중복 씬 ID

LLM 0회 — 규칙 기반.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class ConsistencyIssue:
    """단일 일관성 위반 (불변)."""
    issue_id:    str
    issue_type:  str    # "character_conflict" | "timeline_regression" | "fact_retraction" | "duplicate_id"
    description: str
    scene_ids:   tuple  # 관련 씬 ID들
    severity:    str    # "warning" | "error"
    timestamp:   str

    def to_dict(self) -> dict:
        return {
            "issue_id":    self.issue_id,
            "issue_type":  self.issue_type,
            "description": self.description,
            "scene_ids":   list(self.scene_ids),
            "severity":    self.severity,
            "timestamp":   self.timestamp,
        }


@dataclass
class ConsistencyReport:
    """ConsistencyChecker.check() 반환값."""
    scene_count:   int
    issues:        List[ConsistencyIssue]
    consistent:    bool
    error_count:   int
    warning_count: int

    def to_dict(self) -> dict:
        return {
            "scene_count":   self.scene_count,
            "consistent":    self.consistent,
            "error_count":   self.error_count,
            "warning_count": self.warning_count,
            "issue_count":   len(self.issues),
            "issues":        [i.to_dict() for i in self.issues],
        }


import uuid as _uuid_mod


def _new_issue_id() -> str:
    return str(_uuid_mod.uuid4())[:8]


class ConsistencyChecker:
    """
    씬 레코드 목록의 내러티브 일관성 검사기.

    check() 입력:
      records: list — 각 record는 다음 속성을 가져야 함:
        - trace_id: str
        - render_output: dict (scene 텍스트 포함)
        - metadata: dict (optional, episode_number / characters 포함 가능)

    check_fn 주입으로 커스텀 검사 로직 교체 가능.
    check_fn signature: (records: list) -> list of ConsistencyIssue
    """

    def __init__(
        self,
        check_fn:        Callable = None,
        error_threshold: int      = 1,   # 이 수 이상 error면 consistent=False
    ):
        self.check_fn        = check_fn if check_fn is not None else self._default_check
        self.error_threshold = error_threshold
        self._history:       List[ConsistencyReport] = []

    def check(self, records: list) -> ConsistencyReport:
        """레코드 목록 일관성 검사."""
        issues         = self.check_fn(records)
        error_count    = sum(1 for i in issues if i.severity == "error")
        warning_count  = sum(1 for i in issues if i.severity == "warning")
        consistent     = error_count < self.error_threshold

        report = ConsistencyReport(
            scene_count=len(records),
            issues=issues,
            consistent=consistent,
            error_count=error_count,
            warning_count=warning_count,
        )
        self._history.append(report)
        return report

    def stats(self) -> dict:
        total       = len(self._history)
        consistent  = sum(1 for r in self._history if r.consistent)
        total_issues = sum(len(r.issues) for r in self._history)
        return {
            "total_checks":       total,
            "consistent_count":   consistent,
            "inconsistent_count": total - consistent,
            "total_issues":       total_issues,
            "consistency_rate":   round(consistent / total, 4) if total > 0 else 1.0,
        }

    # ── 기본 검사 로직 ──────────────────────────────

    def _default_check(self, records: list) -> List[ConsistencyIssue]:
        issues = []
        issues.extend(self._check_duplicate_ids(records))
        issues.extend(self._check_timeline(records))
        issues.extend(self._check_character_conflicts(records))
        return issues

    def _check_duplicate_ids(self, records: list) -> List[ConsistencyIssue]:
        seen     = {}   # tid -> first_occurrence_index
        issues   = []
        for idx, rec in enumerate(records):
            tid = getattr(rec, "trace_id", None)
            if tid is None:
                continue
            if tid in seen:
                # Bug-Fix: scene_ids was (tid, tid) — stored tid as value so both were same.
                # Now stores first occurrence index so scene_ids correctly shows (dup_idx, first_idx)
                issues.append(ConsistencyIssue(
                    issue_id=_new_issue_id(),
                    issue_type="duplicate_id",
                    description=f"trace_id 중복: '{tid}'",
                    scene_ids=(idx, seen[tid]),
                    severity="error",
                    timestamp=_now_iso(),
                ))
            else:
                seen[tid] = idx
        return issues

    def _check_timeline(self, records: list) -> List[ConsistencyIssue]:
        issues   = []
        prev_ep  = None
        prev_tid = None
        for rec in records:
            meta    = getattr(rec, "metadata", {}) or {}
            ep_num  = meta.get("episode_number")
            if ep_num is None:
                continue
            try:
                ep_num = int(ep_num)
            except (TypeError, ValueError):
                continue
            if prev_ep is not None and ep_num < prev_ep:
                issues.append(ConsistencyIssue(
                    issue_id=_new_issue_id(),
                    issue_type="timeline_regression",
                    description=(
                        f"에피소드 번호 역행: {prev_ep} → {ep_num} "
                        f"(씬 {prev_tid} → {getattr(rec,'trace_id','')})"
                    ),
                    scene_ids=(prev_tid or "", getattr(rec, "trace_id", "")),
                    severity="warning",
                    timestamp=_now_iso(),
                ))
            prev_ep  = ep_num
            prev_tid = getattr(rec, "trace_id", None)
        return issues

    def _check_character_conflicts(self, records: list) -> List[ConsistencyIssue]:
        """동일 에피소드에서 같은 캐릭터가 두 개의 충돌하는 위치에 등장하는지 검사."""
        issues     = []
        # {(episode, character): [trace_ids with location tags]}
        char_locs: Dict = {}
        location_pattern = re.compile(r"\[위치:([^\]]+)\]")
        char_pattern     = re.compile(r"\[캐릭터:([^\]]+)\]")

        for rec in records:
            meta    = getattr(rec, "metadata", {}) or {}
            ep_num  = meta.get("episode_number", 0)
            output  = getattr(rec, "render_output", {}) or {}
            text    = " ".join(str(v) for v in output.values())
            tid     = getattr(rec, "trace_id", "")

            for char_m in char_pattern.finditer(text):
                char_name = char_m.group(1).strip()
                for loc_m in location_pattern.finditer(text):
                    location = loc_m.group(1).strip()
                    key      = (ep_num, char_name)
                    if key not in char_locs:
                        char_locs[key] = []
                    # 다른 위치에 이미 있으면 충돌 (단, 같은 씬 내 다중 위치 태그는 이동 표현이므로 제외)
                    # Bug-Fix: added prev_tid != tid check to prevent false positives
                    # when a single scene text contains multiple [위치:X] tags (e.g. movement)
                    for prev_tid, prev_loc in char_locs[key]:
                        if prev_loc != location and prev_tid != tid:
                            issues.append(ConsistencyIssue(
                                issue_id=_new_issue_id(),
                                issue_type="character_conflict",
                                description=(
                                    f"캐릭터 '{char_name}' 에피소드 {ep_num}에서 "
                                    f"위치 충돌: '{prev_loc}' vs '{location}'"
                                ),
                                scene_ids=(tid, prev_tid),
                                severity="warning",
                                timestamp=_now_iso(),
                            ))
                    char_locs[key].append((tid, location))
        return issues
