#!/usr/bin/env python3
"""EXT6 V1.2 Phase02 DesignSeed gate (SEED-A/B/C + evaluation checks).
Exit: 0 PASS, 1 FAIL, 3 HOLD_SOURCE_REQUIRED. Deterministic; no LLM.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, unicodedata
from pathlib import Path

K={
"seed":set("work_id derivation_mode read_span evidenced_initial_configuration evidenced_world_constraints evidenced_opening_disturbance judged_logline judged_central_lack judged_governing_question judged_central_opposition_axis judged_ending_direction judged_cost_structure contract_version by".split()),
"adm":set("work_id derivation_mode compatible_work_ids compatibility_count alternative_structures specificity_violations verdict".split()),
"run":set("work_id derivation_mode read_span run_id provider model_id source_file_refs source_sha256s downstream_layers_blocked downstream_blocklist cross_provider_outputs_blocked prior_mode_ref sealed_at content_sha256 by".split()),
"pred":set("work_id derivation_mode indicator predicted_value observed_value observation_source match corpus_prior by".split()),
"contam":set("work_id mode_b_ref mode_c_ref field_level_diff diverged_fields mode_b_prediction_accuracy mode_c_prediction_accuracy leakage_estimate".split())}
N={"initial":set("character_key initial_position initial_relation_axis evidence_ref".split()),"constraint":set("rule scope evidence_ref".split()),"disturbance":set("summary scene_no evidence_ref".split()),"cost":set("cost_type cost_bearer cost_summary".split()),"alt":set("sketch divergence_point".split()),"viol":set("field token violation_type".split())}
MODES={"PLAN_DOCUMENT","EP01_02_BLIND","FULL_READ"}; END={"ACHIEVE","ACHIEVE_WITH_COST","FAIL","FAIL_BUT_TRANSFORM","REFUSE","AMBIGUOUS"}
SCOPES={"SOCIAL","INSTITUTIONAL","PHYSICAL","SUPERNATURAL","ECONOMIC","RELATIONAL","PROFESSIONAL","LEGAL","CULTURAL","OTHER"}
CT={"IDENTITY","RELATIONSHIP","STATUS","SAFETY","MORAL","MATERIAL","TIME","LIFE","MIXED","NONE","AMBIGUOUS"}; CB={"PROTAGONIST","ALLY","RELATIONSHIP","COMMUNITY","ANTAGONISTIC_FORCE","MULTIPLE","NONE","AMBIGUOUS"}
VER={"ADMISSIBLE","TOO_SPECIFIC","TOO_VAGUE","REVIEW"}; IND={"center_count","opposition_persistence","conflict_persist","ending_direction","cost_realized"}
VT={"PROPER_NAME","EPISODE_NUMBER","SCENE_NUMBER","EXACT_EVENT","TERMINAL_EVENT","DOWNSTREAM_LEAKAGE","OTHER"}
EV=re.compile(r"^EP(?P<ep>\d{2})-S(?P<sc>\d+)\s+L(?P<ln>\d+)\s+(?P<q>.+)$"); NUM=re.compile(r"(?:EP|회|화|S|씬|장면)\s*\d+|\d+\s*(?:회|화|씬|장면)",re.I)
BAD={"TODO","TBD","PLACEHOLDER","???","N/A","NULL","XXX","미상","보류"}

def norm(s): return re.sub(r"\s+","",unicodedata.normalize("NFKC",str(s))).lower()
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def path1(ps): return next((p for p in ps if p.exists()),None)

class R:
 def __init__(self,w,m,phase): self.w=w; self.m=m; self.phase=phase; self.e=[]; self.h=[]; self.warn=[]; self.c={}
 def err(self,g,c,s): self.e.append(f"[{g}][{c}] {s}")
 def hold(self,g,c,s): self.h.append(f"[{g}][{c}] {s}")
 def status(self): return "FAIL" if self.e else "HOLD_SOURCE_REQUIRED" if self.h else "PASS"
 def out(self): return {"schema":"EXT6_PHASE02_SEED_GATE_REPORT_V1","work_id":self.w,"derivation_mode":self.m,"phase":self.phase,"status":self.status(),"errors":self.e,"holds":self.h,"warnings":self.warn,"counts":self.c}

def keys(r,o,k,label,g="A",code="A1"):
 if not isinstance(o,dict): r.err(g,code,f"{label} not object"); return False
 if set(o)!=k: r.err(g,code,f"{label} key mismatch missing={sorted(k-set(o))} extra={sorted(set(o)-k)}"); return False
 return True

def text(r,v,label,g="A",c="A3"):
 if not isinstance(v,str) or not v.strip(): r.err(g,c,f"{label} empty/non-string"); return False
 if v.strip().upper() in BAD: r.err(g,c,f"{label} placeholder"); return False
 return True

def span(r,m,v,label):
 if not isinstance(v,list) or not v or not all(isinstance(x,int) and x>0 for x in v): r.err("A","A6",f"{label} invalid"); return []
 if v!=sorted(set(v)): r.err("A","A6",f"{label} not sorted unique")
 if m=="EP01_02_BLIND" and v!=[1,2]: r.err("A","A6",f"blind span must [1,2], got {v}")
 if m=="FULL_READ" and v[:2]!=[1,2]: r.err("A","A6","full read must include EP01-02")
 return v

def bridge(root,w):
 p=path1([root/"authored_bridge"/f"{w}.bridge.jsonl",root/"ext6_entity_bridge"/f"{w}.entity_bridge.jsonl"])
 return (p,{str(x.get("character_key")) for x in readjl(p) if x.get("character_key")}) if p else (None,set())
def scfile(root,w,ep): return path1([root/"authored"/f"{w}_{ep:02d}.seqcard.jsonl",root/"stage01"/f"{w}_{ep:02d}.seqcard.jsonl"])
def corpus(root):
 s=set(); d=root/"authored_bridge"
 if d.exists(): s|={p.name.removesuffix(".bridge.jsonl") for p in d.glob("*.bridge.jsonl")}
 d=root/"authored"
 if d.exists():
  for p in d.glob("*.seqcard.jsonl"):
   m=re.match(r"(.+)_\d{2}\.seqcard\.jsonl$",p.name)
   if m:s.add(m.group(1))
 return s

def src(source,ref,w,ep):
 return path1([source/Path(ref),source/"original_extracted"/w/f"{w}_{ep:02d}.txt",source/w/f"{w}_{ep:02d}.txt",source/f"{w}_{ep:02d}.txt"])

def validate_seed(r,s,bkeys,scenes):
 refs=[]
 if not keys(r,s,K["seed"],"seed"): return refs
 if s["work_id"]!=r.w or s["derivation_mode"]!=r.m:r.err("A","A4","seed grain mismatch")
 rs=span(r,r.m,s["read_span"],"seed.read_span")
 a=s["evidenced_initial_configuration"]
 if not isinstance(a,list) or not a:r.err("A","A3","initial configuration empty")
 else:
  for i,x in enumerate(a):
   if keys(r,x,N["initial"],f"initial[{i}]"):
    text(r,x["character_key"],f"initial[{i}].character_key"); text(r,x["initial_position"],f"initial[{i}].initial_position"); text(r,x["initial_relation_axis"],f"initial[{i}].axis")
    if bkeys and x["character_key"] not in bkeys:r.err("A","A5",f"Bridge FK missing {x['character_key']}")
    refs.append((f"initial[{i}]",x["evidence_ref"]))
 a=s["evidenced_world_constraints"]
 if not isinstance(a,list) or not a:r.err("A","A3","world constraints empty")
 else:
  for i,x in enumerate(a):
   if keys(r,x,N["constraint"],f"constraint[{i}]"):
    text(r,x["rule"],f"constraint[{i}].rule")
    if x["scope"] not in SCOPES:r.err("A","A2",f"bad scope {x['scope']}")
    refs.append((f"constraint[{i}]",x["evidence_ref"]))
 d=s["evidenced_opening_disturbance"]
 if keys(r,d,N["disturbance"],"disturbance"):
  text(r,d["summary"],"disturbance.summary")
  if not isinstance(d["scene_no"],int) or d["scene_no"]<1:r.err("A","A3","disturbance.scene_no invalid")
  refs.append(("disturbance",d["evidence_ref"]))
 for k in ("judged_logline","judged_central_lack","judged_governing_question","judged_central_opposition_axis"): text(r,s[k],k)
 if s["judged_ending_direction"] not in END:r.err("A","A2","bad ending direction")
 c=s["judged_cost_structure"]
 if keys(r,c,N["cost"],"cost"):
  if c["cost_type"] not in CT:r.err("A","A2","bad cost_type")
  if c["cost_bearer"] not in CB:r.err("A","A2","bad cost_bearer")
  text(r,c["cost_summary"],"cost_summary")
 text(r,s["contract_version"],"contract_version"); text(r,s["by"],"by")
 judged=[s["judged_logline"],s["judged_central_lack"],s["judged_governing_question"],s["judged_central_opposition_axis"],c.get("cost_summary","") if isinstance(c,dict) else ""]
 for t in judged:
  if NUM.search(str(t)):r.err("C","C1",f"number leakage {t!r}")
  if "evidence_ref" in str(t):r.err("B","B6","evidence wrapper in judged field")
  nt=norm(t)
  for ck in bkeys:
   n=norm(ck.split(":")[-1])
   if len(n)>=2 and n in nt:r.err("C","C1",f"proper name leakage {ck.split(':')[-1]}"); break
 for label,e in refs:
  m=EV.match(str(e).strip())
  if not m:continue
  ep,sc=int(m["ep"]),int(m["sc"])
  if ep not in rs:r.err("B","B4",f"{label} episode outside read_span")
  if ep in scenes and sc not in scenes[ep]:r.err("A","A5",f"{label} scene FK missing EP{ep:02d}-S{sc}")
 r.c["evidence_refs"]=len(refs); return refs

def validate_adm(r,a,works):
 if not keys(r,a,K["adm"],"admissibility"):return
 if a["work_id"]!=r.w or a["derivation_mode"]!=r.m:r.err("A","A4","admissibility grain mismatch")
 ids=a["compatible_work_ids"]
 if not isinstance(ids,list) or not all(isinstance(x,str) and x for x in ids):r.err("A","A3","compatible_work_ids invalid"); ids=[]
 if len(ids)!=len(set(ids)):r.err("A","A4","duplicate compatible_work_ids")
 if a["compatibility_count"]!=len(ids):r.err("A","A3","compatibility_count mismatch")
 miss=set(ids)-works
 if works and miss:r.err("A","A7",f"corpus IDs missing {sorted(miss)[:10]}")
 al=a["alternative_structures"]
 if not isinstance(al,list) or len(al)<3:r.err("C","C2","need >=3 alternative structures")
 else:
  for i,x in enumerate(al):
   if keys(r,x,N["alt"],f"alternative[{i}]"):text(r,x["sketch"],f"alternative[{i}].sketch","C","C2");text(r,x["divergence_point"],f"alternative[{i}].divergence","C","C2")
 vv=a["specificity_violations"]
 if not isinstance(vv,list):r.err("A","A3","specificity_violations invalid")
 else:
  for i,x in enumerate(vv):
   if keys(r,x,N["viol"],f"violation[{i}]") and x["violation_type"] not in VT:r.err("A","A2","bad violation type")
  if vv:r.err("C","C1",f"specificity violations={len(vv)}")
 n=len(ids); exp="TOO_SPECIFIC" if n<=1 else "ADMISSIBLE" if n<=10 else "REVIEW" if n<=30 else "TOO_VAGUE"
 if a["verdict"] not in VER:r.err("A","A2","bad verdict")
 if a["verdict"]!=exp:r.err("C","C3",f"verdict {a['verdict']} expected {exp}")
 if a["verdict"]!="ADMISSIBLE":r.err("C","C3","pilot seal requires ADMISSIBLE")
 r.c["alternative_structures"]=len(al) if isinstance(al,list) else 0

def validate_run(r,m,seedp,source):
 if not keys(r,m,K["run"],"run manifest"):return
 if m["work_id"]!=r.w or m["derivation_mode"]!=r.m:r.err("A","A4","run grain mismatch")
 span(r,r.m,m["read_span"],"manifest.read_span")
 for k in ("run_id","provider","model_id","sealed_at","content_sha256","by"):text(r,m[k],f"manifest.{k}")
 refs,hs=m["source_file_refs"],m["source_sha256s"]
 if not isinstance(refs,list) or not all(isinstance(x,str) and x for x in refs):r.err("A","A3","source_file_refs invalid");refs=[]
 if not isinstance(hs,dict) or set(hs)!=set(refs) or not all(re.fullmatch(r"[0-9a-f]{64}",str(x)) for x in hs.values()):r.err("A","A3","source_sha256s invalid");hs={}
 if sha(seedp)!=m["content_sha256"]:r.err("A","A8","seed content SHA mismatch")
 if r.m=="EP01_02_BLIND":
  if m["downstream_layers_blocked"] is not True:r.err("C","C4","downstream block not true")
  if m["cross_provider_outputs_blocked"] is not True:r.err("C","C6","provider block not true")
  bl=m["downstream_blocklist"]
  if not isinstance(bl,list):r.err("C","C4","blocklist invalid");bl=[]
  for token in ("CharacterArc","RelationshipArc","FullSeriesArc","Stage04","Seed FULL_READ"):
   if not any(token.lower() in str(x).lower() for x in bl):r.err("C","C4",f"blocklist missing {token}")
  if m["prior_mode_ref"] not in (None,""):r.err("C","C5","blind prior_mode_ref must be null")
 if r.m=="FULL_READ" and (not isinstance(m["prior_mode_ref"],str) or "EP01_02_BLIND" not in m["prior_mode_ref"]):r.err("C","C5","FULL_READ missing prior blind seal")
 if source is None:r.hold("B","B0","--source-root required");return
 for ref in refs:
  mm=re.search(r"_(\d{2})(?:\D|$)",Path(ref).stem); ep=int(mm[1]) if mm else m["read_span"][0]
  p=src(source,ref,r.w,ep)
  if not p:r.err("B","B7",f"source missing {ref}")
  elif hs.get(ref) and sha(p)!=hs[ref]:r.err("B","B7",f"source SHA mismatch {ref}")
 r.c["source_files"]=len(refs)

def verify_refs(r,refs,m,source):
 if source is None:return
 cache={}
 for label,e in refs:
  if not text(r,e,f"{label}.evidence","B","B1"):continue
  mm=EV.match(e.strip())
  if not mm:r.err("B","B2",f"bad evidence format {label}");continue
  ep,ln,q=int(mm["ep"]),int(mm["ln"]),mm["q"]
  if len(norm(q))<8:r.err("B","B3",f"quote too short {label}");continue
  file_ref=next((x for x in m.get("source_file_refs",[]) if re.search(fr"_{ep:02d}(?:\D|$)",Path(x).stem)),"")
  p=src(source,file_ref,r.w,ep)
  if not p:r.err("B","B3",f"cannot resolve EP{ep:02d}");continue
  if p not in cache:cache[p]=p.read_text(encoding="utf-8").splitlines()
  lines=cache[p]; lo=max(1,ln-3);hi=min(len(lines),ln+3);nq=norm(q)
  if not any(nq in norm(lines[i-1]) or (norm(lines[i-1]) and norm(lines[i-1]) in nq) for i in range(lo,hi+1)):r.err("B","B3",f"line mismatch {label} EP{ep:02d} L{ln}")

def evaluate(r,root):
 pp=root/"derived_seed_prediction"/f"{r.w}.pred.jsonl"
 if not pp.exists():r.hold("D","D0",f"missing {pp}")
 else:
  rows=[x for x in readjl(pp) if x.get("work_id")==r.w and x.get("derivation_mode")==r.m]; seen=set()
  for i,x in enumerate(rows):
   if not keys(r,x,K["pred"],f"prediction[{i}]"):continue
   g=(x["work_id"],x["derivation_mode"],x["indicator"])
   if g in seen:r.err("A","A4",f"duplicate prediction {g}")
   seen.add(g)
   if x["indicator"] not in IND:r.err("A","A2","bad indicator")
   if not isinstance(x["match"],bool):r.err("A","A3","match not bool")
   if not isinstance(x["corpus_prior"],(int,float)) or not 0<=x["corpus_prior"]<=1:r.err("A","A3","corpus_prior invalid")
   if x["by"]!="derived_deterministic":r.err("A","A3","prediction by invalid")
  if {x.get("indicator") for x in rows}!=IND or len(rows)!=5:r.err("A","A9","need exactly five indicators")
  r.c["prediction_rows"]=len(rows)
 cp=root/"derived_seed_contamination"/f"{r.w}.contam.json"
 if not cp.exists():r.hold("D","D0",f"missing {cp}")
 else:
  x=readj(cp)
  if keys(r,x,K["contam"],"contamination"):
   try: exp=round(float(x["mode_c_prediction_accuracy"])-float(x["mode_b_prediction_accuracy"]),10)
   except Exception:r.err("A","A3","accuracy/leakage nonnumeric")
   else:
    if abs(float(x["leakage_estimate"])-exp)>1e-9:r.err("A","A10",f"leakage formula mismatch expected {exp}")

def run(a):
 root=Path(a.root).resolve(); source=Path(a.source_root).resolve() if a.source_root else None; r=R(a.work,a.mode,a.phase)
 ps={n:root/d/f for n,d,f in [("seed","advisory_seed",f"{a.work}.{a.mode}.seed.json"),("adm","advisory_seed_admissibility",f"{a.work}.{a.mode}.adm.json"),("run","advisory_seed_runs",f"{a.work}.{a.mode}.run.json")]}
 for n,p in ps.items():
  if not p.exists():r.err("A","A0",f"missing {n}: {p}")
 if r.e:return r
 try:s,ad,m=readj(ps["seed"]),readj(ps["adm"]),readj(ps["run"])
 except Exception as e:r.err("A","A0",f"parse error {e}");return r
 bp,bk=bridge(root,a.work)
 if not bp:r.err("A","A5","EntityBridge missing")
 scenes={}
 for ep in s.get("read_span",[]):
  p=scfile(root,a.work,ep)
  if not p:r.err("A","A5",f"SceneCard missing EP{ep:02d}")
  else:
   try:scenes[ep]={int(x["scene_no"]) for x in readjl(p)}
   except Exception as e:r.err("A","A0",f"SceneCard parse EP{ep:02d}: {e}")
 refs=validate_seed(r,s,bk,scenes);validate_adm(r,ad,corpus(root));validate_run(r,m,ps["seed"],source);verify_refs(r,refs,m,source)
 if a.phase=="evaluate":evaluate(r,root)
 return r

def main():
 p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--work",required=True);p.add_argument("--mode",required=True,choices=sorted(MODES));p.add_argument("--phase",choices=("seal","evaluate"),default="seal");p.add_argument("--source-root");p.add_argument("--json-out");a=p.parse_args();r=run(a);o=r.out();print(json.dumps(o,ensure_ascii=False,indent=2))
 if a.json_out:Path(a.json_out).write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return 1 if r.e else 3 if r.h else 0
if __name__=="__main__":sys.exit(main())
