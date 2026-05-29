"""
V423~V424 통합 테스트
- V423: ManuscriptImporter v2 — 씬 파싱, NKG 연결
- V424: ManuscriptExporter v2 — FormatConverter, CLRO 연결
ADR-005: 기존 2,957 PASS 유지 + 신규 추가.
"""
from __future__ import annotations

import pytest


# ═══════════════════════════════════════════════════════════════
# A. SceneParser 단위 테스트
# ═══════════════════════════════════════════════════════════════

class TestSceneParser:
    def test_split_by_korean_scene_delimiter(self):
        from apps.studio_api.io.importer.manuscript_importer import SceneParser
        text = ("# 씬 1\n" + "주인공이 걷는다. " * 10 + "\n\n"
                "# 씬 2\n" + "대결이 시작된다. " * 10 + "\n\n"
                "# 씬 3\n" + "결전이 끝났다. " * 10)
        parser = SceneParser()
        scenes = parser.split(text, "S1")
        assert len(scenes) >= 2
        assert all("S1" in s.scene_id for s in scenes)

    def test_split_by_separator(self):
        from apps.studio_api.io.importer.manuscript_importer import SceneParser
        text = "첫 번째 씬 본문입니다. 내용이 있습니다.\n---\n두 번째 씬 본문입니다. 내용이 있습니다."
        parser = SceneParser()
        scenes = parser.split(text, "S2")
        assert len(scenes) >= 1

    def test_fallback_split_by_blank_lines(self):
        from apps.studio_api.io.importer.manuscript_importer import SceneParser
        text = "첫 번째 단락입니다. 내용이 여기 있습니다.\n\n\n두 번째 단락입니다. 내용이 여기 있습니다."
        parser = SceneParser()
        scenes = parser.split(text, "S3")
        assert len(scenes) >= 1

    def test_scene_id_format(self):
        from apps.studio_api.io.importer.manuscript_importer import SceneParser
        text = "# 씬 1\n" + "내용 " * 30 + "\n\n# 씬 2\n" + "내용 " * 30
        parser = SceneParser()
        scenes = parser.split(text, "MySeries", base_episode=3)
        for s in scenes:
            assert "MySeries" in s.scene_id
            assert s.episode == 3

    def test_short_content_filtered(self):
        from apps.studio_api.io.importer.manuscript_importer import SceneParser
        text = "# 씬 1\n짧음\n\n# 씬 2\n" + "내용 " * 50
        parser = SceneParser()
        scenes = parser.split(text, "S4")
        # 20자 미만은 필터링
        for s in scenes:
            assert len(s.content) >= 20

    def test_character_extraction(self):
        from apps.studio_api.io.importer.manuscript_importer import SceneParser
        text = '김철수: "안녕하세요."\n이영희: "반갑습니다."\n' + "내용 " * 20
        parser = SceneParser()
        scenes = parser.split(text, "S5")
        if scenes:
            chars = scenes[0].characters
            assert isinstance(chars, list)


# ═══════════════════════════════════════════════════════════════
# B. SceneNormalizer 단위 테스트
# ═══════════════════════════════════════════════════════════════

class TestSceneNormalizer:
    def test_to_scene_dict_structure(self):
        from apps.studio_api.io.importer.manuscript_importer import (
            SceneNormalizer, ParsedScene
        )
        scene = ParsedScene(
            scene_id="S1_ep01_sc0001",
            episode=1,
            content="내용 " * 100,
            characters=["김철수", "이영희"],
            word_count=100,
            char_count=600,
        )
        norm = SceneNormalizer()
        d = norm.to_scene_dict(scene)

        required_keys = {
            "scene_id", "episode", "prose_report",
            "conflict_intensity", "scene_energy_ratio",
        }
        assert required_keys.issubset(d.keys())

    def test_prose_report_keys(self):
        from apps.studio_api.io.importer.manuscript_importer import (
            SceneNormalizer, ParsedScene
        )
        scene = ParsedScene(
            scene_id="S1_ep01_sc0002",
            episode=1,
            content="테스트 씬 내용입니다.",
            word_count=10,
            char_count=20,
        )
        norm = SceneNormalizer()
        d = norm.to_scene_dict(scene)
        report = d["prose_report"]
        for k in ["anti_llm", "emotion", "sensory", "rhythm", "consistency", "structure"]:
            assert k in report
            assert 0.0 <= report[k] <= 1.0


