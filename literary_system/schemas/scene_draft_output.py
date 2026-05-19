"""V328 Task17: SceneDraftOutput — Pydantic 구조화 출력 스키마."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional


class SceneQuality(str, Enum):
    EXCELLENT  = "excellent"
    GOOD       = "good"
    ACCEPTABLE = "acceptable"
    POOR       = "poor"

def _quality_from_score(score: float) -> SceneQuality:
    if score >= 0.85: return SceneQuality.EXCELLENT
    if score >= 0.70: return SceneQuality.GOOD
    if score >= 0.55: return SceneQuality.ACCEPTABLE
    return SceneQuality.POOR

try:
    from pydantic import BaseModel, ConfigDict, Field
    _PYDANTIC = True
except ImportError:
    _PYDANTIC = False

if _PYDANTIC:
    class EmotionalVectorSchema(BaseModel):
        tension:   float = Field(default=0.5, ge=0.0, le=1.0)
        sympathy:  float = Field(default=0.5, ge=0.0, le=1.0)
        dread:     float = Field(default=0.3, ge=0.0, le=1.0)
        catharsis: float = Field(default=0.0, ge=0.0, le=1.0)
        dominant:  str   = "tension"
        model_config = ConfigDict(extra="ignore")

    class SceneDraftOutput(BaseModel):
        scene_id:        str              = Field(...)
        episode_no:      int              = Field(..., ge=1)
        seq_index:       int              = Field(default=0, ge=0)
        scene_index:     int              = Field(default=0, ge=0)
        draft_text:      str              = Field(...)
        word_count:      int              = Field(default=0, ge=0)
        mae_score:       float            = Field(default=0.0, ge=0.0, le=1.0)
        quality:         SceneQuality     = Field(default=SceneQuality.ACCEPTABLE)
        emotional_vector: Optional[EmotionalVectorSchema] = None
        tension_actual:  float            = Field(default=0.5, ge=0.0, le=1.0)
        rerender_count:  int              = Field(default=0, ge=0)
        gate_passed:     bool             = True
        mise_hint:       Optional[str]    = None
        graph_docs_used: int              = Field(default=0, ge=0)
        char_state_valid: bool            = True
        extra:           Dict[str,Any]    = Field(default_factory=dict)
        model_config = ConfigDict(extra="ignore")

        def __init__(self, **data):
            if "word_count" not in data and "draft_text" in data:
                data["word_count"] = len(data["draft_text"].split())
            if "quality" not in data and "mae_score" in data:
                data["quality"] = _quality_from_score(float(data["mae_score"]))
            super().__init__(**data)

        def to_dict(self):
            try: return self.model_dump()
            except Exception:
                return self.dict()

        @classmethod
        def from_scene_record(cls, record, episode_no=1, seq_index=0,
                              scene_index=0, emotional_vector=None):
            text = getattr(record,"draft_text","") or getattr(record,"text","") or ""
            mae  = float(getattr(record,"mae_score",0.0) or 0.0)
            sid  = getattr(record,"scene_id",f"scene_{episode_no}_{seq_index}_{scene_index}")
            ten  = float(getattr(record,"tension_actual",0.5) or 0.5)
            ev   = None
            if emotional_vector is not None:
                try:
                    ev = EmotionalVectorSchema(
                        tension=emotional_vector.tension, sympathy=emotional_vector.sympathy,
                        dread=emotional_vector.dread, catharsis=emotional_vector.catharsis,
                        dominant=emotional_vector.dominant_dim() if hasattr(emotional_vector,"dominant_dim") else "tension")
                except Exception:

                    pass
            return cls(scene_id=str(sid), episode_no=episode_no, seq_index=seq_index,
                       scene_index=scene_index, draft_text=text, mae_score=mae,
                       quality=_quality_from_score(mae), tension_actual=ten,
                       emotional_vector=ev)
else:
    from dataclasses import dataclass
    from dataclasses import field as dc_field
    @dataclass
    class EmotionalVectorSchema:
        tension:float=0.5; sympathy:float=0.5; dread:float=0.3; catharsis:float=0.0; dominant:str="tension"

    @dataclass
    class SceneDraftOutput:
        scene_id:str=""; episode_no:int=1; seq_index:int=0; scene_index:int=0
        draft_text:str=""; word_count:int=0; mae_score:float=0.0; quality:str="acceptable"
        emotional_vector:object=None; tension_actual:float=0.5; rerender_count:int=0
        gate_passed:bool=True; mise_hint:str=""; graph_docs_used:int=0
        char_state_valid:bool=True; extra:dict=dc_field(default_factory=dict)

        def to_dict(self):
            import dataclasses
            return dataclasses.asdict(self)

        @classmethod
        def from_scene_record(cls, record, episode_no=1, seq_index=0,
                              scene_index=0, emotional_vector=None):
            text = getattr(record,"draft_text","") or getattr(record,"text","") or ""
            mae  = float(getattr(record,"mae_score",0.0) or 0.0)
            sid  = getattr(record,"scene_id",f"scene_{episode_no}_{seq_index}_{scene_index}")
            ten  = float(getattr(record,"tension_actual",0.5) or 0.5)
            ev   = None
            if emotional_vector is not None:
                try:
                    ev = EmotionalVectorSchema(
                        tension=emotional_vector.tension, sympathy=emotional_vector.sympathy,
                        dread=emotional_vector.dread, catharsis=emotional_vector.catharsis,
                        dominant=emotional_vector.dominant_dim() if hasattr(emotional_vector,"dominant_dim") else "tension")
                except Exception:

                    pass
            return cls(scene_id=str(sid), episode_no=episode_no, seq_index=seq_index,
                       scene_index=scene_index, draft_text=text, word_count=len(text.split()),
                       mae_score=mae, quality=_quality_from_score(mae).value,
                       tension_actual=ten, emotional_vector=ev)
