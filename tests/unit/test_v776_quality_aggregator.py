"""test_v776 — 다신호 2축 자동 집계 (V776, ADR-236). TC01~14."""
from literary_system.quality.quality_aggregator import (
    AggInput, aggregate, build_labels, from_drama_dict, label_summary,
    commercial_from_viewership, craft_from_expert, CHANNEL_CEILING)
from literary_system.quality.quality_labels import QualityTier

def test_tc01_craft_from_expert():
    assert craft_from_expert(4)==1.0 and craft_from_expert(2)==0.5
def test_tc02_craft_award_bonus():
    assert craft_from_expert(3, awards=2) > 0.75
def test_tc03_commercial_terrestrial():
    assert commercial_from_viewership(45, "KBS")==1.0
def test_tc04_channel_correction_cable():
    # 케이블 8.2%가 지상파 8.2%보다 높게 보정
    assert commercial_from_viewership(8.2,"tvN") > commercial_from_viewership(8.2,"KBS")
def test_tc05_aggregate_drama():
    l=aggregate(AggInput("태양의후예",3,viewership_pct=38.8,channel="KBS"))
    assert l.positive_target  # 흥행작 → 명작 계열
def test_tc06_aggregate_film_boxoffice():
    l=aggregate(AggInput("살인의추американ",4,admissions_10k=500,awards=2))
    assert l.craft==1.0 and 0<l.commercial<=1.0
def test_tc07_poor_both_low():
    l=aggregate(AggInput("졸작",1,viewership_pct=13,channel="SBS"))
    assert l.tier==QualityTier.POOR
def test_tc08_independent_axes():
    # 흥행 높아도 craft는 expert만 반영(인기≠작품성)
    l=aggregate(AggInput("흥행평범",2,viewership_pct=45,channel="KBS"))
    assert l.craft==0.5 and l.commercial==1.0
def test_tc09_from_drama_dict():
    labels=from_drama_dict({"미생":(8.2,4,"tvN"),"알게될거야":(13,1,"SBS")})
    assert len(labels)==2 and labels[0].positive_target and labels[1].is_poor
def test_tc10_summary_no_double_count():
    labels=from_drama_dict({"a":(13,1,"SBS"),"b":(13,1,"SBS")})  # 둘 다 poor
    s=label_summary(labels)
    assert s["poor"]==2 and s["tiers"]["poor"]==2  # 이중계수 없음
def test_tc11_real_meta_gt_runs():
    import importlib.util
    from pathlib import Path
    p=Path("docs/sessions/2026-06-13_corpus_ko_build/experiments/meta_gt_drama.py")
    sp=importlib.util.spec_from_file_location("m",p); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    labels=from_drama_dict(m.DRAMA)
    s=label_summary(labels)
    assert s["total"]>=29 and s["positive_target"]>0 and s["poor"]>0
def test_tc12_deterministic():
    a=aggregate(AggInput("x",3,viewership_pct=20,channel="MBC"))
    b=aggregate(AggInput("x",3,viewership_pct=20,channel="MBC"))
    assert a.to_dict()==b.to_dict()
def test_tc13_taeyang_positive_in_engine():
    labels=from_drama_dict({"태양의후예":(38.8,3,"KBS")})
    assert labels[0].positive_target  # 사용자 정정 엔진서도 유지
def test_tc14_export():
    import literary_system.quality as Q
    assert hasattr(Q,"from_drama_dict") and hasattr(Q,"aggregate")
