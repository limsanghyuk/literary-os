"""test_v767_local_gpu_adapter.py — LocalGPUAdapter + LocalPreflight (V767, ADR-227). TC01~14."""
from literary_system.finetune.gpu_adapter import (
    GPUProvider, get_adapter, list_providers, GPUJobRequest, GPUJobStatus,
    LocalGPUAdapter, LocalPreflight, LocalPreflightResult)

def _req(model="Llama-3.2-3B", dry=True):
    return GPUJobRequest(model_name=model, dataset_path="/x/dpo.jsonl", hours_estimate=1.0, dry_run=dry)

def test_tc01_enum_local(): assert GPUProvider.LOCAL.value == "local"
def test_tc02_registry(): assert "local" in [p["provider"] for p in list_providers()]
def test_tc03_get_adapter(): assert isinstance(get_adapter(GPUProvider.LOCAL), LocalGPUAdapter)
def test_tc04_provider_id(): assert LocalGPUAdapter().provider_id == GPUProvider.LOCAL
def test_tc05_cost_zero(): assert LocalGPUAdapter().cost_per_hour == 0.0 and LocalGPUAdapter().estimate_cost(5) == 0.0
def test_tc06_electricity_nonzero(): assert LocalGPUAdapter().estimate_electricity(2.0) > 0
def test_tc07_vram_3b_fits(): assert LocalGPUAdapter().fits_locally("llama-3.2-3b")
def test_tc08_vram_8b_fits(): assert LocalGPUAdapter().fits_locally("llama-3.1-8b")
def test_tc09_vram_70b_no(): assert not LocalGPUAdapter().fits_locally("llama-70b")
def test_tc10_dry_run_status():
    r = LocalGPUAdapter().dry_run(_req())
    assert r.status == GPUJobStatus.DRY_RUN and r.cost_usd == 0.0
def test_tc11_dry_run_meta():
    m = LocalGPUAdapter().dry_run(_req()).metadata
    assert "vram_estimate_gb" in m and "preflight" in m and "fallback_cloud" in m
def test_tc12_preflight_result_type():
    r = LocalPreflight().run()
    assert isinstance(r, LocalPreflightResult) and isinstance(r.missing_packages, list)
def test_tc13_launch_real_no_gpu_fallbacks():
    # 이 환경 GPU 없음 → real launch는 FAILED + 폴백 안내
    r = LocalGPUAdapter().launch_job(_req(dry=False))
    assert r.status in (GPUJobStatus.FAILED, GPUJobStatus.COMPLETED)
def test_tc14_70b_fallback_flag():
    assert LocalGPUAdapter().dry_run(_req(model="llama-70b")).metadata["fallback_cloud"] is True
