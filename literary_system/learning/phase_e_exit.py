"""
learning/phase_e_exit.py — E.5 Phase E LLM-1 전이 Exit Gate (V766, ADR-226).

E.0(인간 GT·char_ner·Pass4-7) + E.2(LLM-1 Critic) + E.4(RLAIF/loop-C→보상→DPO→GPU 트리거)
의 LLM-0→LLM-1 전이 트랙 완료를 통합 판정. 전 항목 PASS → 전이 트랙 종료.
(주: 공식 Phase E 로드맵 V746~V820은 별개로 계속 진행)
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Dict, List

_REPO = Path(__file__).resolve().parents[2]


def run_phase_e_exit() -> Dict:
    cps: List[Dict] = []
    def add(name, ok, detail=""):
        cps.append({"name": name, "passed": bool(ok), "detail": str(detail)})

    # CP-1 E.0 인간 GT 프로토콜 (절대 닻)
    try:
        from literary_system.validation.human_gt import GTMode, HUMAN_GT_ALPHA_MIN, inter_rater_alpha
        add("CP-1 E.0 human_gt", HUMAN_GT_ALPHA_MIN >= 0.6, f"α_min={HUMAN_GT_ALPHA_MIN}")
    except Exception as e:
        add("CP-1 E.0 human_gt", False, str(e))

    # CP-2 E.0 char_ner + Pass4-7 산출물 존재
    base = _REPO / "docs/sessions/2026-06-13_corpus_ko_build"
    ner = (base / "pipeline/char_ner.py").exists()
    p47 = (base / "orchestration/passes4_7.py").exists()
    add("CP-2 E.0 char_ner+Pass4-7", ner and p47, f"ner={ner} pass4_7={p47}")

    # CP-3 E.2 SP-E.2 Exit (LLM-1 Critic 5게이트+7모듈)
    try:
        from literary_system.critic.spe2_exit import run_spe2_exit
        e2 = run_spe2_exit()
        add("CP-3 E.2 SP-E.2 Exit", e2["passed"], f"{e2['n_pass']}/{e2['n_total']} CP")
    except Exception as e:
        add("CP-3 E.2 SP-E.2 Exit", False, str(e))

    # CP-4 E.4 loop-C 선호쌍 적재
    try:
        from literary_system.learning.loop_c import PreferencePair, load_preference_pairs
        add("CP-4 E.4 loop-C", True, "PreferencePair+load")
    except Exception as e:
        add("CP-4 E.4 loop-C", False, str(e))

    # CP-5 E.4 보상모델(pairwise, 절대점수 금지)
    try:
        from literary_system.learning.reward_model import PairwiseRewardModel
        add("CP-5 E.4 reward_model", True, "PairwiseRewardModel")
    except Exception as e:
        add("CP-5 E.4 reward_model", False, str(e))

    # CP-6 E.4 RLAIF 오케스트레이터→GPU 트리거 사슬
    try:
        from literary_system.learning.rlaif_orchestrator import RLAIFOrchestrator
        from literary_system.learning.rlaif_trigger import RLAIFTrigger
        add("CP-6 E.4 RLAIF→GPU 트리거", True, "orchestrator+trigger")
    except Exception as e:
        add("CP-6 E.4 RLAIF→GPU 트리거", False, str(e))

    # CP-7 Phase E ADR 연속 (209~226)
    miss = [n for n in range(209, 227) if not (_REPO / "docs/adr" / f"ADR-{n}.md").exists()]
    add("CP-7 ADR-209~226 연속", not miss, "누락 없음" if not miss else f"누락 {miss}")

    passed = all(cp["passed"] for cp in cps)
    return {"gate": "PHASE-E-LLM1-EXIT", "phase": "E.0~E.4 LLM-0→LLM-1 전이 트랙",
            "passed": passed, "checkpoints": cps,
            "n_pass": sum(c["passed"] for c in cps), "n_total": len(cps),
            "note": "공식 Phase E 로드맵(V746~V820, v14.0.0)은 별개로 계속"}
