"""
learning/first_training_kit.py — 4070 첫 실 학습 실행 킷 (V771, ADR-231).

목적: 개발자가 RTX 4070에서 **첫 실 QLoRA DPO 학습 1회**를 돌려 baseline 승률 이동을
측정하도록 돕는 준비·계획·검증 도구. 실 학습은 train_local.py(사용자 PC)에서 수행.

원칙:
- 저작권 보호: 명작/생성 텍스트를 킷에 싣지 않음. 개발자의 로컬 dpo_pairs.jsonl(전체)을 가리킴.
- 1회=메커니즘 증명(승률이 움직이는가). 본 성과는 데이터 확대+가드레일 반복(데이터 적으면 경고).
LLM-0: 외부 LLM 미호출(준비·계획만).
"""
from __future__ import annotations
from typing import Any, Dict, List

from literary_system.learning.loop_c import (
    PreferencePair, load_preference_pairs, write_dpo_jsonl, generation_win_rate)
from literary_system.finetune.gpu_adapter import LocalGPUAdapter

DEFAULT_BASE = "meta-llama/Llama-3.2-3B"     # 4070 안전(3B QLoRA ~6GB)
MIN_RECOMMENDED_PAIRS = 50                    # 이하면 '메커니즘 증명용'으로만


def baseline_winrate(pairs: List[PreferencePair]) -> float:
    """학습 전 생성 vs 명작 승률(loop-C 격차)."""
    return generation_win_rate(pairs)


def make_smoke_dataset(path: str, n: int = 4) -> int:
    """저작권 무관 합성 선호쌍 → 개발자 원본포맷(func/genre/ref_id/winner/draft/ref) jsonl.
    파이프라인 스모크 전용(품질 의미 없음). build_training_plan/prepare_dpo가 소비."""
    import json
    with open(path, "w", encoding="utf-8") as f:
        for i in range(n):
            f.write(json.dumps({
                "func": "setup", "genre": "thriller", "ref_id": f"smoke::{i}",
                "winner": "draft" if i % 2 == 0 else "ref",
                "draft": f"[합성 생성 초안 {i}] 인물이 문을 열고 복도로 들어선다. 긴장이 흐른다.",
                "ref":   f"[합성 참조 {i}] 그는 멈췄다. 숨을 골랐다. 다시 걸음을 옮겼다.",
            }, ensure_ascii=False) + "\n")
    return n


def prepare_dpo(pairs_path: str, out_path: str) -> int:
    """개발자 dpo_pairs.jsonl(전체) → DPO 표준(prompt/chosen/rejected) jsonl 변환."""
    return write_dpo_jsonl(load_preference_pairs(pairs_path), out_path)


def build_training_plan(pairs_path: str, base_model: str = DEFAULT_BASE,
                        out_dir: str = "./lora_out", rank: int = 16,
                        epochs: float = 1.0) -> Dict[str, Any]:
    """첫 학습 계획서 — 데이터·VRAM·명령·경고 일괄."""
    pairs = load_preference_pairs(pairs_path)
    n = len(pairs)
    adapter = LocalGPUAdapter()
    vram = adapter.estimate_vram_gb(base_model)
    fits = adapter.fits_locally(base_model)
    warnings: List[str] = []
    if n < MIN_RECOMMENDED_PAIRS:
        warnings.append(f"데이터 {n}쌍 < 권장 {MIN_RECOMMENDED_PAIRS} → 1회 결과는 '메커니즘 증명'용. "
                        f"품질 향상엔 데이터 확대+반복 필요")
    if not fits:
        warnings.append(f"{base_model} VRAM {vram}GB > 12GB → 더 작은 모델 또는 클라우드 권장")
    dpo_out = out_dir.rstrip("/") + "/dpo_dataset.jsonl"
    cmd = (f"python -m literary_system.finetune.train_local "
           f"--dataset {dpo_out} --base {base_model} --out {out_dir} "
           f"--rank {rank} --epochs {epochs}")
    return {
        "n_pairs": n,
        "baseline_winrate": baseline_winrate(pairs),
        "base_model": base_model,
        "vram_estimate_gb": vram,
        "fits_4070": fits,
        "dpo_dataset": dpo_out,
        "train_command": cmd,
        "epochs": epochs,
        "warnings": warnings,
        "note": "학습 후 eval_winrate로 재측정 → baseline 대비 이동 확인. 1회=증명, 반복=향상.",
    }


def winrate_delta(before: float, after: float) -> Dict[str, Any]:
    """학습 전후 승률 비교 — 메커니즘 증명 판정(이동했는가)."""
    delta = round(after - before, 4)
    return {
        "before": before, "after": after, "delta": delta,
        "moved": delta != 0.0,
        "improved": delta > 0.0,
        "verdict": ("향상" if delta > 0 else "정체/하락" if delta <= 0 else "무변화"),
    }
