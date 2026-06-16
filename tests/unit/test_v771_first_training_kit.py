"""test_v771_first_training_kit — 4070 첫 학습 킷 (V771, ADR-231). TC01~12."""
import tempfile, json, os
from literary_system.learning.first_training_kit import (
    build_training_plan, prepare_dpo, make_smoke_dataset, baseline_winrate,
    winrate_delta, DEFAULT_BASE, MIN_RECOMMENDED_PAIRS)
from literary_system.learning.loop_c import load_preference_pairs

def _smoke(n=4):
    fd, p = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    make_smoke_dataset(p, n); return p

def test_tc01_smoke_raw_format():
    p = _smoke(4)
    rows = [json.loads(l) for l in open(p, encoding="utf-8")]
    assert len(rows) == 4 and {"func","genre","ref_id","winner","draft","ref"} <= set(rows[0])
def test_tc02_smoke_loadable():
    assert len(load_preference_pairs(_smoke(4))) == 4
def test_tc03_plan_keys():
    pl = build_training_plan(_smoke())
    assert {"n_pairs","baseline_winrate","base_model","vram_estimate_gb","fits_4070",
            "dpo_dataset","train_command","warnings"} <= set(pl)
def test_tc04_default_base_3b_fits():
    assert build_training_plan(_smoke())["fits_4070"] is True
    assert DEFAULT_BASE == "meta-llama/Llama-3.2-3B"
def test_tc05_small_data_warning():
    assert any("메커니즘 증명" in w for w in build_training_plan(_smoke(4))["warnings"])
def test_tc06_command_has_train_local():
    assert "literary_system.finetune.train_local" in build_training_plan(_smoke())["train_command"]
def test_tc07_prepare_dpo_standard():
    p = _smoke(4); fd, out = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    n = prepare_dpo(p, out)
    rows = [json.loads(l) for l in open(out, encoding="utf-8")]
    assert n == 4 and {"prompt","chosen","rejected"} <= set(rows[0])
def test_tc08_baseline_winrate_range():
    assert 0.0 <= baseline_winrate(load_preference_pairs(_smoke(4))) <= 1.0
def test_tc09_delta_improved():
    d = winrate_delta(0.588, 0.65); assert d["improved"] and d["verdict"] == "향상"
def test_tc10_delta_stagnant():
    d = winrate_delta(0.6, 0.55); assert not d["improved"] and d["moved"]
def test_tc11_oversize_model_warning():
    assert any("12GB" in w for w in build_training_plan(_smoke(), base_model="llama-70b")["warnings"])
def test_tc12_export():
    import literary_system.learning as L
    assert hasattr(L,"build_training_plan") and hasattr(L,"make_smoke_dataset")
