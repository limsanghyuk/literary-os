"""test_v786 — 클라우드 저장 + 실측 학습 노드 (V786, ADR-247). TC01~15."""
import tempfile, os
from literary_system.finetune.cloud_storage import PresignedHttpStore, encrypt_bytes, decrypt_bytes, CloudStore
from literary_system.finetune.cloud_training_node import CloudTrainingNode, CloudNodeReport
from literary_system.finetune.runpod_real_adapter import RealRunPodAdapter

def _store(blob, key="SECRET"):
    def url(k,op): return f"https://store/{k}?{op}"
    def tr(m,u,h,b):
        kk=u.split("/store/")[1].split("?")[0]
        if m=="PUT": blob[kk]=b; return 201,b""
        if m=="GET": return 200,blob.get(kk,b"LORA_BYTES")
        if m=="DELETE": blob.pop(kk,None); return 204,b""
        return 400,b""
    return PresignedHttpStore(url, encrypt_key=key, transport=tr)
def _rp():
    def tr(m,u,h,b):
        if m=="GET" and u.endswith("/pods"): return 200,[]
        if m=="POST": return 201,{"id":"pod_x"}
        if m=="GET": return 200,{"desiredStatus":"EXITED"}
        return 404,{}
    return RealRunPodAdapter(api_key="rpa_K", transport=tr)
def _pairs():
    fd,p=tempfile.mkstemp(suffix=".jsonl"); os.write(fd,'{"draft":"d","ref":"명작 verbatim"}'.encode()); os.close(fd); return p

# 암호화
def test_tc01_encrypt_roundtrip():
    d="명작 텍스트".encode(); assert decrypt_bytes(encrypt_bytes(d,"K"),"K")==d
def test_tc02_encrypt_changes_bytes():
    d=b"hello world data"; assert encrypt_bytes(d,"K")!=d
def test_tc03_wrong_key_fails():
    d=b"secret"; assert decrypt_bytes(encrypt_bytes(d,"K1"),"K2")!=d
# 저장
def test_tc04_put_encrypts():
    blob={}; st=_store(blob); st.put(_pairs())
    assert all(b"verbatim" not in v for v in blob.values())   # 평문 미노출
def test_tc05_put_get_roundtrip():
    blob={}; st=_store(blob); p=_pairs(); url=st.put(p)
    fd,d=tempfile.mkstemp();os.close(fd); assert st.get(url,d) and open(p,encoding="utf-8").read()==open(d,encoding="utf-8").read()
def test_tc06_cleanup_deletes():
    blob={}; st=_store(blob); st.put(_pairs()); assert st.cleanup()==1 and len(blob)==0
def test_tc07_url_for():
    st=_store({}); assert "get" in st.url_for("k","get")
def test_tc08_is_cloudstore():
    assert isinstance(_store({}), CloudStore)
# 노드
def test_tc09_node_completed():
    blob={}; r=CloudTrainingNode(_rp(),_store(blob),max_polls=2).run(_pairs(),"Qwen",dry_run=False)
    assert r.status=="completed" and isinstance(r,CloudNodeReport)
def test_tc10_node_auto_delete():
    blob={}; r=CloudTrainingNode(_rp(),_store(blob),max_polls=2).run(_pairs(),"Qwen",dry_run=False)
    assert r.deleted>=1 and len(blob)==0   # 저작권 안전: 자동삭제
def test_tc11_node_delta_w():
    r=CloudTrainingNode(_rp(),_store({}),max_polls=2).run(_pairs(),"Qwen",dry_run=False,w0=0.588,measured_w1=0.64)
    assert r.delta_w==0.052
def test_tc12_node_gate_adopt():
    r=CloudTrainingNode(_rp(),_store({}),max_polls=2).run(_pairs(),"Qwen",dry_run=False,w0=0.5,measured_w1=0.7,kl=0.05)
    assert r.gate and r.gate["decision"]=="adopt"
def test_tc13_node_dry_run_planned():
    assert CloudTrainingNode(_rp(),_store({})).run(_pairs(),"Qwen",dry_run=True).status=="planned"
def test_tc14_node_to_dict():
    assert "delta_w" in CloudTrainingNode(_rp(),_store({}),max_polls=2).run(_pairs(),"Qwen",dry_run=False,w0=0.5,measured_w1=0.6).to_dict()
def test_tc15_export():
    import literary_system.finetune as F
    assert hasattr(F,"CloudTrainingNode") and hasattr(F,"PresignedHttpStore")
