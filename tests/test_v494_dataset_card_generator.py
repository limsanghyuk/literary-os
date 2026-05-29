"""
tests/test_v494_dataset_card_generator.py
V494: DatasetCardGenerator 단위 테스트

대상:
  - DatasetStats.to_dict() — 통계 딕셔너리 직렬화
  - DatasetCard.to_yaml_header() — HuggingFace YAML front-matter
  - DatasetCard.to_markdown() — 전체 마크다운 카드
  - DatasetCard.to_dict() — JSON 직렬화
  - DatasetCardGenerator.generate() — DatasetCard 생성
  - DatasetCardGenerator.save() — 파일 저장 (markdown + json)
  - 통계 자동 계산 (text_length, quality, tier_distribution)
  - pii_scrubbed / dedup_removed 전파
  - 샘플 n_samples 개수 제한
"""

import json
import os
import tempfile

import pytest
from literary_system.slm.dataset_card_generator import (
    DatasetCardGenerator,
    DatasetCard,
    DatasetStats,
)


# ─────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────
def _make_records(count=10, tier="A", quality=0.9) -> list:
    return [
        {
            "id": f"r{i}",
            "text": f"드라마 씬 텍스트 {i} " + "가나다라마바사" * (i + 1),
            "tier": tier,
            "quality_score": quality,
        }
        for i in range(count)
    ]


def _make_generator(**kw) -> DatasetCardGenerator:
    defaults = dict(
        dataset_name="test-dataset",
        version="1.2.3",
        description="테스트용 데이터셋",
    )
    defaults.update(kw)
    return DatasetCardGenerator(**defaults)


# ─────────────────────────────────────────────────────────────────────
# TestDatasetStats
# ─────────────────────────────────────────────────────────────────────
class TestDatasetStats:
    def _stats(self, **kw) -> DatasetStats:
        defaults = dict(
            total_records=100, train_count=70, val_count=15, test_count=15,
            avg_text_length=128.5, min_text_length=20, max_text_length=512,
            avg_quality=0.85, tier_distribution={"A": 60, "B": 40},
            pii_scrubbed=5, dedup_removed=3,
        )
        defaults.update(kw)
        return DatasetStats(**defaults)

    def test_to_dict_has_all_keys(self):
        d = self._stats().to_dict()
        assert "total_records" in d
        assert "splits" in d
        assert "text_length" in d
        assert "avg_quality_score" in d
        assert "tier_distribution" in d
        assert "pii_scrubbed" in d
        assert "dedup_removed" in d

    def test_to_dict_splits(self):
        d = self._stats().to_dict()
        assert d["splits"]["train"] == 70
        assert d["splits"]["val"] == 15
        assert d["splits"]["test"] == 15

    def test_to_dict_text_length(self):
        d = self._stats().to_dict()
        assert d["text_length"]["avg"] == 128.5
        assert d["text_length"]["min"] == 20
        assert d["text_length"]["max"] == 512

    def test_to_dict_pii_and_dedup(self):
        d = self._stats(pii_scrubbed=7, dedup_removed=2).to_dict()
        assert d["pii_scrubbed"] == 7
        assert d["dedup_removed"] == 2


# ─────────────────────────────────────────────────────────────────────
# TestDatasetCard
# ─────────────────────────────────────────────────────────────────────
class TestDatasetCard:
    def _card(self) -> DatasetCard:
        gen = _make_generator()
        train = _make_records(8)
        val = _make_records(1)
        test = _make_records(1)
        return gen.generate(train, val, test)

    def test_to_yaml_header_starts_with_dashes(self):
        yaml = self._card().to_yaml_header()
        assert yaml.startswith("---")
        assert yaml.strip().endswith("---")

    def test_to_yaml_header_contains_dataset_name(self):
        yaml = self._card().to_yaml_header()
        assert "test-dataset" in yaml

    def test_to_yaml_header_contains_version(self):
        yaml = self._card().to_yaml_header()
        assert "1.2.3" in yaml

    def test_to_yaml_header_contains_license(self):
        yaml = self._card().to_yaml_header()
        assert "cc-by-sa-4.0" in yaml

    def test_to_yaml_header_contains_language(self):
        yaml = self._card().to_yaml_header()
        assert "ko" in yaml

    def test_to_markdown_includes_yaml_header(self):
        md = self._card().to_markdown()
        assert "---" in md
        assert "dataset_info:" in md

    def test_to_markdown_includes_title(self):
        md = self._card().to_markdown()
        assert "test-dataset" in md

    def test_to_markdown_includes_stats_table(self):
        md = self._card().to_markdown()
        assert "총 레코드" in md
        assert "Train" in md

    def test_to_dict_is_json_serializable(self):
        d = self._card().to_dict()
        s = json.dumps(d, ensure_ascii=False)
        assert "test-dataset" in s

    def test_to_dict_has_version(self):
        d = self._card().to_dict()
        assert d["version"] == "1.2.3"

    def test_to_dict_stats_nested(self):
        d = self._card().to_dict()
        assert "stats" in d
        assert "splits" in d["stats"]


