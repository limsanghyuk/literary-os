"""e2e_pass5.py — Pass5 실 LLM E2E 1편 실측 (생성→Pass6→공식 채점)."""
import sys, os, json, re, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, REPO)
from schema import WorkSpec
from passes import pass2_causality, pass3_scene_brief
from passes4_7 import pass4_rag, pass6_gate
from literary_system.constitution.los_constitution import LOSConstitution

KEY = os.environ["OPENAI_API_KEY"]
def llm(prompt, mt=2600):
    body = json.dumps({"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.7, "max_tokens": mt}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=42))
    return r["choices"][0]["message"]["content"], r["usage"]

spec = WorkSpec(title="균열", genre="thriller", n_episodes=1, master_theme="신뢰의 붕괴",
                conflict_axis="형사 준호 vs 내부자 세아", core_dilemma="진실 vs 안전",
                characters=[{"name":"준호","role":"형사","want":"진실","flaw":"의심"},
                            {"name":"세아","role":"내부자","want":"은폐","flaw":"공포"}],
                arc_summary="의심에서 확신으로, 신뢰가 무너진다")
beats = pass2_causality(spec, motifs=["깨진 유리", "녹취 파일"])
briefs = pass3_scene_brief(spec, beats)[:4]
pass4_rag(briefs)

# Pass5: 실 LLM — 4씬 일괄 생성
sb_lines = []
for i, b in enumerate(briefs, 1):
    tb = b.targets["tension_band"]; cb = " ".join(b.targets.get("callback_motifs") or []) or "없음"
    sb_lines.append(f"[S{i}] 기능={b.dramatic_function} 인물={','.join(b.characters)} "
                    f"목표긴장={tb} 회수모티프={cb}")
prompt = ("아래 비트 명세로 한국 드라마 '균열'(스릴러)의 연속 4개 씬을 산문으로 써라. "
          "각 씬 300~430자, 지문+대사. 회수모티프가 지정된 씬은 그 모티프를 반드시 반영. "
          "출력형식: 각 씬을 '[S1]'~'[S4]' 헤더로 시작, 본문만.\n\n" + "\n".join(sb_lines))
text, usage = llm(prompt)
for i, b in enumerate(briefs, 1):
    m = re.search(rf"\[S{i}\](.*?)(?=\[S\d\]|$)", text, re.S)
    b.draft = (m.group(1).strip() if m else "")

failed = pass6_gate(briefs)
con = LOSConstitution()
cost = usage["prompt_tokens"]*0.15/1e6 + usage["completion_tokens"]*0.6/1e6
print("="*64); print(f"  Pass5 실 LLM E2E — '균열' 4씬 | gpt-4o-mini | ${cost:.5f} | {usage['completion_tokens']}tok"); print("="*64)
rows = []
for i, b in enumerate(briefs, 1):
    s = con.score_scene_full(b.draft)
    g = b.gate
    rows.append({"scene": f"S{i}", "func": b.dramatic_function, "len": len(b.draft),
                 "gate_pass": g["pass"], "gate_fail": g["fail_reasons"],
                 "R": round(s.total,3), "drse": round(s.drse,3), "debt": round(s.debt,3),
                 "arc": round(s.arc,3), "tension": round(s.tension,3), "prose": round(s.prose,3)})
    print(f"\n── S{i} [{b.dramatic_function}] {len(b.draft)}자 | Pass6={'PASS' if g['pass'] else 'FAIL '+str(g['fail_reasons'])} ──")
    print(b.draft[:240] + ("..." if len(b.draft) > 240 else ""))
    print(f"   공식 R={s.total:.3f} (drse {s.drse:.2f}/debt {s.debt:.2f}/arc {s.arc:.2f}/tens {s.tension:.2f}/prose {s.prose:.2f})")
gp = sum(1 for r in rows if r["gate_pass"])
print(f"\n[요약] Pass6 통과 {gp}/{len(rows)} | 평균 R={sum(r['R'] for r in rows)/len(rows):.3f} | 비용 ${cost:.5f}")
json.dump({"rows": rows, "drafts": [b.draft for b in briefs], "cost": cost,
           "briefs": [{"func": b.dramatic_function, "callback": b.targets.get("callback_motifs")} for b in briefs]},
          open("/tmp/e2e_results.json", "w"), ensure_ascii=False, indent=1)
print("저장 /tmp/e2e_results.json")
