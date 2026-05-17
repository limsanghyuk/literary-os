"""V370: KoreanRhythmRewriter — 한국어 문장 리듬 분석·교정."""
from __future__ import annotations
import re
import statistics
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class RhythmResult:
    rewritten:     List[str]
    rhythm_score:  float        # 0.0~10.0 (높을수록 리듬 균일)
    interventions: int          # 교정된 문장 수
    original:      List[str] = field(default_factory=list)

    @property
    def joined(self) -> str:
        return " ".join(self.rewritten)


# ── 마지막 비트 단락 풀 ──────────────────────────────────────────────────
_LAST_BEAT_POOL = [
    "그리고 아무 말도 없었다.",
    "잠시 후, 누군가의 발소리가 복도에서 멀어졌다.",
    "창밖의 빛이 조금 낮아졌다.",
    "냉기가 방 안을 한 바퀴 돌았다.",
    "그것으로 그 씬은 끝났다.",
    "한동안 아무것도 움직이지 않았다.",
    "숨소리만 남았다.",
]


def _mora_count(sentence: str) -> int:
    """한글 글자 수 기반 모라(mora) 근사치. 공백 제외."""
    return len(re.sub(r"\s+", "", sentence))


class KoreanRhythmRewriter:
    """
    한국어 문장 리듬을 분석하고 NarrativeScopeResolver의 scene_rhythm에
    맞게 마지막 비트 단락 삽입 또는 이상치 문장을 교정한다.
    """

    def __init__(self, scene_rhythm: str = "medium") -> None:
        """scene_rhythm: 'slow' | 'medium' | 'fast'"""
        self.scene_rhythm = scene_rhythm

    def rewrite(self, sentences: List[str]) -> RhythmResult:
        if not sentences:
            return RhythmResult(rewritten=[], rhythm_score=10.0, interventions=0, original=[])

        moras = [_mora_count(s) for s in sentences]
        avg   = statistics.mean(moras) if moras else 1
        std   = statistics.stdev(moras) if len(moras) > 1 else 0.0
        threshold = 2.0  # 2σ 이상치

        result   = list(sentences)
        interventions = 0

        # 이상치 탐지 및 처리
        for i, (s, m) in enumerate(zip(sentences, moras)):
            if std > 0 and abs(m - avg) > threshold * std:
                # 너무 짧은 문장: 앞 문장과 합치거나 유지
                # 너무 긴 문장: 중간에 분리 마커 삽입 (간단 처리)
                if m < avg - threshold * std and i > 0:
                    result[i] = result[i - 1].rstrip(".") + ", " + s
                    result[i - 1] = ""
                    interventions += 1

        # 빈 항목 제거
        result = [s for s in result if s.strip()]

        # slow 리듬: 마지막 비트 단락 삽입
        if self.scene_rhythm == "slow":
            beat_idx = hash("|".join(sentences[:2])) % len(_LAST_BEAT_POOL)
            result.append(_LAST_BEAT_POOL[beat_idx])
            interventions += 1

        # 점수 계산: 이상치 비율 역수
        if len(sentences) == 0:
            score = 10.0
        else:
            anomaly_ratio = interventions / max(len(sentences), 1)
            score = round(10.0 * (1.0 - min(anomaly_ratio, 1.0)), 3)

        return RhythmResult(
            rewritten=result,
            rhythm_score=score,
            interventions=interventions,
            original=sentences,
        )

    def set_rhythm(self, rhythm: str) -> None:
        self.scene_rhythm = rhythm

    @staticmethod
    def _split_static(text: str) -> List[str]:
        """문자열을 한국어 문장 단위 리스트로 분리 (static 유틸)."""
        if not text or not text.strip():
            return [""]
        # 마침표·느낌표·물음표 뒤에서 분리, 빈 항목 제거
        parts = re.split(r"(?<=[.!?。])\s+", text.strip())
        result = [p.strip() for p in parts if p.strip()]
        return result if result else [""]

    def _split(self, text: str) -> List[str]:
        """인스턴스 메서드 — _split_static 위임."""
        return KoreanRhythmRewriter._split_static(text)