# ─────────────────────────────────────────────────────────────────────
# TestDatasetCardGenerator — 생성 로직
# ─────────────────────────────────────────────────────────────────────
class TestDatasetCardGenerator:
    def test_generate_returns_dataset_card(self):
        gen = _make_generator()
        card = gen.generate(_make_records(8), _make_records(1), _make_records(1))
        assert isinstance(card, DatasetCard)

    def test_generate_stats_total_records(self):
        gen = _make_generator()
        train = _make_records(8)
        val = _make_records(1)
        test = _make_records(1)
        card = gen.generate(train, val, test)
        assert card.stats.total_records == 10

    def test_generate_stats_split_counts(self):
        gen = _make_generator()
        card = gen.generate(_make_records(7), _make_records(2), _make_records(1))
        assert card.stats.train_count == 7
        assert card.stats.val_count == 2
        assert card.stats.test_count == 1

    def test_generate_stats_pii_scrubbed_propagated(self):
        gen = _make_generator()
        card = gen.generate(_make_records(5), _make_records(1), _make_records(1),
                            pii_scrubbed=4, dedup_removed=2)
        assert card.stats.pii_scrubbed == 4
        assert card.stats.dedup_removed == 2

    def test_generate_stats_text_length_computed(self):
        gen = _make_generator()
        card = gen.generate(_make_records(5), _make_records(1), _make_records(1))
        assert card.stats.avg_text_length > 0
        assert card.stats.min_text_length >= 0
        assert card.stats.max_text_length >= card.stats.min_text_length

    def test_generate_stats_quality_score_computed(self):
        gen = _make_generator()
        records = _make_records(5, quality=0.75)
        card = gen.generate(records, _make_records(1, quality=0.75), [])
        assert abs(card.stats.avg_quality - 0.75) < 0.01

    def test_generate_tier_distribution(self):
        gen = _make_generator()
        train = _make_records(6, tier="A") + _make_records(4, tier="B")
        card = gen.generate(train, [], [])
        assert "A" in card.stats.tier_distribution
        assert "B" in card.stats.tier_distribution

    def test_generate_samples_capped_at_n_samples(self):
        gen = _make_generator(n_samples=2)
        card = gen.generate(_make_records(10), [], [])
        assert len(card.samples) <= 2

    def test_generate_samples_from_train(self):
        gen = _make_generator(n_samples=3)
        train = _make_records(5)
        card = gen.generate(train, [], [])
        assert len(card.samples) <= 3

    def test_generate_dataset_name(self):
        gen = _make_generator(dataset_name="my-drama-slm")
        card = gen.generate(_make_records(3), [], [])
        assert card.dataset_name == "my-drama-slm"

    def test_generate_version_string(self):
        gen = _make_generator(version="2.0.0")
        card = gen.generate(_make_records(3), [], [])
        assert card.version == "2.0.0"

    def test_generate_custom_license(self):
        gen = _make_generator(license="apache-2.0")
        card = gen.generate(_make_records(3), [], [])
        assert card.license == "apache-2.0"

    def test_generate_empty_splits(self):
        gen = _make_generator()
        card = gen.generate([], [], [])
        assert card.stats.total_records == 0

    def test_generate_extra_metadata_passed_through(self):
        gen = _make_generator()
        card = gen.generate(_make_records(3), [], [],
                            extra_metadata={"custom_key": "custom_value"})
        assert card.extra_metadata.get("custom_key") == "custom_value"
    def test_generate_proprietary_license_raises(self):
        """ADR-008: 독점 라이선스는 ValueError 발생."""
        gen = DatasetCardGenerator(license="proprietary")
        with pytest.raises(ValueError, match="ADR-008"):
            gen.generate([], [], [])

    def test_generate_all_rights_reserved_raises(self):
        """ADR-008: 모든 독점 표기는 차단."""
        gen = DatasetCardGenerator(license="all-rights-reserved")
        with pytest.raises(ValueError, match="ADR-008"):
            gen.generate([], [], [])

    def test_generate_internal_license_allowed(self):
        """ADR-008 허용 목록: internal은 허용."""
        gen = DatasetCardGenerator(license="internal")
        card = gen.generate([], [], [])
        assert card.license == "internal"



# ─────────────────────────────────────────────────────────────────────
# TestDatasetCardGeneratorSave — 파일 저장 테스트
# ─────────────────────────────────────────────────────────────────────
class TestDatasetCardGeneratorSave:
    def test_save_returns_markdown_and_json_paths(self):
        gen = _make_generator()
        card = gen.generate(_make_records(3), [], [])
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = gen.save(card, tmpdir)
            assert "markdown" in paths
            assert "json" in paths

    def test_save_markdown_file_exists(self):
        gen = _make_generator()
        card = gen.generate(_make_records(3), [], [])
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = gen.save(card, tmpdir)
            assert os.path.isfile(paths["markdown"])

    def test_save_json_file_exists(self):
        gen = _make_generator()
        card = gen.generate(_make_records(3), [], [])
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = gen.save(card, tmpdir)
            assert os.path.isfile(paths["json"])

    def test_save_markdown_contains_dataset_name(self):
        gen = _make_generator(dataset_name="save-test-ds")
        card = gen.generate(_make_records(3), [], [])
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = gen.save(card, tmpdir)
            content = open(paths["markdown"], encoding="utf-8").read()
            assert "save-test-ds" in content

    def test_save_json_is_valid_json(self):
        gen = _make_generator()
        card = gen.generate(_make_records(3), [], [])
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = gen.save(card, tmpdir)
            with open(paths["json"], encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, dict)
            assert "dataset_name" in data

    def test_save_creates_output_dir_if_missing(self):
        gen = _make_generator()
        card = gen.generate(_make_records(3), [], [])
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "nested", "path")
            paths = gen.save(card, new_dir)
            assert os.path.isfile(paths["markdown"])
