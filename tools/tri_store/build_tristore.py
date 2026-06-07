import json,sqlite3,math,os,urllib.request
import networkx as nx
KEY=os.environ["GEMINI_API_KEY"]
works=[json.loads(l) for l in open("scenes5.jsonl")]
KEYS=["conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","reader_surface_score","arc_tension_score"]

# ① 피처 테이블 (SQLite) — 신규 제3 스토어
con=sqlite3.connect("feature_store.db"); cur=con.cursor()
cur.execute("CREATE TABLE scenes(work TEXT,sid TEXT,present TEXT,beat TEXT,subplot TEXT,macro_phase TEXT,"+",".join(f"{k} REAL" for k in KEYS)+",quality REAL)")
rows=0
for w in works:
    for s in w["scenes"]:
        cur.execute("INSERT INTO scenes VALUES(?,?,?,?,?,?,"+",".join("?"*7)+")",
            (w["title"],s["sid"],"|".join(s.get("present",[])),s["beat"],s.get("subplot",""),s.get("macro_phase",""),
             *[float(s[k]) for k in KEYS],float(s["quality"])))
        rows+=1
con.commit()
print(f"① 피처테이블(SQLite): {rows}행 적재")
print("  질의1 — 고갈등 상위3:")
for r in cur.execute("SELECT work,sid,conflict_intensity,quality FROM scenes ORDER BY conflict_intensity DESC LIMIT 3"):
    print(f"    {r[0]} {r[1]} conflict={r[2]} q={r[3]}")
print("  질의2 — macro_phase별 평균 품질:")
for r in cur.execute("SELECT macro_phase,ROUND(AVG(quality),2),COUNT(*) FROM scenes GROUP BY macro_phase ORDER BY 2 DESC"):
    print(f"    {r[0]:6s} avgQ={r[1]} n={r[2]}")

# ② NKG 그래프 (networkx)
G=nx.DiGraph()
for w in works:
    for r in w.get("relationships",[]):
        G.add_edge(r["from"],r["to"],type=r.get("type",""),polarity=r.get("polarity",0),strength=r.get("strength",0),work=w["title"])
nx.write_graphml(G,"nkg.graphml")
print(f"\n② NKG 그래프: 노드 {G.number_of_nodes()} 엣지 {G.number_of_edges()}")
deg=sorted(G.degree,key=lambda x:-x[1])[:3]
print("  질의 — 연결 중심 인물 top3:", [(n,d) for n,d in deg])

# ③ 벡터 (Gemini 임베딩) — 의미 검색 시연
def emb(texts):
    url=f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={KEY}"
    reqs=[{"model":"models/gemini-embedding-001","content":{"parts":[{"text":t}]}} for t in texts]
    r=urllib.request.Request(url,data=json.dumps({"requests":reqs}).encode(),headers={"content-type":"application/json"})
    with urllib.request.urlopen(r,timeout=60) as x: return [e["values"] for e in json.load(x)["embeddings"]]
def cos(a,b):
    s=sum(x*y for x,y in zip(a,b));na=math.sqrt(sum(x*x for x in a));nb=math.sqrt(sum(y*y for y in b));return s/(na*nb) if na*nb else 0
beats=[(w["title"],s["sid"],s["beat"]) for w in works for s in w["scenes"]]
query="권력·시스템에 맞서는 개인의 결단"
vecs=emb([b[2] for b in beats]+[query])
qv=vecs[-1]; sims=sorted([(cos(vecs[i],qv),beats[i]) for i in range(len(beats))],reverse=True)[:3]
print(f"\n③ 벡터 검색: '{query}' 유사 씬 top3:")
for sim,(t,sid,beat) in sims: print(f"    {sim:.3f} {t} {sid}: {beat[:40]}")
con.close()
