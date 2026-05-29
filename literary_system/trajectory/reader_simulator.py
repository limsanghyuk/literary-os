"""
V314: ReaderSimulator
독자 반응 3지표 — 로컬 deterministic 구현.

3개 지표:
  1. reader_uncertainty  — 독자의 혼란/불확실성 (RU)
  2. reader_pull         — 독자를 당기는 힘 (정보 비대칭)
  3. reader_afterimage   — 씬 종료 후 남는 구체 이미지

⚠️ 중요: 이것은 "독자 반응 추정치"이지 실제 독자 반응이 아님.
   정확도 한계를 명시하고 "근사 지표"로 사용.

LLM 0회.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# ── 언어적 신호 사전 ────────────────────────────────────────

# 독자 불확실성을 높이는 신호 (RU ↑)
_TENSION_SIGNALS = [
    "왜", "어째서", "무슨", "혹시", "설마", "정말",
    "뭔가", "이상한", "낯선", "모르는", "의심",
    "침묵", "멈추", "굳", "굳어", "얼어",
    "?", "···", "…"
]

# 감정 직설 누수 신호 (reader_pull ↓)
_EMOTION_LEAK_SIGNALS = [
    "슬펐다", "기뻤다", "두려웠다", "화가 났다", "느꼈다",
    "깨달았다", "알았다", "이해했다", "당황했다", "놀랐다",
    "그는 슬", "그녀는 슬", "너무 슬", "너무 기", "너무 두"
]

# 정보 비대칭 신호 (reader_pull ↑)
_INFORMATION_GAP_SIGNALS = [
    "아직", "그전에", "나중에", "언젠가", "비밀",
    "숨긴", "감춘", "말하지 않", "모른 척",
    "사실은", "실은", "진짜는"
]

# 구체 이미지 신호 (afterimage ↑)
_CONCRETE_IMAGE_SIGNALS = [
    # 물리적 사물
    "서류", "편지", "사진", "열쇠", "반지", "유리",
    "창문", "불빛", "그림자", "손", "눈", "입술",
    # 감각
    "차가운", "뜨거운", "젖은", "건조한", "무거운", "가벼운",
    "빛", "어둠", "소리", "냄새", "먼지",
    # 날씨/자연
    "비", "눈", "바람", "안개", "햇살",
]

# AI 문체 냄새 신호 (품질 저하 지표)
_AI_SMELL_SIGNALS = [
    "결국", "마치", "그제야", "이상하게도", "어쩌면",
    "왠지 모르게", "묘한", "한편으로는", "동시에",
    "그리하여", "이렇게 하여", "이처럼"
]


@dataclass
class ReaderStateEstimate:
    """독자 반응 3지표 추정값."""
    reader_uncertainty: float   # [0, 1] — 높을수록 독자가 더 모름 (좋은 것)
    reader_pull: float          # [0, 1] — 높을수록 독자가 더 당겨짐
    reader_afterimage: float    # [0, 1] — 높을수록 씬 후 이미지 잔류
    ai_smell_score: float       # [0, 1] — 높을수록 AI 냄새 강함 (나쁜 것)
    confidence: float           # 이 추정치의 신뢰도
    signals_found: dict[str, list[str]]  # 감지된 신호 목록

    @property
    def composite_quality(self) -> float:
        """복합 품질 점수 [0, 1]. 높을수록 좋음."""
        return round(
            (self.reader_pull * 0.35
             + self.reader_afterimage * 0.30
             + self.reader_uncertainty * 0.20
             - self.ai_smell_score * 0.15),
            4
        )

    def as_loss_components(self) -> dict[str, float]:
        """V312 loss_function_calculator와 호환되는 형식."""
        return {
            "L_reader_pull":       round(max(0.0, 1.0 - self.reader_pull), 4),
            "L_reader_afterimage": round(max(0.0, 1.0 - self.reader_afterimage), 4),
            "L_smell_surface":     round(self.ai_smell_score, 4),
        }


class ReaderSimulator:
    """
    텍스트에서 독자 반응 3지표를 로컬 추정.
    ⚠️ 근사치. 실제 독자 반응과 다를 수 있음.
    """

    def estimate(
        self,
        text: str,
        literary_state_before: dict[str, float] | None = None,
        reveal_budget_remaining: float = 1.0,
    ) -> ReaderStateEstimate:
        """텍스트 → 독자 반응 3지표 추정."""
        if not text or not text.strip():
            return ReaderStateEstimate(
                reader_uncertainty=0.3, reader_pull=0.3, reader_afterimage=0.2,
                ai_smell_score=0.0, confidence=0.1, signals_found={}
            )

        sentences = self._split_sentences(text)
        words = text.split()
        total_words = max(len(words), 1)

        # ── 1. reader_uncertainty (독자 혼란/불확실성) ──────
        tension_found = [s for s in _TENSION_SIGNALS if s in text]
        tension_density = min(len(tension_found) / 10.0, 1.0)

        # Literary State의 RU를 베이스로
        base_ru = (literary_state_before or {}).get("RU", 0.50)
        reader_uncertainty = round(
            base_ru * 0.5 + tension_density * 0.3 + (1.0 - reveal_budget_remaining) * 0.2,
            4
        )

        # ── 2. reader_pull (독자 당김) ──────────────────────
        # 정보 비대칭 신호
        gap_found = [s for s in _INFORMATION_GAP_SIGNALS if s in text]
        gap_score = min(len(gap_found) / 5.0, 1.0)

        # 감정 직설 누수 (당김 감소)
        leak_found = [s for s in _EMOTION_LEAK_SIGNALS if s in text]
        leak_penalty = min(len(leak_found) / 3.0, 0.40)

        # 미해결 끝맺음 (마지막 문장)
        last_sentence = sentences[-1].strip() if sentences else ""
        open_ending = 1.0 if (
            last_sentence.endswith("···") or
            last_sentence.endswith("…") or
            last_sentence.endswith("?") or
            len(last_sentence) < 20
        ) else 0.0

        reader_pull = round(
            max(0.0, gap_score * 0.40 + open_ending * 0.30 + tension_density * 0.20 - leak_penalty),
            4
        )

        # ── 3. reader_afterimage (씬 종료 후 이미지) ────────
        # 마지막 2문장의 구체 이미지 밀도
        last_two = " ".join(sentences[-2:]) if len(sentences) >= 2 else text[-200:]
        image_found = [s for s in _CONCRETE_IMAGE_SIGNALS if s in last_two]
        image_density = min(len(image_found) / 6.0, 1.0)

        # 짧고 구체적인 마지막 문장
        short_concrete = (
            len(last_sentence) < 30 and
            any(s in last_sentence for s in _CONCRETE_IMAGE_SIGNALS)
        )

        reader_afterimage = round(
            image_density * 0.60 + (0.30 if short_concrete else 0.0) + tension_density * 0.10,
            4
        )

        # ── 4. ai_smell_score (AI 문체 냄새) ────────────────
        smell_found = [s for s in _AI_SMELL_SIGNALS if s in text]
        ai_smell_score = round(min(len(smell_found) / 4.0, 1.0), 4)

        # ── 신뢰도 계산 ──────────────────────────────────────
        # 텍스트가 길수록, literary_state가 있을수록 신뢰도 높음
        confidence = round(min(0.75, 0.30 + total_words / 500.0 +
                                (0.15 if literary_state_before else 0.0)), 4)

        return ReaderStateEstimate(
            reader_uncertainty=min(1.0, reader_uncertainty),
            reader_pull=min(1.0, reader_pull),
            reader_afterimage=min(1.0, reader_afterimage),
            ai_smell_score=ai_smell_score,
            confidence=confidence,
            signals_found={
                "tension": tension_found,
                "information_gap": gap_found,
                "emotion_leak": leak_found,
                "concrete_image": image_found,
                "ai_smell": smell_found,
            }
        )

    def estimate_batch(
        self,
        scenes: dict[str, str],
        literary_state_before: dict[str, float] | None = None,
    ) -> dict[str, ReaderStateEstimate]:
        """여러 씬 동시 추정."""
        return {
            scene_id: self.estimate(text, literary_state_before)
            for scene_id, text in scenes.items()
        }

    def should_repair(
        self,
        estimate: ReaderStateEstimate,
        threshold_pull: float = 0.35,
        threshold_afterimage: float = 0.30,
    ) -> tuple[bool, list[str]]:
        """수리 필요 여부 + 이유 반환."""
        reasons = []
        if estimate.reader_pull < threshold_pull:
            reasons.append(f"reader_pull={estimate.reader_pull:.2f} < {threshold_pull}")
        if estimate.reader_afterimage < threshold_afterimage:
            reasons.append(f"reader_afterimage={estimate.reader_afterimage:.2f} < {threshold_afterimage}")
        if estimate.ai_smell_score > 0.40:
            reasons.append(f"ai_smell={estimate.ai_smell_score:.2f} > 0.40")
        return len(reasons) > 0, reasons

    def _split_sentences(self, text: str) -> list[str]:
        return [s.strip() for s in re.split(r"[.!?。···…\n]", text) if s.strip()]
