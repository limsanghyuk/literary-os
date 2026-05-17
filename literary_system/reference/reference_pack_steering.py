"""
V318: ReferencePackSteering
GPT v1500 reference_conditioned_render + reference_weighted_trajectory 흡수.

핵심 이론 (수석 뉴럴):
  참조 팩(Reference Pack)은 단순한 예시 모음이 아니다.
  "이 씬이 어떤 문체/플롯/모티프 방향으로 가야 하는가"를
  수치 가중치(steering_weights)로 표현한 방향 제어기다.

GPT v1500 핵심 패턴:
  - ReferenceBundle: {style, plot, motif, moodboard} 참조 목록
  - ReferencePack: 참조 목록 → resolved notes + steering_weights + patch_preferences
  - TrajectorySoftPromptTranslator: 궤도 + reader_state + 참조팩 → LLM soft instruction

  즉 참조팩은:
  1. 궤도 계획에 영향을 준다 (steering_weights → trajectory deviation 계산)
  2. 패치 선택에 영향을 준다 (patch_preferences → specialized patch family 선택)
  3. LLM 렌더링에 영향을 준다 (soft instruction)

우리 V313~V317 격차:
  - V313 PromptAssembler: bundle.json 조립 ○
  - V313 StyleDNAEngine: 문체 프로파일 ○
  - V317 TrajectoryFamilyInterpolator: 궤도 패밀리 보간 ○
  - V317 SpecializedLocalPatch: 특화 수술 ○
  - 없는 것: 참조팩이 궤도/패치에 통합되는 로직

V318에서 ReferencePackSteering으로 이 격차를 메운다.
LLM 0회.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


# ── 참조 팩 스키마 ─────────────────────────────────────────
@dataclass
class ReferenceBundle:
    """사용자/설계자가 지정하는 참조 목록."""
    project_id: str
    style_reference_ids: list[str] = field(default_factory=list)
    plot_reference_ids: list[str] = field(default_factory=list)
    motif_reference_ids: list[str] = field(default_factory=list)
    fiction_moodboard_tags: list[str] = field(default_factory=list)
    strictness: float = 0.5   # 참조 준수 강도 [0, 1]


@dataclass
class ResolvedReferenceBundle:
    """참조 목록 → 실제 지시 텍스트."""
    style_notes: list[str] = field(default_factory=list)
    plot_notes: list[str] = field(default_factory=list)
    motif_notes: list[str] = field(default_factory=list)
    moodboard_tags: list[str] = field(default_factory=list)

    def flatten(self) -> list[str]:
        return self.style_notes + self.plot_notes + self.motif_notes


@dataclass
class ReferencePack:
    """
    참조 팩 — ReferenceBundle → 궤도/패치 제어 신호.
    GPT v1500 reference_pack.py 흡수.
    """
    project_id: str
    pack_id: str
    source_bundle: ReferenceBundle
    resolved_bundle: ResolvedReferenceBundle
    # 궤도 제어 가중치: Literary State 축별 push 방향
    steering_weights: dict[str, float] = field(default_factory=dict)
    # 패치 선택 선호도
    patch_preferences: list[str] = field(default_factory=list)
    # 연속화 포커스 지시
    continuation_focus: list[str] = field(default_factory=list)
    # 선호 residue 힌트
    preferred_residue_hint: str | None = None


# ── 참조 DB (GPT의 DummyReferenceRegistry 흡수) ────────────
_STYLE_DB: dict[str, str] = {
    "style_restrained_kdrama_v1": (
        "감정을 직접 해설하지 말고, 행동/침묵/사물로 압력을 전달하라. "
        "대사는 짧고 무겁게. 설명 없는 행동이 우선."
    ),
    "style_korean_noir_v1": (
        "문장은 짧고 건조하게. 정보는 늦게 풀고, 분위기는 도시적이고 냉랭하게. "
        "빗소리, 형광등, 좁은 공간."
    ),
    "style_literary_restraint_v1": (
        "과장된 비유를 피하고, 작은 물리 이미지가 감정을 대신하도록. "
        "한 문단에 핵심 사물 하나."
    ),
    "style_political_cold_v1": (
        "기관의 언어. 간접 위협. 침묵이 권력. 개인 고백 금지."
    ),
}

_PLOT_DB: dict[str, str] = {
    "plot_delayed_reveal_opening_v2": (
        "오프닝 3화 동안 핵심 진실은 완전 개봉하지 말고, 질문만 깊게 남겨라. "
        "cost before truth."
    ),
    "plot_tension_rise_no_explosion_v1": (
        "텐션은 화마다 상승시키되 값싼 폭발로 해소하지 말라. "
        "압력은 구조적 긴장으로."
    ),
    "plot_false_opening_lock_v1": (
        "작은 돌파구를 준 뒤 더 깊은 잠금을 만든다. "
        "거짓 해방 이후 더 좁아진 선택지."
    ),
}

_MOTIF_DB: dict[str, str] = {
    "motif_rusted_locker_v1": (
        "녹슨 철제 보관함 — 묻힌 진실, 열 수 없는 과거. "
        "씬 배경에 배치하되 직접 언급 최소화."
    ),
    "motif_wet_gloves_v1": (
        "젖은 장갑 — 지울 수 없는 행위, 손에 남은 죄책감. "
        "마지막 씬 마무리 이미지로 활용."
    ),
    "motif_broken_clock_v1": (
        "멈춘 시계 — 시간이 멈춘 상처, 반복되는 순간. "
        "대사 없이 카메라가 머물게."
    ),
}

_MOODBOARD_MAP: dict[str, list[str]] = {
    "cold":    ["차가운 조명", "짧은 문장", "침묵의 무게"],
    "urban":   ["도시 소음 배경", "형광등", "좁은 공간"],
    "funeral": ["절제된 애도", "오브제 중심", "침묵"],
    "rain":    ["빗소리 배경", "젖은 질감", "차단된 시야"],
}


class ReferenceRegistry:
    """참조 팩 레지스트리."""

    def resolve(self, bundle: ReferenceBundle) -> ResolvedReferenceBundle:
        style = [_STYLE_DB[sid] for sid in bundle.style_reference_ids if sid in _STYLE_DB]
        plot  = [_PLOT_DB[pid]  for pid in bundle.plot_reference_ids  if pid in _PLOT_DB]
        motif = [_MOTIF_DB[mid] for mid in bundle.motif_reference_ids if mid in _MOTIF_DB]
        mood_hints = []
        for tag in bundle.fiction_moodboard_tags:
            mood_hints.extend(_MOODBOARD_MAP.get(tag, []))
        return ResolvedReferenceBundle(
            style_notes=style,
            plot_notes=plot,
            motif_notes=motif,
            moodboard_tags=mood_hints,
        )


class ReferencePackBuilder:
    """
    ReferenceBundle → ReferencePack.
    steering_weights + patch_preferences 계산.
    GPT v1500 reference_pack_builder.py 흡수.
    """

    def __init__(self):
        self.registry = ReferenceRegistry()

    def build(
        self,
        bundle: ReferenceBundle,
        continuation_packet: dict | None = None,
        project_memory: dict | None = None,
    ) -> ReferencePack:
        import uuid
        resolved = self.registry.resolve(bundle)
        pack_id = f"refpack_{uuid.uuid4().hex[:8]}"

        # ── steering_weights 계산 ──────────────────────────
        steering: dict[str, float] = {}
        patch_prefs: list[str] = []
        continuation_focus: list[str] = []
        preferred_residue: str | None = None

        # 스타일 참조 → Literary State 방향
        for sid in bundle.style_reference_ids:
            if "restrained" in sid or "noir" in sid:
                steering["SP"] = steering.get("SP", 0) + 0.05
                steering["RU"] = steering.get("RU", 0) + 0.03
                patch_prefs.append("pdi_fix")
                patch_prefs.append("dialogue_compression")
            if "political" in sid:
                steering["AC"] = steering.get("AC", 0) + 0.04
                patch_prefs.append("reveal_delay")

        # 플롯 참조 → 궤도/continuation 방향
        for pid in bundle.plot_reference_ids:
            if "delayed_reveal" in pid:
                steering["RU"] = steering.get("RU", 0) + 0.05
                continuation_focus.append("information_gap_widening")
                patch_prefs.append("reveal_delay")
            if "tension_rise" in pid:
                steering["SP"] = steering.get("SP", 0) + 0.04
                continuation_focus.append("pressure_escalation")
            if "false_opening" in pid:
                continuation_focus.append("relock_after_opening")

        # 모티프 참조 → residue 힌트
        for mid in bundle.motif_reference_ids:
            if "rusted_locker" in mid:
                preferred_residue = "rusted_locker"
                patch_prefs.append("residue_boost")
            elif "wet_gloves" in mid:
                preferred_residue = "wet_gloves"
                patch_prefs.append("residue_boost")

        # continuation_packet에서 추가 컨텍스트
        if continuation_packet:
            open_tensions = continuation_packet.get("open_tensions", [])
            if open_tensions:
                continuation_focus.extend(open_tensions[:2])
            active_residues = continuation_packet.get("active_residues", [])
            for r in active_residues[:2]:
                obj = r.get("object_name", r) if isinstance(r, dict) else str(r)
                continuation_focus.append(f"carry_residue:{obj}")

        # 중복 제거
        patch_prefs = list(dict.fromkeys(patch_prefs))
        continuation_focus = list(dict.fromkeys(continuation_focus))

        # strictness에 따라 steering 가중치 조정
        for k in steering:
            steering[k] = round(steering[k] * bundle.strictness, 4)

        return ReferencePack(
            project_id=bundle.project_id,
            pack_id=pack_id,
            source_bundle=bundle,
            resolved_bundle=resolved,
            steering_weights=steering,
            patch_preferences=patch_prefs,
            continuation_focus=continuation_focus,
            preferred_residue_hint=preferred_residue,
        )


class TrajectorySoftPromptTranslator:
    """
    궤도 패킷 + reader_state + 참조팩 → LLM soft instruction.
    GPT v1500 trajectory_soft_prompt_translator.py 흡수.
    """

    def translate(
        self,
        trajectory_state: dict[str, float],   # Literary State
        target_signal: dict[str, float],        # 목표 신호
        reader_state: dict[str, float],         # 독자 상태
        reference_pack: ReferencePack,
        episode_no: int,
        patch_contract: str | None = None,      # specialized patch soft_instruction
    ) -> str:
        """
        모든 제어 신호를 하나의 LLM soft instruction으로 통합.
        V312 bundle.json의 render_instruction 필드에 추가.
        """
        lines: list[str] = []

        # ① 궤도 제어
        sp_target = target_signal.get("SP", trajectory_state.get("SP", 0.5))
        ru_target = target_signal.get("RU", trajectory_state.get("RU", 0.5))
        lines.append(
            f"[TRAJECTORY] EP{episode_no:02d} — "
            f"압력 목표 SP={sp_target:.2f}, 불확실성 목표 RU={ru_target:.2f}."
        )

        # ② 독자 상태 제어
        pull = reader_state.get("reader_pull", 0.5)
        afterimage = reader_state.get("reader_afterimage", 0.5)
        if pull < 0.4:
            lines.append("[READER] 독자 당김 부족 — 정보 비대칭을 강화하라. 마지막 문장 개방적으로.")
        if afterimage < 0.35:
            lines.append("[READER] afterimage 부족 — 마지막 씬에 구체 오브제를 남겨라.")

        # ③ 참조 팩 지시
        resolved = reference_pack.resolved_bundle
        if resolved.style_notes:
            lines.append(f"[STYLE] {resolved.style_notes[0][:100]}")
        if resolved.plot_notes:
            lines.append(f"[PLOT] {resolved.plot_notes[0][:100]}")
        if resolved.motif_notes:
            lines.append(f"[MOTIF] {resolved.motif_notes[0][:80]}")
        if resolved.moodboard_tags:
            lines.append(f"[MOOD] {' / '.join(resolved.moodboard_tags[:3])}")

        # ④ 연속화 포커스
        if reference_pack.continuation_focus:
            focus_str = " | ".join(reference_pack.continuation_focus[:2])
            lines.append(f"[FOCUS] {focus_str}")

        # ⑤ 패치 지시 (있으면)
        if patch_contract:
            lines.append(f"[PATCH_OVERRIDE] {patch_contract[:120]}")

        # ⑥ residue 힌트
        if reference_pack.preferred_residue_hint:
            lines.append(
                f"[RESIDUE] '{reference_pack.preferred_residue_hint}' 잔향을 씬에 배치하라."
            )

        return "\n".join(lines)
