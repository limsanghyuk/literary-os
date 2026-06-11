#!/usr/bin/env python3
"""장기(에피소드) 실측 — 씨드→실LLM 다중씬 생성 → LOSConstitution 공식 채점.
LF-1 6씬 에피소드 채점(궤적+score_work) · LF-2 arc 키워드 통제 프로브 · LF-3 변별(원본 vs 열화).
재현: OPENAI_API_KEY=... python tools/formula_validation/longform/run_longform.py
"""
import os, re, json, sys
sys.path.insert(0, os.getcwd())
from types import SimpleNamespace
from literary_system.adapters_live.real_openai_adapter import RealOpenAIAdapter
from literary_system.constitution.los_constitution import LOSConstitution

PREMISE = ("한국 드라마 1개 에피소드를 '연속된 6개 씬'으로 써라. 동일 인물·연속 사건·기승전결. "
 "인물: 폐업 직전 노포 식당을 지키려는 30대 딸 '미정'과 빚 독촉에 시달리는 아버지 '성철'. "
 "거시 갈등: 건물주의 퇴거 통보와 가족의 비밀(아버지의 옛 빚보증). "
 "각 씬 320~430자, 지문+대사. 마지막 씬에 1씬의 복선(간장 항아리)이 회수되게 하라.\n"
 "출력 형식(정확히 준수): 각 씬을 '[S1]'~'[S6]' 헤더로 시작. 설명·제목 없이 본문만.\n"
 "추가로, S4를 긴장·감각·디테일만 제거하고 사건·인물·분량은 동일하게 평탄화한 열화판을 '[S4D]' 헤더로 1개 더 출력.")

adapter = RealOpenAIAdapter()
con = LOSConstitution()
ctx = SimpleNamespace(extra={"user_prompt": PREMISE}, max_tokens=3600, timeout=42)
r = adapter.call(ctx)
if not r.success:
    print("생성 실패:", r.error); sys.exit(1)
raw = r.text
# 파싱
def grab(tag, nxt):
    m = re.search(rf"\[{tag}\](.*?)(?=\[(?:{nxt})\]|$)", raw, re.S)
    return (m.group(1).strip() if m else "")
scenes = [grab(f"S{i}", "S[0-9]D?") for i in range(1,7)]
s4d = grab("S4D", "S[0-9]D?")
scenes = [s for s in scenes if len(s) > 40]

def comp(s):
    sc = con.score_scene_full(s)
    return dict(R=sc.total, drse=sc.drse, debt=sc.debt, arc=sc.arc, tension=sc.tension, prose=sc.prose)

per = [comp(s) for s in scenes]
work = con.score_work(scenes)

# LF-2: arc 키워드 통제 프로브 — S3에 기/승/전/결 마커 강제 주입
base = scenes[2] if len(scenes) >= 3 else scenes[0]
sents = [x for x in re.split(r'(?<=[.!?\n])', base) if x.strip()]
q = max(1, len(sents)//4)
inj = ("처음 미정은 식당 문을 열며 하루를 시작했다. " + "".join(sents[:q]) +
       " 이어서 상황은 발전했고 그녀는 변화를 알게 됐다. " + "".join(sents[q:2*q]) +
       " 하지만 갑자기 위기가 닥쳤고 예상치 못한 반전이 일어났다. " + "".join(sents[2*q:3*q]) +
       " 마침내 결국 모든 것이 끝을 향했다. " + "".join(sents[3*q:]))
arc_probe = dict(base_arc=comp(base)["arc"], injected_arc=comp(inj)["arc"])

# LF-3: 변별 — S4 원본 vs 열화판
disc = None
if s4d and len(scenes) >= 4:
    a, b = comp(scenes[3]), comp(s4d)
    disc = dict(orig=a, degraded=b, dR=round(a["R"]-b["R"],4),
                d_by={k: round(a[k]-b[k],4) for k in ("drse","debt","arc","tension","prose")})

out = dict(model="gpt-4o-mini", n_scenes=len(scenes), cost_usd=round(r.cost_usd,5),
           out_tokens=r.output_tokens, per_scene=per,
           work=dict(mean=work.mean_total, variance=work.variance_total, W=work.work_score),
           arc_probe=arc_probe, discrimination=disc,
           scenes=scenes, s4_degraded=s4d)
json.dump(out, open("/tmp/lf_results.json","w"), ensure_ascii=False, indent=2)

# 출력
print("="*70); print(f"  장기 실측 LF — {len(scenes)}씬 에피소드 | gpt-4o-mini | ${r.cost_usd:.5f} | {r.output_tokens}tok"); print("="*70)
print(f"\n[LF-1] 씬별 공식 궤적")
print(f"{'씬':>3} {'R':>6} {'drse':>6} {'debt':>6} {'arc':>6} {'tens':>6} {'prose':>6}")
for i,p in enumerate(per,1):
    print(f"S{i:>2} {p['R']:6.3f} {p['drse']:6.3f} {p['debt']:6.3f} {p['arc']:6.3f} {p['tension']:6.3f} {p['prose']:6.3f}")
print(f"  score_work: mean={work.mean_total}  var={work.variance_total}  W(work)={work.work_score}")
print(f"\n[LF-2] arc 키워드 통제 프로브 (S3): base_arc={arc_probe['base_arc']} → 마커주입 arc={arc_probe['injected_arc']}")
if disc:
    print(f"\n[LF-3] 변별 R(원본)={disc['orig']['R']:.3f} vs R(열화)={disc['degraded']['R']:.3f}  ΔR={disc['dR']:+.3f}")
    print(f"       컴포넌트별 Δ(원본−열화): {disc['d_by']}")
print("\n저장: /tmp/lf_results.json")
