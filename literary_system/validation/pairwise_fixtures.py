"""
pairwise_fixtures.py — G_PAIRWISE_REGRESSION 픽스처 정의 (ADR-211, WP-4b)

명작(CANONICAL) vs 강열화(DEGRADED) 11쌍 골든셋.
각 쌍은 (canonical_id, degraded_id) 형태.

규칙:
- 픽스처는 이 파일에서만 선언 (단일 진실 원천)
- canonical은 반드시 CANONICAL_WORKS 목록에 속해야 함
- degraded는 _deg 접미사 규칙 (검사는 게이트에서)
"""
from __future__ import annotations

from typing import Final, List, Tuple

# §0: ANCHOR_SET_V1 와 겹치지 않는 독립 픽스처
REGRESSION_PAIRS: Final[List[Tuple[str, str]]] = [
    # (canonical_id, degraded_id)
    ("운수좋은날_s01", "운수좋은날_s01_deg"),
    ("운수좋은날_s03", "운수좋은날_s03_deg"),
    ("운수좋은날_s04", "운수좋은날_s04_deg"),
    ("운수좋은날_s05", "운수좋은날_s05_deg"),
    ("운수좋은날_s06", "운수좋은날_s06_deg"),
    ("운수좋은날_s07", "운수좋은날_s07_deg"),
    ("운수좋은날_s08", "운수좋은날_s08_deg"),
    ("운수좋은날_s09", "운수좋은날_s09_deg"),
    ("pd_canon_s01",   "pd_canon_s01_deg"),
    ("pd_canon_s02",   "pd_canon_s02_deg"),
    ("pd_canon_s03",   "pd_canon_s03_deg"),
]

assert len(REGRESSION_PAIRS) == 11, "REGRESSION_PAIRS must have exactly 11 pairs"

REGRESSION_MIN_WIN_RATE: Final[float] = 9 / 11  # ≥ 81.8%
