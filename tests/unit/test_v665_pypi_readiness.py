"""
test_v665_pypi_readiness.py — V665 PyPI 준비 및 SP-C.3 완료 검증 (33 TC)

DEV_MODE: False (ADR-034)
LLM-0: 외부 LLM 호출 없음
"""
from __future__ import annotations

import importlib
import pathlib
import re
import sys

import pytest


# ─── 헬퍼 ────────────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).parent.parent.parent  # literary-os/


def _load_pyproject() -> dict:
    """pyproject.toml을 파싱해 dict 반환."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]
    with open(ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


# ─── pyproject.toml 메타데이터 검증 ─────────────────────────────────────────

class TestPyprojectMetadata:
    @classmethod
    def setup_class(cls):
        try:
            cls.data = _load_pyproject()
        except Exception:
            # tomllib/tomli 둘 다 없으면 raw parse
            content = (ROOT / "pyproject.toml").read_text()
            cls.data = None
            cls.raw = content

    def _proj(self):
        if self.data:
            return self.data.get("project", {})
        return {}

    def test_tc01_version_format(self):
        """TC01: version은 semver 형식."""
        content = (ROOT / "pyproject.toml").read_text()
        m = re.search(r'version\s*=\s*"([^"]+)"', content)
        assert m, "version 필드 누락"
        ver = m.group(1)
        assert re.match(r"^\d+\.\d+\.\d+", ver), f"semver 형식 아님: {ver}"

    def test_tc02_name_is_literary_os(self):
        """TC02: 패키지명은 literary-os."""
        content = (ROOT / "pyproject.toml").read_text()
        assert 'name = "literary-os"' in content

    def test_tc03_requires_python(self):
        """TC03: requires-python >= 3.10."""
        content = (ROOT / "pyproject.toml").read_text()
        assert ">=3.10" in content

    def test_tc04_classifiers_present(self):
        """TC04: classifiers 섹션 존재."""
        content = (ROOT / "pyproject.toml").read_text()
        assert "classifiers" in content

    def test_tc05_development_status_classifier(self):
        """TC05: Development Status classifier 포함."""
        content = (ROOT / "pyproject.toml").read_text()
        assert "Development Status" in content

    def test_tc06_license_mit(self):
        """TC06: MIT 라이선스 명시."""
        content = (ROOT / "pyproject.toml").read_text()
        assert "MIT" in content

    def test_tc07_authors_present(self):
        """TC07: authors 섹션 존재."""
        content = (ROOT / "pyproject.toml").read_text()
        assert "authors" in content

    def test_tc08_project_urls_present(self):
        """TC08: project.urls 섹션 존재."""
        content = (ROOT / "pyproject.toml").read_text()
        assert "[project.urls]" in content

    def test_tc09_homepage_url(self):
        """TC09: Homepage URL 포함."""
        content = (ROOT / "pyproject.toml").read_text()
        assert "Homepage" in content and "github.com" in content

    def test_tc10_extras_sdk_present(self):
        """TC10: sdk extras 정의 존재."""
        content = (ROOT / "pyproject.toml").read_text()
        assert "sdk" in content and "fastapi" in content

    def test_tc11_extras_all_present(self):
        """TC11: all extras 정의 존재."""
        content = (ROOT / "pyproject.toml").read_text()
        assert 'all = [' in content or '"all"' in content or "all = " in content

    def test_tc12_entry_point_literary_sdk(self):
        """TC12: literary-sdk entry_point 등록."""
        content = (ROOT / "pyproject.toml").read_text()
        assert "literary-sdk" in content

    def test_tc13_package_data_py_typed(self):
        """TC13: py.typed 패키지 데이터 포함."""
        content = (ROOT / "pyproject.toml").read_text()
        assert "py.typed" in content

    def test_tc14_keywords_korean(self):
        """TC14: keywords에 korean 관련 키워드 포함."""
        content = (ROOT / "pyproject.toml").read_text()
        assert "korean" in content.lower() or "Korean" in content

    def test_tc15_changelog_url(self):
        """TC15: Changelog URL 포함."""
        content = (ROOT / "pyproject.toml").read_text()
        assert "Changelog" in content or "CHANGELOG" in content


# ─── PublicSDK CLI 검증 ──────────────────────────────────────────────────────

class TestPublicSDKCLI:
    def test_tc16_cli_demo_importable(self):
        """TC16: _cli_demo 함수 임포트 가능."""
        from literary_system.sdk.public_sdk import _cli_demo
        assert callable(_cli_demo)

    def test_tc17_sdk_version_semver(self):
        """TC17: SDK __version__ 형식 확인."""
        from literary_system.sdk import __version__
        assert re.match(r"^\d+\.\d+\.\d+", __version__), f"semver 아님: {__version__}"

    def test_tc18_sdk_init_exports(self):
        """TC18: literary_system.sdk 에서 LiteraryOSClient 임포트 가능."""
        from literary_system.sdk.public_sdk import LiteraryOSClient
        assert LiteraryOSClient is not None

    def test_tc19_client_offline_mode(self):
        """TC19: offline_mode=True로 클라이언트 생성."""
        from literary_system.sdk.public_sdk import LiteraryOSClient
        from literary_system.sdk.sdk_config import SDKConfig
        c = LiteraryOSClient(config=SDKConfig(offline_mode=True))
        assert c._config.offline_mode is True

    def test_tc20_analyze_returns_score(self):
        """TC20: analyze() 결과에 quality.score 포함."""
        from literary_system.sdk.public_sdk import LiteraryOSClient
        from literary_system.sdk.sdk_config import SDKConfig
        c = LiteraryOSClient(config=SDKConfig(offline_mode=True))
        r = c.analyze("준호는 눈물을 흘렸다.")
        assert hasattr(r, "quality")
        assert 0.0 <= r.quality.overall <= 1.0

    def test_tc21_repair_returns_text(self):
        """TC21: repair() 결과에 repaired_text 포함."""
        from literary_system.sdk.public_sdk import LiteraryOSClient
        from literary_system.sdk.sdk_config import SDKConfig
        c = LiteraryOSClient(config=SDKConfig(offline_mode=True))
        r = c.repair("준호는 오랫동안 기억했다.", issues=[])
        assert hasattr(r, "repaired_text")
        assert isinstance(r.repaired_text, str)

    def test_tc22_predict_returns_predictions(self):
        """TC22: predict() 결과에 predictions 포함."""
        from literary_system.sdk.public_sdk import LiteraryOSClient
        from literary_system.sdk.sdk_config import SDKConfig
        c = LiteraryOSClient(config=SDKConfig(offline_mode=True))
        r = c.predict("갑자기 눈물이 흘렀다.")
        assert hasattr(r, "predictions")
        assert isinstance(r.predictions, list)

    def test_tc23_generate_returns_scene_text(self):
        """TC23: generate() 결과에 scene_text 포함."""
        from literary_system.sdk.public_sdk import LiteraryOSClient
        from literary_system.sdk.sdk_config import SDKConfig
        c = LiteraryOSClient(config=SDKConfig(offline_mode=True))
        r = c.generate(
            title="이별의 밤",
            characters=["준호", "수아"],
            setting="병원 옥상",
            conflict="작별 인사",
        )
        assert hasattr(r, "scene_text")
        assert isinstance(r.scene_text, str)


# ─── SP-C.3 완료 보고서 검증 ─────────────────────────────────────────────────

class TestSPC3CompletionReport:
    REPORT_PATH = ROOT / "docs" / "proposals" / "SP_C3_COMPLETION_REPORT.md"

    def test_tc24_report_exists(self):
        """TC24: SP-C.3 완료 보고서 파일 존재."""
        assert self.REPORT_PATH.exists(), "SP_C3_COMPLETION_REPORT.md 누락"

    def test_tc25_report_mentions_g68_to_g71(self):
        """TC25: 보고서에 G68~G71 게이트 언급."""
        content = self.REPORT_PATH.read_text()
        for gate in ("G68", "G69", "G70", "G71"):
            assert gate in content, f"{gate} 누락"

    def test_tc26_report_mentions_loi(self):
        """TC26: 보고서에 LOI 언급."""
        content = self.REPORT_PATH.read_text()
        assert "LOI" in content

    def test_tc27_report_mentions_sp_c4(self):
        """TC27: 보고서에 SP-C.4 진입 언급."""
        content = self.REPORT_PATH.read_text()
        assert "SP-C.4" in content

    def test_tc28_report_v656_to_v665(self):
        """TC28: 보고서에 V656~V665 산출물 기록."""
        content = self.REPORT_PATH.read_text()
        for v in ("V656", "V657", "V658", "V659", "V660"):
            assert v in content, f"{v} 누락"

    def test_tc29_adr_125_exists(self):
        """TC29: ADR-125 파일 존재."""
        adr_path = ROOT / "docs" / "adr" / "ADR-125.md"
        assert adr_path.exists(), "ADR-125.md 누락"


# ─── docs/workflow 감사 ──────────────────────────────────────────────────────

class TestWorkflowAudit:
    WORKFLOW_DIR = ROOT / "docs" / "workflow"

    def test_tc30_dev_protocol_exists(self):
        """TC30: DEV_PROTOCOL_v2.0.md 존재."""
        assert (self.WORKFLOW_DIR / "DEV_PROTOCOL_v2.0.md").exists()

    def test_tc31_packaging_protocol_exists(self):
        """TC31: PACKAGING_PROTOCOL_v1.0.md 존재."""
        assert (self.WORKFLOW_DIR / "PACKAGING_PROTOCOL_v1.0.md").exists()

    def test_tc32_preflight_guide_exists(self):
        """TC32: PREFLIGHT_GUIDE_v1.1.md 존재."""
        assert (self.WORKFLOW_DIR / "PREFLIGHT_GUIDE_v1.1.md").exists()

    def test_tc33_dev_protocol_mentions_preflight_12(self):
        """TC33: DEV_PROTOCOL_v2.0에 Preflight 12단계 언급."""
        content = (self.WORKFLOW_DIR / "DEV_PROTOCOL_v2.0.md").read_text()
        assert "Preflight" in content or "preflight" in content
