#!/usr/bin/env python3
"""
e2e_pass5_home.py — 집 로컬 환경 맞춤 E2E 측정 (ChromaDB 불요).

이 환경 제약 대응:
  - ChromaDB FUSE 쓰기불가 → emb_cache(.npy) 인메모리 코사인으로 Pass4 RAG.
  - scene_features.db 0바이트 → 미사용(공식은 LOSConstitution로 직접 채점).
  - 45초 한계 → 샤드/레퍼런스 샘플 캡(환경변수로 조절, 로컬은 풀 가능).

설정(환경변수):
  CORPUS_DIR  corpus_ko 경로(필수)  · MAX_SHARDS 임베딩 샤드 수(기본 30)
  N_SCENES    생성 씬 수(기본 2)     · GEN_MODEL 생성 모델(기본 gpt-4o-mini)
실행:
  CORPUS_DIR=/path/to/corpus_ko OPENAI_API_KEY=... python e2e_pass5_home.py
"""
from __future__ import annotations
import os, sys, json, glob, re, random, urllib.request
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, REPO)
from schema import WorkSpec
from passes import pass2_causality, pass3_scene_brief
from passes4_7 import pass4_rag, pass5_draft, pass6_gate, pass7_panel
from literary_system.constitution.los_constitution import LOSConstitution

CORPUS = os.environ["CORPUS_DIR"]
KEY = os.environ["OPENAI_API_KEY"]
MAX_SHARDS = int(os.environ.get("MAX_SHARDS", "30"))
N_SCENES = int(os.environ.get("N_SCENES", "2"))
GEN_MODEL = os.environ.get("GEN_MODEL", "gpt-4o-mini")
TIER1 = ["올드보이", "살인의추억", "곡성", "부산행", "괴물", "마더", "박쥐", "추격자", "신세계", "밀양", "타짜", "광해"]


def _post(url, body, mt=42):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=mt))


def chat(prompt, model=GEN_MODEL, mt=1800, temp=0.7):
    p = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    if model.startswith("gpt-5"): p["max_completion_tokens"] = mt
    else: p["max_tokens"] = mt; p["temperature"] = temp
    return _post("https://api.openai.com/v1/chat/completions", p)["choices"][0]["message"]["content"]


def embed_many(texts):
    r = _post("https://api.openai.com/v1/embeddings", {"model": "text-embedding-3-small", "input": texts}, 30)
    return np.array([d["embedding"] for d in r["data"]], dtype=np.float32)


# ── Pass4: emb_cache 인메모리 코사인 ─────────────────────────────────────────
def load_emb_pool():
    shards = sorted(glob.glob(os.path.join(CORPUS, "emb_cache", "shard_*.npy")))
    random.Random(0).shuffle(shards)
    mats, ids = [], []
    for npy in shards[:MAX_SHARDS]:
        try:
            meta = json.load(open(npy[:-4] + ".json", encoding="utf-8"))
            emb = np.load(npy)
        except Exception:
            continue
        for i, sid in enumerate(meta["ids"]):
            if "::scene::" in sid:
                mats.append(emb[i]); ids.append(sid)
    M = np.array(mats, dtype=np.float32)
    M /= (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
    return M, ids


def make_retriever(M, ids, k=3):
    def retrieve(brief):
        q = f"{brief.dramatic_function} {' '.join(brief.characters)} {' '.join(brief.targets.get('callback_motifs') or [])}"
        qe = embed_many([q])[0]; qe /= (np.linalg.norm(qe) + 1e-9)
        top = np.argsort(-(M @ qe))[:k]
        return [f"sim::{ids[i]}" for i in top]
    return retrieve


# ── Pass7: 실명작 레퍼런스 풀 ────────────────────────────────────────────────
def load_masterpiece_pool(lo=200, hi=700):
    pool = []
    for w in TIER1:
        p = os.path.join(CORPUS, "scenes", f"{w}.jsonl")
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line:
                d = json.loads(line); t = d.get("text", "")
                if lo <= len(t) <= hi:
                    pool.append((f"{d['work_id']}::S{d['scene_no']}", t))
    return pool


def panel_judge_3persona(draft, ref):
    swap = random.random() < 0.5
    A, B = (ref, draft) if swap else (draft, ref)
    p = ("3인 패널(문학평론가·드라마투르그·일반시청자)이 두 한국 드라마 씬 A/B를 블라인드로 보고 "
         "서사적 완성도(긴장·디테일·극적효과)가 높은 쪽을 각자 고른다. "
         "마지막 줄에 정확히 'WINNER: A' 또는 'WINNER: B'(다수결).\n\n[A]\n" + A + "\n\n[B]\n" + B)
    r = chat(p, "gpt-4o-mini", 250, 0.2)
    m = re.search(r"WINNER\s*[:：]\s*(A|B)", r, re.I)
    w = m.group(1).upper() if m else "B"
    return "draft" if (w == ("B" if swap else "A")) else "ref"


def main():
    print(f"[로딩] emb_cache {MAX_SHARDS}샤드...", flush=True)
    M, ids = load_emb_pool()
    pool = load_masterpiece_pool()
    print(f"  임베딩 풀 {len(ids)}씬 · 명작 풀 {len(pool)}씬 (Tier-1)", flush=True)

    spec = WorkSpec(title="균열", genre="thriller", n_episodes=1, master_theme="신뢰의 붕괴",
                    conflict_axis="형사 준호 vs 내부자 세아", core_dilemma="진실 vs 안전",
                    characters=[{"name": "준호", "role": "형사", "want": "진실", "flaw": "의심"},
                                {"name": "세아", "role": "내부자", "want": "은폐", "flaw": "공포"}],
                    arc_summary="의심에서 확신으로")
    briefs = pass3_scene_brief(spec, pass2_causality(spec, ["깨진 유리", "녹취 파일"]))[:N_SCENES]
    pass4_rag(briefs, retrieve=make_retriever(M, ids))            # 실 RAG(코사인)
    pass5_draft(briefs, generate=lambda b, refs: chat(
        f"한국 드라마 스릴러 씬 산문(300~430자, 지문+대사). 기능={b.dramatic_function} "
        f"인물={','.join(b.characters)} 회수모티프={' '.join(b.targets.get('callback_motifs') or []) or '없음'}. 본문만."))
    pass6_gate(briefs)
    rng = random.Random(7)
    pass7_panel(briefs, judge=panel_judge_3persona, reference_of=lambda b: rng.choice(pool))

    con = LOSConstitution()
    gp = sum(1 for b in briefs if b.gate["pass"])
    dw = sum(1 for b in briefs if b.panel and b.panel.get("pairwise_pref") == "draft")
    print("=" * 60)
    for i, b in enumerate(briefs, 1):
        s = con.score_scene_full(b.draft)
        print(f"S{i}[{b.dramatic_function}] Pass6={'P' if b.gate['pass'] else 'F'} R={s.total:.3f} "
              f"RAG={b.rag_refs[:1]} 패널={b.panel.get('pairwise_pref')}")
    print(f"\n[집 로컬 E2E] Pass6 {gp}/{len(briefs)} · 평균 R={sum(con.score_scene_full(b.draft).total for b in briefs)/len(briefs):.3f} "
          f"· Pass7 생성 vs 실명작 {dw}/{len(briefs)}")
    print("  ※ 생성<<명작이 정상(LLM-0 생성, 격차=loop-C 목표). 풀 측정은 MAX_SHARDS↑·N_SCENES↑로 로컬 실행.")


if __name__ == "__main__":
    main()
