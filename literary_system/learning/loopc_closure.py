"""
learning/loopc_closure.py — loop-C 폐회로 오케스트레이션 (V774, ADR-234).

회사 설계도 §1~2 구현. RLAIF 부품(트리거·라우터·어댑터·first_training_kit)을
"선호쌍 → 학습 → 명작 대비 재측정 → 수용판정 → 다음 라운드"의 닫힌 루프로 잇는 글루.
실 학습은 GPU(4070/클라우드)에서 수행 → 본 모듈은 ①라운드 계획(dry) + ⑤수용판정 + ⑥결정.
LLM-0: 생성기만 학습 대상. 외부 LLM 미호출.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from literary_system.learning.pareto_router import dispatch_training, TrainingMode
from literary_system.learning.provider_router import RoutingSignals
from literary_system.learning.rlaif_orchestrator import RLAIFOrchestrator
from literary_system.learning.loop_c import load_preference_pairs, generation_win_rate
from literary_system.learning.winrate_gate import g_loopc_winrate, WinrateGateResult, TAU_KL_DEFAULT

TARGET_W_DEFAULT = 0.60         # 단계적 상향(0.55→0.60→...) 목표 승률

# ── SP-E.10.2 졸업 불변식 게이트 상수(DESIGN 수렴값) ──────────────
GRAD_CONSEC_REQUIRED = 5        # 연속 adopt 라운드 수
GRAD_MIN_PAIRS       = 250      # 윈도 누적 held 선호쌍 하한
GRAD_CI_LOWER_MIN    = 0.5      # per-token W₁ CI 하한이 넘어야 할 기준
GRAD_LENGTH_RULE_MAX = 0.60     # length-rule 재현율 상한(길이혼입 차단)


def _rec(r: Any, k: str, default=None):
    return r.get(k, default) if isinstance(r, dict) else getattr(r, k, default)


def graduation_invariant(rounds: List[Any], *,
                         consec: int = GRAD_CONSEC_REQUIRED,
                         min_pairs: int = GRAD_MIN_PAIRS,
                         ci_min: float = GRAD_CI_LOWER_MIN,
                         len_max: float = GRAD_LENGTH_RULE_MAX) -> Dict[str, Any]:
    """L1→L2 졸업 불변식 감사(누적 어댑터 루프). 학습 미수행 — 라운드 원장만 채점.

    불변식(전부 충족 시 graduated): ①말미 연속 adopt ≥ consec ∧ ②윈도 내 rollback=0
    ∧ ③Σ held 쌍수 ≥ min_pairs ∧ ④전 라운드 per-token W₁ CI하한 > ci_min
    ∧ ⑤전 라운드 length-rule 재현율 ≤ len_max ∧ ⑥전 라운드 c3 PASS.

    각 round 레코드(dict/obj)는 decision('adopt'/'rollback'), n_pairs,
    w1_ci_lower, length_rule_rate, c3_passed 를 제공해야 한다. **fail-closed**:
    필드 누락은 통과가 아니라 위반으로 기록(V792 G-B 교훈). 반환은 감사 가능한 dict."""
    rounds = list(rounds or [])
    # 말미 연속 adopt 스트릭(rollback 만나면 끊김)
    streak: List[Any] = []
    for r in reversed(rounds):
        if str(_rec(r, "decision", "")).lower().startswith("adopt"):
            streak.append(r)
        else:
            break
    streak.reverse()
    window = streak

    viol: List[str] = []
    consec_ok = len(window) >= consec
    if not consec_ok:
        viol.append(f"연속 adopt {len(window)} < {consec}")

    no_rollback = all(str(_rec(r, "decision", "")).lower().startswith("adopt") for r in window) and len(window) > 0
    if not no_rollback:
        viol.append("윈도 내 rollback 존재 또는 빈 윈도")

    # Σ 쌍수 (누락=fail-closed: 0으로 취급되어 합 미달 유발)
    sum_pairs = 0
    for i, r in enumerate(window):
        np_ = _rec(r, "n_pairs", None)
        if np_ is None:
            viol.append(f"R{i}: n_pairs 누락(fail-closed)")
        else:
            sum_pairs += int(np_)
    pairs_ok = sum_pairs >= min_pairs
    if not pairs_ok:
        viol.append(f"Σ쌍수 {sum_pairs} < {min_pairs}")

    ci_ok = True
    for i, r in enumerate(window):
        v = _rec(r, "w1_ci_lower", None)
        if v is None or float(v) <= ci_min:
            ci_ok = False
            viol.append(f"R{i}: W₁ CI하한 {v} ≤ {ci_min}(또는 누락)")

    len_ok = True
    for i, r in enumerate(window):
        v = _rec(r, "length_rule_rate", None)
        if v is None or float(v) > len_max:
            len_ok = False
            viol.append(f"R{i}: length-rule 재현율 {v} > {len_max}(또는 누락)")

    c3_ok = True
    for i, r in enumerate(window):
        v = _rec(r, "c3_passed", None)
        if v is not True:
            c3_ok = False
            viol.append(f"R{i}: c3 PASS 아님({v})")

    checks = {
        "consecutive_adopt_ge_required": consec_ok,
        "no_rollback": no_rollback,
        "sum_pairs_ge_min": pairs_ok,
        "all_ci_lower_gt_min": ci_ok,
        "all_length_rule_le_max": len_ok,
        "all_c3_passed": c3_ok,
    }
    graduated = all(checks.values())
    return {
        "graduated": graduated,
        "consecutive_adopt": len(window),
        "n_rounds_total": len(rounds),
        "sum_pairs": sum_pairs,
        "thresholds": {"consec": consec, "min_pairs": min_pairs,
                       "ci_min": ci_min, "len_max": len_max},
        "checks": checks,
        "violations": viol,
        "exit_version": "v14.0.0" if graduated else None,
        "detail": ("졸업 가능(Phase E Exit v14.0.0): 불변식 6/6 충족"
                   if graduated else "졸업 차단: " + "; ".join(viol)),
    }


def scenes_for_c3(result: Any) -> List[Dict[str, Any]]:
    """7-pass GenerationResult → c3(structure_conformance) 입력 씬 dict 시퀀스.

    핵심: SceneBrief에는 plant/payoff 모티프가 없다(Beat에만 존재) → beat_id로 조인해
    plant_motifs/payoff_motifs를 전파한다. 이로써 r_struct의 plant→payoff 체크(가중 0.20)가
    실제 생성 초안 기준으로 동작한다(전파 전엔 항상 중립 1.0 = dead score였음).
    LLM-0: 순수 데이터 조인(LLM 미호출)."""
    beats = list(getattr(result, "beats", []) or [])
    briefs = list(getattr(result, "briefs", []) or [])
    beat_by_id = {getattr(b, "beat_id", None): b for b in beats}
    scenes: List[Dict[str, Any]] = []
    for s in briefs:
        beat = beat_by_id.get(getattr(s, "beat_id", None))
        scenes.append({
            "scene_id": getattr(s, "scene_id", ""),
            "draft": getattr(s, "draft", None),
            "characters": list(getattr(s, "characters", []) or []),
            "targets": dict(getattr(s, "targets", {}) or {}),
            "dramatic_function": getattr(s, "dramatic_function", ""),
            "plant_motifs": list(getattr(beat, "plant_motifs", []) or []) if beat else [],
            "payoff_motifs": list(getattr(beat, "payoff_motifs", []) or []) if beat else [],
            "rag_refs": list(getattr(s, "rag_refs", []) or []),
        })
    return scenes


@dataclass
class LoopCRoundReport:
    round_idx:     int
    n_pairs:       int
    w0:            float
    w1:            Optional[float]
    training_plan: Dict[str, Any]
    gate:          Optional[WinrateGateResult]
    next_action:   str
    summary:       str

    def to_dict(self) -> Dict[str, Any]:
        return {"round_idx": self.round_idx, "n_pairs": self.n_pairs, "w0": self.w0, "w1": self.w1,
                "training_plan": self.training_plan,
                "gate": self.gate.to_dict() if self.gate else None,
                "next_action": self.next_action, "summary": self.summary}


class LoopCClosure:
    """1 라운드: 선호쌍 → 학습계획 → (실측 W₁ 주입) → 수용판정 → 다음행동."""

    def __init__(self, mode: TrainingMode = TrainingMode.LOCAL,
                 target_w: float = TARGET_W_DEFAULT, tau_kl: float = TAU_KL_DEFAULT,
                 base_model: str = "meta-llama/Llama-3.2-3B") -> None:
        self._mode = mode
        self._target = target_w
        self._tau = tau_kl
        self._base = base_model

    def plan_round(self, pairs_path: str, signals: Optional[RoutingSignals] = None,
                   real: bool = False, api_key: Optional[str] = None) -> Dict[str, Any]:
        """①~③ 계획(dry): 선호쌍 적재 → 스펙 → dispatch(dry_run) 학습 계획."""
        import tempfile, os
        pairs = load_preference_pairs(pairs_path)
        w0 = generation_win_rate(pairs)
        fd, out = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
        spec = RLAIFOrchestrator(base_model=self._base).prepare(pairs, out)
        plan = dispatch_training(spec, self._mode, signals or RoutingSignals(),
                                 dry_run=True, real=real, api_key=api_key)
        return {"w0": w0, "n_pairs": len(pairs), "base_model": self._base,
                "mode": self._mode.value, "dispatch": plan}

    def evaluate_round(self, round_idx: int, w0: float, w1: float, n_pairs: int,
                       kl: float = 0.0, r_before: Optional[float] = None,
                       r_after: Optional[float] = None,
                       training_plan: Optional[Dict[str, Any]] = None) -> LoopCRoundReport:
        """⑤수용판정 + ⑥⑦결정(채택→다음/완료, 롤백→약점피드백)."""
        gate = g_loopc_winrate(w0, w1, kl=kl, r_before=r_before, r_after=r_after,
                               n_pairs=n_pairs, tau_kl=self._tau)
        if gate.passed:
            if w1 >= self._target:
                action = "adopt_done(목표 승률 도달 — 종료조건)"
            else:
                action = "adopt_continue(채택 → 선호쌍 확대 후 다음 라운드)"
        else:
            action = "rollback_feedback(폐기 → 약한 기능축 데이터트랙 피드백)"
        summary = (f"R{round_idx}: W {w0}→{w1} (ΔW {gate.delta_w:+}) | {gate.decision} | {action} "
                   f"| {'신뢰O' if gate.reliable else '신뢰약(표본↑)'}")
        return LoopCRoundReport(round_idx, n_pairs, w0, w1, training_plan or {}, gate, action, summary)


    def compute_structural_r(self, before_scenes, after_scenes,
                             rag_refs=None, critic=None):
        """before/after 생성 작품(SceneBrief 시퀀스) → c3 구조 R (r_before, r_after, 판정).
        winrate_gate.c3의 결손 생산자(구조 비퇴행)를 실제로 계산해 주입값을 만든다.
        반환 dict: {r_before, r_after, nonregression(상세)}. LLM-0(결정론)."""
        from literary_system.critic.structure_conformance import structural_nonregression
        nr = structural_nonregression(before_scenes, after_scenes,
                                      rag_refs=rag_refs, critic=critic)
        return {"r_before": nr.r_before, "r_after": nr.r_after, "nonregression": nr.to_dict()}

    def c3_from_generations(self, before_result: Any, after_result: Any,
                            rag_refs: Optional[List[str]] = None, critic=None):
        """7-pass 생성물(before-어댑터 vs after-어댑터, 동일 씨드) → c3 구조 비퇴행.
        파이프라인 GenerationResult를 그대로 받아 mock 없이 실제 초안 구조를 채점한다.
        rag_refs 미지정 시 after 작품 brief들의 rag_refs를 수집해 G_LLM1_RAG 충족."""
        before = scenes_for_c3(before_result)
        after = scenes_for_c3(after_result)
        if rag_refs is None:
            collected: List[str] = []
            for sc in after:
                collected.extend(sc.get("rag_refs") or [])
            rag_refs = collected or None
        return self.compute_structural_r(before, after, rag_refs=rag_refs, critic=critic)

    def run_round(self, pairs_path: str, round_idx: int = 1,
                  measured_w1: Optional[float] = None, kl: float = 0.0,
                  r_before: Optional[float] = None, r_after: Optional[float] = None,
                  before_scenes=None, after_scenes=None,
                  before_result=None, after_result=None,
                  signals: Optional[RoutingSignals] = None,
                  real: bool = False, api_key: Optional[str] = None) -> LoopCRoundReport:
        """계획 + (실측 W₁ 있으면) 수용판정까지. 실측 없으면 계획만(학습 대기)."""
        plan = self.plan_round(pairs_path, signals, real, api_key)
        if (r_before is None or r_after is None) and before_result is not None and after_result is not None:
            _r = self.c3_from_generations(before_result, after_result)
            r_before, r_after = _r["r_before"], _r["r_after"]
        if (r_before is None or r_after is None) and before_scenes and after_scenes:
            _r = self.compute_structural_r(before_scenes, after_scenes)
            r_before, r_after = _r["r_before"], _r["r_after"]
        if measured_w1 is None:
            return LoopCRoundReport(round_idx, plan["n_pairs"], plan["w0"], None, plan,
                                    None, "await_training(GPU 학습 후 W₁ 재측정 필요)",
                                    f"R{round_idx} 계획: W₀={plan['w0']} → 4070/클라우드 학습 대기")
        return self.evaluate_round(round_idx, plan["w0"], measured_w1, plan["n_pairs"],
                                   kl, r_before, r_after, plan)


# ── SP-E.10.3 누적 어댑터 체이닝 오케스트레이터 ──────────────────────
@dataclass
class CumulativeRoundResult:
    round_idx:      int
    decision:       str            # adopt | rollback
    init_adapter:   Optional[str]  # 이 라운드 학습 시작점(직전 채택 어댑터) = 체이닝 링크
    adapter_path:   Optional[str]  # 이 라운드 산출 어댑터
    current_adapter: Optional[str] # 라운드 후 누적 채택 어댑터(롤백 시 불변)
    report:         Dict[str, Any]
    ledger_record:  Dict[str, Any]
    graduation:     Dict[str, Any]
    exit:           bool           # graduation.graduated

    def to_dict(self) -> Dict[str, Any]:
        return {"round_idx": self.round_idx, "decision": self.decision,
                "init_adapter": self.init_adapter, "adapter_path": self.adapter_path,
                "current_adapter": self.current_adapter, "report": self.report,
                "ledger_record": self.ledger_record, "graduation": self.graduation,
                "exit": self.exit}


class CumulativeLoopC:
    """누적 어댑터 체이닝 루프(SP-E.10.3). 실 학습은 외부(4070/클라우드) — 본 클래스는
    상태기계: ①직전 채택 어댑터를 다음 라운드 init으로 링크 ②실측 주입→수용판정
    ③adopt면 어댑터 승격(누적), rollback이면 폐기(직전 어댑터 유지) ④base-anchored KL
    병행 기록(누적 드리프트 은폐 방지) ⑤졸업 불변식 5연속 → Phase E Exit v14.0.0.

    실 학습 비수행 → run_round의 계획·게이트만 사용. measured_w1 등은 GPU 측 산출."""

    def __init__(self, closure: Optional[LoopCClosure] = None,
                 base_model: str = "meta-llama/Llama-3.1-8B-Instruct") -> None:
        self.closure = closure or LoopCClosure(base_model=base_model)
        self.base_model = base_model
        self.current_adapter: Optional[str] = None   # None = base만(첫 라운드)
        self.ledger: List[Dict[str, Any]] = []

    def submit_round(self, *, pairs_path: str, measured_w1: float, kl: float,
                     w1_ci_lower: float, length_rule_rate: float,
                     n_pairs: int, adapter_path: Optional[str] = None,
                     base_anchored_kl: Optional[float] = None,
                     before_result: Any = None, after_result: Any = None,
                     r_before: Optional[float] = None, r_after: Optional[float] = None,
                     signals: Optional[RoutingSignals] = None) -> CumulativeRoundResult:
        """1 누적 라운드 제출. GPU 학습 산출(measured_w1/kl/ci/length_rule_rate/adapter_path)을
        받아 수용판정 → 어댑터 승격/폐기 + 졸업 판정."""
        round_idx = len(self.ledger) + 1
        init_adapter = self.current_adapter   # 체이닝: 직전 채택 어댑터에서 출발

        rep = self.closure.run_round(
            pairs_path, round_idx=round_idx, measured_w1=measured_w1, kl=kl,
            r_before=r_before, r_after=r_after,
            before_result=before_result, after_result=after_result, signals=signals)

        gate = rep.gate
        decision = "adopt" if (gate is not None and gate.passed) else "rollback"
        c3_passed = bool(getattr(gate, "c3_structure", False)) if gate else False

        record = {
            "round_idx": round_idx, "decision": decision, "n_pairs": int(n_pairs),
            "w1": measured_w1, "kl": kl, "base_anchored_kl": base_anchored_kl,
            "w1_ci_lower": w1_ci_lower, "length_rule_rate": length_rule_rate,
            "c3_passed": c3_passed,
            "init_adapter": init_adapter, "adapter_path": adapter_path,
        }
        # 승격(누적) / 폐기
        if decision == "adopt" and adapter_path:
            self.current_adapter = adapter_path      # 다음 라운드 init으로 체이닝
        # rollback: current_adapter 불변(직전 채택 유지)

        self.ledger.append(record)
        grad = graduation_invariant(self.ledger)
        return CumulativeRoundResult(
            round_idx=round_idx, decision=decision, init_adapter=init_adapter,
            adapter_path=adapter_path, current_adapter=self.current_adapter,
            report=rep.to_dict(), ledger_record=record, graduation=grad,
            exit=bool(grad["graduated"]))
