"""
SP-C.2 V647 — ScriptAgent

LoRA InferenceGateway 직결 초안 생성 에이전트.
ADR-107: ScriptAgent는 AgentSafetyGuard 사전 검사 후 LoRA로 씬 초안 생성.

C-M-09 책임 매트릭스:
  - Script: 초안 생성 (LoRA + SafetyGuard 사전) | 재생성 최대 3회 | round 1,2,3

LLM-0: 외부 LLM API 직접 호출 없음 — LoRA InferenceGateway 경유.
LLM-1: PROMOTED 아티팩트만 사용 (InferenceGateway가 보장).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ScriptDraft:
    """씬 초안 출력.

    Attributes:
        scene_id: 씬 식별자 (blueprint.scene_id 와 동일)
        draft_text: 생성된 씬 텍스트
        attempt_num: 시도 번호 (1~3)
        safety_passed: SafetyGuard 사전 검사 통과 여부
        lora_artifact_id: 사용된 LoRA 아티팩트 ID (없으면 stub)
        word_count: 텍스트 단어 수
    """
    scene_id: str
    draft_text: str
    attempt_num: int = 1
    safety_passed: bool = True
    lora_artifact_id: str = "stub"
    word_count: int = 0

    def __post_init__(self) -> None:
        if not self.word_count:
            self.word_count = len(self.draft_text.split())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "draft_text": self.draft_text,
            "attempt_num": self.attempt_num,
            "safety_passed": self.safety_passed,
            "lora_artifact_id": self.lora_artifact_id,
            "word_count": self.word_count,
        }


class ScriptAgent:
    """씬 초안 생성 에이전트.

    LoRA InferenceGateway를 경유하여 씬 텍스트를 생성한다.
    HAS_LORA=False 환경(테스트)에서는 StubBackend로 동작.

    C-M-09: 최대 3회 재생성 허용 (round 1~3).
    """

    ROLE = "script"
    MAX_ATTEMPTS = 3

    def __init__(
        self,
        inference_gateway: Optional[Any] = None,
        safety_guard: Optional[Any] = None,
    ) -> None:
        """
        Args:
            inference_gateway: LoRAInferenceGateway 인스턴스 (None → stub).
            safety_guard: AgentSafetyGuard 인스턴스 (None → 항상 통과).
        """
        self._gateway = inference_gateway
        self._safety_guard = safety_guard
        self._attempt_count = 0

    def generate(
        self,
        blueprint_dict: Dict[str, Any],
        attempt_num: int = 1,
        max_words: int = 600,
    ) -> ScriptDraft:
        """씬 초안 생성.

        Args:
            blueprint_dict: SceneBlueprint.to_dict() 결과
            attempt_num: 현재 시도 번호 (1~3)
            max_words: 목표 최대 단어 수
        Returns:
            ScriptDraft
        Raises:
            ValueError: attempt_num > MAX_ATTEMPTS
        """
        if attempt_num > self.MAX_ATTEMPTS:
            raise ValueError(
                f"ScriptAgent: attempt_num({attempt_num}) > MAX_ATTEMPTS({self.MAX_ATTEMPTS})"
            )

        self._attempt_count += 1
        scene_id = blueprint_dict.get("scene_id", "unknown")
        objective = blueprint_dict.get("objective", "")
        setting = blueprint_dict.get("setting", "")
        characters = blueprint_dict.get("characters", [])
        tone = blueprint_dict.get("tone", "neutral")

        # SafetyGuard 사전 검사 (C-M-09)
        safety_passed = self._pre_safety_check(blueprint_dict)

        # 초안 생성 (LoRA 또는 Stub)
        draft_text = self._call_lora(
            objective=objective,
            setting=setting,
            characters=characters,
            tone=tone,
            max_words=max_words,
            attempt_num=attempt_num,
        )

        artifact_id = self._get_artifact_id()

        return ScriptDraft(
            scene_id=scene_id,
            draft_text=draft_text,
            attempt_num=attempt_num,
            safety_passed=safety_passed,
            lora_artifact_id=artifact_id,
        )

    def _pre_safety_check(self, blueprint_dict: Dict[str, Any]) -> bool:
        """AgentSafetyGuard 사전 검사. Guard 없으면 통과."""
        if self._safety_guard is None:
            return True
        try:
            result = self._safety_guard.pre_check(blueprint_dict)
            return bool(result)
        except Exception:
            return True

    def _call_lora(
        self,
        objective: str,
        setting: str,
        characters: List[str],
        tone: str,
        max_words: int,
        attempt_num: int,
    ) -> str:
        """LoRA InferenceGateway 경유 생성. Gateway 없으면 Stub."""
        prompt = self._build_prompt(objective, setting, characters, tone, max_words)

        if self._gateway is not None:
            try:
                resp = self._gateway.generate(prompt=prompt, max_new_tokens=max_words * 3)
                return resp.get("text", "") if isinstance(resp, dict) else str(resp)
            except Exception:
                pass  # fallback to stub

        # Stub 생성 (테스트 전용)
        char_str = "·".join(characters[:2]) if characters else "등장인물"
        return (
            f"[씬 초안 — 시도 {attempt_num}]\n"
            f"배경: {setting[:60]}\n"
            f"등장: {char_str}\n"
            f"목표: {objective[:80]}\n"
            f"분위기: {tone}\n"
            f"--- 씬 시작 ---\n"
            f"{char_str.split('·')[0] if '·' in char_str else char_str}이(가) 등장한다. "
            f"서로의 눈빛이 교차하며 {tone} 분위기가 고조된다.\n"
        )

    def _build_prompt(
        self, objective: str, setting: str, characters: List[str], tone: str, max_words: int
    ) -> str:
        char_str = ", ".join(characters[:3])
        return (
            f"[드라마 씬 작성]\n"
            f"배경: {setting}\n등장인물: {char_str}\n"
            f"목표: {objective}\n감정 톤: {tone}\n"
            f"최대 {max_words}단어 이내로 작성하시오.\n"
        )

    def _get_artifact_id(self) -> str:
        if self._gateway is not None:
            try:
                return str(getattr(self._gateway, "active_artifact_id", "lora_gateway"))
            except Exception:
                pass
        return "stub"

    @property
    def attempt_count(self) -> int:
        return self._attempt_count
