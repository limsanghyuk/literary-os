"""
generation/schema.py — 7-pass 생성 본체 타입 계약 (V781, ADR-241).

docs/sessions 실험 골격을 literary_system 정식 계약으로 승격. 각 Pass의 입출력 단위.
LLM-0: 스키마는 순수 데이터(LLM 미호출). 생성은 Pass5 훅에서만.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class WorkSpec:                       # Pass1 출력 — 거시 설계
    title: str
    genre: str
    n_episodes: int
    master_theme: str
    conflict_axis: str
    core_dilemma: str
    characters: List[Dict[str, Any]]  # [{name, role, want, flaw}]
    arc_summary: str

    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class Beat:                           # Pass2 출력 — 인과 비트
    beat_id: str
    function: str                     # setup|inciting|rising|midpoint|crisis|climax|resolution
    pos: float
    causal_parent: Optional[str]
    intent: str
    plant_motifs: List[str]
    payoff_motifs: List[str]
    target_tension: float

    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class SceneBrief:                     # Pass3 출력 — 생성 단위 계약
    scene_id: str
    beat_id: str
    slug: Dict[str, Any]
    characters: List[str]
    dramatic_function: str
    targets: Dict[str, Any]           # {tension_band:[lo,hi], conflict_intensity_min, callback_motifs}
    rag_refs: List[str] = field(default_factory=list)   # Pass4
    draft: Optional[str] = None       # Pass5 (생성기 출력)
    gate: Optional[Dict[str, Any]] = None    # Pass6 (구조 게이트)
    panel: Optional[Dict[str, Any]] = None   # Pass7 (패널 판정)

    def to_dict(self) -> Dict[str, Any]: return asdict(self)


# 표준 7기능 아크 (정규위치, 인과부모)
STANDARD_ARC = [
    ("setup", 0.04, None), ("inciting", 0.12, "setup"), ("rising", 0.30, "inciting"),
    ("midpoint", 0.50, "rising"), ("crisis", 0.68, "midpoint"),
    ("climax", 0.85, "crisis"), ("resolution", 0.96, "climax"),
]
INTENT = {"setup": "세계·인물·결핍 제시", "inciting": "균형을 깨는 사건",
          "rising": "갈등 상승·정보 통제", "midpoint": "판을 뒤집는 전환",
          "crisis": "최저점·딜레마 직면", "climax": "핵심 대결·선택",
          "resolution": "여파·잔향(미해소 여지)"}