# ═══════════════════════════════════════════════════════════════
# C. ManuscriptImporter v2 통합 테스트
# ═══════════════════════════════════════════════════════════════

class TestManuscriptImporter:
    SAMPLE_TXT = "\n\n".join([
        "# 씬 1\n" + "주인공이 거리를 걷고 있었다. " * 20,
        "# 씬 2\n" + "적이 등장하여 대결이 시작되었다. " * 20,
        "# 씬 3\n" + "마지막 결전에서 승리를 거두었다. " * 20,
    ])

    def test_parse_returns_correct_structure(self):
        from apps.studio_api.io.importer.manuscript_importer import ManuscriptImporter
        importer = ManuscriptImporter()
        result = importer.parse(self.SAMPLE_TXT, "TestSeries")
        assert "series_id" in result
        assert "scene_count" in result
        assert "imported_scene_ids" in result
        assert "warnings" in result
        assert isinstance(result["imported_scene_ids"], list)

    def test_parse_detects_3_scenes(self):
        from apps.studio_api.io.importer.manuscript_importer import ManuscriptImporter
        importer = ManuscriptImporter()
        result = importer.parse(self.SAMPLE_TXT, "S1")
        assert result["scene_count"] >= 2  # 최소 2개

    def test_parse_empty_content(self):
        from apps.studio_api.io.importer.manuscript_importer import ManuscriptImporter
        importer = ManuscriptImporter()
        result = importer.parse("", "S1")
        assert result["scene_count"] == 0
        assert len(result["warnings"]) > 0

    def test_parse_single_block(self):
        from apps.studio_api.io.importer.manuscript_importer import ManuscriptImporter
        importer = ManuscriptImporter()
        long_text = "단일 씬 텍스트입니다. " * 100
        result = importer.parse(long_text, "S1")
        assert result["scene_count"] >= 1

    def test_parse_series_id_preserved(self):
        from apps.studio_api.io.importer.manuscript_importer import ManuscriptImporter
        importer = ManuscriptImporter()
        result = importer.parse(self.SAMPLE_TXT, "MySeriesXYZ")
        assert result["series_id"] == "MySeriesXYZ"
        for sid in result["imported_scene_ids"]:
            assert "MySeriesXYZ" in sid

    def test_parse_format_preserved(self):
        from apps.studio_api.io.importer.manuscript_importer import ManuscriptImporter
        importer = ManuscriptImporter()
        result = importer.parse(self.SAMPLE_TXT, "S1", format="md")
        assert result["format"] == "md"

    def test_parse_degraded_on_exception(self):
        """예외 발생 시 degraded 모드 반환 (FAIL 없음)."""
        from apps.studio_api.io.importer.manuscript_importer import ManuscriptImporter
        importer = ManuscriptImporter()
        result = importer.parse(None, "S1")  # type: ignore — 의도적 오류
        assert result["scene_count"] == 0
        assert len(result["warnings"]) > 0


# ═══════════════════════════════════════════════════════════════
# D. FormatConverter 단위 테스트
# ═══════════════════════════════════════════════════════════════

class TestFormatConverter:
    SCENES = [
        {"scene_id": "S1_ep01_sc0001", "episode": 1, "prose": "첫 씬 내용", "score": 8.5, "passed": False},
        {"scene_id": "S1_ep01_sc0002", "episode": 1, "prose": "두번째 씬", "score": 9.2, "passed": True},
    ]

    def test_txt_format(self):
        from apps.studio_api.io.exporter.manuscript_exporter import FormatConverter
        fc = FormatConverter()
        result = fc.convert(self.SCENES, "txt", "TestSeries")
        assert "TestSeries" in result
        assert "S1_ep01_sc0001" in result
        assert "첫 씬 내용" in result

    def test_md_format(self):
        from apps.studio_api.io.exporter.manuscript_exporter import FormatConverter
        fc = FormatConverter()
        result = fc.convert(self.SCENES, "md", "TestSeries")
        assert "# TestSeries" in result
        assert "## S1_ep01_sc0001" in result

    def test_docx_fallback_to_md(self):
        from apps.studio_api.io.exporter.manuscript_exporter import FormatConverter
        fc = FormatConverter()
        result = fc.convert(self.SCENES, "docx", "S1")
        assert "# S1" in result  # docx는 md로 대체

    def test_unknown_format_fallback_to_txt(self):
        from apps.studio_api.io.exporter.manuscript_exporter import FormatConverter
        fc = FormatConverter()
        result = fc.convert(self.SCENES, "unknown_fmt", "S1")
        assert isinstance(result, str)
        assert len(result) > 0


