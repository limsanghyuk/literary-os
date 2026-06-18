"""
critic/distribution_guard.py — M3 분포 매칭 음성 가드레일 (V784, ADR-245).

명작 통계(대사/지문 비, 비트별 감정어 빈도, 씬 길이)를 **상한·하한 가드로만** 사용.
★비대칭 원칙(ADR-243 M3):
- **금지**: 분포 일치를 *양성 보상*으로 → 평균회귀(mode-seeking, 밋밋한 중앙) + 굿하트(통계만 맞는 영혼없는 텍스트). 명작은 평균을 *일탈*한다 = 일치 보상은 탁월함을 억제.
- **허용**: *병리적 이상치*(대사 0% / 감정어 90% / 씬 길이 폭주)만 **감점·기각**.
- "깨진 것을 거르되 전형성을 보상하지 않는다." → 점수는 [페널티, 0] 범위(보너스 없음).
LLM-0: 순수 텍스트 통계(LLM 미호출).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# 명작 코퍼스 통계에서 유도된 '정상 범위'(데모 근사). 범위 *밖*(병리)만 감점.
NORMAL_BANDS: Dict[str, Tuple[float, float]] = {
    "dialogue_ratio":   (0.10, 0.75),   # 대사 비율: 0%(설명만)·~100%(지문없음) 병리
    "emotion_word_rate": (0.0, 0.20),   # 감정어 비율 상한(과잉 신파 차단). 하한 없음
    "avg_sentence_len": (2.0, 60.0),    # 평균 문장 길이(토큰): 한국어 단문체 허용, 폭주만 병리
    "scene_len_tokens": (20.0, 1200.0), # 씬 길이: 빈약/폭주 병리
}
EMOTION_WORDS = ["사랑", "분노", "슬픔", "두려움", "절망", "환희", "그리움", "외로움",
                 "행복", "고통", "기쁨", "눈물", "심장", "가슴", "떨림"]
PATHOLOGY_PENALTY = -1.0    # 병리 1건당 감점(누적). 정상=0(무보상)


def _tokens(text: str) -> List[str]:
    return re.findall(r"\w+", text)


def _sentences(text: str) -> List[str]:
    return [s for s in re.split(r"(?<=[.!?。])\s+|(?<=다)\s+", text.strip()) if s]


def compute_stats(text: str) -> Dict[str, float]:
    toks = _tokens(text); sents = _sentences(text)
    n_tok = len(toks) or 1
    # 대사 비율: 따옴표 안 토큰 비중(근사)
    quoted = re.findall(r'["“”‘’\'](.*?)["“”‘’\']', text)
    q_tok = sum(len(_tokens(q)) for q in quoted)
    emo = sum(text.count(w) for w in EMOTION_WORDS)
    return {
        "dialogue_ratio":   round(q_tok / n_tok, 4),
        "emotion_word_rate": round(emo / n_tok, 4),
        "avg_sentence_len": round(n_tok / (len(sents) or 1), 2),
        "scene_len_tokens": float(n_tok),
    }


@dataclass
class GuardResult:
    penalty:      float                 # ≤0 (병리 누적 감점). 0=정상(무보상)
    pathologies:  List[Dict[str, Any]]  # 위반 항목
    stats:        Dict[str, float]
    rejected:     bool                  # 심각 병리 → 기각

    @property
    def is_pathological(self) -> bool:
        return self.penalty < 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"penalty": self.penalty, "pathologies": self.pathologies,
                "stats": self.stats, "rejected": self.rejected,
                "is_pathological": self.is_pathological}


def distribution_guard(text: str,
                       bands: Optional[Dict[str, Tuple[float, float]]] = None,
                       reject_threshold: float = -2.0) -> GuardResult:
    """
    명작 정상범위 *밖*(병리)만 감점. 범위 안=0(보너스 없음 — 전형성 무보상).
    누적 감점 ≤ reject_threshold → 기각.
    """
    bands = bands or NORMAL_BANDS
    stats = compute_stats(text)
    paths: List[Dict[str, Any]] = []
    penalty = 0.0
    for key, (lo, hi) in bands.items():
        v = stats.get(key, 0.0)
        if v < lo:
            paths.append({"metric": key, "value": v, "band": [lo, hi], "side": "below"})
            penalty += PATHOLOGY_PENALTY
        elif v > hi:
            paths.append({"metric": key, "value": v, "band": [lo, hi], "side": "above"})
            penalty += PATHOLOGY_PENALTY
    penalty = round(penalty, 3)
    return GuardResult(penalty, paths, stats, rejected=penalty <= reject_threshold)


def apply_guard_to_reward(base_reward: float, text: str, **kw) -> float:
    """
    보상에 음성 가드만 적용: reward + penalty(≤0). 분포 일치 보너스 없음.
    기각이면 강한 하한(-inf 대용 큰 음수).
    """
    g = distribution_guard(text, **kw)
    if g.rejected:
        return -9.99
    return round(base_reward + g.penalty, 4)
