"""V370: EmotionToBehaviorRenderer — 4D 감정 벡터 → 신체·행동 표현 변환."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EmotionalDelta:
    tension:   float = 0.0   # 긴장 (0.0~1.0)
    sympathy:  float = 0.0   # 공감·연민 (0.0~1.0)
    dread:     float = 0.0   # 공포·불안 (0.0~1.0)
    catharsis: float = 0.0   # 해소·안도 (0.0~1.0)

    def dominant(self) -> str:
        """가장 강한 감정 축 이름 반환."""
        vals = {"tension": self.tension, "sympathy": self.sympathy,
                "dread": self.dread, "catharsis": self.catharsis}
        return max(vals, key=vals.get)

    def intensity(self) -> float:
        """4D 벡터의 L-inf 노름 (최댓값)."""
        return max(self.tension, self.sympathy, self.dread, self.catharsis)


@dataclass
class BehaviorText:
    text:      str
    intensity: float           # 0.0~1.0 (cluster_weight 반영)
    emotion:   str             # dominant 감정 레이블
    metadata:  Dict[str, Any] = field(default_factory=dict)


# ── 30+ 변환 규칙 테이블 ─────────────────────────────────────────────────
# (dominant_emotion, weight_band) → 행동 표현 목록 [(저강도, 고강도)]
# weight_band: "low"(0.0~0.4), "mid"(0.4~0.7), "high"(0.7~1.0)
_RULES: Dict[Tuple[str, str], List[str]] = {
    # tension
    ("tension", "low"):  ["눈이 문 쪽으로 갔다", "손이 무릎 위에서 멈췄다"],
    ("tension", "mid"):  ["손바닥을 바지선에 한 번 문질렀다", "어깨가 귀 쪽으로 올라갔다"],
    ("tension", "high"): ["이를 악물었다", "손이 주먹을 쥐었다"],
    # sympathy
    ("sympathy", "low"):  ["컵 바닥에 시선을 오래 두었다", "손끝을 늦게 접었다"],
    ("sympathy", "mid"):  ["숨을 한 번 천천히 내쉬었다", "시선이 그쪽에서 떨어지지 않았다"],
    ("sympathy", "high"): ["눈 안쪽이 뜨거워졌다", "손을 뻗다가 멈췄다"],
    # dread
    ("dread", "low"):  ["등 뒤가 서늘했다", "손가락 끝이 식었다"],
    ("dread", "mid"):  ["발바닥이 바닥에 들러붙는 것 같았다", "문고리 쪽으로 눈이 갔다"],
    ("dread", "high"): ["손바닥의 물기를 바지선에 문질렀다", "숨이 반 박자 늦게 나왔다"],
    # catharsis
    ("catharsis", "low"):  ["어깨가 한 박자 늦게 내려갔다", "뒷목이 천천히 식었다"],
    ("catharsis", "mid"):  ["숨을 크게 한 번 들이쉬었다", "손이 풀렸다"],
    ("catharsis", "high"): ["발끝까지 따뜻한 것 같았다", "눈을 한 번 크게 떴다가 감았다"],
    # 복합: tension + dread
    ("dread+tension", "low"):  ["등골이 서늘했다"],
    ("dread+tension", "mid"):  ["손이 떨렸다", "턱에 힘이 들어갔다"],
    ("dread+tension", "high"): ["발이 움직이지 않았다", "혀가 입천장에 붙었다"],
    # 복합: tension + sympathy (배신)
    ("sympathy-tension", "low"):  ["그의 이름이 든 봉투를 한 번 접었다"],
    ("sympathy-tension", "mid"):  ["그의 이름이 든 봉투를 두 번 접었다"],
    ("sympathy-tension", "high"): ["봉투 모서리를 손톱 밑으로 눌렀다"],
    # 복합: tension + catharsis (분노)
    ("tension+catharsis", "low"):  ["말끝을 삼켰다"],
    ("tension+catharsis", "mid"):  ["말끝을 삼키고 의자 등받이를 밀었다"],
    ("tension+catharsis", "high"): ["봉투 모서리를 손톱 밑으로 눌렀다"],
}


def _weight_band(w: float) -> str:
    if w < 0.4: return "low"
    if w < 0.7: return "mid"
    return "high"


def _select_complex_key(delta: EmotionalDelta) -> Optional[str]:
    """복합 감정 키 선택."""
    if delta.dread >= 0.5 and delta.tension >= 0.5:
        return "dread+tension"
    if delta.tension >= 0.5 and delta.sympathy < 0.3:
        return "tension+catharsis"
    if delta.sympathy < 0.3 and delta.tension >= 0.4:
        return "sympathy-tension"
    return None


class EmotionToBehaviorRenderer:
    """
    V360 EmotionalMomentumTracker의 4D 벡터를 구체적 신체·행동 표현으로 변환.
    cluster_weight는 CharacterClusterDetector.cohesion_score를 직접 반영.
    """

    def __init__(self, cluster_registry: Optional[Dict[str, float]] = None) -> None:
        """
        cluster_registry: {char_id: cohesion_score} 사전.
        없으면 weight=0.5 (중립) 사용.
        """
        self._registry: Dict[str, float] = cluster_registry or {}

    def register_cluster(self, char_id: str, cohesion_score: float) -> None:
        self._registry[char_id] = max(0.0, min(1.0, cohesion_score))

    def get_cluster_weight(self, char_id: str) -> float:
        return self._registry.get(char_id, 0.5)

    def render(self, delta: EmotionalDelta, char_id: str = "") -> BehaviorText:
        """4D 벡터 + char_id → 신체·행동 표현 BehaviorText."""
        weight = self.get_cluster_weight(char_id)
        band   = _weight_band(weight)

        # 복합 키 우선
        complex_key = _select_complex_key(delta)
        if complex_key and (complex_key, band) in _RULES:
            candidates = _RULES[(complex_key, band)]
        else:
            dom  = delta.dominant()
            key  = (dom, band)
            candidates = _RULES.get(key, [f"{dom} 감정이 신체에 나타났다"])

        # weight가 높을수록 목록 뒷부분(더 강렬한 표현) 선택
        idx = min(int(weight * len(candidates)), len(candidates) - 1)
        text = candidates[idx]

        return BehaviorText(
            text=text,
            intensity=round(weight * delta.intensity(), 3),
            emotion=complex_key or delta.dominant(),
        )

    def render_sequence(self, deltas: List[Tuple[EmotionalDelta, str]]) -> List[BehaviorText]:
        """여러 (delta, char_id) 쌍을 순서대로 변환."""
        return [self.render(d, cid) for d, cid in deltas]
