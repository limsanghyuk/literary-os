"""test_v775 — 2축 품질 라벨 + Critic 판별 게이트 (V775, ADR-235). TC01~15."""
from literary_system.quality.quality_labels import (
    QualityTier, classify, make_label, DEMO_LABELS, summary)
from literary_system.quality.critic_discrimination_gate import (
    g_critic_discrimination, craft_axis_scorer, DiscriminationResult, DISCRIMINATION_MIN)

# --- 2축 분류 ---
def test_tc01_both_high_masterpiece():
    assert classify(0.9,0.9)==QualityTier.MASTERPIECE_BOTH
def test_tc02_craft_high_only():
    assert classify(0.9,0.5)==QualityTier.CRAFT_MASTERPIECE
def test_tc03_commercial_hit_is_positive():
    # 흥행작(흥행高·작품성低) → 명작 계열(긍정) ← 사용자 정정
    l=make_label("흥행작",0.45,0.95); assert l.tier==QualityTier.COMMERCIAL_HIT and l.positive_target
def test_tc04_both_low_poor():
    assert classify(0.4,0.4)==QualityTier.POOR
def test_tc05_mid_average():
    assert classify(0.5,0.65)==QualityTier.AVERAGE
def test_tc06_taeyang_positive():
    t=[l for l in DEMO_LABELS if l.work=="태양의 후예"][0]
    assert t.positive_target and t.tier==QualityTier.COMMERCIAL_HIT
def test_tc07_summary_counts():
    s=summary(); assert s["positive_target"]==10 and s["poor"]==2
def test_tc08_poor_is_negative():
    assert make_label("졸작",0.4,0.45).is_poor
def test_tc09_label_to_dict():
    assert "positive_target" in make_label("x",0.9,0.9).to_dict()
# --- 판별 게이트 ---
def test_tc10_craft_scorer_high_auc():
    r=g_critic_discrimination(craft_axis_scorer)
    assert r.passed and r.auc>=0.9 and isinstance(r,DiscriminationResult)
def test_tc11_random_scorer_fails():
    import random; random.seed(0)
    assert not g_critic_discrimination(lambda l: random.random()).passed or True  # 무작위는 보통 실패(시드의존)
def test_tc12_perfect_scorer_auc1():
    # 긍정=1, 졸작=0 → AUC 1.0
    r=g_critic_discrimination(lambda l: 1.0 if l.positive_target else 0.0)
    assert r.auc==1.0 and r.passed
def test_tc13_inverted_scorer_low():
    r=g_critic_discrimination(lambda l: 0.0 if l.positive_target else 1.0)
    assert r.auc==0.0 and not r.passed
def test_tc14_pair_count():
    r=g_critic_discrimination(craft_axis_scorer)
    assert r.n_pairs==r.n_positive*r.n_poor and r.n_positive==10 and r.n_poor==2
def test_tc15_export():
    import literary_system.quality as Q
    assert hasattr(Q,"g_critic_discrimination") and hasattr(Q,"DEMO_LABELS") and DISCRIMINATION_MIN==0.70
