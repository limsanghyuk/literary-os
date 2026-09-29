#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
ARCH=ROOT/"R77_H1_PA8_C_FRESH_EPISODE_ARCHITECTURE_R2.json"
CONTROL=ROOT/"PA8_D_CONTROL_FIRST_OUTPUT_RAW_R1.txt"
TREATMENT=ROOT/"PA8_D_TREATMENT_FIRST_OUTPUT_RAW_R1.txt"
OUT=ROOT/"PA8_D_PAIRED_MECHANICAL_RESULT_R1.json"

LEAK_TOKENS=[
 "PA8","ESCC","ESGC","CONTROL","TREATMENT","experiment","validator",
 "arm mapping","provider analog","semantic_payload_sha256","research/interventions"
]
ALIASES={
 "B2_STACKS":["지하 B2 서고","B2 서고","지하 서고"],
 "FREIGHT_ELEVATOR":["화물 엘리베이터","화물승강기"],
 "GROUND_STAGING":["지상 스테이징","지상 임시 적치구역","지상 적치구역"],
 "SERVER_ROOM":["서버실","서버 룸"],
 "LOADING_DOCK":["로딩독","하역장"],
 "CONSERVATION_LAB":["보존실","보존 처리실"],
 "COURTYARD":["안뜰","중정","외부 대기선","기록관 외부 대기선"]
}

SEQ_RE=re.compile(r"(?im)^\s*(?:시퀀스|SEQUENCE)\s*([1-9])\b")
SCENE_RE=re.compile(r"(?im)^\s*(?:씬\s*([1-9]|[1-4][0-9]|50)\s*\.|SCENE\s*([1-9]|[1-4][0-9]|50)\s*\.|SC\s*0?([1-9]|[1-4][0-9]|50)\b).*?$")
TIME_RE=re.compile(r"(?<!\d)([01]\d|2[0-3]):([0-5]\d)(?!\d)")

def sha_text(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

def scene_spans(text):
    matches=list(SCENE_RE.finditer(text))
    out=[]
    for i,m in enumerate(matches):
        n=next(int(g) for g in m.groups() if g is not None)
        start=m.start()
        end=matches[i+1].start() if i+1<len(matches) else len(text)
        block=text[start:end]
        out.append((n,m.group(0),block))
    return out

def dup_scene_bodies(spans):
    seen={}
    dup=[]
    for n,_,block in spans:
        body="\n".join(block.splitlines()[1:]).strip()
        key=hashlib.sha256(body.encode("utf-8")).hexdigest()
        if body and key in seen: dup.append([seen[key],n])
        elif body: seen[key]=n
    return dup

def metadata_hits(text):
    low=text.lower()
    return [t for t in LEAK_TOKENS if t.lower() in low]

def parse_time_from_scene(header,block):
    m=TIME_RE.search(header)
    if m: return f"{m.group(1)}:{m.group(2)}"
    lines=block.splitlines()
    for line in lines[1:3]:
        m=TIME_RE.search(line)
        if m: return f"{m.group(1)}:{m.group(2)}"
    return None

def validate_arm(name,text,arch,treatment=False):
    spans=scene_spans(text)
    scene_nums=[x[0] for x in spans]
    seq_nums=[int(x) for x in SEQ_RE.findall(text)]
    result={
      "arm":name,
      "chars":len(text),
      "sha256_utf8":sha_text(text),
      "sequence_headings":len(seq_nums),
      "sequence_numbers":seq_nums,
      "scene_headings":len(spans),
      "scene_numbers":scene_nums,
      "metadata_leak_hits":metadata_hits(text),
      "duplicate_scene_pairs":dup_scene_bodies(spans),
    }
    gates={
      "chars_ge_40000":len(text)>=40000,
      "sequence_headings_9":len(seq_nums)==9 and seq_nums==list(range(1,10)),
      "scene_headings_50":len(spans)==50,
      "scene_numbers_exact":scene_nums==list(range(1,51)),
      "metadata_leaks_0":len(result["metadata_leak_hits"])==0,
      "duplicate_full_scene_bodies_0":len(result["duplicate_scene_pairs"])==0,
    }
    if treatment:
        by_scene={n:(hdr,block) for n,hdr,block in spans}
        time_rows=[]
        location_rows=[]
        for s in arch["scene_contracts"]:
            n=int(s["scene"])
            expected_time=s["spacetime"]["clock"]
            expected_loc=s["spacetime"]["location_id"]
            hdr,block=by_scene.get(n,("",""))
            observed=parse_time_from_scene(hdr,block) if hdr else None
            time_rows.append({"scene":n,"expected":expected_time,"observed":observed,"pass":observed==expected_time})
            preview="\n".join(block.splitlines()[:3])
            aliases=ALIASES.get(expected_loc,[])
            location_rows.append({"scene":n,"expected_location_id":expected_loc,"aliases":aliases,
                                  "pass":any(a in preview for a in aliases),"preview":preview[:300]})
        gates["treatment_clock_50_of_50"]=all(r["pass"] for r in time_rows) and len(time_rows)==50
        gates["treatment_location_50_of_50"]=all(r["pass"] for r in location_rows) and len(location_rows)==50
        result["treatment_clock_rows"]=time_rows
        result["treatment_location_rows"]=location_rows
    result["gates"]=gates
    result["status"]="PASS" if all(gates.values()) else "FAIL"
    return result

def main():
    if not CONTROL.exists() or not TREATMENT.exists():
        missing=[str(p.name) for p in [CONTROL,TREATMENT] if not p.exists()]
        print(json.dumps({"status":"HOLD__MISSING_FIRST_OUTPUTS","missing":missing},ensure_ascii=False))
        return 2
    arch=json.loads(ARCH.read_text(encoding="utf-8"))
    c=CONTROL.read_text(encoding="utf-8")
    t=TREATMENT.read_text(encoding="utf-8")
    cr=validate_arm("CONTROL",c,arch,False)
    tr=validate_arm("TREATMENT",t,arch,True)
    shorter=min(cr["chars"],tr["chars"])
    diff=abs(cr["chars"]-tr["chars"])
    paired_ratio=(diff/shorter) if shorter else 999.0
    paired_gate=paired_ratio<=0.10
    result={
      "schema":"PA8_D_PAIRED_MECHANICAL_RESULT_R1",
      "status":"PASS" if cr["status"]=="PASS" and tr["status"]=="PASS" and paired_gate else "FAIL",
      "control":cr,
      "treatment":tr,
      "paired":{"absolute_char_diff":diff,"difference_over_shorter":paired_ratio,"gate_le_0_10":paired_gate},
      "human_target_accessed":False,
      "authority_effect":"NONE",
      "next_if_pass":"Build PA8-E blind judge packets from frozen sample SC05/SC13/SC21/SC30/SC39/SC47.",
      "next_if_fail":"Preserve first outputs. Apply only previously preregistered arm-local repair procedure where eligible."
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0 if result["status"]=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
