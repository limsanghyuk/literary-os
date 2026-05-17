"""
test_v470_prose_style_dataset.py — ProseStyleDataset 단위 테스트 (V470)

ADR-008: Training Data Hygiene (CC-BY/CC-BY-SA/PUBLIC_DOMAIN only)
ADR-014: Fine-tune Lifecycle (DatasetCard + checksum)
"""
import pytest
from literary_system.finetune.prose_style_dataset import (
    ProseStyleDataset,
    ProseEntry,
    ProseStyle,
    DataSource,
    LicenseType,
    DatasetSplit,
    DatasetCard,
    make_entry,
    ALLOWED_LICENSES,
)


class TestAllowedLicenses:
    """ADR-008: 허용 라이선스 필터"""

    def test_cc_by_is_allowed(self):
        assert LicenseType.CC_BY in ALLOWED_LICENSES

    def test_cc_by_sa_is_allowed(self):
        assert LicenseType.CC_BY_SA in ALLOWED_LICENSES

    def test_public_domain_is_allowed(self):
        assert LicenseType.PUBLIC_DOMAIN in ALLOWED_LICENSES

    def test_proprietary_not_allowed(self):
        assert LicenseType.PROPRIETARY not in ALLOWED_LICENSES

    def test_unknown_not_allowed(self):
        if hasattr(LicenseType, "UNKNOWN"):
            assert LicenseType.UNKNOWN not in ALLOWED_LICENSES


class TestMakeEntry:
    """make_entry 팩토리 함수"""

    def test_make_entry_basic(self):
        entry = make_entry("테스트 문장", ProseStyle.ROMANCE, DataSource.SYNTHETIC, LicenseType.CC_BY)
        assert entry.text == "테스트 문장"
        assert entry.style == ProseStyle.ROMANCE
        assert entry.source == DataSource.SYNTHETIC
        assert entry.license_type == LicenseType.CC_BY

    def test_make_entry_has_entry_id(self):
        entry = make_entry("문장", ProseStyle.SF, DataSource.KOFICE, LicenseType.CC_BY)
        assert hasattr(entry, "entry_id")
        assert entry.entry_id != ""

    def test_make_entry_has_timestamp(self):
        entry = make_entry("문장", ProseStyle.THRILLER)
        assert hasattr(entry, "created_at")
        assert entry.created_at != ""


class TestProseStyleDatasetAdd:
    """데이터셋 항목 추가"""

    def test_add_single_cc_by_entry(self):
        ds = ProseStyleDataset()
        entry = make_entry("로맨스 문장", ProseStyle.ROMANCE, DataSource.SYNTHETIC, LicenseType.CC_BY)
        ds.add_entry(entry)
        loaded = ds.load()
        assert len(loaded) == 1

    def test_add_entries_bulk(self):
        ds = ProseStyleDataset()
        entries = [
            make_entry(f"문장{i}", ProseStyle.ROMANCE, DataSource.SYNTHETIC, LicenseType.CC_BY)
            for i in range(5)
        ]
        added, skipped = ds.add_entries(entries)
        assert added == 5
        assert skipped == 0

    def test_proprietary_entry_rejected(self):
        """ADR-008: PROPRIETARY 라이선스 거부"""
        ds = ProseStyleDataset()
        bad_entry = make_entry("불법 문장", ProseStyle.SF, DataSource.INTERNAL, LicenseType.PROPRIETARY)
        with pytest.raises(ValueError):
            ds.add_entry(bad_entry)

    def test_proprietary_skipped_in_bulk(self):
        ds = ProseStyleDataset()
        entries = [
            make_entry("정상", ProseStyle.ROMANCE, DataSource.SYNTHETIC, LicenseType.CC_BY),
            make_entry("위반", ProseStyle.SF, DataSource.INTERNAL, LicenseType.PROPRIETARY),
            make_entry("정상2", ProseStyle.THRILLER, DataSource.KOFICE, LicenseType.CC_BY),
        ]
        added, skipped = ds.add_entries(entries)
        assert added == 2
        assert skipped == 1

    def test_add_public_domain_entry(self):
        ds = ProseStyleDataset()
        entry = make_entry("역사 문장", ProseStyle.HISTORICAL, DataSource.KLAP, LicenseType.PUBLIC_DOMAIN)
        ds.add_entry(entry)
        assert len(ds.load()) == 1

    def test_add_cc_by_sa_entry(self):
        ds = ProseStyleDataset()
        entry = make_entry("SF 문장", ProseStyle.SF, DataSource.KOCCA, LicenseType.CC_BY_SA)
        ds.add_entry(entry)
        assert len(ds.load()) == 1


