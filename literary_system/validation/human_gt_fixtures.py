"""
human_gt_fixtures.py — G_HUMAN_GT_ALIGNMENT 픽스처 (ADR-213, V750)
명작(canon) vs 열화(deg) 6쌍 · 평가자 3명 · 캘리브레이션용 합성 GT.
실데이터 불요(DoD를 픽스처로 충족). canon 위치를 좌/우 섞어 across-unit 변별을 만든다.
"""
from __future__ import annotations
from typing import Dict, List
from literary_system.validation.human_gt import GTPair, GTRecord

# 픽스처 DB (scene_id → text). 실제 코퍼스 대체용 결정론 텍스트.
FIXTURE_DB: Dict[str, str] = {}
for i in range(1, 7):
    FIXTURE_DB[f"hgt_canon_{i:02d}"] = f"명작 씬 {i}: 절제된 지문과 긴장된 대사가 인물의 결단을 드러낸다."
    FIXTURE_DB[f"hgt_deg_{i:02d}"] = f"열화 씬 {i}: 사건만 평탄하게 나열되고 긴장과 디테일이 제거되었다."

# canon 위치를 섞음(좌3·우3) → 정답 winner가 left/right로 갈려 α가 well-defined
GT_FIXTURE_PAIRS: List[GTPair] = [
    GTPair("hgt_p01", "hgt_canon_01", "hgt_deg_01", "B", True, True, difficulty="wide"),
    GTPair("hgt_p02", "hgt_canon_02", "hgt_deg_02", "B", True, True, difficulty="wide"),
    GTPair("hgt_p03", "hgt_deg_03", "hgt_canon_03", "B", True, True, difficulty="wide"),
    GTPair("hgt_p04", "hgt_deg_04", "hgt_canon_04", "B", True, True, difficulty="wide"),
    GTPair("hgt_p05", "hgt_canon_05", "hgt_deg_05", "B", True, True, difficulty="close"),
    GTPair("hgt_p06", "hgt_deg_06", "hgt_canon_06", "B", True, True, difficulty="close"),
]

# canon-쪽 winner (정답): canon이 left면 "left", right면 "right"
_CANON_WINNER = {
    "hgt_p01": "left", "hgt_p02": "left", "hgt_p03": "right",
    "hgt_p04": "right", "hgt_p05": "left", "hgt_p06": "right",
}
_LR = {p.pair_id: (p.left_id, p.right_id) for p in GT_FIXTURE_PAIRS}

GT_FIXTURE_RECORDS: List[GTRecord] = []
for ev in ("writer_1", "writer_2", "writer_3"):
    for pid, win in _CANON_WINNER.items():
        w = win
        if ev == "writer_3" and pid == "hgt_p06":   # 1건 불일치(현실성)
            w = "tie"
        l, r = _LR[pid]
        GT_FIXTURE_RECORDS.append(
            GTRecord(pid, l, r, w, "preference", ev, "B"))

# 패널(LLM) 판정 — 인간 다수결과 대부분 일치
PANEL_FIXTURE_JUDGMENTS = [
    {"pair_id": pid, "left_id": _LR[pid][0], "right_id": _LR[pid][1], "winner": win}
    for pid, win in _CANON_WINNER.items()
]
