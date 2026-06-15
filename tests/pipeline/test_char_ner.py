"""test_char_ner.py — 시리즈 단위 인물 NER 파이프라인 테스트 (V751)."""
import importlib.util
from pathlib import Path
import pytest

_P = (Path(__file__).resolve().parents[2]
      / "docs/sessions/2026-06-13_corpus_ko_build/pipeline/char_ner.py")

if not _P.exists():
    pytest.skip("char_ner.py 파이프라인 파일 없음", allow_module_level=True)

_spec = importlib.util.spec_from_file_location("char_ner_pipeline", _P)
cn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cn)

DRAMA = [
    {"work_id": "옥탑방고양이1부", "scene_no": 1, "heading": "S#1. 거실. 낮.",
     "text": "정우: 혜련아 어디 가?\n혜련\n나 회사 가.\n안방\n아버지: 들어와라."},
    {"work_id": "옥탑방고양이2부", "scene_no": 1, "heading": "S#1. 거실. 아침.",
     "text": "혜련: 정우야 일어나.\n정우: 응."},
]
FILM = [
    {"work_id": "곡성", "scene_no": 1, "heading": "S1. 산속.",
     "text": "종구: 뭐여?\n종구: 누구여?\n이삼: 몰라."},
    {"work_id": "곡성", "scene_no": 2, "heading": "S2. 마을.",
     "text": "종구: 가자.\n종구: 빨리."},
]

def test_tc01_series_of_drama(): assert cn.series_of("옥탑방고양이1부") == "옥탑방고양이"
def test_tc02_series_of_sn(): assert cn.series_of("별순검S1") == "별순검"
def test_tc03_series_of_num(): assert cn.series_of("궁24") == "궁"
def test_tc04_series_of_film(): assert cn.series_of("곡성") == "곡성"
def test_tc05_is_location_word(): assert cn.is_location("거실", set())
def test_tc06_is_location_suffix(): assert cn.is_location("상무실", set())
def test_tc07_name_not_location(): assert not cn.is_location("정우", set())
def test_tc08_speaker_colon(): assert "정우" in cn.speaker_candidates("정우: 안녕")
def test_tc09_speaker_standalone(): assert "혜련" in cn.speaker_candidates("혜련\n대사")
def test_tc10_selftest_passes(): assert cn._selftest() == 0

def test_tc11_drama_cast():
    r = cn.extract_cast(DRAMA)
    assert set(r["옥탑방고양이"]["characters"]) >= {"정우", "혜련"}
def test_tc12_location_excluded():
    r = cn.extract_cast(DRAMA)
    assert "안방" not in r["옥탑방고양이"]["characters"]
def test_tc13_kinship_role():
    r = cn.extract_cast(DRAMA)
    assert "아버지" in r["옥탑방고양이"]["person_roles"]
def test_tc14_reappearance_2ep():
    r = cn.extract_cast(DRAMA)
    assert r["옥탑방고양이"]["n_episodes"] == 2
def test_tc15_film_freq_threshold():
    r = cn.extract_cast(FILM)
    assert r["곡성"]["characters"] == ["종구"]  # 이삼(1회) 제외
def test_tc16_llm_fallback_hook():
    sparse = [{"work_id": "궁1부", "scene_no": 1, "heading": "S1.", "text": "(지문만)"}]
    r = cn.extract_cast(sparse, llm_fallback=lambda s, sc: ["신", "채경"])
    assert "신" in r["궁"]["characters"] and r["궁"]["method"].endswith("llm")
def test_tc17_char_scene_edges():
    r = cn.extract_cast(FILM)
    assert r["곡성"]["char_scene_edges"] >= 2
