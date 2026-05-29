"""V329: SceneNodeAdapter — SceneDraftOutput → NKGSceneNode 단방향 변환.

설계 원칙:
  - 역의존성 없음: NKG 모듈이 schemas를 참조하되, schemas는 NKG를 모름
  - V328 기존 1,000 PASS에 영향 없음
  - SceneDraftOutput.emotional_vector → NKG 감정 엣지 가중치 자동 변환
  - Pydantic 없는 환경에서도 동작 (duck-typing 기반 속성 접근)
"""
from __future__ import annotations

from typing import Any, List, Optional

from literary_system.nkg.schema import SceneNode as NKGSceneNode


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _extract_ev_list(ev: Any) -> List[float]:
    """EmotionalVectorSchema / dataclass / raw list → 4D float list 추출."""
    if ev is None:
        return [0.5, 0.5, 0.3, 0.0]
    # raw list / tuple 지원 (V340: adapter가 list를 직접 받을 수 있음)
    if isinstance(ev, (list, tuple)):
        raw = list(ev)
        defaults = [0.5, 0.5, 0.3, 0.0]
        result = []
        for i in range(4):
            result.append(_safe_float(raw[i] if i < len(raw) else defaults[i], defaults[i]))
        return result
    # Pydantic EmotionalVectorSchema 또는 dataclass EmotionalVector 공통 처리
    return [
        _safe_float(getattr(ev, "tension",   0.5), 0.5),
        _safe_float(getattr(ev, "sympathy",  0.5), 0.5),
        _safe_float(getattr(ev, "dread",     0.3), 0.3),
        _safe_float(getattr(ev, "catharsis", 0.0), 0.0),
    ]


class SceneNodeAdapter:
    """SceneDraftOutput → NKGSceneNode 단방향 어댑터.

    V328의 SceneDraftOutput (Pydantic BaseModel) 또는
    일반 scene record (duck-typing) 모두 지원한다.

    Examples::

        from literary_system.nkg.adapters.scene_node_adapter import SceneNodeAdapter

        node = SceneNodeAdapter.from_draft_output(draft_output)
        nodes = SceneNodeAdapter.batch_convert(draft_outputs)
    """

    # ── 단일 변환 ────────────────────────────────────────────
    @staticmethod
    def from_draft_output(draft_output: Any,
                          episode_id: Optional[str] = None) -> NKGSceneNode:
        """SceneDraftOutput → NKGSceneNode.

        Args:
            draft_output: SceneDraftOutput 인스턴스 (Pydantic) 또는
                          scene_id, draft_text 등을 가진 임의 객체.
            episode_id:   명시적 에피소드 ID. draft_output에서 추론 불가 시 사용.

        Returns:
            NKGSceneNode 인스턴스. content_hash가 자동 계산됨.
        """
        # scene_id
        scene_id = str(
            getattr(draft_output, "scene_id", None)
            # removed mock-unsafe .id fallback
            or "unknown_scene"
        )

        # episode_id 결정 순서: 인자 > draft_output.episode_id > episode_no > 기본값
        ep_id = (
            episode_id
            or getattr(draft_output, "episode_id",  None)
            or str(getattr(draft_output, "episode_no", None) or "ep_unknown")
        )

        # 텍스트 내용
        content = (
            getattr(draft_output, "draft_text", None)
            or getattr(draft_output, "scene_text", None)
            or getattr(draft_output, "text",  None)
            or ""
        )

        # 감정 벡터
        ev_raw = (
            getattr(draft_output, "emotional_vector", None)
        )
        ev_list = _extract_ev_list(ev_raw)

        # 품질 문자열
        quality_raw = getattr(draft_output, "quality", None)
        if quality_raw is None:
            quality = "UNRATED"
        elif hasattr(quality_raw, "value"):
            quality = str(quality_raw.value).upper()
        else:
            quality = str(quality_raw).upper()

        # MAE 점수
        mae = _safe_float(getattr(draft_output, "mae_score", 0.0), 0.0)

        # scene_index
        scene_index = int(getattr(draft_output, "scene_index", 0) or 0)

        return NKGSceneNode(
            scene_id         = scene_id,
            episode_id       = ep_id,
            content          = content,
            emotional_vector = ev_list,
            quality          = quality,
            scene_index      = scene_index,
            mae_score        = mae,
        )

    # ── 배치 변환 ────────────────────────────────────────────
    @staticmethod
    def batch_convert(draft_outputs: List[Any],
                      episode_id: Optional[str] = None,
                      skip_none: bool = True) -> List[NKGSceneNode]:
        """여러 SceneDraftOutput을 NKGSceneNode 리스트로 일괄 변환.

        Args:
            draft_outputs: SceneDraftOutput 목록.
            episode_id:    공통 에피소드 ID (개별 draft_output 우선).
            skip_none:     None 항목 무시 여부 (기본 True).

        Returns:
            NKGSceneNode 리스트. 변환 실패 항목은 건너뜀.
        """
        result: List[NKGSceneNode] = []
        for item in draft_outputs:
            if item is None:
                if not skip_none:
                    continue
                continue
            try:
                node = SceneNodeAdapter.from_draft_output(item, episode_id=episode_id)
                result.append(node)
            except Exception:
                if not skip_none:
                    raise
        return result

    # ── scene_record (SGO 내부 타입) 변환 ───────────────────
    @staticmethod
    def from_scene_record(record: Any,
                          episode_id: str = "ep_unknown",
                          scene_index: int = 0,
                          emotional_vector: Any = None) -> NKGSceneNode:
        """SGO 내부 scene record → NKGSceneNode.

        SceneDraftOutput.from_scene_record()과 동일한 인터페이스를 제공하여
        SGO 코드에서 직접 호출 가능하도록 한다.
        """
        text = (
            getattr(record, "draft_text", "")
            or getattr(record, "text", "")
            or ""
        )
        mae = _safe_float(getattr(record, "mae_score", 0.0), 0.0)
        sid = str(
            getattr(record, "scene_id", None)
            or f"scene_{episode_id}_{scene_index}"
        )
        quality_raw = getattr(record, "quality", None)
        quality = (
            str(quality_raw.value).upper() if hasattr(quality_raw, "value")
            else str(quality_raw).upper() if quality_raw
            else "UNRATED"
        )

        ev_list = _extract_ev_list(emotional_vector)

        return NKGSceneNode(
            scene_id         = sid,
            episode_id       = episode_id,
            content          = text,
            emotional_vector = ev_list,
            quality          = quality,
            scene_index      = scene_index,
            mae_score        = mae,
        )
