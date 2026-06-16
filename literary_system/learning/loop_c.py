"""
learning/loop_c.py — E.4 RLAIF 긴 루프(loop-C): 패널 선호쌍 → DPO 적재 + 생성 격차 지표 (V762, ADR-222)

Pass7 패널 판정(생성 draft vs 실명작 ref)을 DPO 선호쌍으로 정규화한다.
- 절대점수 금지: 쌍대 선호(chosen/rejected)만.
- 개발자 dpo_pairs.jsonl 포맷({func,genre,ref_id,winner,draft,ref}) 직접 인입.
- DPO 데이터셋 → finetune.lora_* (GPU 학습, Phase F)로 결선.
loop-C 격차 지표 = 생성 vs 명작 승률(현 baseline ~0.5, 학습으로 상승이 목표).
"""
from __future__ import annotations
import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PreferencePair:
    """DPO 학습 단위. winner_side ∈ {draft, ref}."""
    prompt: str
    chosen: str            # 선호된 텍스트
    rejected: str          # 비선호 텍스트
    source: str            # "panel" | "human"
    meta: Dict = field(default_factory=dict)

    @classmethod
    def from_pass7(cls, func: str, genre: str, draft: str, ref: str,
                   winner: str, ref_id: str = "", source: str = "panel") -> "PreferencePair":
        if winner not in ("draft", "ref"):
            raise ValueError(f"winner는 draft|ref: {winner}")
        chosen, rejected = (draft, ref) if winner == "draft" else (ref, draft)
        return cls(prompt=f"[{genre}/{func}] 한국 드라마 씬 생성",
                   chosen=chosen, rejected=rejected, source=source,
                   meta={"func": func, "genre": genre, "ref_id": ref_id, "winner": winner})


def load_preference_pairs(path: str) -> List[PreferencePair]:
    """dpo_pairs.jsonl({func,genre,ref_id,winner,draft,ref}) → PreferencePair[]."""
    out: List[PreferencePair] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out.append(PreferencePair.from_pass7(
                d.get("func", ""), d.get("genre", ""), d["draft"], d["ref"],
                d["winner"], d.get("ref_id", "")))
    return out


def to_dpo_dataset(pairs: List[PreferencePair]) -> List[Dict]:
    """DPO 표준 포맷 [{prompt, chosen, rejected}]."""
    return [{"prompt": p.prompt, "chosen": p.chosen, "rejected": p.rejected} for p in pairs]


def write_dpo_jsonl(pairs: List[PreferencePair], path: str) -> int:
    with open(path, "w", encoding="utf-8") as f:
        for r in to_dpo_dataset(pairs):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(pairs)


def generation_win_rate(pairs: List[PreferencePair]) -> float:
    """생성 vs 명작 승률(loop-C 격차 지표). winner=='draft' 비율."""
    n = len(pairs)
    return round(sum(1 for p in pairs if p.meta.get("winner") == "draft") / n, 4) if n else 0.0


def reference_strength(pairs: List[PreferencePair]) -> Dict[str, float]:
    """레퍼런스(명작 ref_id)별 강도 = pairwise BT (반복 등장 시 의미)."""
    from literary_system.validation.pairwise import bt_scores
    judgments = []
    for p in pairs:
        rid = p.meta.get("ref_id") or "ref"
        # draft(공통 'GEN') vs ref_id 쌍대: draft 패배(=ref 우세)면 ref가 left win
        if p.meta.get("winner") == "ref":
            judgments.append({"left_id": rid, "right_id": "GEN", "winner": "left"})
        else:
            judgments.append({"left_id": rid, "right_id": "GEN", "winner": "right"})
    return bt_scores(judgments) if judgments else {}


@dataclass(frozen=True)
class LoopCReport:
    n_pairs: int
    draft_win_rate: float
    by_function: Dict[str, int]
    by_winner: Dict[str, int]

    @property
    def summary(self) -> str:
        return (f"loop-C: {self.n_pairs}쌍 · 생성 승률={self.draft_win_rate} "
                f"(목표 baseline↑) · {self.by_winner}")


def summarize(pairs: List[PreferencePair]) -> LoopCReport:
    return LoopCReport(
        n_pairs=len(pairs),
        draft_win_rate=generation_win_rate(pairs),
        by_function=dict(Counter(p.meta.get("func", "?") for p in pairs)),
        by_winner=dict(Counter(p.meta.get("winner", "?") for p in pairs)))