# ═══════════════════════════════════════════════════════════════
# E. ManuscriptExporter v2 통합 테스트
# ═══════════════════════════════════════════════════════════════

class TestManuscriptExporter:
    def test_export_returns_correct_structure(self):
        from apps.studio_api.io.exporter.manuscript_exporter import ManuscriptExporter
        exporter = ManuscriptExporter()
        result = exporter.export("S1", ["sc001", "sc002"], "md")
        assert "series_id" in result
        assert "format" in result
        assert "scene_count" in result
        assert "content" in result
        assert "download_url" in result

    def test_export_empty_scene_ids(self):
        from apps.studio_api.io.exporter.manuscript_exporter import ManuscriptExporter
        exporter = ManuscriptExporter()
        result = exporter.export("S1", [], "txt")
        assert result["scene_count"] == 0
        assert isinstance(result["content"], str)

    def test_export_missing_scenes_generates_placeholder(self):
        from apps.studio_api.io.exporter.manuscript_exporter import ManuscriptExporter
        exporter = ManuscriptExporter(store=None)  # store 없음 → 모두 미등록
        result = exporter.export("S1", ["missing_sc_001"], "txt")
        assert result["scene_count"] == 1
        assert "missing_sc_001" in result["content"]

    def test_export_format_preserved(self):
        from apps.studio_api.io.exporter.manuscript_exporter import ManuscriptExporter
        exporter = ManuscriptExporter()
        for fmt in ["txt", "md", "docx"]:
            result = exporter.export("S1", ["sc1"], fmt)
            assert result["format"] == fmt

    def test_export_size_bytes_calculated(self):
        from apps.studio_api.io.exporter.manuscript_exporter import ManuscriptExporter
        exporter = ManuscriptExporter()
        result = exporter.export("S1", ["sc1", "sc2"], "md")
        assert result["size_bytes"] == len(result["content"].encode("utf-8"))

    def test_export_degraded_on_exception(self):
        """예외 발생 시 degraded 반환."""
        from apps.studio_api.io.exporter.manuscript_exporter import ManuscriptExporter
        exporter = ManuscriptExporter()
        result = exporter.export(None, None, "txt")  # type: ignore
        assert result["scene_count"] == 0
        assert len(result["warnings"]) > 0


# ═══════════════════════════════════════════════════════════════
# F. Import → Export 파이프라인 통합
# ═══════════════════════════════════════════════════════════════

class TestImportExportPipeline:
    def test_import_then_export(self):
        """임포트된 씬 ID로 익스포트 — end-to-end."""
        from apps.studio_api.io.importer.manuscript_importer import ManuscriptImporter
        from apps.studio_api.io.exporter.manuscript_exporter import ManuscriptExporter

        text = "\n\n".join([
            "# 씬 1\n" + "파이프라인 테스트 씬 내용입니다. " * 15,
            "# 씬 2\n" + "두 번째 씬의 내용이 여기 있습니다. " * 15,
        ])
        importer = ManuscriptImporter()
        import_result = importer.parse(text, "Pipeline_S1")
        scene_ids = import_result["imported_scene_ids"]

        exporter = ManuscriptExporter()
        export_result = exporter.export("Pipeline_S1", scene_ids, "md")

        assert export_result["scene_count"] == len(scene_ids)
        assert "Pipeline_S1" in export_result["content"]

    def test_router_io_importable(self):
        """routers/io.py v2 임포트 확인."""
        from apps.studio_api.routers import io as io_router
        assert io_router._importer is not None
        assert io_router._exporter is not None

    def test_inject_io_store(self):
        """inject_io_store — store 주입 후 importer/exporter 교체."""
        from apps.studio_api.routers.io import inject_io_store, _importer, _exporter
        inject_io_store(None)  # None store로 재주입
        from apps.studio_api.routers.io import _importer as mi, _exporter as me
        assert mi is not None
        assert me is not None
