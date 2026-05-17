from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

_KOREAN_STOPWORDS = {
    "그리고", "그러나", "하지만", "그래서", "정말", "그냥", "아주", "너무", "조금", "다시", "오늘", "내일",
    "우리", "나는", "너는", "그는", "그녀는", "이건", "저건", "있다", "없다", "한다", "했다", "한다는",
    "비가", "오는", "장면", "집으로", "돌아온", "아무", "말", "scene", "bundle", "project", "canon",
    "notes", "seed", "the", "and", "but", "for", "with", "still", "already", "there", "that",
}
_KNOWN_CHARACTER_WORDS = {"주인공", "형", "누나", "동생", "어머니", "엄마", "아버지", "아빠", "친구", "선배", "후배", "형사", "의사"}
_KNOWN_MOTIF_HINTS = {"부고장", "젖은", "수건", "침묵", "정적", "비", "복도", "문", "식탁", "우산", "장례식장"}
_EMOTION_LEXICON = {
    "불안": (0.10, 0.20, 0.05), "두려움": (0.15, 0.20, 0.05), "분노": (0.24, 0.18, 0.10),
    "죄책감": (0.18, 0.14, 0.08), "회피": (0.12, 0.15, -0.02), "비밀": (0.10, 0.17, -0.01),
    "침묵": (0.05, 0.08, -0.04), "정적": (0.05, 0.08, -0.06), "눈물": (0.08, 0.05, -0.08),
    "사과": (-0.04, 0.05, 0.10), "위로": (-0.08, -0.03, 0.15), "화해": (-0.10, -0.04, 0.20),
    "betrayal": (0.24, 0.20, 0.06), "guilt": (0.18, 0.16, 0.04), "silence": (0.05, 0.08, -0.03),
    "comfort": (-0.06, -0.03, 0.12), "fear": (0.12, 0.18, 0.04), "anger": (0.22, 0.17, 0.10),
}
_TENSION_HINTS = {
    "죄책감", "회피", "분노", "침묵", "비밀", "부채", "상실", "위로", "화해",
    "guilt", "avoidance", "anger", "silence", "secret", "debt", "loss", "comfort", "reconciliation",
}
_PARTICLE_SUFFIXES = ("은", "는", "이", "가", "을", "를", "와", "과", "도", "로", "으로", "만", "께", "에", "에서")


@dataclass
class SceneFeatures:
    source_refs: list[dict[str, str]]
    raw_text: str
    tokens: list[str]
    speakers: list[str]
    mentioned_characters: list[str]
    motifs: list[str]
    tension_axes: list[str]
    emotional_delta: tuple[float, float, float]
    quoted_turns: int


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_name(name: str) -> str:
    name = name.strip()
    for suffix in _PARTICLE_SUFFIXES:
        if name.endswith(suffix) and len(name) >= 3:
            return name[: -len(suffix)]
    return name


def split_into_candidate_scenes(text: str) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    chunks = re.split(r"\n\s*\n+|(?=SCENE\s+\d+)|(?=INT\.)|(?=EXT\.)|(?=장면\s*\d+)", text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def extract_speakers(text: str) -> list[str]:
    speakers: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^([A-Z][A-Z0-9_ ]{1,30}|[가-힣A-Za-z]{1,20})\s*[:：]", line)
        if m:
            speaker = normalize_name(m.group(1).strip())
            speakers.append(speaker)
    return list(dict.fromkeys(speakers))


def tokenize_keywords(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-']{2,}|[가-힣]{2,}", text)
    cleaned = []
    for word in words:
        token = normalize_name(word)
        if token.lower() in _KOREAN_STOPWORDS or token in _KOREAN_STOPWORDS:
            continue
        cleaned.append(token)
    return cleaned


def infer_motifs(texts: Iterable[str], explicit_candidates: Iterable[str] | None = None, top_k: int = 6) -> list[str]:
    counter: Counter[str] = Counter()
    if explicit_candidates:
        counter.update([normalize_name(c.strip()) for c in explicit_candidates if c and c.strip()])
    for text in texts:
        counter.update(tokenize_keywords(text))
    scored = []
    for token, count in counter.items():
        if token in _KNOWN_CHARACTER_WORDS:
            continue
        score = count
        if token in _KNOWN_MOTIF_HINTS:
            score += 2
        if token in _TENSION_HINTS:
            score += 2
        if len(token) <= 1:
            continue
        if score >= 2:
            scored.append((token, score, count))
    scored.sort(key=lambda item: (-item[1], -item[2], len(item[0]), item[0]))
    return [token for token, _, _ in scored[:top_k]]


def infer_tension_axes(text: str, explicit_axes: Iterable[str] | None = None) -> list[str]:
    axes: list[str] = []
    if explicit_axes:
        axes.extend([normalize_name(a) for a in explicit_axes if a])
    lower = text.lower()
    for hint in _TENSION_HINTS:
        if hint in text or hint in lower:
            axes.append(hint)
    return list(dict.fromkeys(axes))[:4]


def emotional_signature(text: str) -> tuple[float, float, float]:
    sp = ru = et = 0.0
    lower = text.lower()
    for key, (d_sp, d_ru, d_et) in _EMOTION_LEXICON.items():
        if key in text or key in lower:
            sp += d_sp
            ru += d_ru
            et += d_et
    punctuation_force = min(0.12, text.count("!") * 0.02 + text.count("?") * 0.02)
    sp += punctuation_force
    ru += min(0.10, text.count("...") * 0.03 + text.count("?") * 0.02)
    quoted = len(re.findall(r'".*?"|“.*?”|‘.*?’', text))
    et += min(0.08, quoted * 0.01)
    return round(sp, 3), round(ru, 3), round(max(-1.0, min(1.0, et)), 3)


def find_character_mentions(text: str, character_names: Iterable[str]) -> list[str]:
    mentions = []
    lower = text.lower()
    normalized_text = normalize_text(text)
    for name in character_names:
        if not name:
            continue
        if name in normalized_text or name.lower() in lower:
            mentions.append(name)
    return list(dict.fromkeys(mentions))


def scene_features_from_text(
    source_refs: list[dict[str, str]],
    text: str,
    character_names: Iterable[str],
    explicit_motifs: Iterable[str] | None = None,
    explicit_axes: Iterable[str] | None = None,
) -> SceneFeatures:
    normalized = normalize_text(text)
    speakers = extract_speakers(normalized)
    mentions = find_character_mentions(normalized, character_names)
    motifs = infer_motifs([normalized], explicit_candidates=explicit_motifs)
    axes = infer_tension_axes(normalized, explicit_axes=explicit_axes)
    quoted_turns = len(re.findall(r"[:：]", normalized))
    return SceneFeatures(
        source_refs=source_refs,
        raw_text=normalized,
        tokens=tokenize_keywords(normalized),
        speakers=speakers,
        mentioned_characters=mentions,
        motifs=motifs,
        tension_axes=axes,
        emotional_delta=emotional_signature(normalized),
        quoted_turns=quoted_turns,
    )
