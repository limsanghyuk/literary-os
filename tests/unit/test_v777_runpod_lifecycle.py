"""test_v777 — RunPod 운영 라이프사이클 (V777, ADR-237). TC01~13."""
from literary_system.finetune.runpod_real_adapter import RealRunPodAdapter
from literary_system.finetune.runpod_lifecycle import RunPodJobLifecycle, LifecycleReport, LifecycleStage, TERMINAL
from literary_system.finetune.gpu_adapter import GPUJobStatus

def _tr(post=201, pod={"id":"pod_x"}, poll="EXITED", rec=None):
    def t(m,u,h,b):
        if rec is not None: rec.append((m,u))
        if m=="GET" and u.endswith("/pods"): return 200,[]
        if m=="POST": return post,pod
        if m=="GET": return 200,{"desiredStatus":poll}
        return 404,{}
    return t
def _adp(**kw): return RealRunPodAdapter(api_key="rpa_K", transport=_tr(**kw))
_UP=lambda p:"https://s/"+p.split("/")[-1]; _DOWN=lambda u,d:True

def test_tc01_plan_when_no_key():
    r=RunPodJobLifecycle(RealRunPodAdapter(api_key="")).run("/x.jsonl","m",dry_run=True)
    assert r.status=="planned" and r.stages[0].name=="plan"
def test_tc02_plan_when_dry_run():
    r=RunPodJobLifecycle(_adp()).run("/x.jsonl","m",dry_run=True)
    assert r.status=="planned"
def test_tc03_full_completed():
    r=RunPodJobLifecycle(_adp(),uploader=_UP,downloader=_DOWN,max_polls=2).run("/x.jsonl","m",output_url="https://s/o",dry_run=False)
    assert r.status=="completed" and r.pod_id=="pod_x" and r.artifact_path
def test_tc04_stage_order():
    r=RunPodJobLifecycle(_adp(),uploader=_UP,downloader=_DOWN).run("/x.jsonl","m",output_url="https://s/o",dry_run=False)
    names=[s.name for s in r.stages]; assert names[:4]==["upload","launch","poll","retrieve"]
def test_tc05_upload_invoked():
    rec=[]; up=lambda p:(rec.append(p) or "https://s/u")
    RunPodJobLifecycle(_adp(),uploader=up,downloader=_DOWN).run("/data/dpo.jsonl","m",output_url="x",dry_run=False)
    assert rec==["/data/dpo.jsonl"]
def test_tc06_no_uploader_skip():
    r=RunPodJobLifecycle(_adp(),downloader=_DOWN).run("/x.jsonl","m",output_url="x",dry_run=False)
    assert any(s.name=="upload" and s.status=="skipped" for s in r.stages)
def test_tc07_launch_failed():
    r=RunPodJobLifecycle(_adp(post=401,pod={"error":"unauth"}),uploader=_UP).run("/x.jsonl","m",dry_run=False)
    assert r.status=="failed"
def test_tc08_poll_timeout():
    r=RunPodJobLifecycle(_adp(poll="RUNNING"),uploader=_UP,downloader=_DOWN,max_polls=2).run("/x.jsonl","m",output_url="x",dry_run=False)
    assert r.status=="failed" and any(s.name=="poll" and s.status=="timeout" for s in r.stages)
def test_tc09_poll_failed_status():
    r=RunPodJobLifecycle(_adp(poll="FAILED"),uploader=_UP).run("/x.jsonl","m",dry_run=False)
    assert r.status=="failed"
def test_tc10_retrieve_skipped_no_output():
    r=RunPodJobLifecycle(_adp(),uploader=_UP,downloader=_DOWN,max_polls=2).run("/x.jsonl","m",dry_run=False)  # output_url=""
    assert any(s.name=="retrieve" and s.status=="skipped" for s in r.stages)
def test_tc11_report_to_dict():
    d=RunPodJobLifecycle(_adp(),uploader=_UP,downloader=_DOWN).run("/x.jsonl","m",output_url="x",dry_run=False).to_dict()
    assert "stages" in d and "summary" in d
def test_tc12_terminal_set():
    assert "EXITED" in TERMINAL and "COMPLETED" in TERMINAL
def test_tc13_key_not_leaked():
    import json
    r=RunPodJobLifecycle(_adp(),uploader=_UP,downloader=_DOWN).run("/x.jsonl","m",output_url="x",dry_run=False)
    assert "rpa_K" not in json.dumps(r.to_dict())
