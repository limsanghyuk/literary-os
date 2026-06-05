#!/usr/bin/env python3
"""corpus_migrate.py — V21 Master DB(XML 덤프 docx) → v22 JSON L0 정규화.
입력: [V21.0 Master DB ...].docx 3종 / 출력: corpus_seed_L0.json (179 엔트리)
저장 대상은 '서사 DNA 분석'(verbatim 0, 저작권 안전)."""
import docx, glob, re, json, hashlib, datetime

def blob(fn):
    d=docx.Document(fn)
    return "\n".join(p.text for p in d.paragraphs)

def grab(seg, tag):
    m=re.search(r"<%s[^>]*>(.*?)</%s>"%(tag,tag), seg, re.S)
    return re.sub(r"\s+"," ",m.group(1)).strip() if m else None

def grab_all(seg, tag):
    out=[]
    for m in re.finditer(r'<%s id="([^"]*)"[^>]*>(.*?)</%s>'%(tag,tag), seg, re.S):
        out.append({"id":m.group(1).strip(), "desc":re.sub(r"\s+"," ",m.group(2)).strip()})
    return out

def style_modules(seg):
    out=[]
    for m in re.finditer(r'<Style_Module id="([^"]*)"[^>]*>(.*?)</Style_Module>', seg, re.S):
        out.append({"id":m.group(1).strip(), "dialogue_tone":grab(m.group(2),"Dialogue_Tone")})
    return out

entries=[]
for fn in sorted(glob.glob("*.docx")):
    t=blob(fn)
    src="film" if "영화" in fn else "drama"
    for em in re.finditer(r'<Drama_Entry id="([^"]+)" title="([^"]+)" genre="([^"]+)">(.*?)</Drama_Entry>', t, re.S):
        eid,title,genre,seg=em.group(1),em.group(2),em.group(3),em.group(4)
        e={
          "drama_id":eid, "title":title, "genre":genre,
          "engine_ver":"v22", "source_kind":"analysis", "media":src,
          "core_philosophy":{
             "master_theme":grab(seg,"Master_Theme"),
             "conflict_axis":grab(seg,"Conflict_Axis"),
             "core_dilemma":grab(seg,"Core_Dilemma")},
          "lorebook":{
             "characters":grab_all(seg,"Character"),
             "key_objects":grab_all(seg,"Key_Object")},
          "macro_causality":{
             "causality_matrix":{
                "trigger":grab(seg,"Trigger"),
                "resolution":grab(seg,"Resolution"),
                "residue":grab(seg,"Residue")},
             "tragic_engine":{
                "catastrophe_source":grab(seg,"Catastrophe_Source"),
                "logic_consistency":grab(seg,"Logic_Consistency")}},
          "rendering":{
             "style_modules":style_modules(seg),
             "critic_thresholds":{
                "logic_consistency":grab(seg,"Logic_Consistency"),
                "tone_penalty":grab(seg,"Tone_Penalty")}},
          "provenance":{
             "source_file":fn, "verbatim":False,
             "source_kind":"public_work_analysis",
             "sha256":hashlib.sha256((eid+title).encode()).hexdigest()[:16],
             "migrated_at":datetime.datetime.utcnow().isoformat()+"Z",
             "layer":"L0"}}
        entries.append(e)

json.dump(entries, open("corpus_seed_L0.json","w"), ensure_ascii=False, indent=1)
# 검증
def nz(x): return 1 if x else 0
print("총 엔트리:",len(entries))
print("media:", {m:sum(1 for e in entries if e['media']==m) for m in ('drama','film')})
miss_theme=sum(1 for e in entries if not e['core_philosophy']['master_theme'])
miss_caus=sum(1 for e in entries if not e['macro_causality']['causality_matrix']['trigger'])
chars=sum(len(e['lorebook']['characters']) for e in entries)
objs=sum(len(e['lorebook']['key_objects']) for e in entries)
print(f"인물 총 {chars} / 핵심오브제 {objs}")
print(f"누락 점검: master_theme 없음={miss_theme}, causality.trigger 없음={miss_caus}")
print("파일 크기:", __import__('os').path.getsize("corpus_seed_L0.json"), "bytes")
