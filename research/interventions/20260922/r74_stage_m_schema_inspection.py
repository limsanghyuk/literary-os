import base64, gzip, json, pathlib, hashlib

ROOT = pathlib.Path(__file__).resolve().parents[3]

FILES = {
    "R68": ROOT / "research/interventions/20260920/R68_FRESH_PRIMARY_CASES_R1.json.gz.b64",
    "R69": ROOT / "research/interventions/20260921/R69_FRESH_PRIMARY_CASES_R1.json.gz.b64",
}

out = {"schema":"R74_STAGE_M_FROZEN_CASE_SCHEMA_INSPECTION_R1","sets":{}}
for rid, path in FILES.items():
    b64 = path.read_text(encoding="utf-8").strip()
    raw = gzip.decompress(base64.b64decode(b64))
    obj = json.loads(raw.decode("utf-8"))
    summary = {
        "decoded_sha256": hashlib.sha256(raw).hexdigest(),
        "top_type": type(obj).__name__,
    }
    if isinstance(obj, dict):
        summary["top_keys"] = sorted(obj.keys())
        # Bounded structural summary only.
        for k,v in obj.items():
            if isinstance(v,list):
                summary.setdefault("list_fields",{})[k] = {
                    "len": len(v),
                    "first_type": type(v[0]).__name__ if v else None,
                    "first_keys": sorted(v[0].keys()) if v and isinstance(v[0],dict) else None,
                }
            elif isinstance(v,dict):
                summary.setdefault("dict_fields",{})[k] = sorted(v.keys())[:100]
    elif isinstance(obj, list):
        summary["len"] = len(obj)
        summary["first_type"] = type(obj[0]).__name__ if obj else None
        summary["first_keys"] = sorted(obj[0].keys()) if obj and isinstance(obj[0],dict) else None
        # Include one redacted structural record with scalar values and nested keys only.
        if obj and isinstance(obj[0],dict):
            fr={}
            for k,v in obj[0].items():
                if isinstance(v,(str,int,float,bool)) or v is None:
                    fr[k]=v
                elif isinstance(v,dict):
                    fr[k]={"__keys__":sorted(v.keys())}
                elif isinstance(v,list):
                    fr[k]={"__list_len__":len(v),"first_keys":sorted(v[0].keys()) if v and isinstance(v[0],dict) else None}
            summary["first_record_structure"]=fr
    out["sets"][rid]=summary

dest = pathlib.Path("/tmp/R74_STAGE_M_FROZEN_CASE_SCHEMA_INSPECTION_R1.json")
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(dest.read_text(encoding="utf-8"))
