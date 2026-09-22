import json, os, pathlib, hashlib, zipfile, urllib.request, sys

event_path=os.environ["GITHUB_EVENT_PATH"]
event=json.loads(pathlib.Path(event_path).read_text())
body=(event.get("pull_request",{}).get("body") or "")
fields={}
for line in body.splitlines():
    if "=" in line:
        k,v=line.split("=",1)
        fields[k.strip()]=v.strip()
url=fields.get("transfer_url")
expected_size=int(fields.get("expected_size","0") or "0")
if not url:
    raise SystemExit("missing transfer_url")
target=pathlib.Path("transfer_payload.zip")
with urllib.request.urlopen(url, timeout=120) as r, target.open("wb") as w:
    while True:
        chunk=r.read(1024*1024)
        if not chunk: break
        w.write(chunk)
size=target.stat().st_size
sha=hashlib.sha256(target.read_bytes()).hexdigest()
if expected_size and size!=expected_size:
    raise SystemExit(f"size mismatch: {size} != {expected_size}")
with zipfile.ZipFile(target) as z:
    bad=z.testzip()
    names=[x.filename for x in z.infolist()]
result={
 "status":"PASS" if bad is None else "FAIL",
 "size_bytes":size,
 "sha256":sha,
 "entry_count":len(names),
 "crc_bad_entry":bad,
 "first_entries":names[:80],
}
pathlib.Path("r74_secure_transfer_probe_result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(0 if bad is None else 3)
