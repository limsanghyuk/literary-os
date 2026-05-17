"""
V322 V1650 Node2 Extensions
V1650의 Node2 생성 핵심 모듈들을 V320 구조에 맞게 흡수.

포함 모듈:
  EmotionToBehaviorTransformer  — 감정 직접 표현 → 행동/오브제
  AntiClicheSubstitutionEngine  — 클리셰 제거
  SubtextDialoguePlanner        — 대사 서브텍스트
  ForbiddenRevealScanner        — 금지 공개 탐지 (Node3용)
  Node2AuthorityGuard           — 권한 침범 차단

LLM 0회. 완전 로컬 판정.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ══════════════════════════════════════════════════════════════════
# EmotionToBehaviorTransformer (V1650 흡수)
# ══════════════════════════════════════════════════════════════════

# PDI 위반 패턴 — 직접 감정 표현
DIRECT_EMOTION_PATTERNS = [
    r"(그는|그녀는|나는).{0,10}(슬펐다|슬펐|슬퍼했다)",
    r"(그는|그녀는|나는).{0,10}(화가 났다|분노했다|화를 냈다)",
    r"(그는|그녀는|나는).{0,10}(두려웠다|겁이 났다|무서웠다)",
    r"마치 .{0,20}처럼",
    r"이상하게도",
    r"왠지 모르게",
    r"묘한 감정",
    r"감정이 복잡",
    r"운명(의|적|처럼)",
    r"갑자기 모든 것이",
    r"드디어 진실을 깨달았다",
    r"너무나도 (고통|슬|기쁘)",
]

BEHAVIOR_SUGGESTIONS = {
    "슬펐다": "그는 말을 삼켰다. / 입술이 굳었다.",
    "화가 났다": "그는 서류를 내려놓았다. / 창문 쪽으로 걸어갔다.",
    "두려웠다": "손이 멈췄다. / 걸음을 늦췄다.",
    "마치": "[오브제나 행동으로 대체하세요]",
    "이상하게도": "[구체적 관찰로 대체하세요]",
}


@dataclass
class TransformResult:
    original_text: str
    violations: list[str]
    suggestions: list[str]
    pdi_score: float        # [0, 1] 1 = PDI 완전 준수
    needs_rewrite: bool


class EmotionToBehaviorTransformer:
    """
    PDI (Prose Directness Index) 위반 탐지 + 행동화 제안.
    V1650 emotion_to_behavior_transformer.py 로직 흡수.
    """

    def __init__(self, violation_threshold: float = 0.05):
        self.threshold = violation_threshold

    def analyze(self, text: str) -> TransformResult:
        words = text.split()
        total = max(len(words), 1)
        violations: list[str] = []
        suggestions: list[str] = []

        for pattern in DIRECT_EMOTION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                violations.append(f"패턴 감지: '{pattern}'")
                for key, sug in BEHAVIOR_SUGGESTIONS.items():
                    if key in pattern:
                        suggestions.append(f"→ 대안: {sug}")

        violation_ratio = len(violations) / total
        pdi_score = max(0.0, 1.0 - violation_ratio * 10)
        needs_rewrite = pdi_score < (1.0 - self.threshold)

        return TransformResult(
            original_text=text,
            violations=violations,
            suggestions=suggestions,
            pdi_score=round(pdi_score, 4),
            needs_rewrite=needs_rewrite,
        )

    def check_pdi(self, text: str) -> bool:
        """PDI 준수 여부 (True = 통과)."""
        return not self.analyze(text).needs_rewrite


# ══════════════════════════════════════════════════════════════════
# AntiClicheSubstitutionEngine (V1650 흡수)
# ══════════════════════════════════════════════════════════════════

CLICHE_PATTERNS = {
    "마음이 무거웠다": "어깨가 내려앉았다",
    "가슴이 두근거렸다": "손이 잡고 싶어졌다",
    "눈물이 차올랐다": "[차오름 대신 눈을 감는 행동]",
    "비수처럼 꽂혔다": "[비수 클리셰 — 오브제로 대체]",
    "운명의 순간": "[운명 선언 금지 — 행동으로]",
    "갑자기": "[갑자기 금지 — 구체적 트리거로]",
    "드디어": "[드디어 금지 — 장면 흐름으로]",
    "어색한 침묵": "[어색한 금지 — 침묵의 내용으로]",
    "뭔가 달랐다": "[달랐다 금지 — 구체적 차이로]",
}


@dataclass
class ClicheReport:
    found: list[tuple[str, str]]   # (원본, 대안)
    clean_ratio: float              # 1.0 = 클리셰 없음
    needs_attention: bool


class AntiClicheSubstitutionEngine:
    """클리셰 탐지 + 대안 제안. V1650 anti_cliche 로직 흡수."""

    def analyze(self, text: str) -> ClicheReport:
        found = []
        for cliche, alt in CLICHE_PATTERNS.items():
            if cliche in text:
                found.append((cliche, alt))
        ratio = max(0.0, 1.0 - len(found) * 0.15)
        return ClicheReport(found=found, clean_ratio=round(ratio, 4),
                            needs_attention=len(found) > 0)


# ══════════════════════════════════════════════════════════════════
# SubtextDialoguePlanner (V1650 흡수)
# ══════════════════════════════════════════════════════════════════

@dataclass
class SubtextPlan:
    explicit_line: str          # 표면 대사
    subtext_layer: str          # 숨겨진 의미
    suggested_rewrite: str      # 서브텍스트 반영 대안


class SubtextDialoguePlanner:
    """대사 서브텍스트 플래닝. V1650 subtext_dialogue_planner 흡수."""

    TENSION_MARKERS = ["괜찮아", "별거 아니야", "나 괜찮아", "신경 쓰지 마"]

    def plan(self, dialogue: str, tension_context: str = "") -> SubtextPlan:
        subtext = "표면 대사와 다른 감정 내포"
        rewrite = dialogue

        for marker in self.TENSION_MARKERS:
            if marker in dialogue:
                subtext = f"'{marker}' = 실제로는 괜찮지 않음을 암시"
                rewrite = dialogue + " [행동으로 보완: 눈을 마주치지 않음]"
                break

        return SubtextPlan(
            explicit_line=dialogue,
            subtext_layer=subtext,
            suggested_rewrite=rewrite,
        )


# ══════════════════════════════════════════════════════════════════
# ForbiddenRevealScanner (V1650 흡수 — Node3용)
# ══════════════════════════════════════════════════════════════════

@dataclass
class RevealScanReport:
    candidate_text: str
    direct_hits: list[str]          # 직접 금지어 발견
    implicit_risks: list[str]       # 암시적 위험
    severity: str                   # "high" / "medium" / "none"
    rationale: list[str]
    passed: bool                    # severity == "none"

    def to_dict(self) -> dict[str, Any]:
        return {
            "direct_hits": self.direct_hits,
            "implicit_risks": self.implicit_risks,
            "severity": self.severity,
            "rationale": self.rationale,
            "passed": self.passed,
        }


class ForbiddenRevealScanner:
    """
    금지 공개 탐지 — Node3 사후 검증용.
    V1650 forbidden_reveal_scanner 흡수 + DRSE KnowledgeBoundaryGate 이중 방어선.

    DRSE(사전) → Node2 렌더링 → ForbiddenRevealScanner(사후)
    """

    def scan(
        self,
        candidate_text: str,
        forbidden_reveals: list[str],
        possible_implicit_risks: list[str] | None = None,
    ) -> RevealScanReport:
        direct = [r for r in forbidden_reveals if r and r in candidate_text]
        implicit = list(possible_implicit_risks or [])

        if direct:
            severity = "high"
            rationale = ["direct_forbidden_reveal_hit"]
        elif implicit:
            severity = "medium"
            rationale = ["implicit_reveal_risk"]
        else:
            severity = "none"
            rationale = ["no_forbidden_reveal_detected"]

        return RevealScanReport(
            candidate_text=candidate_text[:200],
            direct_hits=direct,
            implicit_risks=implicit,
            severity=severity,
            rationale=rationale,
            passed=(severity == "none"),
        )


# ══════════════════════════════════════════════════════════════════
# Node2AuthorityGuard (V1650 흡수 — AuthorityRiskPenalty 기반)
# ══════════════════════════════════════════════════════════════════

AUTHORITY_VIOLATION_PATTERNS = [
    r"사실은 .{0,20}이었다",    # 새로운 사실 선언 (Node1 권한)
    r"(알고 보니|알고보니)",     # 반전 공개 (Node1 권한)
    r"세계관 법칙에 의하면",     # WORLD_RULE 직접 언급
    r"(진짜|실제로는) .{0,15}이다",
]


@dataclass
class AuthorityGuardReport:
    violations: list[str]
    authority_safe: bool


class Node2AuthorityGuard:
    """
    Node2(문학 렌더링)가 Node1(이야기 권한) 침범하지 않는지 검사.
    V1650 node2_authority_guard 흡수.
    """

    def check(self, rendered_text: str) -> AuthorityGuardReport:
        violations = []
        for pattern in AUTHORITY_VIOLATION_PATTERNS:
            if re.search(pattern, rendered_text, re.IGNORECASE):
                violations.append(f"권한 침범 패턴: '{pattern}'")
        return AuthorityGuardReport(
            violations=violations,
            authority_safe=len(violations) == 0,
        )
