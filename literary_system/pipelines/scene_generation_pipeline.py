"""
literary_system/pipelines/scene_generation_pipeline.py
V484 — SceneGenerationPipeline

EpisodeStructureCalculator → KoreanCadencePlanner → UnifiedLLMGateway
를 연결하여 1개 에피소드의 씬 텍스트 배열을 생성하는 오케스트레이터.

흐름:
  1. EpisodeStructureCalculator.calculate() → EpisodeStructure (타임라인)
  2. KoreanCadencePlanner.plan_episode()    → List[CadencePlan] (문체 파라미터)
  3. 씬별 프롬프트 조립 (PromptAssembler)
  4. UnifiedLLMGateway.call_text()          → 씬 텍스트
  5. SceneGenerationResult 반환

LLM-0 원칙: 라우팅·구조 계산은 LLM-free. 오직 step 4만 LLM 호출.
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from literary_system.episode.episode_structure_calculator import (
    EpisodeStructureCalculator, EpisodeStructureConfig,
    EpisodeStructure, SceneSlot,
)
from literary_system.prose.korean_cadence_planner import (
    KoreanCadencePlanner, CadencePlan,
)
from literary_system.llm_bridge.llm_context import LLMContext

logger = logging.getLogger(__name__)


# ── 결과 모델 ─────────────────────────────────────────────────────

@dataclass
class GeneratedScene:
    """생성된 씬 1개의 결과."""
    scene_idx: int
    slot: SceneSlot
    cadence: CadencePlan
    prompt: str
    text: str                           # LLM이 생성한 씬 텍스트
    provider_id: str = ""
    latency_ms: float = 0.0
    error: str = ""

    @property
    def success(self) -> bool:
        return bool(self.text) and not self.error

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    def to_dict(self) -> dict:
        return {
            "scene_idx": self.scene_idx,
            "role": self.slot.role.value,
            "act_position": self.slot.act_position.value,
            "slot_function": self.slot.slot_function,
            "start_min": round(self.slot.start_min, 2),
            "end_min": round(self.slot.end_min, 2),
            "cadence_pattern": self.cadence.cadence_pattern.value,
            "word_count": self.word_count,
            "provider_id": self.provider_id,
            "latency_ms": round(self.latency_ms, 1),
            "success": self.success,
            "error": self.error,
        }


@dataclass
class SceneGenerationResult:
    """에피소드 전체 씬 생성 결과."""
    episode_idx: int
    structure: EpisodeStructure
    scenes: List[GeneratedScene] = field(default_factory=list)
    total_elapsed_s: float = 0.0

    @property
    def success_count(self) -> int:
        return sum(1 for s in self.scenes if s.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for s in self.scenes if not s.success)

    @property
    def total_word_count(self) -> int:
        return sum(s.word_count for s in self.scenes if s.success)

    @property
    def avg_latency_ms(self) -> float:
        lats = [s.latency_ms for s in self.scenes if s.success]
        return round(sum(lats) / len(lats), 1) if lats else 0.0

    def to_dict(self) -> dict:
        return {
            "episode_idx": self.episode_idx,
            "total_scene_count": len(self.scenes),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_word_count": self.total_word_count,
            "avg_latency_ms": self.avg_latency_ms,
            "total_elapsed_s": round(self.total_elapsed_s, 2),
            "runtime_min": self.structure.runtime_min,
            "scenes": [s.to_dict() for s in self.scenes],
        }

    def full_text(self) -> str:
        """모든 씬 텍스트를 순서대로 합친 전체 스크립트."""
        parts = []
        for s in self.scenes:
            if s.success:
                header = (
                    f"\n\n{'='*60}\n"
                    f"[씬 {s.scene_idx:03d}] {s.slot.role.value.upper()} "
                    f"| {s.slot.slot_function} "
                    f"| {s.slot.start_min:.1f}~{s.slot.end_min:.1f}분\n"
                    f"{'='*60}\n"
                )
                parts.append(header + s.text)
        return "\n".join(parts)


# ── 프롬프트 조립기 ────────────────────────────────────────────────

class ScenePromptAssembler:
    """
    SceneSlot + CadencePlan → LLM 프롬프트 문자열.

    한국 드라마 씬 작성 지시를 구조화된 프롬프트로 변환.
    """

    def assemble(
        self,
        slot: SceneSlot,
        cadence: CadencePlan,
        episode_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        ctx = episode_context or {}
        series_title = ctx.get("series_title", "무제 드라마")
        ep_idx = ctx.get("episode_idx", 0)
        characters = ctx.get("characters", ["주인공A", "주인공B"])
        char_list = ", ".join(characters)

        # 리듬 지시
        cadence_desc = self._cadence_description(cadence)

        prompt = f"""[드라마 씬 작성 지시]

시리즈: {series_title}
화수: {ep_idx + 1}화
씬 번호: {slot.scene_idx:03d}
씬 역할: {slot.role.value} ({slot.slot_function})
막 위치: {slot.act_position.value}
타임코드: {slot.start_min:.1f}분 ~ {slot.end_min:.1f}분 ({slot.duration_min:.1f}분)
등장인물: {char_list}

[서사 파라미터]
- 감정 강도: {slot.emotional_target:.2f} (0=냉담, 1=극도 감정)
- 갈등 강도: {slot.conflict_weight:.2f} (0=평온, 1=극한 갈등)
- reveal 예산: {slot.reveal_budget:.3f} (이번 씬에서 공개 가능한 정보량)
- 핵심 씬 여부: {"예 (클라이맥스/반전)" if slot.is_critical else "아니오"}

[문체 리듬 지시]
{cadence_desc}

