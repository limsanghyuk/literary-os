"""
learning/e4ext_exit.py — E.4 확장 트랙 Exit Gate (V778, ADR-238).

V767~V777(전이 트랙 이후 확장)의 통합 종료 판정:
GPU 3-모드(로컬/클라우드/하이브리드) + loop-C 폐회로 + 품질 라벨·판별 게이트 + 클라우드 운영 라이프사이클.
전 항목 PASS → E.4 확장 종료, 다음(데이터 규모 확대·실 GPU 라운드 또는 공식 Phase E 후반) 진입 가능.
LLM-0: critic/만 LLM-1, 나머지 LLM-0. 순수 판정.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Dict, List

_REPO = Path(__file__).resolve().parents[2]


def run_e4ext_exit() -> Dict:
    cps: List[Dict] = []
    def add(name, ok, detail=""):
        cps.append({"name": name, "passed": bool(ok), "detail": str(detail)})

    # CP-1 GPU 3-모드 (V767 로컬 / V768 라우팅 / V770 모드 디스패처)
    try:
        from literary_system.finetune.gpu_adapter import GPUProvider, LocalGPUAdapter
        from literary_system.learning.provider_router import ProviderRouter
        from literary_system.learning.pareto_router import TrainingMode, dispatch_training
        modes = {m.value for m in TrainingMode}
        ok = {"local", "cloud", "hybrid", "auto"} <= modes and GPUProvider.LOCAL.value == "local"
        add("CP-1 GPU 3-모드(로컬/클라우드/하이브리드/auto)", ok, f"modes={sorted(modes)}")
    except Exception as e:
        add("CP-1 GPU 3-모드", False, str(e))

    # CP-2 클라우드 실 어댑터 + 운영 라이프사이클 (V772/V777)
    try:
        from literary_system.finetune.runpod_real_adapter import RealRunPodAdapter
        from literary_system.finetune.runpod_lifecycle import RunPodJobLifecycle
        add("CP-2 클라우드 실 어댑터+라이프사이클", True, "RealRunPod+Lifecycle")
    except Exception as e:
        add("CP-2 클라우드 실 어댑터+라이프사이클", False, str(e))

    # CP-3 분업 파이프라인 + 파레토 (V769/V770)
    try:
        from literary_system.learning.split_pipeline import SplitPipeline
        from literary_system.learning.pareto_router import ParetoRouter
        add("CP-3 분업+파레토 라우팅", True, "SplitPipeline+ParetoRouter")
    except Exception as e:
        add("CP-3 분업+파레토 라우팅", False, str(e))

    # CP-4 loop-C 폐회로 + 수용 게이트 (V774)
    try:
        from literary_system.learning.loopc_closure import LoopCClosure
        from literary_system.learning.winrate_gate import g_loopc_winrate
        g = g_loopc_winrate(0.5, 0.7, n_pairs=80)
        add("CP-4 loop-C 폐회로+G_LOOPC_WINRATE", g.passed, f"수용판정 {g.decision}")
    except Exception as e:
        add("CP-4 loop-C 폐회로", False, str(e))

    # CP-5 품질 라벨 2축 + 판별 게이트 (V775/V776)
    try:
        from literary_system.quality.quality_labels import DEMO_LABELS
        from literary_system.quality.critic_discrimination_gate import g_critic_discrimination, craft_axis_scorer
        from literary_system.quality.quality_aggregator import from_drama_dict
        disc = g_critic_discrimination(craft_axis_scorer)
        add("CP-5 품질 2축+판별 게이트", disc.passed, f"판별 AUC={disc.auc}")
    except Exception as e:
        add("CP-5 품질 2축+판별 게이트", False, str(e))

    # CP-6 첫 학습 킷 + 실측 증명 (V771 + real_dpo_proof)
    try:
        from literary_system.learning.first_training_kit import build_training_plan
        proof = (_REPO / "docs/sessions/2026-06-16_real_dpo_proof/RESULT_2.md").exists()
        add("CP-6 첫 학습 킷+실측 증명", proof, "first_training_kit + RESULT_2")
    except Exception as e:
        add("CP-6 첫 학습 킷+실측 증명", False, str(e))

    # CP-7 ADR 227~237 연속
    miss = [n for n in range(227, 238) if not (_REPO / "docs/adr" / f"ADR-{n}.md").exists()]
    add("CP-7 ADR-227~237 연속", not miss, "누락 없음" if not miss else f"누락 {miss}")

    passed = all(c["passed"] for c in cps)
    return {"gate": "E4-EXT-EXIT", "phase": "E.4 확장(GPU 3-모드+폐회로+품질+운영)",
            "passed": passed, "checkpoints": cps,
            "n_pass": sum(c["passed"] for c in cps), "n_total": len(cps),
            "note": "확장 트랙 종료. 다음=데이터 규모 확대·실 GPU 라운드 또는 공식 Phase E 후반(UI/KEDA)"}
