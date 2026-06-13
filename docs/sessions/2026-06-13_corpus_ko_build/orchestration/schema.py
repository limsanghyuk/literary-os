"""생성 본체 데이터 계약 (L4 명세 GENERATION_BODY_L4_v1 준수)."""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

@dataclass
class WorkSpec:                       # Pass1 출력
    title: str
    genre: str
    n_episodes: int
    master_theme: str
    conflict_axis: str                # 대립 축 (A세력 vs B세력 / 내적 딜레마)
    core_dilemma: str
    characters: List[Dict]            # [{name, role, want, flaw}]
    arc_summary: str

@dataclass
class Beat:                           # Pass2 출력 (인과 비트)
    beat_id: str
    function: str                     # setup|inciting|rising|midpoint|crisis|climax|resolution
    pos: float                        # 정규 위치 0~1
    causal_parent: Optional[str]
    intent: str                       # 이 비트가 해야 할 일
    plant_motifs: List[str]           # 심는 모티프(나중 콜백 대상)
    payoff_motifs: List[str]          # 회수하는 기성 모티프
    target_tension: float             # 장르 곡선 T_ideal

@dataclass
class SceneBrief:                     # Pass3 출력 (생성의 단위 계약)
    scene_id: str
    beat_id: str
    slug: Dict                        # {location,time,int_ext}
    characters: List[str]
    dramatic_function: str
    targets: Dict                     # {tension_band:[lo,hi], conflict_intensity_min, callback_motifs:[]}
    rag_refs: List[str] = field(default_factory=list)   # Pass4
    draft: Optional[str] = None       # Pass5
    gate: Optional[Dict] = None       # Pass6
    panel: Optional[Dict] = None      # Pass7

def dump(obj): return asdict(obj)
