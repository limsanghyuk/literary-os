"""
SP-A.7 (V594) — LOSConstitution v1.0

Han-dramaturgy 5-축 장면 품질 헌법.

5축 가중합:
  drse    0.30 — DRSE S-score (내러티브 밀도)
  debt    0.20 — 이야기 빚(미결 플롯훅) 해소율
  arc     0.20 — 4막(기승전결) 구조 신호
  tension 0.15 — 갈등/긴장 밀도
  prose   0.15 — 산문 품질 (어휘 다양성 + 문장 변화)

ADR-054 참조.
LLM-0 준수: 외부 LLM 호출 없음 — 순수 텍스트 메트릭.
"""
from __future__ import annotations

import math
import re
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

# ---------------------------------------------------------------------------
# ConstitutionWeights — 5축 가중치
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConstitutionWeights:
    """
    LOSConstitution 5축 가중치 (합계 = 1.0).

    ADR-054 기본값:
        drse=0.30, debt=0.20, arc=0.20, tension=0.15, prose=0.15
    """
    drse:    float = 0.30
    debt:    float = 0.20
    arc:     float = 0.20
    tension: float = 0.15
    prose:   float = 0.15

    def __post_init__(self):
        total = self.drse + self.debt + self.arc + self.tension + self.prose
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"ConstitutionWeights 합계 != 1.0 (got {total:.6f})")

    def as_dict(self) -> Dict[str, float]:
        return {
            "drse":    self.drse,
            "debt":    self.debt,
            "arc":     self.arc,
            "tension": self.tension,
            "prose":   self.prose,
        }


# ---------------------------------------------------------------------------
# 결과 dataclass
# ---------------------------------------------------------------------------

@dataclass
class ConstitutionSceneScore:
    """단일 장면 5축 점수 + 가중합."""
    scene_id:   str
    drse:       float
    debt:       float
    arc:        float
    tension:    float
    prose:      float
    total:      float       # 가중합 R(scene)
    weights:    ConstitutionWeights = field(default_factory=ConstitutionWeights)

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "drse":     self.drse,
            "debt":     self.debt,
            "arc":      self.arc,
            "tension":  self.tension,
            "prose":    self.prose,
            "total":    self.total,
        }


@dataclass
class ConstitutionWorkScore:
    """작품(장면 집합) 집계 점수."""
    mean_total:     float       # 장면 점수 평균
    variance_total: float       # 장면 점수 분산
    work_score:     float       # mean - 0.10·variance
    scene_count:    int
    scene_scores:   List[ConstitutionSceneScore] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "mean_total":     self.mean_total,
            "variance_total": self.variance_total,
            "work_score":     self.work_score,
            "scene_count":    self.scene_count,
        }


# ---------------------------------------------------------------------------
# 텍스트 메트릭 함수 (LLM-0)
# ---------------------------------------------------------------------------

_NARRATIVE_KO = [
    "했다", "였다", "이었다", "라고", "하며", "그리고", "하지만", "그러나",
    "때문에", "때", "에서", "라는", "하여", "이며", "으로", "가며",
]
_TENSION_KO = [
    "위기", "갈등", "충돌", "대립", "긴장", "공포", "분노", "절망",
    "싸움", "전쟁", "배신", "죽음", "위험", "비밀", "거짓", "협박",
    "도망", "추격", "반전", "충격",
]
_ARC_KO = {
    "기": ["시작", "처음", "소개", "등장", "만났", "도착", "출발", "새로운"],
    "승": ["발전", "진행", "이어", "계속", "성장", "변화", "발견", "알게"],
    "전": ["반전", "위기", "갑자기", "예상치", "하지만", "그러나", "충격", "문제"],
    "결": ["해결", "끝", "마침내", "결국", "드디어", "완성", "마지막", "이후"],
}
_DEBT_HOOKS = [
    r"\?",                          # 물음표 (미답 질문)
    r"[\.。]{3}",                   # 말줄임표 (미결 여운)
    r"언젠가|나중에|다음에|곧",      # 미래 약속 → 빚
]
_DEBT_RESOLUTIONS = [
    r"했다\.",                      # 완결 행동
    r"이었다\.",
    r"였다\.",
    r"해결",
    r"끝났다",
    r"마침내",
    r"드디어",
]


def _words(text: str) -> List[str]:
    return text.split()


