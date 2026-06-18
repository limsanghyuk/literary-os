"""
critic/critic_qualification.py — M1 Critic 자격검정 (V782, ADR-243).

인간 작가 GT는 '최종시험'으로 보류 → 빈 alignment_monitor 닻을 인간 없이 *부분* 대체:
앵커를 "Critic↔인간GT"가 아니라 "**명작 > 등급화 열화판** 판별"로.

원칙(ADR-243 M1):
- 단일 픽 아닌 **등급화 열화 사다리**(미세→심각) → 단조 증가 변별곡선 + 올바른 순위 = 변별 *해상도*.
- **축별 표적 열화**(복선 제거·감정 평탄화·인과 단절·상투 어휘) → 통과하려면 그 축의 판단력 필요(표면 흔적 부정통과 차단).
- 자격 = 사다리 전 구간 명작 우위 + 단조성. (필요조건; 신작 *생성* 판정 자격 아님 — 천장=모작 정직 명시).
LLM-0: 열화 변환은 결정론(LLM 미호출). judge 훅(critic)만 LLM-1 경계.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

WIN_MIN = 0.80                  # 사다리 전체 명작 우위 최소 승률
JudgeFn = Callable[[str, str], str]   # (a=명작, b=열화) → 'a'|'b'|'tie'


class DegradeAxis(str, Enum):
    EMOTION    = "flatten_emotion"     # 감정 평탄화
    FORESHADOW = "remove_foreshadow"   # 복선/콜백 제거
    CAUSALITY  = "break_causality"     # 인과 단절(문장 셔플)
    DICTION    = "generic_diction"     # 상투/일반 어휘 치환


# 생생한 동사/감각어 → 평이어(상투 어휘 치환·감정 평탄화용)
_VIVID2FLAT = {
    "멈췄다": "갔다", "숨을 골랐다": "쉬었다", "심장이 뛰었다": "긴장했다",
    "떨렸다": "있었다", "깜빡였다": "켜졌다", "빛났다": "보였다",
    "흘렀다": "내렸다", "마주 섰다": "만났다", "붙었다": "기댔다",
}
_EMOTION_MARKERS = ["침묵", "어둠", "긴장", "그저", "천천히", "차가운"]


def _sentences(text: str) -> List[str]:
    parts = re.split(r'(?<=[.!?。])\s+|(?<=다)\s+', text.strip())
    return [p for p in parts if p]


def degrade(text: str, axis: DegradeAxis, severity: float) -> str:
    """명작 텍스트를 축별·등급별로 열화. severity 0(원본)~1(심각)."""
    severity = max(0.0, min(1.0, severity))
    if severity == 0.0:
        return text
    sents = _sentences(text)
    n_hit = max(1, int(round(len(sents) * severity)))

    if axis == DegradeAxis.CAUSALITY:
        # 인과 단절: 앞쪽 n_hit 문장을 역순으로(흐름 깨기)
        head = sents[:n_hit][::-1]
        return " ".join(head + sents[n_hit:])

    if axis == DegradeAxis.FORESHADOW:
        # 복선/여백 제거: 짧은(여운) 문장 n_hit개 삭제
        order = sorted(range(len(sents)), key=lambda i: len(sents[i]))
        drop = set(order[:n_hit])
        kept = [s for i, s in enumerate(sents) if i not in drop]
        return " ".join(kept) if kept else sents[0]

    # EMOTION / DICTION: 어휘 치환(감각·감정어 → 평이어), severity만큼 적용
    out = text
    items = list(_VIVID2FLAT.items())
    k = max(1, int(round(len(items) * severity)))
    for vivid, flat in items[:k]:
        out = out.replace(vivid, flat)
    if axis == DegradeAxis.EMOTION:
        for m in _EMOTION_MARKERS[:max(1, int(len(_EMOTION_MARKERS) * severity))]:
            out = out.replace(m, "")
    return re.sub(r'\s+', ' ', out).strip()


@dataclass
class DegradeRung:
    axis:     str
    severity: float
    text:     str


def build_ladder(masterpiece: str, axis: DegradeAxis,
                 severities: Tuple[float, ...] = (0.25, 0.5, 0.75, 1.0)) -> List[DegradeRung]:
    return [DegradeRung(axis.value, s, degrade(masterpiece, axis, s)) for s in severities]


@dataclass
class QualificationResult:
    passed:      bool
    win_rate:    float                 # 전체 명작 우위 비율
    monotone:    bool                  # severity↑ → 승률 단조(변별 해상도)
    per_axis:    Dict[str, Dict[str, Any]]
    n_trials:    int
    detail:      str

    def to_dict(self) -> Dict[str, Any]:
        return {"passed": self.passed, "win_rate": self.win_rate, "monotone": self.monotone,
                "per_axis": self.per_axis, "n_trials": self.n_trials, "detail": self.detail}


def _win(judge: JudgeFn, master: str, degraded: str) -> float:
    v = judge(master, degraded)         # a=master 우위면 1.0
    return 1.0 if v == "a" else (0.5 if v == "tie" else 0.0)


def qualify_critic(judge: JudgeFn, masterpieces: List[str],
                   axes: Optional[List[DegradeAxis]] = None,
                   severities: Tuple[float, ...] = (0.25, 0.5, 0.75, 1.0),
                   win_min: float = WIN_MIN) -> QualificationResult:
    """
    judge가 명작 > 열화판을 (a) 전 구간 우위(win≥win_min) (b) 단조 변별곡선으로 가르는지 검정.
    둘 다 충족한 critic만 자체평가 심판 자격.
    """
    axes = axes or list(DegradeAxis)
    per_axis: Dict[str, Dict[str, Any]] = {}
    all_wins: List[float] = []
    all_monotone = True

    for axis in axes:
        sev_win: Dict[float, List[float]] = {s: [] for s in severities}
        for mp in masterpieces:
            for rung in build_ladder(mp, axis, severities):
                w = _win(judge, mp, rung.text)
                sev_win[rung.severity].append(w)
                all_wins.append(w)
        curve = [round(sum(sev_win[s]) / len(sev_win[s]), 3) if sev_win[s] else 0.0 for s in severities]
        mono = all(curve[i] <= curve[i+1] + 1e-9 for i in range(len(curve)-1))
        all_monotone &= mono
        per_axis[axis.value] = {"curve": curve, "severities": list(severities),
                                "mean_win": round(sum(curve)/len(curve), 3), "monotone": mono}

    win_rate = round(sum(all_wins) / len(all_wins), 4) if all_wins else 0.0
    passed = win_rate >= win_min and all_monotone
    detail = (f"승률 {win_rate} (min {win_min}) · 단조 {all_monotone} → "
              f"{'자격 통과(심판 자격)' if passed else '자격 미달(자체평가 심판 부적격)'}")
    return QualificationResult(passed, win_rate, all_monotone, per_axis, len(all_wins), detail)
