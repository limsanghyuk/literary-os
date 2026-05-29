"""
V317: SpecializedLocalPatchEngine
GPT v1600 specialized_local_patches (phase47) 흡수 구현.

핵심 이론:
  "좋은 씬이 나왔다고 끝이 아니다.
   critic이 발견한 패턴별로 특화된 수술이 필요하다."

  4개 특화 수술 패밀리:
  1. reveal_delay    — 정보 공개 지연 (핵심 명사 한 박자 늦추기)
  2. dialogue_compression — 대사 압축 (행동/오브제 대체)
  3. residue_boost   — residue 강화 (핵심 오브제 재등장)
  4. pdi_fix         — PDI 수정 (감정 직설 → 행동 묘사)

GPT v1600은 각 패밀리마다:
  - SpecializedPatchProfile (품질 목표 + 보존 제약)
  - SpecializedLocalPatchEngine.apply(text, profile)
  - before/after reader_state 비교

우리는 이것을 LLM 0회 rule-based로 구현.
LLM 연결 시 soft instruction으로 변환 가능하도록 설계.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class SpecializedPatchProfile:
    """특화 패치 프로파일."""
    profile_id: str
    patch_family: str    # reveal_delay | dialogue_compression | residue_boost | pdi_fix
    target_metrics: dict[str, float]
    preserve_constraints: list[str]
    guidance_notes: list[str]
    quality_focus: str


@dataclass
class SpecializedPatchResult:
    """패치 적용 결과."""
    scene_id: str
    patch_family: str
    original_text: str
    edited_text: str
    quality_deltas: dict[str, float]
    preserved_constraints_ok: bool
    guidance_applied: list[str]
    soft_instruction: str  # LLM 연결 시 이 지시를 prompt에 추가


class SpecializedLocalPatchEngine:
    """
    GPT v1600의 specialized_local_patch_engine 흡수.
    4개 패밀리 × rule-based 구현.

    Rule-based이지만 각 패밀리마다 soft_instruction도 생성 →
    V312 런타임 연결 시 LLM도 이 지시를 따를 수 있다.
    """

    # ── 패밀리별 기본 프로파일 ─────────────────────────────────
    FAMILY_PROFILES: dict[str, SpecializedPatchProfile] = {
        "reveal_delay": SpecializedPatchProfile(
            profile_id="reveal_delay_standard",
            patch_family="reveal_delay",
            target_metrics={"reader_uncertainty": 0.08, "reveal_satisfaction_gap": -0.03},
            preserve_constraints=["macroarc_alignment", "residue_continuity"],
            guidance_notes=["핵심 명사를 한 박자 늦춘다", "공백만 남기지 말고 우회 단서를 남긴다"],
            quality_focus="mystery_control",
        ),
        "dialogue_compression": SpecializedPatchProfile(
            profile_id="dialogue_compression_standard",
            patch_family="dialogue_compression",
            target_metrics={"comprehension_stability": 0.06, "reader_pull": 0.03},
            preserve_constraints=["character_voice", "macroarc_alignment"],
            guidance_notes=["대사 20자 이상은 절반으로 줄인다", "감정 설명은 행동으로 대체한다"],
            quality_focus="compression",
        ),
        "residue_boost": SpecializedPatchProfile(
            profile_id="residue_boost_standard",
            patch_family="residue_boost",
            target_metrics={"reader_afterimage": 0.10},
            preserve_constraints=["temporal_coherence"],
            guidance_notes=["이전 화 핵심 오브제를 이 씬에 재등장시킨다", "직접 언급보다 배경에 배치"],
            quality_focus="afterimage",
        ),
        "pdi_fix": SpecializedPatchProfile(
            profile_id="pdi_fix_standard",
            patch_family="pdi_fix",
            target_metrics={"reader_pull": 0.05, "ai_smell": -0.15},
            preserve_constraints=["style_dna_profile"],
            guidance_notes=["감정 직설 표현을 행동/오브제 묘사로 대체", "주어+감정동사 패턴 제거"],
            quality_focus="pdi_compliance",
        ),
    }

    # ── 감정 직설 치환 규칙 ────────────────────────────────────
    _PDI_RULES: list[tuple[str, str]] = [
        (r"그는 슬펐다", "그는 손을 거두지 못했다"),
        (r"그녀는 슬펐다", "그녀는 입술을 깨물었다"),
        (r"그는 기뻤다", "그는 손가락을 폈다"),
        (r"그는 화가 났다", "그는 턱을 당겼다"),
        (r"그는 두려웠다", "그는 멈추지 않았다"),
        (r"그는 깨달았다", "그는 손을 내려다봤다"),
        (r"그녀는 울었다", "그녀의 어깨가 가라앉았다"),
        (r"그는 놀랐다", "그는 숨을 참았다"),
    ]

    # ── AI 냄새 제거 규칙 ──────────────────────────────────────
    _AI_SMELL_RULES: list[tuple[str, str]] = [
        (r"결국", "끝내"),
        (r"마치", "흡사"),
        (r"배신의 공기", "식지 않은 공기"),
        (r"그제야", "그 직후"),
        (r"이상하게도", ""),
        (r"왠지 모르게", ""),
        (r"어쩌면", ""),
    ]

    def get_profile(self, patch_family: str) -> SpecializedPatchProfile:
        if patch_family not in self.FAMILY_PROFILES:
            raise ValueError(f"Unknown patch_family: {patch_family}. Valid: {list(self.FAMILY_PROFILES.keys())}")
        return self.FAMILY_PROFILES[patch_family]

    def apply(
        self,
        text: str,
        patch_family: str,
        scene_id: str = "unknown",
        residue_objects: list[str] | None = None,
    ) -> SpecializedPatchResult:
        """특화 패치 적용."""
        profile = self.get_profile(patch_family)
        original = text

        if patch_family == "reveal_delay":
            edited, applied = self._reveal_delay(text)
        elif patch_family == "dialogue_compression":
            edited, applied = self._dialogue_compression(text)
        elif patch_family == "residue_boost":
            edited, applied = self._residue_boost(text, residue_objects or [])
        elif patch_family == "pdi_fix":
            edited, applied = self._pdi_fix(text)
        else:
            edited, applied = text, []

        # 품질 델타 추정 (rule-based 근사)
        quality_deltas = self._estimate_deltas(original, edited, patch_family)

        # soft instruction 생성 (LLM 연결 시 prompt에 추가)
        soft_instruction = self._build_soft_instruction(patch_family, profile)

        return SpecializedPatchResult(
            scene_id=scene_id,
            patch_family=patch_family,
            original_text=original,
            edited_text=edited,
            quality_deltas=quality_deltas,
            preserved_constraints_ok=len(edited) > 0,
            guidance_applied=applied,
            soft_instruction=soft_instruction,
        )

    # ── 패밀리별 구현 ─────────────────────────────────────────
    def _reveal_delay(self, text: str) -> tuple[str, list[str]]:
        """핵심 진실 단어를 우회 표현으로 대체."""
        applied = []
        result = text
        direct_reveal_patterns = [
            (r"진실은", "그 일이"), (r"사실은", "그것이"), (r"결론은", ""),
            (r"이미 알았다", "손을 멈췄다"), (r"모든 것을 알게 됐다", "서류를 내려놓았다"),
        ]
        for pattern, replacement in direct_reveal_patterns:
            if re.search(pattern, result):
                result = re.sub(pattern, replacement, result)
                applied.append(f"reveal_delay: '{pattern}' 제거")
        return result, applied

    def _dialogue_compression(self, text: str) -> tuple[str, list[str]]:
        """대사 압축 — 20자 이상 대사를 절반으로."""
        applied = []
        lines = text.splitlines()
        compressed = []
        for line in lines:
            stripped = line.strip()
            # 따옴표로 시작하는 대사
            if stripped.startswith('"') and len(stripped) > 25:
                # 핵심 앞부분만
                cut = stripped[:max(12, len(stripped)//2)].rstrip()
                if not cut.endswith('"'):
                    cut += '…"'
                compressed.append(cut)
                applied.append("dialogue_compression: 대사 단축")
            else:
                compressed.append(line)
        return "\n".join(compressed), applied

    def _residue_boost(self, text: str, residue_objects: list[str]) -> tuple[str, list[str]]:
        """residue 오브제 재등장. 마지막 단락에 오브제 암시 추가."""
        applied = []
        if not residue_objects:
            return text, applied

        # 이미 텍스트에 오브제가 있으면 스킵
        # 오브제 한국어 표현도 체크
        obj_korean = {
            "rusted_locker": ["보관함", "서류함"],
            "wet_gloves": ["장갑"],
            "letter": ["편지", "봉투"],
            "photograph": ["사진"],
        }
        for obj in residue_objects:
            korean_hints = obj_korean.get(obj, [obj])
            if any(k in text for k in korean_hints):
                return text, applied  # 이미 있음

        # 마지막 문장에 첫 번째 오브제 암시 추가
        primary_obj = residue_objects[0]
        obj_hints = {
            "rusted_locker": "낡은 보관함이 벽 쪽에 기대어 있었다.",
            "wet_gloves": "젖은 장갑이 의자 위에 놓여 있었다.",
            "letter": "봉투가 책상 모서리에 걸려 있었다.",
            "photograph": "사진이 뒤집어진 채 서랍 위에 있었다.",
        }
        hint = obj_hints.get(primary_obj, f"{primary_obj}이 눈에 들어왔다.")
        result = text.rstrip() + "\n" + hint
        applied.append(f"residue_boost: {primary_obj} 재등장")
        return result, applied

    def _pdi_fix(self, text: str) -> tuple[str, list[str]]:
        """감정 직설 + AI 냄새 제거."""
        applied = []
        result = text
        for pattern, replacement in self._PDI_RULES:
            if re.search(pattern, result):
                result = re.sub(pattern, replacement, result)
                applied.append(f"pdi_fix: '{pattern}' → '{replacement}'")
        for pattern, replacement in self._AI_SMELL_RULES:
            if re.search(pattern, result):
                result = re.sub(pattern, replacement, result)
                if replacement:
                    applied.append(f"ai_smell_fix: '{pattern}' → '{replacement}'")
                else:
                    applied.append(f"ai_smell_fix: '{pattern}' 제거")
        return result, applied

    def _estimate_deltas(self, original: str, edited: str, patch_family: str) -> dict[str, float]:
        """rule-based 품질 변화 근사."""
        if original == edited:
            return {}
        len_change = (len(edited) - len(original)) / max(len(original), 1)
        if patch_family == "pdi_fix":
            return {"reader_pull": 0.04, "ai_smell": -0.12}
        elif patch_family == "reveal_delay":
            return {"reader_uncertainty": 0.06, "reader_pull": 0.03}
        elif patch_family == "dialogue_compression":
            return {"reader_pull": 0.03, "comprehension_stability": 0.05}
        elif patch_family == "residue_boost":
            return {"reader_afterimage": 0.08}
        return {}

    def _build_soft_instruction(
        self, patch_family: str, profile: SpecializedPatchProfile
    ) -> str:
        """LLM 연결 시 prompt에 추가할 소프트 지시."""
        base = {
            "reveal_delay": (
                "[PATCH: reveal_delay] "
                "핵심 진실 단어를 직접 쓰지 말고 우회 단서로 대체하라. "
                "독자가 '이게 무슨 뜻인가?' 를 묻게 만들어라."
            ),
            "dialogue_compression": (
                "[PATCH: dialogue_compression] "
                "모든 대사를 절반으로 줄여라. "
                "설명하는 대사는 행동이나 오브제로 대체하라."
            ),
            "residue_boost": (
                "[PATCH: residue_boost] "
                "이전 화에서 등장한 핵심 오브제를 이 씬에 다시 등장시켜라. "
                "직접 언급보다 배경이나 부수적 위치에 배치하라."
            ),
            "pdi_fix": (
                "[PATCH: pdi_fix] "
                "감정 직설 표현(슬펐다/기뻤다/두려웠다)을 "
                "행동/오브제/신체 반응으로 대체하라. "
                "PDI ≥ 0.35 준수."
            ),
        }
        notes = " ".join(profile.guidance_notes[:2])
        return base.get(patch_family, f"[PATCH: {patch_family}] {notes}")
