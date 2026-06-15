#!/usr/bin/env python3
"""
e2e_pass5_local.py — Pass4 RAG(실 ChromaDB) + Pass7 실명작 결선 E2E (로컬 corpus_ko 전용)

샌드박스 불가(verbatim 데이터 없음) → 개발자 로컬에서 실행.
필요 로컬 데이터:
  - ChromaDB (ko_scenes 컬렉션)  ← chroma_export.tar.gz 복원 또는 store_chroma.py 재생성
  - corpus_ko/scenes/*.jsonl     ← 실제 씬 본문(레퍼런스 앵커, verbatim=평가입력만)
  - OPENAI_API_KEY

실행:
  cd <corpus_ko 작업폴더>
  CHROMA_PATH=./chroma SCENES_DIR=./scenes OPENAI_API_KEY=... \
    python <repo>/docs/sessions/2026-06-13_corpus_ko_build/orchestration/e2e_pass5_local.py
"""
from __future__ import annotations
import os, sys, json, glob, re, random, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, REPO)
from schema import WorkSpec
from passes import pass2_causality, pass3_scene_brief
from passes4_7 import pass4_rag, pass5_draft, pass6_gate, pass7_panel
from literary_system.constitution.los_constitution import LOSConstitution

KEY = os.environ["OPENAI_API_KEY"]
CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma")
SCENES_DIR = os.environ.get("SCENES_DIR", "./scenes")
GEN_MODEL = os.environ.get("GEN_MODEL", "gpt-4o-mini")


def _chat(prompt, model=GEN_MODEL, mt=2200, temp=0.7):
    p = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    if model.startswith("gpt-5"): p["max_completion_tokens"] = mt
    else: p["max_tokens"] = mt; p["temperature"] = temp
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
        data=json.dumps(p).encode(), headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))["choices"][0]["message"]["content"]


def _embed(text):
    req = urllib.request.Request("https://api.openai.com/v1/embeddings",
        data=json.dumps({"model": "text-embedding-3-small", "input": text}).encode(),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))["data"][0]["embedding"]


# ── Pass4: 실 ChromaDB 유사 씬 retrieve ──────────────────────────────────────
def make_chroma_retriever():
    import chromadb  # pip install chromadb
    col = chromadb.PersistentClient(path=CHROMA_PATH).get_collection("ko_scenes")
    def retrieve(brief):
        q = f"{brief.dramatic_function} {' '.join(brief.characters)} {' '.join(brief.targets.get('callback_motifs') or [])}"
        res = col.query(query_embeddings=[_embed(q)], n_results=3)
        return [f"ko_scene::{i}" for i in res["ids"][0]]
    return retrieve


# ── Pass7: 실명작 레퍼런스(scene_id) 풀 ──────────────────────────────────────
def load_real_scenes(min_len=200, max_len=700):
    pool = []
    for f in glob.glob(os.path.join(SCENES_DIR, "*.jsonl")):
        for line in open(f, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if not line: continue
            s = json.loads(line); t = s.get("text", "")
            if min_len <= len(t) <= max_len:
                pool.append((f"{s['work_id']}::S{s['scene_no']}", t))
    return pool


def make_reference_picker(pool, seed=7):
    rng = random.Random(seed)
    def reference_of(brief):
        if not pool: return (None, None)
        return rng.choice(pool)   # 실명작 씬(verbatim은 평가 입력만, 저장은 결과·id)
    return reference_of


def make_panel_judge():
    def judge(draft, ref):
        # 3페르소나 합의 블라인드(생성 draft vs 실명작 ref)
        swap = random.random() < 0.5
        A, B = (ref, draft) if swap else (draft, ref)
        p = ("3인 패널(문학평론가·드라마투르그·일반시청자) 블라인드. 두 씬 A/B 중 서사적 완성도가 높은 쪽을 각자 고른다. "
             "마지막 줄: 'WINNER: A' 또는 'WINNER: B' (다수결).\n\n[A]\n" + A + "\n\n[B]\n" + B)
        r = _chat(p, "gpt-4o-mini", 200, 0.2)
        m = re.search(r"WINNER\s*[:：]\s*(A|B)", r, re.I)
        w = m.group(1).upper() if m else "B"
        draft_disp = "B" if swap else "A"
        return "draft" if w == draft_disp else "ref"
    return judge


def main():
    spec = WorkSpec(title="균열", genre="thriller", n_episodes=1, master_theme="신뢰의 붕괴",
                    conflict_axis="형사 준호 vs 내부자 세아", core_dilemma="진실 vs 안전",
                    characters=[{"name": "준호", "role": "형사", "want": "진실", "flaw": "의심"},
                                {"name": "세아", "role": "내부자", "want": "은폐", "flaw": "공포"}],
                    arc_summary="의심에서 확신으로")
    briefs = pass3_scene_brief(spec, pass2_causality(spec, ["깨진 유리", "녹취 파일"]))[:4]
    # Pass4 실 RAG
    pass4_rag(briefs, retrieve=make_chroma_retriever())
    # Pass5 실 생성
    def gen(b, refs):
        return _chat(f"한국 드라마 스릴러 씬을 산문으로(300~430자, 지문+대사). "
                     f"기능={b.dramatic_function} 인물={','.join(b.characters)} "
                     f"회수모티프={' '.join(b.targets.get('callback_motifs') or []) or '없음'}. 본문만.")
    pass5_draft(briefs, generate=gen)
    pass6_gate(briefs)
    # Pass7 실명작 레퍼런스 패널
    pool = load_real_scenes()
    pairs = pass7_panel(briefs, judge=make_panel_judge(), reference_of=make_reference_picker(pool))
    con = LOSConstitution()
    gp = sum(1 for b in briefs if b.gate["pass"])
    draft_win = sum(1 for b in briefs if b.panel and b.panel.get("pairwise_pref") == "draft")
    print(f"[로컬 E2E] Pass6 {gp}/{len(briefs)} | 평균 R={sum(con.score_scene_full(b.draft).total for b in briefs)/len(briefs):.3f}")
    print(f"  Pass7 생성 vs 실명작: 생성 승 {draft_win}/{len(pairs)} (실명작 풀 {len(pool)}씬)")
    print("  ※ 생성<<실명작이면 정상(아직 LLM-0 생성). 격차가 곧 학습 목표(loop-C).")


if __name__ == "__main__":
    main()
