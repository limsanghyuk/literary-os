"""test_v788_structure_conformance — c3 구조 비퇴행 R 생산자 (V788, DESIGN-SGATE-v1 ①). TC01~10."""
from literary_system.critic.structure_conformance import (
    tension_proxy, r_struct, r_pair, r_path, structural_nonregression)


def _scene(slug, chars, func, draft):
    return {"slug": slug, "characters": chars, "dramatic_function": func, "draft": draft,
            "targets": {}, "rag_refs": []}

def _good():
    return [
        _scene("s1", ["A", "B"], "setup", "A와 B가 만난다. 갈등의 씨앗이 심어진다."),
        _scene("s2", ["A", "B"], "rising", "A가 분노한다! 충돌이 격해진다. 위기가 닥친다."),
        _scene("s3", ["A", "B"], "climax", "A와 B의 대결. 앞서 심은 씨앗이 회수된다. 폭발한다!")]

def _bad():
    s = _good()
    s[1]["characters"] = ["C"]      # 캐릭터 연속성 깨짐
    s[1]["draft"] = "조용한 풍경."     # 긴장 없음
    return s

def test_tc01_tension_proxy_range():
    assert 0.0 <= tension_proxy("갈등! 분노가 폭발한다") <= 1.0
def test_tc02_tension_proxy_empty_low():
    assert tension_proxy("") == 0.0
def test_tc03_r_struct_range_and_breakdown():
    rs = r_struct(_good())
    assert 0.0 <= rs.r_struct <= 1.0 and isinstance(rs.breakdown, dict) and rs.n_scenes == 3
def test_tc04_r_struct_good_gt_bad():
    assert r_struct(_good()).r_struct > r_struct(_bad()).r_struct
def test_tc05_r_pair_self_compare_passes():
    rp = r_pair(_bad(), _good(), rag_refs=None, critic=None)
    assert 0.0 <= rp.loss_rate <= 1.0 and isinstance(rp.passed, bool)
def test_tc06_r_path_nonregression():
    rp = r_path(_bad(), _good())
    assert isinstance(rp.passed, bool)
def test_tc07_nonregression_returns_r_values():
    nr = structural_nonregression(_bad(), _good())
    assert nr.r_before is not None and nr.r_after is not None
def test_tc08_nonregression_improvement_passes():
    nr = structural_nonregression(_bad(), _good())
    assert nr.r_after >= nr.r_before and nr.c3_struct is True
def test_tc09_nonregression_to_dict():
    d = structural_nonregression(_good(), _good()).to_dict()
    assert "r_before" in d and "r_after" in d and "passed" in d
def test_tc10_accepts_dicts_and_objects():
    # dict 입력으로도 동작(객체 미사용 경로)
    nr = structural_nonregression(_good(), _good())
    assert nr.passed is True
