"""
critic/self_eval_pipeline.py — 자체평가 → loop-C 통합 배선 (V785, ADR-246).

ADR-243 §2 배선 구현: 명작 정적 닻으로 인간 없이 학습 신호 생성.
  M1 자격검정(critic) ─► 자격 통과 critic만 심판
  M2 NextEpisodeBench ─► 생성 vs 실제 쌍대(필적) ─► loop-C 선호쌍(주 보상)
  M3 분포 가드 ─► 생성물 병리 이상치 감점(전형성 무보상)
  ─► loop-C 선호쌍 + 보상조정 ─► (LoopCClosure → DPO+KL → G_LOOPC_WINRATE)

원칙: M1 미통과 → 전체 차단(자격 없는 심판으로 학습 금지). M3는 음성 가드만.
천장=모작(독창성=인간 최종시험). LLM-0: 오케스트레이션 결정론, judge/generate만 LLM-1.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from literary_system.critic.critic_qualification import qualify_critic, DegradeAxis
from literary_system.critic.next_episode_bench import run_next_episode_bench, NextEpItem
from literary_system.critic.distribution_guard import distribution_guard

JudgeFn = Callable[[str, str], str]
GenerateFn = Callable[[Dict[str, Any]], str]


@dataclass
class SelfEvalReport:
    qualified:        bool                  # M1 통과 여부(전제)
    qual_win_rate:    float
    n_pairs:          int                   # loop-C 선호쌍 수
    parity_rate:      float                 # M2 필적률
    n_guarded:        int                   # M3 병리 감점 건수
    pairs:            List[Dict[str, Any]]  # loop-C 선호쌍(+ guard_penalty)
    blocked_reason:   str = ""

    @property
    def ready_for_loopc(self) -> bool:
        return self.qualified and self.n_pairs > 0

    def summary(self) -> str:
        if not self.qualified:
            return f"자체평가 차단: {self.blocked_reason}"
        return (f"SelfEval: M1자격 통과(승률 {self.qual_win_rate}) · M2 필적률 {self.parity_rate} "
                f"· 선호쌍 {self.n_pairs} · M3 병리감점 {self.n_guarded} → loop-C 준비={self.ready_for_loopc}")

    def to_dict(self) -> Dict[str, Any]:
        return {"qualified": self.qualified, "qual_win_rate": self.qual_win_rate,
                "n_pairs": self.n_pairs, "parity_rate": self.parity_rate,
                "n_guarded": self.n_guarded, "pairs": self.pairs,
                "blocked_reason": self.blocked_reason, "ready_for_loopc": self.ready_for_loopc}


class SelfEvalPipeline:
    """M1→M2→M3를 하나의 자체평가 파이프라인으로 묶어 loop-C 입력 생성."""

    def __init__(self, qual_masterpieces: List[str], genre: str = "",
                 qual_win_min: float = 0.80) -> None:
        self._qual_mps = qual_masterpieces
        self._genre = genre
        self._qual_win_min = qual_win_min

    def run(self, items: List[NextEpItem], *, judge: JudgeFn,
            generate: GenerateFn) -> SelfEvalReport:
        # M1: critic 자격검정 (전제) ───────────────────────────
        qual = qualify_critic(judge, self._qual_mps, win_min=self._qual_win_min)
        if not qual.passed:
            return SelfEvalReport(False, qual.win_rate, 0, 0.0, 0, [],
                                  blocked_reason=f"M1 자격 미달({qual.win_rate}<{self._qual_win_min}) — 심판 부적격")

        # M2: NextEpisodeBench (자격 critic만) → 선호쌍 ─────────
        bench = run_next_episode_bench(items, generate=generate, judge=judge,
                                       critic_qualified=True)

        # M3: 생성물 분포 가드 → 병리 감점(음성만) ──────────────
        pairs: List[Dict[str, Any]] = []
        guarded = 0
        for p in bench.pairs:
            g = distribution_guard(p.get("draft", ""))
            if g.is_pathological:
                guarded += 1
            pairs.append({**p, "guard_penalty": g.penalty, "guard_rejected": g.rejected,
                          "genre": self._genre})

        return SelfEvalReport(True, qual.win_rate, len(pairs), bench.parity_rate, guarded, pairs)

    def to_preference_pairs(self, report: SelfEvalReport):
        """loop-C PreferencePair[] 변환(병리 기각쌍 제외)."""
        from literary_system.learning.loop_c import PreferencePair
        out = []
        for p in report.pairs:
            if p["winner"] not in ("draft", "ref"):
                continue
            # M3: 병리 생성이 '이긴' 쌍은 모순 → 제외. '진' 쌍(생성=rejected)은 유지(부정 신호).
            if p.get("guard_rejected") and p["winner"] == "draft":
                continue
            out.append(PreferencePair.from_pass7(
                p.get("func", "next_ep"), p.get("genre", self._genre),
                p["draft"], p["ref"], p["winner"], p.get("work_id", "")))
        return out
