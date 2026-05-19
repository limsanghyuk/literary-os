"""V328 Task17: EmotionalMomentumTracker — 4D 감정 모멘텀 벡터."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import math

@dataclass
class EmotionalVector:
    tension:   float = 0.5
    sympathy:  float = 0.5
    dread:     float = 0.3
    catharsis: float = 0.0

    def __post_init__(self):
        for a in ("tension","sympathy","dread","catharsis"):
            setattr(self, a, max(0.0, min(1.0, float(getattr(self, a)))))

    def magnitude(self) -> float:
        return math.sqrt(self.tension**2+self.sympathy**2+self.dread**2+self.catharsis**2)

    def dominant_dim(self) -> str:
        d = {"tension":self.tension,"sympathy":self.sympathy,
             "dread":self.dread,"catharsis":self.catharsis}
        return max(d, key=d.__getitem__)

    def __repr__(self):
        return (f"EmotionalVector(T={self.tension:.2f} S={self.sympathy:.2f} "
                f"D={self.dread:.2f} C={self.catharsis:.2f})")

class EmotionalMomentumTracker:
    DECAY = 0.85
    ALPHA = 0.15
    _T_KW = {"위기","충돌","긴장","위험","폭발","갈등","crisis","conflict","tension","danger","explode"}
    _S_KW = {"눈물","공감","슬픔","연민","위로","사랑","tears","sympathy","grief","comfort","love"}
    _D_KW = {"공포","불안","두려움","암울","절망","어둠","fear","dread","despair","dark","ominous"}
    _C_KW = {"해방","해결","승리","안도","성장","극복","relief","resolved","victory","catharsis","freedom"}

    def __init__(self, initial: Optional[EmotionalVector] = None):
        self._current = initial or EmotionalVector()
        self._history: list[EmotionalVector] = []

    def update(self, scene_record, seq_plan=None) -> EmotionalVector:
        delta = self._estimate(scene_record, seq_plan)
        p = self._current
        self._current = EmotionalVector(
            tension  = self.DECAY*p.tension   + self.ALPHA*delta.tension,
            sympathy = self.DECAY*p.sympathy  + self.ALPHA*delta.sympathy,
            dread    = self.DECAY*p.dread     + self.ALPHA*delta.dread,
            catharsis= self.DECAY*p.catharsis + self.ALPHA*delta.catharsis,
        )
        self._history.append(self._current)
        return self._current

    def current(self)  -> EmotionalVector: return self._current
    def history(self)  -> list[EmotionalVector]: return list(self._history)
    def reset(self):
        self._current = EmotionalVector(); self._history.clear()

    def to_prompt_hint(self) -> str:
        v = self._current
        return (f"[EmotionalMomentum] tension={v.tension:.2f} sympathy={v.sympathy:.2f} "
                f"dread={v.dread:.2f} catharsis={v.catharsis:.2f} | dominant={v.dominant_dim()}")

    def _estimate(self, record, seq_plan=None) -> EmotionalVector:
        text = getattr(record,"draft_text","") or getattr(record,"text","") or ""
        mae  = float(getattr(record,"mae_score",0.5) or 0.5)
        tt   = 0.5
        if seq_plan and hasattr(seq_plan,"tension_target"):
            try: tt = float(seq_plan.tension_target)
            except Exception:

                pass
        tl = text.lower(); ws = set(tl.split())
        def ks(kws): return min(1.0, sum(1 for k in kws if k in tl or k in ws)/max(1,len(kws)*0.15))
        return EmotionalVector(
            tension  = 0.6*tt + 0.4*ks(self._T_KW),
            sympathy = 0.5*mae + 0.5*ks(self._S_KW),
            dread    = 0.4*(1-mae) + 0.6*ks(self._D_KW),
            catharsis= 0.3*max(0.0,mae-0.6)/0.4 + 0.7*ks(self._C_KW),
        )
