"""
CharacterBirthGate — 캐릭터 탄생 시점 판정

[갭 1 수정] Literary State (SP/RU/ET/RD) 연동 추가.
  - SP (Scene Pressure): 장면 압력이 높을 때 강한 캐릭터 등장이 효과적
  - RU (Reveal Budget Used): 정보 공개 소진율 — 너무 이른 등장 방지
  - ET (Emotional Tension): 감정 긴장도 — 감정 피크에 등장하면 기억됨

literary_state를 받지 않으면 기존 로직(서사 구조 기반)으로 동작 (하위 호환).
literary_state를 받으면 추가 Literary State 압력 판정 수행.
"""
from __future__ import annotations

from typing import Any


CORE_GATE_KEYS = (
    "act_necessity",
    "pressure_target_defined",
    "unique_residue_defined",
    "structure_collapse_if_removed",
)

# Literary State 임계값
LS_SP_MIN   = 0.45   # SP 이 이상이어야 주요 캐릭터 탄생 허용
LS_RU_MAX   = 0.75   # RU 이 이하여야 (너무 늦은 등장 방지)
LS_ET_BOOST = 0.60   # ET 이 이상이면 탄생 압력 점수 +1


def evaluate_character_birth(
    characters: list[dict[str, Any]],
    literary_state: dict[str, float] | None = None,  # [갭 1 수정] Literary State 연동
) -> list[dict[str, Any]]:
    """
    캐릭터 탄생 시점 판정.

    Args:
        characters: 캐릭터 속성 리스트
        literary_state: V312 Literary State {"SP": 0.62, "RU": 0.68, "ET": 0.02, "RD": 0.45}
                        None이면 기존 서사 구조 기반 판정만 수행 (하위 호환)
    """
    results = []

    # Literary State 추출
    sp = literary_state.get("SP", 0.5) if literary_state else 0.5
    ru = literary_state.get("RU", 0.5) if literary_state else 0.5
    et = literary_state.get("ET", 0.0) if literary_state else 0.0

    for char in characters:
        residue_binding = char.get("residue_binding", {})
        residue_defined = any(bool(items) for items in residue_binding.values())
        memory_weight   = float(char.get("memory_weight", 0.0))
        role_type       = char.get("role_type", "")
        pressure_target = char.get("pressure_target", "")

        # ── 기존 서사 구조 판정 ─────────────────────────────────
        questions = {
            "act_necessity":                bool(role_type and pressure_target),
            "pressure_target_defined":      bool(pressure_target and pressure_target != "story_pressure"),
            "unique_residue_defined":       residue_defined,
            "structure_collapse_if_removed":bool(
                role_type in {"pressure", "mirror", "structure"}
                or memory_weight >= 0.68
            ),
            "act_variation_possible":       bool(char.get("act_evolution")),
            "rememberable_after_two_scenes":memory_weight >= 0.55 or residue_defined,
        }

        # ── [갭 1 수정] Literary State 압력 판정 ────────────────
        ls_questions: dict[str, Any] = {}
        if literary_state:
            ls_questions["ls_sp_sufficient"]  = sp >= LS_SP_MIN    # 장면 압력 충분
            ls_questions["ls_ru_not_late"]     = ru <= LS_RU_MAX    # 공개 소진율 과잉 아님
            ls_questions["ls_et_peak_timing"]  = et >= LS_ET_BOOST  # 감정 피크 타이밍
            ls_questions["ls_connected"]       = True               # Literary State 연동 확인용

        # ── 최종 판정 ────────────────────────────────────────────
        core_pass    = all(questions[k] for k in CORE_GATE_KEYS)
        full_pass    = core_pass and questions["act_variation_possible"] and questions["rememberable_after_two_scenes"]
        ls_favorable = (
            ls_questions.get("ls_sp_sufficient", True)
            and ls_questions.get("ls_ru_not_late", True)
        ) if literary_state else True

        if full_pass and ls_favorable:
            decision = "pass"
        elif core_pass and ls_favorable:
            decision = "provisional"
        elif core_pass and not ls_favorable:
            decision = "deferred"   # [갭 1] LS 조건 미달 — 탄생 시점 연기 권장
        else:
            decision = "fail"

        results.append({
            "character_id":      char["character_id"],
            "questions":         {**questions, **ls_questions},
            "decision":          decision,
            "prunable_candidate":decision not in ("pass", "provisional"),
            "notes":             char.get("notes", ""),
            "literary_state_applied": literary_state is not None,  # 연동 여부 명시
        })

    return results
