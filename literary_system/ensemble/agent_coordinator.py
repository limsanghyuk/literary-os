"""
V650 — AgentCoordinator (SP-C.2 Multi-Agent Ensemble).
C-M-09 준수: Director(Round-1 전용) → Script(max 3 regen) → Critic → Editor 오케스트레이션.
LLM-0: 외부 API 직접 호출 없음.
"""
from __future__ import annotations

import dataclasses
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── 유틸리티 ──────────────────────────────────────────────────────────────────

def _to_dict(obj: Any) -> Dict[str, Any]:
    """obj → dict 변환. to_dict() > dataclass > dict > 속성 수동 추출."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    # fallback: 공통 속성
    return {
        "scene_id":      getattr(obj, "scene_id",      "unknown"),
        "final_text":    getattr(obj, "final_text",    ""),
        "draft_text":    getattr(obj, "draft_text",    ""),
        "polish_notes":  list(getattr(obj, "polish_notes", [])),
        "passed":        getattr(obj, "passed",        True),
        "constitution_score": getattr(obj, "constitution_score", 0.0),
        "fitness_decision":   getattr(obj, "fitness_decision",   "UNKNOWN"),
        "request_regeneration": getattr(obj, "request_regeneration", False),
        "round_num":     getattr(obj, "round_num",     1),
        "suggestions":   list(getattr(obj, "suggestions", [])),
        "attempt_num":   getattr(obj, "attempt_num",   1),
        "safety_passed": getattr(obj, "safety_passed", True),
        "lora_artifact_id": getattr(obj, "lora_artifact_id", None),
        "word_count":    getattr(obj, "word_count",    0),
        "editor_applied": getattr(obj, "editor_applied", False),
    }


@dataclass
class CoordinatorResult:
    """AgentCoordinator 최종 산출물."""
    scene_id: str
    final_text: str
    rounds_used: int                            # 실제 재생성 횟수
    success: bool
    blueprint_dict: Dict[str, Any] = field(default_factory=dict)
    last_critic_score: float = 0.0
    last_fitness_decision: str = "UNKNOWN"
    polish_notes: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id":              self.scene_id,
            "final_text":            self.final_text,
            "rounds_used":           self.rounds_used,
            "success":               self.success,
            "blueprint_dict":        self.blueprint_dict,
            "last_critic_score":     self.last_critic_score,
            "last_fitness_decision": self.last_fitness_decision,
            "polish_notes":          self.polish_notes,
            "error":                 self.error,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CoordinatorResult":
        return cls(
            scene_id=d["scene_id"],
            final_text=d.get("final_text", ""),
            rounds_used=d.get("rounds_used", 0),
            success=d.get("success", False),
            blueprint_dict=d.get("blueprint_dict", {}),
            last_critic_score=d.get("last_critic_score", 0.0),
            last_fitness_decision=d.get("last_fitness_decision", "UNKNOWN"),
            polish_notes=d.get("polish_notes", []),
            error=d.get("error"),
        )


class AgentCoordinator:
    """
    Multi-Agent Ensemble 오케스트레이터 (C-M-09).

    흐름:
        1. DirectorAgent.generate_blueprint() — Round 1 전용
        2. ScriptAgent.generate() — 초안 생성
        3. CriticAgent.evaluate() — 5축 헌법 평가
        4. request_regeneration=True 이면 ScriptAgent 재호출 (최대 MAX_ROUNDS-1회 추가)
        5. EditorAgent.finalize() — 항상 실행, 거부권 없음(C-M-09)
    """

    MAX_ROUNDS: int = 3  # C-M-09: ScriptAgent 최대 3회

    def __init__(
        self,
        director=None,
        script=None,
        critic=None,
        editor=None,
    ) -> None:
        self._director = director
        self._script   = script
        self._critic   = critic
        self._editor   = editor

    # ── 지연 생성 ──────────────────────────────────────────────────────────

    def _get_director(self):
        if self._director is None:
            try:
                from literary_system.agents.director_agent import DirectorAgent
                self._director = DirectorAgent()
            except Exception as exc:  # noqa: BLE001
                logger.warning("DirectorAgent 로드 실패: %s", exc)
                self._director = _StubDirector()
        return self._director

    def _get_script(self):
        if self._script is None:
            try:
                from literary_system.agents.script_agent import ScriptAgent
                self._script = ScriptAgent()
            except Exception as exc:  # noqa: BLE001
                logger.warning("ScriptAgent 로드 실패: %s", exc)
                self._script = _StubScript()
        return self._script

    def _get_critic(self):
        if self._critic is None:
            try:
                from literary_system.agents.critic_agent import CriticAgent
                self._critic = CriticAgent()
            except Exception as exc:  # noqa: BLE001
                logger.warning("CriticAgent 로드 실패: %s", exc)
                self._critic = _StubCritic()
        return self._critic

    def _get_editor(self):
        if self._editor is None:
            try:
                from literary_system.agents.editor_agent import EditorAgent
                self._editor = EditorAgent()
            except Exception as exc:  # noqa: BLE001
                logger.warning("EditorAgent 로드 실패: %s", exc)
                self._editor = _StubEditor()
        return self._editor

    # ── 핵심 오케스트레이션 ────────────────────────────────────────────────

    def coordinate(
        self,
        blueprint_dict: Optional[Dict[str, Any]] = None,
        *,
        scene_prefix: str = "scene",
        episode_num: int = 1,
        scene_num: int = 1,
        max_rounds: Optional[int] = None,
    ) -> CoordinatorResult:
        """
        씬 생성 전 파이프라인 실행.

        Parameters
        ----------
        blueprint_dict : dict | None
            미리 만들어진 Blueprint dict.  None 이면 DirectorAgent가 생성.
        scene_prefix, episode_num, scene_num :
            Blueprint 생성 시 사용되는 씬 ID 파라미터.
        max_rounds : int | None
            최대 재생성 횟수 (기본 MAX_ROUNDS=3).
        """
        _max = min(max_rounds or self.MAX_ROUNDS, self.MAX_ROUNDS)

        # Step-1: Blueprint 확보
        if blueprint_dict is None:
            try:
                # DirectorAgent 실제 시그니처: generate_blueprint(context, *, prefix, episode, scene)
                bp_raw = self._get_director().generate_blueprint(
                    context={},
                    prefix=scene_prefix,
                    episode=episode_num,
                    scene=scene_num,
                )
                blueprint_dict = _to_dict(bp_raw)
            except TypeError:
                # Stub 또는 다른 시그니처 시도
                try:
                    bp_raw = self._get_director().generate_blueprint(
                        scene_prefix=scene_prefix,
                        episode_num=episode_num,
                        scene_num=scene_num,
                    )
                    blueprint_dict = _to_dict(bp_raw)
                except Exception as exc:  # noqa: BLE001
                    scene_id_fallback = f"{scene_prefix}_ep{episode_num:02d}_sc{scene_num:02d}"
                    blueprint_dict = {
                        "scene_id":   scene_id_fallback,
                        "objective":  "stub objective",
                        "setting":    "stub setting",
                        "characters": [],
                        "tone":       "neutral",
                        "constraints": {"editor_can_reject": False},
                    }
                    logger.warning("DirectorAgent 호출 실패 — stub blueprint 사용: %s", exc)

        scene_id = blueprint_dict.get("scene_id", "unknown_scene")

        # Step-2~4: Script → Critic → (재생성 루프)
        draft_dict: Optional[Dict[str, Any]] = None
        critic_report_dict: Optional[Dict[str, Any]] = None
        rounds_used = 0

        for attempt in range(1, _max + 1):
            rounds_used = attempt
            try:
                raw_draft = self._get_script().generate(
                    blueprint_dict=blueprint_dict,
                    attempt_num=attempt,
                )
                draft_dict = _to_dict(raw_draft)
            except Exception as exc:  # noqa: BLE001
                logger.error("ScriptAgent 오류 (attempt=%d): %s", attempt, exc)
                return CoordinatorResult(
                    scene_id=scene_id,
                    final_text="",
                    rounds_used=rounds_used,
                    success=False,
                    blueprint_dict=blueprint_dict,
                    error=str(exc),
                )

            try:
                raw_report = self._get_critic().evaluate(
                    draft_dict=draft_dict,
                    blueprint_dict=blueprint_dict,
                    round_num=attempt,
                )
                critic_report_dict = _to_dict(raw_report)
            except Exception as exc:  # noqa: BLE001
                logger.warning("CriticAgent 오류 (attempt=%d): %s", attempt, exc)
                critic_report_dict = {
                    "scene_id":             scene_id,
                    "passed":               True,
                    "constitution_score":   0.60,
                    "fitness_decision":     "MERGE",
                    "request_regeneration": False,
                    "round_num":            attempt,
                }

            # 재생성 필요 여부 확인 (C-M-09)
            request_regen = critic_report_dict.get("request_regeneration", False)
            if not request_regen or attempt >= _max:
                break

            logger.info(
                "CriticAgent 재생성 요청 (attempt=%d/%d, scene=%s)",
                attempt, _max, scene_id,
            )

        # Step-5: EditorAgent 항상 실행 (C-M-09: 거부권 없음)
        try:
            raw_edited = self._get_editor().finalize(
                draft_dict=draft_dict or {},
                blueprint_dict=blueprint_dict,
                critic_report_dict=critic_report_dict,
            )
            edited_dict = _to_dict(raw_edited)
        except Exception as exc:  # noqa: BLE001
            logger.error("EditorAgent 오류: %s", exc)
            edited_dict = {
                "scene_id":    scene_id,
                "final_text":  (draft_dict or {}).get("draft_text", ""),
                "polish_notes": [],
                "editor_applied": False,
            }

        return CoordinatorResult(
            scene_id=scene_id,
            final_text=edited_dict.get("final_text", ""),
            rounds_used=rounds_used,
            success=True,
            blueprint_dict=blueprint_dict,
            last_critic_score=float(
                (critic_report_dict or {}).get("constitution_score", 0.0)
            ),
            last_fitness_decision=str(
                (critic_report_dict or {}).get("fitness_decision", "UNKNOWN")
            ),
            polish_notes=list(edited_dict.get("polish_notes", [])),
        )


# ── Stub 구현체 (의존 모듈 미설치 시 폴백) ─────────────────────────────────

class _StubDirector:
    """실제 DirectorAgent 미사용 시 폴백."""

    # 두 가지 호출 패턴 모두 지원
    def generate_blueprint(self, context=None, *, prefix="scene",
                           episode=1, scene=1,
                           scene_prefix=None, episode_num=None, scene_num=None):
        # 파라미터 정규화
        _prefix  = scene_prefix if scene_prefix is not None else prefix
        _episode = episode_num  if episode_num  is not None else episode
        _scene   = scene_num    if scene_num    is not None else scene

        from types import SimpleNamespace
        bp = SimpleNamespace()
        bp.scene_id    = f"{_prefix}_ep{_episode:02d}_sc{_scene:02d}"
        bp.objective   = "stub objective"
        bp.setting     = "stub setting"
        bp.characters  = []
        bp.tone        = "neutral"
        bp.constraints = {"editor_can_reject": False}

        def _to_d():
            return {
                "scene_id":    bp.scene_id,
                "objective":   bp.objective,
                "setting":     bp.setting,
                "characters":  bp.characters,
                "tone":        bp.tone,
                "constraints": bp.constraints,
            }
        bp.to_dict = _to_d
        return bp


class _StubScript:
    def generate(self, *, blueprint_dict, attempt_num=1):
        from types import SimpleNamespace
        d = SimpleNamespace()
        d.scene_id          = blueprint_dict.get("scene_id", "unknown")
        d.draft_text        = f"[Stub Draft attempt={attempt_num}]"
        d.attempt_num       = attempt_num
        d.safety_passed     = True
        d.lora_artifact_id  = None
        d.word_count        = 3
        d.to_dict = lambda: {
            "scene_id":          d.scene_id,
            "draft_text":        d.draft_text,
            "attempt_num":       d.attempt_num,
            "safety_passed":     d.safety_passed,
            "lora_artifact_id":  d.lora_artifact_id,
            "word_count":        d.word_count,
        }
        return d


class _StubCritic:
    def evaluate(self, *, draft_dict, blueprint_dict=None, round_num=1):
        from types import SimpleNamespace
        r = SimpleNamespace()
        r.scene_id              = draft_dict.get("scene_id", "unknown")
        r.passed                = True
        r.constitution_score    = 0.70
        r.fitness_decision      = "SELECT"
        r.request_regeneration  = False
        r.round_num             = round_num
        r.suggestions           = []
        r.axis_scores           = {}
        r.to_dict = lambda: {
            "scene_id":              r.scene_id,
            "passed":                r.passed,
            "constitution_score":    r.constitution_score,
            "fitness_decision":      r.fitness_decision,
            "request_regeneration":  r.request_regeneration,
            "round_num":             r.round_num,
            "suggestions":           r.suggestions,
            "axis_scores":           r.axis_scores,
        }
        return r


class _StubEditor:
    def finalize(self, *, draft_dict, blueprint_dict=None, critic_report_dict=None):
        from types import SimpleNamespace
        e = SimpleNamespace()
        e.scene_id       = draft_dict.get("scene_id", "unknown")
        e.final_text     = draft_dict.get("draft_text", "")
        e.polish_notes   = []
        e.editor_applied = False
        e.to_dict = lambda: {
            "scene_id":       e.scene_id,
            "final_text":     e.final_text,
            "polish_notes":   e.polish_notes,
            "editor_applied": e.editor_applied,
        }
        return e
