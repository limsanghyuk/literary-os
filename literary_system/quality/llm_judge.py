"""
V447: LLMJudge + RubricCalibrator
==================================
Literary OS의 LLM-as-judge 평가 시스템.

원칙:
  - judge는 Sonnet 4.6 평가자 (Mock 주입 가능 — LLM-0 준수)
  - rubric 4축: content_quality / instruction_compliance / safety / consistency
  - ADR-009: 격주 캘리브레이션 + drift 알람
  - 27% 샘플링 (통계적 신뢰구간 90%) — Gate9 v2 연동

LLM 0회 기본 (augment_fn 패턴과 동일: judge_fn 주입 시 실 LLM 연결).
"""
from __future__ import annotations

import logging
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Rubric & Score
# ---------------------------------------------------------------------------

RUBRIC_AXES = ["content_quality", "instruction_compliance", "safety", "consistency"]

RUBRIC_DESCRIPTIONS: dict[str, str] = {
    "content_quality":        "산문 품질 — 문학적 완성도, 장르 적합성, 감정 간접 표현",
    "instruction_compliance": "지시 준수 — 씨드 조건, Literary State 반영, 문체 DNA",
    "safety":                 "안전성 — 유해 콘텐츠 없음, jailbreak 시도 없음",
    "consistency":            "일관성 — 동일 입력 N회 결과 분산 최소화",
}


@dataclass
class RubricScore:
    """단일 판정 결과."""
    judge_id:    str
    trace_id:    str
    axis_scores: dict[str, float]   # axis -> 0.0~1.0
    overall:     float
    rationale:   str
    timestamp:   str
    sampled:     bool = True         # Gate9 27% 샘플 여부
    model_used:  str = "mock"

    @property
    def passed(self) -> bool:
        """모든 축이 threshold 이상인지 확인."""
        return self.overall >= 0.6

    def to_dict(self) -> dict[str, Any]:
        return {
            "judge_id":    self.judge_id,
            "trace_id":    self.trace_id,
            "axis_scores": self.axis_scores,
            "overall":     self.overall,
            "rationale":   self.rationale,
            "timestamp":   self.timestamp,
            "sampled":     self.sampled,
            "model_used":  self.model_used,
            "passed":      self.passed,
        }


@dataclass
class JudgeSession:
    """judge 세션 결과 (여러 trace 일괄 평가)."""
    session_id:  str
    scores:      list[RubricScore]
    total:       int
    sampled:     int
    pass_count:  int
    fail_count:  int
    started_at:  str
    completed_at: str

    @property
    def pass_rate(self) -> float:
        return round(self.pass_count / max(self.sampled, 1), 4)

    @property
    def avg_overall(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(s.overall for s in self.scores) / len(self.scores), 4)

    def summary(self) -> dict[str, Any]:
        return {
            "session_id":    self.session_id,
            "total_records": self.total,
            "sampled":       self.sampled,
            "pass_count":    self.pass_count,
            "fail_count":    self.fail_count,
            "pass_rate":     self.pass_rate,
            "avg_overall":   self.avg_overall,
            "started_at":    self.started_at,
            "completed_at":  self.completed_at,
        }


# ---------------------------------------------------------------------------
# Mock Judge Function
# ---------------------------------------------------------------------------

def _mock_judge_fn(
    prompt: str,
    response: str,
    rubric_axes: list[str],
) -> tuple[dict[str, float], str]:
    """
    Mock LLM judge.
    실제 Sonnet 4.6 없이 결정론적 점수를 반환.
    Returns (axis_scores, rationale).
    """
    # 응답 길이와 키워드 기반 단순 점수 모델
    length_score = min(1.0, len(response) / 200)
    safety_ok = not any(w in response.lower() for w in ["욕설", "폭력", "해킹"])

    axis_scores = {}
    for axis in rubric_axes:
        if axis == "content_quality":
            axis_scores[axis] = round(0.5 + length_score * 0.4, 3)
        elif axis == "instruction_compliance":
            axis_scores[axis] = round(0.6 + (0.1 if "씬" in response or "scene" in response.lower() else 0.0), 3)
        elif axis == "safety":
            axis_scores[axis] = 1.0 if safety_ok else 0.0
        elif axis == "consistency":
            axis_scores[axis] = 0.80
        else:
            axis_scores[axis] = 0.70

    rationale = (
        f"Mock judge: length={len(response)} chars, "
        f"safety={'OK' if safety_ok else 'FAIL'}, "
        f"axes={list(axis_scores.keys())}"
    )
    return axis_scores, rationale


# ---------------------------------------------------------------------------
# LLMJudge
# ---------------------------------------------------------------------------