def _score_drse(text: str) -> float:
    """DRSE S-score: length + vocab TTR + narrative marker."""
    wds = _words(text)
    n = len(wds)
    if n < 5:
        return 0.0
    length_s  = min(1.0, math.log(n + 1) / math.log(101))
    ttr       = len(set(w.lower() for w in wds)) / n
    vocab_s   = min(1.0, ttr * 2)
    tl        = text.lower()
    nm_hits   = sum(1 for m in _NARRATIVE_KO if m in tl)
    density   = nm_hits / max(1, n / 10)
    narrative_s = min(1.0, density * 0.5)
    return round(min(1.0, 0.40 * length_s + 0.35 * vocab_s + 0.25 * narrative_s), 4)


def _score_debt(text: str) -> float:
    """
    이야기 빚 해소율.
    hooks(미결) 대비 resolutions(해결) 비율.
    hooks 없으면 0.80 (중간값 — 미결 부채 없음), hooks > resolutions → 낮은 점수.
    BUG-02 fix: 빈 텍스트 조기 반환 (0.0). 비빈 no-hook은 0.80 유지.
    """
    if not text.strip():                # BUG-02 fix: 빈 텍스트만 0.0
        return 0.0
    hook_count = sum(len(re.findall(p, text)) for p in _DEBT_HOOKS)
    res_count  = sum(len(re.findall(p, text)) for p in _DEBT_RESOLUTIONS)
    if hook_count == 0:
        return 0.80   # 미결 훅 없음 → 부채 해소율 양호 (설계 의도 유지)
    ratio = res_count / hook_count
    return round(min(1.0, 0.5 + ratio * 0.5), 4)


