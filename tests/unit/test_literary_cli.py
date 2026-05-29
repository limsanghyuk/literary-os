"""
SP-A.8 (V595) — test_literary_cli.py

literary_cli.py : analyze / repair / generate CLI 명령 검증

TC01~TC20: 20 cases / 목표 20/20 PASS
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

import pytest
from click.testing import CliRunner

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from apps.cli.literary_cli import literary, analyze_cmd, repair_cmd, generate_cmd


# ===========================================================================
# 공통 픽스처
# ===========================================================================
_RICH_TEXT = (
    "기: 조선 시대 한양의 새벽, 춘향은 광한루에서 이도령을 처음 만났다. "
    "설레임과 두려움이 교차하는 순간, 운명의 실이 두 사람을 묶었다. "
    "승: 사랑이 깊어질수록 신분의 차이가 벽처럼 가로막았다. 위기감이 고조되었다. "
    "갈등이 첨예해지고 두 사람의 앞날은 안개 속에 잠겼다. "
    "전: 변학도의 횡포로 춘향이 옥에 갇히는 반전이 찾아왔다. "
    "절망과 희망이 공존하는 감옥 속에서 그녀의 의지는 더욱 단단해졌다. "
    "결: 암행어사 이도령이 나타나 정의를 실현하고 두 사람은 재회했다. "
)

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def rich_scene_file():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", encoding="utf-8", delete=False
    ) as f:
        f.write(_RICH_TEXT)
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def empty_scene_file():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", encoding="utf-8", delete=False
    ) as f:
        f.write("   ")
        path = f.name
    yield path
    os.unlink(path)


# ===========================================================================
# TC01~TC05 : CLI 그룹 / 메타
# ===========================================================================

class TestCLIMeta:
    """TC01~TC05"""

    def test_tc01_literary_group_exists(self, runner):
        """TC01: literary 그룹 import 성공"""
        assert literary is not None
        assert literary.name == "literary"

    def test_tc02_three_commands(self):
        """TC02: analyze / repair / generate 3개 명령 존재"""
        commands = list(literary.commands.keys())
        assert "analyze" in commands
        assert "repair" in commands
        assert "generate" in commands
        assert len(commands) == 3

    def test_tc03_help_exits_zero(self, runner):
        """TC03: literary --help 종료코드 0"""
        result = runner.invoke(literary, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output

    def test_tc04_version_option(self, runner):
        """TC04: literary --version 출력"""
        result = runner.invoke(literary, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_tc05_subcommand_help(self, runner):
        """TC05: literary analyze --help 정상 출력"""
        result = runner.invoke(literary, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "SCENE_FILE" in result.output


# ===========================================================================
# TC06~TC10 : literary analyze
# ===========================================================================

class TestAnalyzeCommand:
    """TC06~TC10"""

    def test_tc06_analyze_text_output(self, runner, rich_scene_file):
        """TC06: analyze 기본 text 출력 — 5축 존재"""
        result = runner.invoke(literary, ["analyze", rich_scene_file])
        assert result.exit_code == 0, result.output
        assert "drse" in result.output
        assert "R(scene)" in result.output

    def test_tc07_analyze_json_output(self, runner, rich_scene_file):
        """TC07: analyze --format json — 파싱 가능한 JSON"""
        result = runner.invoke(literary, ["analyze", rich_scene_file, "--format", "json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "total" in data
        assert "drse" in data

    def test_tc08_analyze_score_range(self, runner, rich_scene_file):
        """TC08: analyze JSON total 값 [0,1] 범위"""
        result = runner.invoke(literary, ["analyze", rich_scene_file, "--format", "json"])
        data = json.loads(result.output)
        assert 0.0 <= data["total"] <= 1.0

    def test_tc09_analyze_empty_file_exits_nonzero(self, runner, empty_scene_file):
        """TC09: 빈 파일 분석 → 종료코드 1"""
        result = runner.invoke(literary, ["analyze", empty_scene_file])
        assert result.exit_code != 0

    def test_tc10_analyze_missing_file(self, runner):
        """TC10: 존재하지 않는 파일 → 종료코드 2 (click Path 검증)"""
        result = runner.invoke(literary, ["analyze", "/tmp/nonexistent_scene_file_xyz.txt"])
        assert result.exit_code != 0


# ===========================================================================
# TC11~TC14 : literary repair
# ===========================================================================

class TestRepairCommand:
    """TC11~TC14"""

    def test_tc11_repair_dry_run(self, runner):
        """TC11: repair dry-run — 종료코드 0"""
        result = runner.invoke(literary, ["repair", "test-series-001", "--dry-run"])
        assert result.exit_code == 0, result.output

    def test_tc12_repair_help(self, runner):
        """TC12: repair --help 정상 출력"""
        result = runner.invoke(literary, ["repair", "--help"])
        assert result.exit_code == 0
        assert "SERIES_ID" in result.output

    def test_tc13_repair_unknown_series(self, runner):
        """TC13: 존재하지 않는 시리즈 → 샘플 진단 출력 후 종료코드 0"""
        result = runner.invoke(literary, ["repair", "nonexistent-series-xyz"])
        assert result.exit_code == 0
        # 샘플 진단 or 안내 메시지 출력
        assert len(result.output) > 0

    def test_tc14_repair_threshold_option(self, runner):
        """TC14: --threshold 0.70 옵션 적용"""
        result = runner.invoke(
            literary, ["repair", "test-series", "--threshold", "0.70"]
        )
        assert result.exit_code == 0


# ===========================================================================
# TC15~TC20 : literary generate
# ===========================================================================

class TestGenerateCommand:
    """TC15~TC20"""

    def test_tc15_generate_default(self, runner):
        """TC15: generate 기본 실행 — 종료코드 0"""
        result = runner.invoke(literary, ["generate"])
        assert result.exit_code == 0, result.output

    def test_tc16_generate_json_output(self, runner):
        """TC16: generate --format json — 파싱 가능한 JSON 배열"""
        result = runner.invoke(literary, ["generate", "-e", "1", "-s", "2", "--format", "json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_tc17_generate_episode_scene_count(self, runner):
        """TC17: -e 2 -s 3 → 6개 장면"""
        result = runner.invoke(literary, ["generate", "-e", "2", "-s", "3", "--format", "json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert len(data) == 6

    def test_tc18_generate_json_fields(self, runner):
        """TC18: 각 장면 dict에 필수 필드 존재"""
        result = runner.invoke(literary, ["generate", "-e", "1", "-s", "1", "--format", "json"])
        data = json.loads(result.output)
        assert len(data) == 1
        item = data[0]
        assert "episode" in item
        assert "scene" in item
        assert "score" in item
        assert "text" in item

    def test_tc19_generate_score_range(self, runner):
        """TC19: generate 각 장면 score [0,1] 범위"""
        result = runner.invoke(literary, ["generate", "-e", "1", "-s", "3", "--format", "json"])
        data = json.loads(result.output)
        for item in data:
            assert 0.0 <= item["score"] <= 1.0, f"score={item['score']} out of range"

    def test_tc20_llm0_compliance(self):
        """TC20: LLM-0 원칙 — literary_cli.py에 외부 LLM 호출 없음"""
        import inspect
        import apps.cli.literary_cli as mod
        src = inspect.getsource(mod)
        forbidden = [
            "openai.ChatCompletion",
            "anthropic.Anthropic",
            "requests.post",
            "httpx.post",
        ]
        for pat in forbidden:
            assert pat not in src, f"LLM-0 위반: {pat} 발견"
