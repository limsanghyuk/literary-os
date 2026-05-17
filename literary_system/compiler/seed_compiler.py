"""
V313→V322: SeedCompiler
사용자의 자연어 한 줄 입력을 SeedContract로 번역.
복합 장르 지원 + 키워드 스코어링.
LLM 0회 — 로컬 deterministic.
"""
from __future__ import annotations
import re, uuid
from typing import Any

_GENRE_SIGNALS: dict[str, list[str]] = {
    "political_thriller": ["정치", "선거", "국정", "권력", "부패", "로비"],
    "noir_crime":         ["형사", "수사", "살인", "범죄", "느와르", "조직"],
    "revenge_drama":      ["복수", "설욕", "되갚", "원한"],
    "family_melodrama":   ["가족", "부모", "형제", "유산", "이혼"],
    "romance_drama":      ["로맨스", "사랑", "연애", "멜로"],
    "thriller_suspense":  ["스릴러", "납치", "공포", "추격", "위협"],
    "historical_drama":   ["사극", "조선", "시대", "왕"],
    "medical_drama":      ["병원", "의사", "수술", "응급"],
    "legal_drama":        ["변호사", "법정", "재판", "검사"],
    "corporate_drama":    ["회사", "직장", "대기업", "CEO", "스타트업"],
}
_FORMAT_SIGNALS: dict[str, list[str]] = {
    "screenplay": ["드라마", "시나리오", "대본"],
    "novel":      ["소설", "장편", "단편"],
    "documentary":["다큐", "실화"],
}
_TONE_SIGNALS: list[tuple[str, list[str]]] = [
    ("restrained",  ["절제", "차가운", "냉정", "건조", "담담"]),
    ("pressure",    ["긴장", "압박", "숨막", "조여"]),
    ("melancholic", ["우울", "슬픈", "비극", "상실"]),
    ("warm",        ["따뜻", "훈훈", "감동"]),
    ("ironic",      ["아이러니", "역설", "블랙코미디"]),
]
_PDI_MAP: dict[str, float] = {
    "political_thriller": 0.32,
    "noir_crime": 0.30,
    "family_melodrama": 0.40,
    "romance_drama": 0.45,
}
_FORBIDDEN_DEFAULT = [
    "cheap_cliffhanger", "emotion_explanation",
    "generic_ai_phrase", "summary_ending",
]


class SeedCompiler:
    """한 줄 사용자 입력 → SeedContract dict."""

    def compile(self, user_prompt: str) -> dict[str, Any]:
        pid = f"proj_{uuid.uuid4().hex[:8]}"

        # 장르 스코어링 (복합 지원)
        scored = []
        for genre, kws in _GENRE_SIGNALS.items():
            s = sum(1 for kw in kws if kw in user_prompt)
            if s > 0:
                scored.append((genre, s))
        scored.sort(key=lambda x: -x[1])
        primary   = scored[0][0] if scored else "general_drama"
        secondary = scored[1][0] if len(scored) > 1 else None

        # 포맷
        fmt = "screenplay"
        for f, kws in _FORMAT_SIGNALS.items():
            if any(kw in user_prompt for kw in kws):
                fmt = f; break

        # 톤
        tones = [t for t, kws in _TONE_SIGNALS if any(kw in user_prompt for kw in kws)]
        if not tones:
            tones = ["restrained", "pressure-driven"]

        # 에피소드 수
        ep = re.search(r"(\d+)\s*화", user_prompt)
        span = f"ep01_ep{ep.group(1).zfill(2)}_opening" if ep else "ep01_ep03_opening"

        # 오브제 키워드 추출
        obj_pat = r"[가-힣]{2,6}(?:함|서류|장갑|편지|영수증|사진|메모|열쇠|반지|시계|수첩)"
        objects = re.findall(obj_pat, user_prompt)[:3]

        return {
            "project_id":       pid,
            "user_prompt":      user_prompt,
            "genre":            primary,
            "genre_secondary":  secondary,
            "format_type":      fmt,
            "target_span":      span,
            "tone_keywords":    tones,
            "pdi_baseline":     _PDI_MAP.get(primary, 0.35),
            "forbidden_rules":  _FORBIDDEN_DEFAULT.copy(),
            "required_objects": objects,
            "core_conflict":    "to_be_inferred",
            "seed_confidence":  min(0.95, 0.55 + len(scored) * 0.10),
        }