[작성 요령]
- 지문(행동 묘사)과 대사를 적절히 배합하세요
- 한국 드라마 특유의 감성과 호흡을 살리세요
- 씬의 시작과 끝을 명확히 구분하세요
- 분량: 약 {int(slot.duration_min * 150)}자 ~ {int(slot.duration_min * 250)}자

[씬 시작]"""
        return prompt

    def _cadence_description(self, cadence: CadencePlan) -> str:
        pattern = cadence.cadence_pattern.value
        density = cadence.dialogue_density.value
        lines = [
            f"- 리듬 패턴: {pattern} (평균 문장 길이: {cadence.avg_sentence_length:.0f}어절)",
            f"- 대사 밀도: {density}",
            f"- 컷 속도 목표: {cadence.cut_speed_target:.0f}컷/분",
        ]
        if cadence.silence_ratio > 0.2:
            lines.append(f"- 침묵/여백 비율 높음 ({cadence.silence_ratio:.0%}) — 내면 묘사 강조")
        if cadence.refrain_probability > 0.2:
            lines.append(f"- 반복구(refrain) 활용 ({cadence.refrain_probability:.0%} 확률)")
        if cadence.exclamation_weight > 0.3:
            lines.append("- 감탄사·감정 표현 적극 활용")
        if cadence.internal_monologue_weight > 0.3:
            lines.append("- 내레이션·독백 비중 높게")
        return "\n".join(lines)


# ── 메인 파이프라인 ────────────────────────────────────────────────

class SceneGenerationPipeline:
    """
    V484 — 씬 생성 통합 파이프라인.

    gateway가 None이면 빈 텍스트("") 반환 (구조 테스트용).
    """

    def __init__(
        self,
        gateway=None,                          # UnifiedLLMGateway (Optional)
        structure_config: Optional[EpisodeStructureConfig] = None,
        max_scenes: Optional[int] = None,      # 생성할 최대 씬 수 (None=전체)
        skip_roles: Optional[List[str]] = None, # 생략할 씬 역할 (예: ["preview"])
    ) -> None:
        self._gateway       = gateway
        self._calc          = EpisodeStructureCalculator()
        self._cadence       = KoreanCadencePlanner()
        self._assembler     = ScenePromptAssembler()
        self._config        = structure_config
        self._max_scenes    = max_scenes
        self._skip_roles    = set(skip_roles or ["preview"])  # 예고편은 기본 생략

    def run(
        self,
        config: Optional[EpisodeStructureConfig] = None,
        episode_context: Optional[Dict[str, Any]] = None,
    ) -> SceneGenerationResult:
        """
        에피소드 구조 계산 → 씬별 LLM 생성 → 결과 반환.

        Args:
            config: EpisodeStructureConfig (None이면 self._config 또는 기본값)
            episode_context: {"series_title": ..., "characters": [...], ...}
        """
        cfg = config or self._config or EpisodeStructureConfig()
        t_start = time.monotonic()

        # Step 1: 구조 계산
        structure = self._calc.calculate(cfg)
        logger.info(
            "EP%02d 구조 계산 완료: %d씬, K=%d, %.1f분",
            cfg.episode_idx, structure.total_scene_count,
            structure.microplot_count, structure.runtime_min,
        )

        # Step 2: 문체 리듬 계획
        cadence_plans = self._cadence.plan_episode(structure)

        # Step 3: 씬별 생성
        ep_ctx = episode_context or {}
        ep_ctx.setdefault("episode_idx", cfg.episode_idx)
        generated: List[GeneratedScene] = []
        scene_count = 0

        for slot, cadence in zip(structure.scenes, cadence_plans):
            # 생략 조건
            if slot.role.value in self._skip_roles:
                continue
            if self._max_scenes is not None and scene_count >= self._max_scenes:
                break

            prompt = self._assembler.assemble(slot, cadence, ep_ctx)
            text, provider_id, latency_ms, error = self._generate(prompt, slot)

            generated.append(GeneratedScene(
                scene_idx=slot.scene_idx,
                slot=slot,
                cadence=cadence,
                prompt=prompt,
                text=text,
                provider_id=provider_id,
                latency_ms=latency_ms,
                error=error,
            ))
            scene_count += 1

        elapsed = time.monotonic() - t_start
        logger.info(
            "EP%02d 생성 완료: %d/%d씬 성공, %.1fs",
            cfg.episode_idx, sum(1 for g in generated if g.success),
            len(generated), elapsed,
        )

        return SceneGenerationResult(
            episode_idx=cfg.episode_idx,
            structure=structure,
            scenes=generated,
            total_elapsed_s=round(elapsed, 2),
        )

    def _generate(
        self, prompt: str, slot: SceneSlot
    ) -> tuple[str, str, float, str]:
        """
        LLM generate 호출. gateway 없으면 빈 텍스트 반환.
        Returns: (text, provider_id, latency_ms, error)
        """
        if self._gateway is None:
            # 구조 테스트용 — 빈 텍스트
            return ("", "none", 0.0, "")

        # narrative_fitness: emotional_target × conflict_weight 가중 평균
        fitness = (slot.emotional_target * 0.6 + slot.conflict_weight * 0.4) * 10.0
        ctx = LLMContext(
            narrative_fitness=fitness,
            extra={"scene_idx": slot.scene_idx, "role": slot.role.value},
        )

        t0 = time.monotonic()
        try:
            resp = self._gateway.call(prompt, ctx)
            latency = (time.monotonic() - t0) * 1000.0
            return (resp.text, resp.provider_id, round(latency, 1), "")
        except Exception as exc:
            latency = (time.monotonic() - t0) * 1000.0
            logger.error("씬 %d 생성 오류: %s", slot.scene_idx, exc)
            return ("", "", round(latency, 1), str(exc))
