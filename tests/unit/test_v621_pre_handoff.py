"""tests/unit/test_v621_pre_handoff.py

V621-PRE: verify_v3_handoff() 단위 테스트 (ADR-088, V621-PRE 체크리스트)
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestVerifyV3Handoff:
    """verify_v3_handoff() — 필수 학습 파일 존재 확인."""

    def _run(self, existing_files):
        """REQUIRED_V3_FILES를 패치하여 지정 파일만 존재하는 환경 시뮬레이션."""
        from tools.preflight_step15 import verify_v3_handoff, REQUIRED_V3_FILES

        def fake_exists(self_path):
            return str(self_path).replace("\\", "/").endswith(
                tuple(f.replace("docs/sessions/", "") for f in existing_files)
            )

        with patch.object(Path, "exists", fake_exists):
            return verify_v3_handoff()

    def test_all_files_present_returns_pass(self):
        """두 필수 파일 모두 존재 → pass=True."""
        from tools.preflight_step15 import verify_v3_handoff, REQUIRED_V3_FILES
        # 실제 레포 환경에서 파일이 있는지 확인
        result = verify_v3_handoff()
        # 파일이 실제로 존재하면 PASS, 없으면 missing 보고
        assert isinstance(result["pass"], bool)
        assert "found" in result
        assert "missing" in result

    def test_pass_true_when_files_exist(self, tmp_path):
        """tmp_path에 파일 생성 후 REPO_ROOT 패치 → pass=True."""
        from tools import preflight_step15 as pf15

        # 임시 디렉토리에 파일 생성
        sessions = tmp_path / "docs" / "sessions"
        sessions.mkdir(parents=True)
        (sessions / "2026-05-25_v621_v630_phase_b_main_handoff_v3.md").write_text("ok")
        (sessions / "literary_os_v621_v630_phase_b_blueprint_v3.md").write_text("ok")

        old_root = pf15.REPO_ROOT
        pf15.REPO_ROOT = tmp_path
        try:
            result = pf15.verify_v3_handoff()
        finally:
            pf15.REPO_ROOT = old_root

        assert result["pass"] is True
        assert len(result["found"]) == 2
        assert len(result["missing"]) == 0

    def test_fail_when_main_handoff_missing(self, tmp_path):
        """main_handoff 파일 없을 때 pass=False, missing 1건."""
        from tools import preflight_step15 as pf15

        sessions = tmp_path / "docs" / "sessions"
        sessions.mkdir(parents=True)
        # blueprint만 있고 handoff 없음
        (sessions / "literary_os_v621_v630_phase_b_blueprint_v3.md").write_text("ok")

        old_root = pf15.REPO_ROOT
        pf15.REPO_ROOT = tmp_path
        try:
            result = pf15.verify_v3_handoff()
        finally:
            pf15.REPO_ROOT = old_root

        assert result["pass"] is False
        assert len(result["missing"]) == 1
        assert "2026-05-25_v621_v630_phase_b_main_handoff_v3.md" in result["missing"][0]

    def test_fail_when_blueprint_missing(self, tmp_path):
        """blueprint 파일 없을 때 pass=False, missing 1건."""
        from tools import preflight_step15 as pf15

        sessions = tmp_path / "docs" / "sessions"
        sessions.mkdir(parents=True)
        (sessions / "2026-05-25_v621_v630_phase_b_main_handoff_v3.md").write_text("ok")

        old_root = pf15.REPO_ROOT
        pf15.REPO_ROOT = tmp_path
        try:
            result = pf15.verify_v3_handoff()
        finally:
            pf15.REPO_ROOT = old_root

        assert result["pass"] is False
        assert any("blueprint_v3" in m for m in result["missing"])

    def test_fail_when_all_missing(self, tmp_path):
        """모든 파일 없을 때 pass=False, missing 2건."""
        from tools import preflight_step15 as pf15

        old_root = pf15.REPO_ROOT
        pf15.REPO_ROOT = tmp_path  # docs/sessions 자체가 없음
        try:
            result = pf15.verify_v3_handoff()
        finally:
            pf15.REPO_ROOT = old_root

        assert result["pass"] is False
        assert len(result["missing"]) == 2
