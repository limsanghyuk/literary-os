# -*- coding: utf-8 -*-
"""물 흘리기(water) — 배관 PoC에 실제 생성 좌석을 끼워 진짜 산문을 흘린다.
wiring_poc.macro_setup + 동일 기관 재사용, 화 루프만 '문맥 보강 프롬프트 + Port + 품질지표'로 확장.
사용: PYTHONPATH=<repo> python examples/wiring_poc_water.py [frontier|llm1] [episodes]
"""
from __future__ import annotations
import sys, re, statistics, json
from examples.wiring_poc import (macro_setup, EpisodePlanner, PayoffScheduler,
    ConflictCollisionCalculus)
from examples.generative_ports import FrontierPort, LLM1Port

# 로그라인은 Synopsis Assembler(③·빈칸)의 산출 자리 — 지금은 수동 시드
LOGLINE = ("검사 한지수는 형사 박도현과 함께, 내부자 정이 흘린 단서로 피의자 윤을 쫓는다. "
           "쫓을수록 사건은 조직 내부의 은폐로 번지고, 한지수는 자신이 믿던 정의의 경계를 의심하게 된다.")

def build_prompt(ctx, ep, plan, brief, cp_in, prev_oneline):
    chars = ", ".join(ctx.tensor.active_characters)
    emo = round(statistics.mean(plan.emotional_targets), 2) if plan.emotional_targets else "-"
    return (f"[작품] {ctx.config.title} (총 {ctx.config.total_episodes}부작)\n"
            f"[로그라인] {LOGLINE}\n[등장인물] {chars}\n"
            f"[이번 {ep}화 브리프] 미시플롯 K={plan.microplot_count} · 갈등압력(이전화 누적)={cp_in:.3f} "
            f"· 감정목표={emo} · payoff={brief.get('payoff_type')}\n"
            f"[직전화 요약] {prev_oneline or '(1화: 시작)'}\n"
            f"위 브리프에 맞는 {ep}화 오프닝 장면 하나를 한국어 대본체로 써라.")

def metrics(text):
    hangul = sum(1 for c in text if '가' <= c <= '힣')
    lines = [l for l in text.splitlines() if l.strip()]
    dlg = sum(1 for l in lines if re.match(r'^\s*[가-힣A-Za-z_]{1,12}\s*[:：]', l))
    return {"len": len(text), "hangul_ratio": round(hangul/max(1,len(text)),2),
            "lines": len(lines), "dialogue_lines": dlg,
            "is_template": text.startswith("[FORMULA") or text.startswith("[FRONTIER-ERR")}

def run(seat="frontier", episodes=3):
    ctx = macro_setup(episodes, "추적자")
    port = FrontierPort() if seat == "frontier" else LLM1Port()
    print(f"=== 물 흘리기: seat={port.name} · {episodes}화 ===")
    planner, payoff, conflict = EpisodePlanner(), PayoffScheduler(), ConflictCollisionCalculus()
    chars = ctx.tensor.active_characters; n = episodes; prev=""
    results=[]
    for ep in range(1, n+1):
        brief = payoff.get_episode_brief(ctx.schedule, ep)
        cp_in = ctx.tensor.conflict_pressure
        plan = planner.plan(ctx.config, ep-1, ctx.tensor)
        prompt = build_prompt(ctx, ep, plan, brief, cp_in, prev)
        prose = port.generate(prompt, episode_idx=ep)
        m = metrics(prose); results.append({"ep":ep,"K":plan.microplot_count,"cp_in":round(cp_in,3),**m})
        prev = prose[:50].replace("\n"," ")
        # feedback write-back (동일 배관)
        ramp=ep/n; edges=[(chars[0],chars[2]),(chars[1],chars[3]),(chars[0],chars[1])]
        cres=conflict.calculate(chars, edges, {c:0.3+0.6*ramp for c in chars})
        ctx.tensor.conflict_pressure=cres.conflict_intensity
        if plan.emotional_targets: ctx.tensor.avg_emotional_momentum=statistics.mean(plan.emotional_targets)
        print(f"\n────── {ep}화 (K={plan.microplot_count}, cp_in={cp_in:.3f}, {m['len']}자, 대사{m['dialogue_lines']}줄) ──────")
        print(prose[:600])
    print("\n=== 품질지표 요약 ===")
    print(json.dumps(results, ensure_ascii=False))
    real=[r for r in results if not r["is_template"]]
    print(f"\n실생성 {len(real)}/{len(results)}화 · 평균 {round(statistics.mean([r['len'] for r in real]) if real else 0)}자 "
          f"· 평균 대사 {round(statistics.mean([r['dialogue_lines'] for r in real]),1) if real else 0}줄 "
          f"· 한글비율 {round(statistics.mean([r['hangul_ratio'] for r in real]),2) if real else 0}")
    return results

if __name__ == "__main__":
    seat = sys.argv[1] if len(sys.argv)>1 else "frontier"
    eps = int(sys.argv[2]) if len(sys.argv)>2 else 3
    run(seat, eps)
