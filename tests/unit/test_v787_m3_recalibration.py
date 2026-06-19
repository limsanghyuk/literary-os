"""test_v787 — M3 실 corpus 재보정 (V787, ADR-248). TC01~12."""
from literary_system.critic.distribution_guard import (
    distribution_guard, distribution_guard_features, NORMAL_BANDS, CORPUS_FEATURE_BANDS, GuardResult)

def test_tc01_dialogue_band_fixed():
    # 실 corpus 재보정: 하한 0.0(이전 0.10 오보정)
    assert NORMAL_BANDS["dialogue_ratio"][0]==0.0 and NORMAL_BANDS["dialogue_ratio"][1]==0.76
def test_tc02_no_dialogue_scene_not_pathological():
    flat="그는 멈췄다. 복도를 걸었다. 문 앞에 섰다. 손잡이를 잡았다. 천천히 돌렸다. 안은 어두웠다. 그는 들어섰다. 발소리가 울렸다."
    assert not any(p["metric"]=="dialogue_ratio" for p in distribution_guard(flat).pathologies)
def test_tc03_corpus_bands_present():
    assert set(CORPUS_FEATURE_BANDS)>={"conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","dialogue_ratio"}
def test_tc04_corpus_bands_values():
    assert CORPUS_FEATURE_BANDS["conflict_intensity"]==(0.0,1.775)
    assert CORPUS_FEATURE_BANDS["motif_residue_score"]==(0.234,0.666)
def test_tc05_feature_guard_normal_zero():
    f={"conflict_intensity":0.4,"scene_energy_ratio":2.5,"motif_residue_score":0.46,"curiosity_gradient":0.33,"dialogue_ratio":0.0,"n_chars":300}
    assert distribution_guard_features(f).penalty==0.0
def test_tc06_feature_guard_conflict_outlier():
    f={"conflict_intensity":3.0,"motif_residue_score":0.46,"curiosity_gradient":0.33,"dialogue_ratio":0.0,"n_chars":300,"scene_energy_ratio":2.5}
    assert any(p["metric"]=="conflict_intensity" for p in distribution_guard_features(f).pathologies)
def test_tc07_feature_guard_motif_below():
    f={"motif_residue_score":0.1,"conflict_intensity":0.4,"scene_energy_ratio":2.5,"curiosity_gradient":0.33,"dialogue_ratio":0.0,"n_chars":300}
    assert any(p["metric"]=="motif_residue_score" and p["side"]=="below" for p in distribution_guard_features(f).pathologies)
def test_tc08_feature_guard_type():
    assert isinstance(distribution_guard_features({"conflict_intensity":0.4}), GuardResult)
def test_tc09_feature_guard_missing_keys_ok():
    # 일부 키만 있어도 동작(없는 키 무시)
    assert distribution_guard_features({"dialogue_ratio":0.3}).penalty==0.0
def test_tc10_feature_guard_reject():
    f={"conflict_intensity":5.0,"scene_energy_ratio":20.0,"motif_residue_score":0.05,"dialogue_ratio":0.95,"n_chars":3}
    assert distribution_guard_features(f, reject_threshold=-2.0).rejected
def test_tc11_no_positive_reward():
    f={"conflict_intensity":0.4,"scene_energy_ratio":2.5,"motif_residue_score":0.46,"curiosity_gradient":0.33,"dialogue_ratio":0.0,"n_chars":300}
    assert distribution_guard_features(f).penalty<=0.0   # 전형성 무보상
def test_tc12_export():
    import literary_system.critic as C
    assert hasattr(C,"distribution_guard_features") and hasattr(C,"CORPUS_FEATURE_BANDS")
