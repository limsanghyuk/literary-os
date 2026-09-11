import json, re
from pathlib import Path
from collections import Counter

SOURCE_COMMIT = "093fdddb032312b2742dcb7ff9362ff45e9b4d3d"
FILES = [
"handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ01_S01_05_R1_20260911.txt",
"handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ02_S06_10_R1_20260911.txt",
"handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ03_S11_15_R1_20260911.txt",
"handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ04_S16_20_R1_20260911.txt",
"handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ05_S21_25_R1_20260911.txt",
]
META_TOKENS = ["PSSB","shared upstream","future_adoption","decision_owner","scene plan","TREATMENT"]
EMOTION_PATTERNS = [
"불안해","불안한","화가 난","화난","분노","슬퍼","슬픈","기뻐","기쁜","안도하","안도한",
"초조해","초조한","긴장하","긴장한","당황하","당황한","두려워","두려운","걱정스러운","절망","행복해","행복한"
]

def body_of(text):
    m = re.search(r"(?m)^S#\d+\.", text)
    if not m:
        raise SystemExit("missing scene heading")
    return text[m.start():]

segments=[]
all_ids=[]
long_lines=[]
meta_hits=[]
emotion_hits=[]
id_hits=[]
for p in FILES:
    text=Path(p).read_text(encoding="utf-8")
    body=body_of(text)
    ids=[int(x) for x in re.findall(r"(?m)^S#(\d+)\.", body)]
    all_ids += ids
    for tok in META_TOKENS:
        if tok.lower() in body.lower(): meta_hits.append({"file":p,"token":tok})
    for pat in EMOTION_PATTERNS:
        if pat in body: emotion_hits.append({"file":p,"pattern":pat})
    for hit in re.findall(r"\b(?:CH|SQ)\d+\b", body): id_hits.append({"file":p,"token":hit})
    for line in body.splitlines():
        s=line.strip()
        if len(s)>=40 and not re.match(r"^S#\d+\.",s): long_lines.append(s)
    segments.append({"file":p,"body_chars":len(body),"scene_ids":ids})

dups=[{"line":k,"count":v} for k,v in Counter(long_lines).items() if v>1]
total=sum(x["body_chars"] for x in segments)
result={
"schema":"P07I4K5R4AAttempt2ControlMidpointMetricsR1",
"source_commit":SOURCE_COMMIT,
"segments":segments,
"body_chars_total":total,
"body_chars_midpoint_min_18000_pass":total>=18000,
"all_segments_min_3600_pass":all(x["body_chars"]>=3600 for x in segments),
"scene_ids":all_ids,
"scene_ids_exact_1_25":all_ids==list(range(1,26)),
"meta_leak_hits":meta_hits,
"meta_leak_zero":len(meta_hits)==0,
"CH_SQ_id_hits":id_hits,
"CH_SQ_id_zero":len(id_hits)==0,
"direct_emotion_pattern_hits":emotion_hits,
"direct_emotion_pattern_zero":len(emotion_hits)==0,
"exact_long_duplicate_lines":dups,
"exact_long_duplicate_zero":len(dups)==0,
"quality_inspection_performed":False,
}
result["midpoint_gate_pass"] = all([
result["body_chars_midpoint_min_18000_pass"], result["all_segments_min_3600_pass"],
result["scene_ids_exact_1_25"], result["meta_leak_zero"], result["CH_SQ_id_zero"],
result["direct_emotion_pattern_zero"], result["exact_long_duplicate_zero"]])
Path("/tmp/i4k5r4a_attempt2_control_midpoint_metrics.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(result,ensure_ascii=False,indent=2))
