"""
literary_system/prose/korean_cadence_planner.py
V483 — KoreanCadencePlanner

한국 드라마 특유의 문체 리듬(韻律, cadence)을 씬 슬롯에 적용.

한국 드라마 문체 관례:
  - 클라이맥스 씬: 짧은 호흡, 고밀도 대사, 감탄사 빈도 ↑
  - 여백 씬: 긴 호흡, 침묵/내레이션 활용
  - 감정 잔상 씬: 반복구(refrain) 패턴, 느린 컷
  - 반전 씬: 단문 → 침묵 → 긴 문장 순서

LLM-0 원칙: LLM 호출 없음. 파라미터 계산 전용.

인터페이스:
  KoreanCadencePlanner.plan(slot) → CadencePlan
  KoreanCadencePlanner.plan_episode(structure) → List[CadencePlan]
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ── 리듬 타입 ────────────────────────────────────────────────────

class CadencePattern(str, Enum):
    STACCATO    = "staccato"      # 짧은 호흡 (클라이맥스)
    LEGATO      = "legato"        # 긴 호흡 (여백/감성)
    REFRAIN     = "refrain"       # 반복구 (감정 잔상)
    SILENCE     = "silence"       # 침묵/여백 강조
    ACCELERANDO = "accelerando"   # 점점 빠르게 (긴장 고조)
    FERMATA     = "fermata"       # 잠시 멈춤 (반전 전)
    STANDARD    = "standard"      # 기본 리듬


class DialogueDensity(str, Enum):
    SPARSE  = "sparse"    # 대사 적음 (행동·시각 중심)
    MEDIUM  = "medium"    # 중간
    DENSE   = "dense"     # 대사 많음 (심리·감정)
    RAPID   = "rapid"     # 빠른 응수 (갈등·논쟁)


# ── 출력 ─────────────────────────────────────────────────────────

@dataclass
class CadencePlan:
    """씬 1개의 문체 리듬 계획."""
    scene_idx: int
    cadence_pattern: CadencePattern
    dialogue_density: DialogueDensity

    # 수치 파라미터 (문체 생성기에 주입)
    avg_sentence_length: float          # 평균 문장 길이 (어절 수, 목표)
    silence_ratio: float                # 침묵/여백 비율 (0~1)
    refrain_probability: float          # 반복구 발생 확률 (0~1)
    exclamation_weight: float           # 감탄사 가중치 (0~1)
    internal_monologue_weight: float    # 내레이션/독백 비율 (0~1)
    cut_speed_target: float             # 컷 속도 (cuts/min, 목표)

    # 메타
    role: str = ""
    act_position: str = ""
    is_critical: bool = False
    rationale: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "scene_idx": self.scene_idx,
            "cadence_pattern": self.cadence_pattern.value,
            "dialogue_density": self.dialogue_density.value,
            "avg_sentence_length": round(self.avg_sentence_length, 1),
            "silence_ratio": round(self.silence_ratio, 3),
            "refrain_probability": round(self.refrain_probability, 3),
            "exclamation_weight": round(self.exclamation_weight, 3),
            "internal_monologue_weight": round(self.internal_monologue_weight, 3),
            "cut_speed_target": round(self.cut_speed_target, 1),
            "role": self.role,
            "act_position": self.act_position,
            "is_critical": self.is_critical,
        }


# ── 플래너 ────────────────────────────────────────────────────────

class KoreanCadencePlanner:
    """
    V483 — 한국 드라마 문체 리듬 플래너.

    씬의 role/act_position/emotional_target/conflict_weight로부터
    CadencePlan(리듬 파라미터 묶음)을 결정론적으로 계산.

    사용:
        planner = KoreanCadencePlanner()
        plans = planner.plan_episode(episode_structure)
    """

    # 역할별 기본 파라미터 (한국 드라마 관례 기반)
    _ROLE_DEFAULTS: Dict[str, dict] = {
        "cold_open": dict(
            cadence=CadencePattern.STACCATO,
            density=DialogueDensity.SPARSE,
            avg_sent=8.0, silence=0.10, refrain=0.0,
            excl=0.3, mono=0.1, cut=8.0,
        ),
        "setup": dict(
            cadence=CadencePattern.LEGATO,
            density=DialogueDensity.MEDIUM,
            avg_sent=14.0, silence=0.20, refrain=0.0,
            excl=0.1, mono=0.2, cut=4.0,
        ),
        "rising": dict(
            cadence=CadencePattern.ACCELERANDO,
            density=DialogueDensity.MEDIUM,
            avg_sent=11.0, silence=0.10, refrain=0.1,
            excl=0.2, mono=0.15, cut=5.5,
        ),
        "climax": dict(
            cadence=CadencePattern.STACCATO,
            density=DialogueDensity.RAPID,
            avg_sent=6.0, silence=0.05, refrain=0.0,
            excl=0.5, mono=0.1, cut=10.0,
        ),
        "resolution": dict(
            cadence=CadencePattern.FERMATA,
            density=DialogueDensity.MEDIUM,
            avg_sent=12.0, silence=0.25, refrain=0.15,
            excl=0.15, mono=0.3, cut=4.5,
        ),
        "denouement": dict(
            cadence=CadencePattern.REFRAIN,
            density=DialogueDensity.SPARSE,
            avg_sent=16.0, silence=0.35, refrain=0.4,
            excl=0.05, mono=0.45, cut=3.0,
        ),
        "preview": dict(
            cadence=CadencePattern.STACCATO,
            density=DialogueDensity.SPARSE,
            avg_sent=5.0, silence=0.0, refrain=0.0,
            excl=0.2, mono=0.0, cut=12.0,
        ),
    }

    def plan(self, slot) -> CadencePlan:
        """
        SceneSlot 1개 → CadencePlan.

        slot 필수 속성: scene_idx, role, act_position,
                        emotional_target, conflict_weight, is_critical
        """
        role_str = slot.role.value if hasattr(slot.role, "value") else str(slot.role)
        act_str = (
            slot.act_position.value
            if hasattr(slot.act_position, "value")
            else str(slot.act_position)
        )

        defaults = self._ROLE_DEFAULTS.get(role_str, self._ROLE_DEFAULTS["setup"])
        rationale = [f"role={role_str}", f"act={act_str}"]

        # 기본값 복사
        cadence   = defaults["cadence"]
        density   = defaults["density"]
        avg_sent  = defaults["avg_sent"]
        silence   = defaults["silence"]
        refrain   = defaults["refrain"]
        excl      = defaults["excl"]
        mono      = defaults["mono"]
        cut       = defaults["cut"]

        # 감정 타겟 보정 (emotional_target 0.8+ → refrain 강화)
        et = getattr(slot, "emotional_target", 0.5)
        if et >= 0.8:
            refrain = min(1.0, refrain + 0.15)
            mono    = min(1.0, mono + 0.10)
            rationale.append("high_emotion: refrain+mono↑")

        # 갈등 강도 보정 (conflict_weight 0.7+ → staccato 강화)
        cw = getattr(slot, "conflict_weight", 0.5)
        if cw >= 0.7:
            avg_sent = max(5.0, avg_sent - 3.0)
            excl     = min(1.0, excl + 0.15)
            cut      = min(15.0, cut + 2.0)
            cadence  = CadencePattern.STACCATO
            rationale.append("high_conflict: staccato↑")

        # 클라이맥스 씬 보정
        if getattr(slot, "is_critical", False):
            silence = max(0.0, silence - 0.05)
            density = DialogueDensity.RAPID
            cut     = min(15.0, cut + 1.5)
            rationale.append("critical_scene: rapid+cut↑")

        # REVERSAL 특수 처리: Fermata → 침묵 강화
        if act_str == "REVERSAL":
            silence = min(1.0, silence + 0.10)
            cadence = CadencePattern.FERMATA
            rationale.append("reversal: fermata+silence↑")

        return CadencePlan(
            scene_idx=slot.scene_idx,
            cadence_pattern=cadence,
            dialogue_density=density,
            avg_sentence_length=round(avg_sent, 1),
            silence_ratio=round(min(1.0, max(0.0, silence)), 3),
            refrain_probability=round(min(1.0, max(0.0, refrain)), 3),
            exclamation_weight=round(min(1.0, max(0.0, excl)), 3),
            internal_monologue_weight=round(min(1.0, max(0.0, mono)), 3),
            cut_speed_target=round(max(1.0, min(20.0, cut)), 1),
            role=role_str,
            act_position=act_str,
            is_critical=getattr(slot, "is_critical", False),
            rationale=rationale,
        )

    def plan_episode(self, episode_structure) -> List[CadencePlan]:
        """EpisodeStructure의 모든 씬 → CadencePlan 목록."""
        return [self.plan(slot) for slot in episode_structure.scenes]

    def cadence_summary(self, plans: List[CadencePlan]) -> dict:
        """CadencePlan 목록 통계 요약."""
        if not plans:
            return {}
        pattern_counts: Dict[str, int] = {}
        density_counts: Dict[str, int] = {}
        for p in plans:
            pattern_counts[p.cadence_pattern.value] = pattern_counts.get(p.cadence_pattern.value, 0) + 1
            density_counts[p.dialogue_density.value] = density_counts.get(p.dialogue_density.value, 0) + 1

        avg_cut = sum(p.cut_speed_target for p in plans) / len(plans)
        avg_sent = sum(p.avg_sentence_length for p in plans) / len(plans)
        return {
            "total_scenes": len(plans),
            "cadence_distribution": pattern_counts,
            "density_distribution": density_counts,
            "avg_cut_speed": round(avg_cut, 1),
            "avg_sentence_length": round(avg_sent, 1),
        }
