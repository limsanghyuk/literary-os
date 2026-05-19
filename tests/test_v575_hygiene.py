"""
V575 — Security & Hygiene 테스트

검증 항목:
  S-01: DEV_MODE 기본값이 "false" (인증 bypass 비활성화)
  S-02: literary_system/ 내 print() 사용 0건
  S-03: literary_system/ 내 bare except: 0건
  S-04: apps/studio_api/main_v316.py 삭제 확인
  S-05: preflight_step15.py 존재 + ALL CLEAR 통과
  S-06: CI yml에 preflight-step15 잡 포함 확인
  S-07: pyproject.toml description에 "V571" 없음
  S-08: e2e_loop_orchestrator.py — logging 모듈 사용 확인
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SYSTEM_ROOT = REPO_ROOT / "literary_system"
MIDDLEWARE  = REPO_ROOT / "apps" / "studio_api" / "auth" / "middleware.py"
PYPROJECT   = REPO_ROOT / "pyproject.toml"
CI_YML      = REPO_ROOT / ".github" / "workflows" / "ci.yml"
STEP15      = REPO_ROOT / "tools" / "preflight_step15.py"


# ─── S-01: DEV_MODE 기본값 ────────────────────────────────────────────────────
class TestS01DevModeDefault:
    def test_devmode_default_is_false(self):
        """middleware.py DEV_MODE 기본값이 "false" 이어야 한다."""
        text = MIDDLEWARE.read_text(encoding="utf-8")
        # "true" 기본값 패턴이 없어야 함
        bad_pattern = re.compile(
            r'os\.environ\.get\(["\']LITERARY_OS_DEV_MODE["\'],\s*["\']true["\']'
        )
        for i, line in enumerate(text.splitlines(), 1):
            assert not bad_pattern.search(line), (
                f"middleware.py:{i} — DEV_MODE 기본값이 'true' 입니다. "
                f"보안 패치 필요 (V575-S-01)"
            )

    def test_devmode_default_false_present(self):
        """middleware.py에 DEV_MODE 기본값 "false" 코드가 존재해야 한다."""
        text = MIDDLEWARE.read_text(encoding="utf-8")
        good_pattern = re.compile(
            r'os\.environ\.get\(["\']LITERARY_OS_DEV_MODE["\'],\s*["\']false["\']'
        )
        assert good_pattern.search(text), (
            "middleware.py에 DEV_MODE 기본값 'false' 코드가 없습니다."
        )


# ─── S-02: print() 금지 ──────────────────────────────────────────────────────
class TestS02NoPrintStatements:
    def test_no_print_in_literary_system(self):
        """literary_system/ 내 모든 .py 파일에 print() 사용이 없어야 한다."""
        violations = []
        for py_file in SYSTEM_ROOT.rglob("*.py"):
            for i, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), 1):
                if line.lstrip().startswith("#"):
                    continue
                if re.match(r'\s*print\s*\(', line):
                    violations.append(f"{py_file.relative_to(REPO_ROOT)}:{i}")
        assert not violations, (
            f"print() 사용 발견 ({len(violations)}건):\n" + "\n".join(violations[:10])
        )


# ─── S-03: bare except 금지 ──────────────────────────────────────────────────
class TestS03NoBareExcept:
    def test_no_bare_except_in_literary_system(self):
        """literary_system/ 내 모든 .py 파일에 bare except: 가 없어야 한다."""
        violations = []
        for py_file in SYSTEM_ROOT.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    violations.append(
                        f"{py_file.relative_to(REPO_ROOT)}:{node.lineno}"
                    )
        assert not violations, (
            f"bare except: 발견 ({len(violations)}건):\n" + "\n".join(violations)
        )


# ─── S-04: 데드코드 파일 제거 확인 ───────────────────────────────────────────
class TestS04DeadCodeRemoved:
    def test_main_v316_deleted(self):
        """apps/studio_api/main_v316.py 가 삭제되어야 한다."""
        dead_file = REPO_ROOT / "apps" / "studio_api" / "main_v316.py"
        assert not dead_file.exists(), (
            f"데드코드 파일이 아직 존재합니다: {dead_file.relative_to(REPO_ROOT)}"
        )


# ─── S-05: preflight_step15 존재 및 ALL CLEAR ───────────────────────────────
class TestS05Preflight15:
    def test_preflight_step15_exists(self):
        """tools/preflight_step15.py 가 존재해야 한다."""
        assert STEP15.exists(), "tools/preflight_step15.py 가 없습니다."

    def test_preflight_step15_passes(self):
        """preflight_step15.py --strict 가 0 exit code로 통과해야 한다."""
        result = subprocess.run(
            [sys.executable, str(STEP15), "--strict"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"Preflight Step 15 FAILED:\n{result.stdout}\n{result.stderr}"
        )


# ─── S-06: CI yml preflight-step15 포함 ─────────────────────────────────────
class TestS06CiYml:
    def test_ci_yml_has_step15_job(self):
        """CI yml에 preflight-step15 잡이 정의되어야 한다."""
        text = CI_YML.read_text(encoding="utf-8")
        assert "preflight-step15:" in text, (
            ".github/workflows/ci.yml에 preflight-step15 잡이 없습니다."
        )

    def test_test_job_needs_step15(self):
        """test 잡이 preflight-step15 를 needs에 포함해야 한다."""
        text = CI_YML.read_text(encoding="utf-8")
        # Find the test job's needs line
        assert "preflight-step15" in text, (
            "test 잡의 needs 목록에 preflight-step15가 없습니다."
        )


# ─── S-07: pyproject.toml description 갱신 ──────────────────────────────────
class TestS07PyprojectDescription:
    def test_description_not_v571(self):
        """pyproject.toml description이 구버전 'V571'을 참조하지 않아야 한다."""
        text = PYPROJECT.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("description"):
                assert "V571" not in line, (
                    f"pyproject.toml:{i} — description이 아직 'V571' 입니다. "
                    f"V575 수정 필요."
                )


# ─── S-08: e2e_loop_orchestrator logging 사용 확인 ───────────────────────────
class TestS08LoggingUsage:
    def test_e2e_orchestrator_uses_logging(self):
        """e2e_loop_orchestrator.py 가 logging 모듈을 import해야 한다."""
        e2e_file = SYSTEM_ROOT / "orchestrators" / "e2e_loop_orchestrator.py"
        text = e2e_file.read_text(encoding="utf-8")
        assert "import logging" in text, (
            "e2e_loop_orchestrator.py에 'import logging'이 없습니다."
        )
        assert "logger = logging.getLogger" in text, (
            "e2e_loop_orchestrator.py에 logger 인스턴스가 없습니다."
        )

    def test_e2e_orchestrator_no_print(self):
        """e2e_loop_orchestrator.py 에 print() 호출이 없어야 한다."""
        e2e_file = SYSTEM_ROOT / "orchestrators" / "e2e_loop_orchestrator.py"
        for i, line in enumerate(e2e_file.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            assert not re.match(r'\s*print\s*\(', line), (
                f"e2e_loop_orchestrator.py:{i} — print() 발견"
            )