def _score_arc(text: str) -> float:
    """
    4막(기승전결) 구조 신호 탐지 — 위치 기반 순서 검증.
    BUG-07 fix: 단순 존재 여부 → 각 1/4 구간에서 해당 막 탐지.
    역방향(결전승기)은 정방향(기승전결)과 다른 점수를 받음.
    """
    sentences = re.split(r'[.!?\n。]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    n = len(sentences)
    if n < 2:
        # 문장이 1개 이하면 전체 텍스트에서 존재 여부만 확인 (단문 씬 지원)
        tl = text.lower()
        present = sum(
            1 for markers in _ARC_KO.values()
            if any(m in tl for m in markers)
        )
        return round(present / 4.0, 4) * 0.5   # 단문은 최대 0.5점
    quarter = max(1, n // 4)
    acts = list(_ARC_KO.keys())                 # ["기", "승", "전", "결"]
    score = 0
    for i, act in enumerate(acts):
        start = i * quarter
        end = (i + 1) * quarter if i < 3 else n
        section_text = " ".join(sentences[start:end]).lower()
        if any(m in section_text for m in _ARC_KO[act]):
            score += 1
    return round(score / 4.0, 4)


def _score_tension(text: str) -> float:
    """갈등/긴장 마커 밀도."""
    tl = text.lower()
    wds = _words(text)
    if not wds:                        # BUG-02 fix: 빈 텍스트만 0.0
        return 0.0
    hits = sum(1 for m in _TENSION_KO if m in tl)
    density = hits / max(1, len(wds) / 10)
    return round(min(1.0, density * 0.6 + 0.2), 4)   # base 0.2 유지 (비빈 텍스트)


def _score_prose(text: str) -> float:
    """산문 품질: 어휘 다양성 + 문장 변화."""
    sentences = re.split(r'[.!?\n。！？]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    n_sent = len(sentences)
    if n_sent == 0:
        return 0.0
    # 어휘 다양성 (TTR)
    wds = _words(text)
    ttr = len(set(w.lower() for w in wds)) / max(1, len(wds))
    vocab_s = min(1.0, ttr * 1.5)
    # 문장 길이 변화 (표준편차 / 평균)
    lens = [len(s.split()) for s in sentences]
    mean_l = sum(lens) / n_sent
    if mean_l == 0:
        variety_s = 0.0
    else:
        std_l = statistics.pstdev(lens) if len(lens) > 1 else 0.0
        variety_s = min(1.0, std_l / max(1, mean_l))
    return round(0.60 * vocab_s + 0.40 * variety_s, 4)


# ---------------------------------------------------------------------------
# LOSConstitution — 핵심 클래스
# ---------------------------------------------------------------------------

_Scene = Union[str, Dict[str, Any]]


def _extract_text(scene: _Scene) -> str:
    """장면 입력에서 텍스트 추출 (str 또는 dict["text"/"content"/"scene_text"])."""
    if isinstance(scene, str):
        return scene
    for key in ("text", "content", "scene_text", "body", "dialogue"):
        if key in scene and isinstance(scene[key], str):
            return scene[key]
    # 모든 str 값 합치기
    return " ".join(v for v in scene.values() if isinstance(v, str))


def _extract_id(scene: _Scene, idx: int) -> str:
    if isinstance(scene, dict):
        for key in ("id", "scene_id", "entry_id"):
            if key in scene:
                return str(scene[key])
    return f"scene_{idx:04d}"


class LOSConstitution:
    """
    SP-A.7 (V594) — Literary OS 장면 품질 헌법 v1.0.

    5축 가중합으로 장면/작품 품질을 수치화.
    ADR-054 기준: R(scene) 평균 ≥ 0.65, variance ≤ 0.05.

    LLM-0 준수: 외부 LLM 호출 없음.

    Usage::

        los = LOSConstitution()
        score = los.score_scene(scene_text)
        assert score >= 0.0

        work_score = los.score_work(scenes)
        assert work_score.mean_total >= 0.65

        reward = los.rlhf_reward(generated_text, original_text)
        assert -1.0 <= reward <= 1.0
    """

    def __init__(self, weights: Optional[ConstitutionWeights] = None) -> None:
        self._w = weights or ConstitutionWeights()

    @property
    def weights(self) -> ConstitutionWeights:
        return self._w

    # ── 단일 장면 ─────────────────────────────────────────

    def score_scene(
        self,
        scene: _Scene,
        scene_id: Optional[str] = None,
    ) -> float:
        """
        단일 장면 품질 점수 R(scene).

        Args:
            scene:    str 텍스트 또는 {"text": "...", ...} dict
            scene_id: 식별자 (선택)

        Returns:
            float in [0.0, 1.0]
        """
        return self._score_full(scene, scene_id or "scene_0").total

    def score_scene_full(
        self,
        scene: _Scene,
        scene_id: Optional[str] = None,
    ) -> ConstitutionSceneScore:
        """5축 분해 + R(scene) 포함 ConstitutionSceneScore 반환."""
        return self._score_full(scene, scene_id or "scene_0")

    def _score_full(self, scene: _Scene, sid: str) -> ConstitutionSceneScore:
        text = _extract_text(scene)
        drse    = _score_drse(text)
        debt    = _score_debt(text)
        arc     = _score_arc(text)
        tension = _score_tension(text)
        prose   = _score_prose(text)
        w = self._w
        total = round(
            w.drse * drse + w.debt * debt + w.arc * arc +
            w.tension * tension + w.prose * prose,
            4,
        )
        return ConstitutionSceneScore(
            scene_id=sid, drse=drse, debt=debt,
            arc=arc, tension=tension, prose=prose,
            total=total, weights=self._w,
        )

    # ── 작품(장면 집합) ───────────────────────────────────

    def score_work(self, scenes: Sequence[_Scene]) -> ConstitutionWorkScore:
        """
        작품 품질 점수.

        W(work) = mean(R_i) - 0.10 · variance(R_i)

        Args:
            scenes: 장면 시퀀스 (str 또는 dict)

        Returns:
            ConstitutionWorkScore
        """
        if not scenes:
            return ConstitutionWorkScore(
                mean_total=0.0, variance_total=0.0,
                work_score=0.0, scene_count=0,
            )
        scored = [
            self._score_full(s, _extract_id(s, i))
            for i, s in enumerate(scenes)
        ]
        totals = [s.total for s in scored]
        mean_v = statistics.mean(totals)
        var_v  = statistics.pvariance(totals)
        work_v = round(mean_v - 0.10 * var_v, 4)
        return ConstitutionWorkScore(
            mean_total     = round(mean_v, 4),
            variance_total = round(var_v, 4),
            work_score     = work_v,
            scene_count    = len(scored),
            scene_scores   = scored,
        )

    # ── RLHF 보상 ────────────────────────────────────────

    def rlhf_reward(
        self,
        generated: str,
        original: str,
    ) -> float:
        """
        RLHF 보상 신호.

        R_rlhf = R(generated) - R(original)
        클램프: [-1.0, 1.0]

        Args:
            generated: 모델이 생성한 텍스트
            original:  원본(레퍼런스) 텍스트

        Returns:
            float in [-1.0, 1.0]
        """
        r_gen  = self.score_scene(generated)
        r_orig = self.score_scene(original)
        reward = r_gen - r_orig
        return round(max(-1.0, min(1.0, reward)), 4)