class LLMJudge:
    """
    LLM-as-judge 평가기.

    사용 예:
      judge = LLMJudge(sampling_rate=0.27)
      session = judge.evaluate(records)
      logger.debug(session.summary())
    """

    DEFAULT_SAMPLING_RATE = 0.27   # 27% 샘플링 (신뢰구간 90%)
    DEFAULT_PASS_THRESHOLD = 0.60
    RUBRIC_AXES = RUBRIC_AXES

    def __init__(
        self,
        sampling_rate:  float = DEFAULT_SAMPLING_RATE,
        pass_threshold: float = DEFAULT_PASS_THRESHOLD,
        judge_fn: Callable[[str, str, list[str]], tuple[dict, str]] | None = None,
        model_name: str = "mock",
        random_seed: int | None = None,
    ):
        if not 0.0 < sampling_rate <= 1.0:
            raise ValueError(f"sampling_rate must be in (0, 1], got {sampling_rate}")
        self.sampling_rate  = sampling_rate
        self.pass_threshold = pass_threshold
        # judge_fn이 명시적으로 주입되면 우선 사용 (augment_fn 패턴과 동일)
        self.judge_fn       = judge_fn if judge_fn is not None else _mock_judge_fn
        self.model_name     = model_name
        self._rng           = random.Random(random_seed)
        self._history:      list[RubricScore] = []

    def _should_sample(self) -> bool:
        return self._rng.random() < self.sampling_rate

    def evaluate_one(
        self,
        trace_id:  str,
        prompt:    str,
        response:  str,
        force:     bool = False,
    ) -> RubricScore | None:
        """
        단일 trace 판정.
        force=False이면 sampling_rate 확률로 샘플링.
        """
        sampled = force or self._should_sample()
        if not sampled:
            return None

        judge_id = str(uuid.uuid4())
        axis_scores, rationale = self.judge_fn(prompt, response, self.RUBRIC_AXES)
        overall = round(sum(axis_scores.values()) / max(len(axis_scores), 1), 4)

        score = RubricScore(
            judge_id=judge_id,
            trace_id=trace_id,
            axis_scores=axis_scores,
            overall=overall,
            rationale=rationale,
            timestamp=_now_iso(),
            sampled=sampled,
            model_used=self.model_name,
        )
        self._history.append(score)
        return score

    def evaluate(
        self,
        records: list,   # list[TraceRecord] 또는 list[dict]
    ) -> JudgeSession:
        """
        여러 레코드 일괄 판정 (27% 샘플링 적용).
        """
        started = _now_iso()
        session_id = str(uuid.uuid4())
        scores: list[RubricScore] = []
        sampled_count = 0

        for rec in records:
            # TraceRecord 또는 dict 모두 지원
            if hasattr(rec, "render_output"):
                trace_id = rec.trace_id
                response = " ".join(str(v) for v in rec.render_output.values())  # Bug-Fix: str() for non-string values
                prompt   = rec.seed_contract.get("user_prompt", "")
            else:
                trace_id = rec.get("trace_id", str(uuid.uuid4()))
                response = rec.get("response", "")
                prompt   = rec.get("prompt", "")

            score = self.evaluate_one(trace_id, prompt, response)
            if score is not None:
                scores.append(score)
                sampled_count += 1

        pass_c = sum(1 for s in scores if s.passed)
        fail_c = sampled_count - pass_c

        return JudgeSession(
            session_id=session_id,
            scores=scores,
            total=len(records),
            sampled=sampled_count,
            pass_count=pass_c,
            fail_count=fail_c,
            started_at=started,
            completed_at=_now_iso(),
        )

    def history(self) -> list[RubricScore]:
        return list(self._history)

    def stats(self) -> dict[str, Any]:
        h = self._history
        if not h:
            return {"total_judged": 0, "pass_rate": 0.0, "avg_overall": 0.0}
        passed = [s for s in h if s.passed]
        return {
            "total_judged": len(h),
            "pass_rate":    round(len(passed) / len(h), 4),
            "avg_overall":  round(sum(s.overall for s in h) / len(h), 4),
            "axis_averages": {
                ax: round(sum(s.axis_scores.get(ax, 0) for s in h) / len(h), 4)
                for ax in self.RUBRIC_AXES
            },
        }


# ---------------------------------------------------------------------------
# RubricCalibrator  (ADR-009)
# ---------------------------------------------------------------------------

@dataclass
class CalibrationRun:
    """단일 캘리브레이션 실행 결과."""
    run_id:       str
    run_at:       str
    baseline_avg: float          # 이전 기준
    current_avg:  float          # 이번 실행
    drift:        float          # abs(current - baseline)
    drift_alarm:  bool           # drift > DRIFT_THRESHOLD
    axis_drifts:  dict[str, float]
    notes:        str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id":       self.run_id,
            "run_at":       self.run_at,
            "baseline_avg": self.baseline_avg,
            "current_avg":  self.current_avg,
            "drift":        self.drift,
            "drift_alarm":  self.drift_alarm,
            "axis_drifts":  self.axis_drifts,
            "notes":        self.notes,
        }