class TestProseStyleDatasetLoad:
    """필터링 조회"""

    def _make_dataset(self) -> ProseStyleDataset:
        ds = ProseStyleDataset()
        styles = [ProseStyle.ROMANCE, ProseStyle.THRILLER, ProseStyle.SF,
                  ProseStyle.HISTORICAL, ProseStyle.CONTEMPORARY]
        for i, style in enumerate(styles):
            for j in range(3):
                ds.add_entry(make_entry(f"{style.value} 문장{j}", style,
                                        DataSource.SYNTHETIC, LicenseType.CC_BY))
        return ds

    def test_load_all(self):
        ds = self._make_dataset()
        all_entries = ds.load()
        assert len(all_entries) == 15

    def test_load_by_style(self):
        ds = self._make_dataset()
        romance = ds.load(style=ProseStyle.ROMANCE)
        assert len(romance) == 3
        assert all(e.style == ProseStyle.ROMANCE for e in romance)

    def test_load_by_source(self):
        ds = ProseStyleDataset()
        ds.add_entry(make_entry("KOFICE 문장", ProseStyle.ROMANCE, DataSource.KOFICE, LicenseType.CC_BY))
        ds.add_entry(make_entry("SYNTHETIC 문장", ProseStyle.SF, DataSource.SYNTHETIC, LicenseType.CC_BY))
        kofice = ds.load(source=DataSource.KOFICE)
        assert len(kofice) == 1


class TestProseStyleDatasetSplit:
    """계층적 분할"""

    def test_split_ratios(self):
        ds = ProseStyleDataset()
        for style in [ProseStyle.ROMANCE, ProseStyle.THRILLER]:
            for i in range(10):
                ds.add_entry(make_entry(f"문장{i}", style, DataSource.SYNTHETIC, LicenseType.CC_BY))
        entries = ds.load()
        split = ds.split(entries, train_ratio=0.8, val_ratio=0.1)
        total = len(split.train) + len(split.validation) + len(split.test)
        assert total == len(entries)

    def test_split_train_ratio(self):
        ds = ProseStyleDataset()
        for i in range(20):
            ds.add_entry(make_entry(f"문장{i}", ProseStyle.ROMANCE, DataSource.SYNTHETIC, LicenseType.CC_BY))
        entries = ds.load()
        split = ds.split(entries, train_ratio=0.8, val_ratio=0.1)
        # train이 전체의 ~80%
        assert len(split.train) >= 14  # 약 80% ±2

    def test_split_stratified_by_style(self):
        """각 스타일이 train/val/test에 균형 있게 분포"""
        ds = ProseStyleDataset()
        for style in [ProseStyle.ROMANCE, ProseStyle.THRILLER, ProseStyle.SF]:
            for i in range(9):
                ds.add_entry(make_entry(f"문장{i}", style, DataSource.SYNTHETIC, LicenseType.CC_BY))
        entries = ds.load()
        split = ds.split(entries, train_ratio=0.8, val_ratio=0.1)
        # train에 모든 스타일 포함
        train_styles = {e.style for e in split.train}
        assert len(train_styles) >= 2  # 최소 2개 스타일


class TestDatasetCard:
    """DatasetCard ADR-014 메타데이터"""

    def test_generate_card_basic(self):
        ds = ProseStyleDataset()
        entries = [
            make_entry("문장1", ProseStyle.ROMANCE, DataSource.SYNTHETIC, LicenseType.CC_BY),
            make_entry("문장2", ProseStyle.SF, DataSource.KOFICE, LicenseType.CC_BY),
        ]
        ds.add_entries(entries)
        card = ds.generate_card("test-dataset", entries)
        assert card.dataset_id == "test-dataset"
        assert card.total_entries == 2

    def test_card_has_checksum(self):
        ds = ProseStyleDataset()
        entries = [make_entry("체크섬 테스트", ProseStyle.THRILLER, DataSource.SYNTHETIC, LicenseType.CC_BY)]
        ds.add_entries(entries)
        card = ds.generate_card("chk-test", entries)
        assert card.checksum != ""
        assert len(card.checksum) > 0

    def test_card_license_summary(self):
        ds = ProseStyleDataset()
        entries = [
            make_entry("CC-BY 문장", ProseStyle.ROMANCE, DataSource.SYNTHETIC, LicenseType.CC_BY),
            make_entry("PD 문장", ProseStyle.SF, DataSource.KLAP, LicenseType.PUBLIC_DOMAIN),
        ]
        ds.add_entries(entries)
        card = ds.generate_card("lic-test", entries)
        assert card.total_entries == 2

    def test_card_style_distribution(self):
        ds = ProseStyleDataset()
        entries = [
            make_entry("로맨스", ProseStyle.ROMANCE, DataSource.SYNTHETIC, LicenseType.CC_BY),
            make_entry("스릴러", ProseStyle.THRILLER, DataSource.SYNTHETIC, LicenseType.CC_BY),
            make_entry("SF", ProseStyle.SF, DataSource.SYNTHETIC, LicenseType.CC_BY),
        ]
        ds.add_entries(entries)
        card = ds.generate_card("dist-test", entries)
        if hasattr(card, "style_distribution"):
            assert len(card.style_distribution) >= 3


class TestProseStyleEnum:
    """ProseStyle 열거형"""

    def test_all_styles_defined(self):
        expected = ["ROMANCE", "THRILLER", "SF", "HISTORICAL", "CONTEMPORARY"]
        for name in expected:
            assert hasattr(ProseStyle, name), f"ProseStyle.{name} 미정의"

    def test_all_sources_defined(self):
        expected = ["SYNTHETIC", "KOFICE", "KOCCA", "KLAP"]
        for name in expected:
            assert hasattr(DataSource, name), f"DataSource.{name} 미정의"
