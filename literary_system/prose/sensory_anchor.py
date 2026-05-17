"""V370: SensoryAnchorInjector — 3축 감각 앵커 씬 주입."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SettingSeed:
    """SceneIntentIR의 감각 씨앗 정보."""
    visual:   str = ""   # 시각 앵커
    audio:    str = ""   # 청각 앵커
    tactile:  str = ""   # 촉각 앵커
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnchoredSceneIR:
    """감각 앵커가 주입된 씬 IR."""
    scene_id:       str
    base_text:      str
    anchors:        SettingSeed = field(default_factory=SettingSeed)
    injected_text:  str = ""
    density:        float = 0.0   # 앵커 주입 밀도 (0.0~1.0)
    metadata:       Dict[str, Any] = field(default_factory=dict)


# ── 기본 감각 앵커 예시 풀 (장르별) ──────────────────────────────────────
_DEFAULT_ANCHORS: Dict[str, List[str]] = {
    "visual":   [
        "먼지 낀 창문으로 가로등 빛이 길게 들어왔다",
        "형광등이 한 번 깜빡였다",
        "모서리에 쌓인 그림자가 방 안을 반쯤 덮었다",
        "창밖으로 나뭇잎이 하나 지나갔다",
        "벽 쪽 화분에서 흙 냄새가 났다",
    ],
    "audio":    [
        "멀리서 기차 소리가 한 번 났다가 사라졌다",
        "냉장고 소리가 유독 크게 들렸다",
        "빗소리가 창틀을 두드렸다",
        "복도에서 발소리가 멀어져 갔다",
        "시계 초침 소리만 남았다",
    ],
    "tactile":  [
        "손잡이의 냉기가 손바닥에 번졌다",
        "의자 등받이가 등에 닿는 감각이 낯설었다",
        "셔츠 안쪽으로 바람이 스몄다",
        "발바닥 아래 마루가 차가웠다",
        "종이 모서리가 손가락에 닿았다",
    ],
}


class SensoryAnchorInjector:
    """
    SceneIntentIR의 setting_seed에서 3축 감각 앵커를 추출하고 산문에 주입.
    씬 도입부(시각), 감정 전환 전(청각), 신체 행동(촉각) 위치에 삽입.
    """

    def __init__(self, genre_id: str = "literary") -> None:
        self.genre_id = genre_id

    def inject(self, scene_id: str, base_text: str,
               seed: Optional[SettingSeed] = None) -> AnchoredSceneIR:
        """씬 텍스트에 3축 감각 앵커를 주입한다."""
        seed = seed or SettingSeed()
        sentences = self._split(base_text)
        injected = list(sentences)
        injections = 0

        # 시각: 도입부 첫 번째 문장 앞
        visual = seed.visual or (
            _DEFAULT_ANCHORS["visual"][hash(scene_id) % len(_DEFAULT_ANCHORS["visual"])]
            if not seed.visual else ""
        )
        if visual and len(injected) >= 1:
            injected.insert(1, visual)
            injections += 1

        # 청각: 중간 지점
        audio = seed.audio or (
            _DEFAULT_ANCHORS["audio"][hash(scene_id + "a") % len(_DEFAULT_ANCHORS["audio"])]
            if not seed.audio else ""
        )
        mid = max(len(injected) // 2, 1)
        if audio and len(injected) >= 2:
            injected.insert(mid, audio)
            injections += 1

        # 촉각: 마지막 부분
        tactile = seed.tactile or (
            _DEFAULT_ANCHORS["tactile"][hash(scene_id + "t") % len(_DEFAULT_ANCHORS["tactile"])]
            if not seed.tactile else ""
        )
        if tactile and len(injected) >= 3:
            injected.append(tactile)
            injections += 1

        injected_text = " ".join(s for s in injected if s.strip())
        density = injections / max(len(injected), 1)

        return AnchoredSceneIR(
            scene_id=scene_id,
            base_text=base_text,
            anchors=SettingSeed(visual=visual, audio=audio, tactile=tactile),
            injected_text=injected_text,
            density=round(density, 3),
        )

    @staticmethod
    def _split(text: str) -> List[str]:
        """간단한 한국어 문장 분리 (마침표·느낌표·물음표 기준)."""
        parts = []
        for s in __import__("re").split(r"(?<=[.!?])\s+", text):
            s = s.strip()
            if s:
                parts.append(s)
        return parts or [text]
