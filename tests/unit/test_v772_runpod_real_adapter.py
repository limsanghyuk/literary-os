"""test_v772_runpod_real_adapter — RunPod 실 REST 어댑터 (V772, ADR-232). TC01~13."""
import json
from literary_system.finetune.runpod_real_adapter import (
    RealRunPodAdapter, make_real_runpod, RUNPOD_REST_BASE)
from literary_system.finetune.gpu_adapter import GPUJobRequest, GPUJobStatus, GPUProvider

def _req(dry=False, model="llama-3.2-3b"):
    return GPUJobRequest(model_name=model, dataset_path="/x/dpo.jsonl", hours_estimate=2.0, dry_run=dry)

def _fake(record, post_status=201, pod={"id": "pod_x"}):
    def t(method, url, headers, body):
        record.append({"method": method, "url": url, "auth": headers.get("Authorization"),
                       "body": json.loads(body) if body else None})
        if method == "GET" and url.endswith("/pods"): return 200, []
        if method == "POST": return post_status, pod
        if method == "GET": return 200, {"desiredStatus": "RUNNING"}
        return 404, {}
    return t

def test_tc01_provider(): assert RealRunPodAdapter().provider_id == GPUProvider.RUNPOD
def test_tc02_cost(): assert RealRunPodAdapter().estimate_cost(2) == 0.78
def test_tc03_rest_base(): assert RUNPOD_REST_BASE == "https://rest.runpod.io/v1"
def test_tc04_verify_key_true():
    rec = []; a = RealRunPodAdapter(api_key="rpa_K", transport=_fake(rec))
    assert a.verify_key() is True and rec[0]["auth"] == "Bearer rpa_K"
def test_tc05_verify_no_key_false():
    assert RealRunPodAdapter(api_key="").verify_key() is False
def test_tc06_launch_real_running():
    rec = []; a = RealRunPodAdapter(api_key="rpa_K", transport=_fake(rec, 201, {"id": "pod_abc"}))
    r = a.launch_job(_req())
    assert r.status == GPUJobStatus.RUNNING and r.metadata["pod_id"] == "pod_abc"
def test_tc07_launch_payload_has_env():
    rec = []; RealRunPodAdapter(api_key="rpa_K", transport=_fake(rec)).launch_job(_req())
    post = [c for c in rec if c["method"] == "POST"][0]
    assert post["body"]["env"]["BASE_MODEL"] == "llama-3.2-3b" and post["body"]["gpuCount"] == 1
def test_tc08_launch_bearer_header():
    rec = []; RealRunPodAdapter(api_key="rpa_SECRET", transport=_fake(rec)).launch_job(_req())
    assert all(c["auth"] == "Bearer rpa_SECRET" for c in rec)
def test_tc09_no_key_dry_run_no_network():
    rec = []; a = RealRunPodAdapter(api_key="", transport=_fake(rec))
    r = a.launch_job(_req(dry=False))
    assert r.status == GPUJobStatus.DRY_RUN and rec == []   # 네트워크 미호출
def test_tc10_dry_run_flag_safe():
    rec = []; a = RealRunPodAdapter(api_key="rpa_K", transport=_fake(rec))
    assert a.launch_job(_req(dry=True)).status == GPUJobStatus.DRY_RUN and rec == []
def test_tc11_api_error_failed():
    rec = []; a = RealRunPodAdapter(api_key="rpa_K", transport=_fake(rec, post_status=401, pod={"error": "unauthorized"}))
    r = a.launch_job(_req())
    assert r.status == GPUJobStatus.FAILED and "401" in r.error
def test_tc12_poll():
    rec = []; a = RealRunPodAdapter(api_key="rpa_K", transport=_fake(rec))
    assert a.poll("pod_abc")["pod_id"] == "pod_abc"
def test_tc13_key_not_in_result_dict():
    rec = []; a = RealRunPodAdapter(api_key="rpa_SECRET", transport=_fake(rec))
    d = json.dumps(a.launch_job(_req()).to_dict())
    assert "rpa_SECRET" not in d   # 키 누출 없음