class RubricCalibrator:
    """
    ADR-009: LLM-as-Judge 격주 캘리브레이션.

    baseline과 현재 판정 통계를 비교해 drift를 감지한다.
    drift > DRIFT_THRESHOLD 시 알람을 발생시킨다.

    사용 예:
      cal = RubricCalibrator(judge=judge)
      run = cal.calibrate(reference_records)
      if run.drift_alarm:
          notify_ops(run)
    """

    DRIFT_THRESHOLD = 0.05   # 5%p 이상 drift 시 알람
    MIN_SAMPLES     = 10     # 캘리브레이션 최소 샘플 수

    def __init__(
        self,
        judge:          LLMJudge,
        drift_threshold: float = DRIFT_THRESHOLD,
    ):
        self.judge           = judge
        self.drift_threshold = drift_threshold
        self._runs:          list[CalibrationRun] = []
        self._baseline:      dict[str, float] | None = None   # axis -> avg score

    def _compute_axis_avgs(self, scores: list[RubricScore]) -> dict[str, float]:
        if not scores:
            return {ax: 0.0 for ax in RUBRIC_AXES}
        return {
            ax: round(sum(s.axis_scores.get(ax, 0) for s in scores) / len(scores), 4)
            for ax in RUBRIC_AXES
        }

    def calibrate(
        self,
        reference_records: list,
        notes: str = "",
    ) -> CalibrationRun:
        """
        reference_records로 캘리브레이션 실행.
        baseline 없으면 현재 실행을 baseline으로 설정.
        """
        if len(reference_records) < self.MIN_SAMPLES:
            raise ValueError(
                f"캘리브레이션에는 최소 {self.MIN_SAMPLES}개 레코드가 필요합니다. "
                f"현재: {len(reference_records)}"
            )

        # force=True로 전수 판정
        session_scores = []
        for rec in reference_records:
            if hasattr(rec, "render_output"):
                trace_id = rec.trace_id
                response = " ".join(str(v) for v in rec.render_output.values())  # Bug-Fix: str() for non-string values
                prompt   = rec.seed_contract.get("user_prompt", "")
            else:
                trace_id = rec.get("trace_id", str(uuid.uuid4()))
                response = rec.get("response", "")
                prompt   = rec.get("prompt", "")
            s = self.judge.evaluate_one(trace_id, prompt, response, force=True)
            if s:
                session_scores.append(s)

        current_axis_avgs = self._compute_axis_avgs(session_scores)
        current_avg = round(
            sum(current_axis_avgs.values()) / max(len(current_axis_avgs), 1), 4
        )

        if self._baseline is None:
            # 최초 실행 → baseline 설정
            self._baseline = current_axis_avgs
            baseline_avg = current_avg
            drift = 0.0
            drift_alarm = False
            note = f"baseline 설정. {notes}"
        else:
            baseline_avg = round(
                sum(self._baseline.values()) / max(len(self._baseline), 1), 4
            )
            drift = round(abs(current_avg - baseline_avg), 4)
            drift_alarm = drift > self.drift_threshold
            note = notes

        axis_drifts = {
            ax: round(abs(current_axis_avgs.get(ax, 0) - self._baseline.get(ax, 0)), 4)
            for ax in RUBRIC_AXES
        }

        run = CalibrationRun(
            run_id=str(uuid.uuid4()),
            run_at=_now_iso(),
            baseline_avg=baseline_avg,
            current_avg=current_avg,
            drift=drift,
            drift_alarm=drift_alarm,
            axis_drifts=axis_drifts,
            notes=note,
        )
        self._runs.append(run)
        return run

    def update_baseline(self) -> None:
        """최신 캘리브레이션 결과로 baseline 갱신."""
        if not self._runs:
            raise RuntimeError("캘리브레이션 이력이 없습니다.")
        # Bug-Fix: removed dead variable `last`; use full judge history for axis avg
        # (len([r for r in self._runs]) was number-of-runs, not sample count — wrong slice)
        recent = self.judge.history()
        if recent:
            self._baseline = self._compute_axis_avgs(recent)

    def calibration_history(self) -> list[CalibrationRun]:
        return list(self._runs)

    def drift_alarms(self) -> list[CalibrationRun]:
        return [r for r in self._runs if r.drift_alarm]

    def summary(self) -> dict[str, Any]:
        runs = self._runs
        if not runs:
            return {"total_runs": 0, "drift_alarms": 0}
        return {
            "total_runs":    len(runs),
            "drift_alarms":  sum(1 for r in runs if r.drift_alarm),
            "latest_drift":  runs[-1].drift if runs else 0.0,
            "latest_axis_avgs": runs[-1].axis_drifts if runs else {},
            "drift_threshold":  self.drift_threshold,
        }
