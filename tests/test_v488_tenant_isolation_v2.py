"""
tests/test_v488_tenant_isolation_v2.py
V488 TenantIsolationV2 + KMSKeyManager + DataHygieneFilter 테스트
"""
import pytest
from literary_system.tenant.tenant_isolation_v2 import (
    TenantIsolationV2,
    KMSKeyManager,
    DataHygieneFilter,
    DataHygieneViolation,
    TenantRAGRegistry,
    HygieneResult,
)


class TestKMSKeyManager:

    def test_derive_key_deterministic(self):
        kms = KMSKeyManager()
        k1 = kms.derive_key("tenant_A")
        k2 = kms.derive_key("tenant_A")
        assert k1 == k2

    def test_different_tenants_different_keys(self):
        kms = KMSKeyManager()
        assert kms.derive_key("tenant_A") != kms.derive_key("tenant_B")

    def test_key_is_32_bytes(self):
        kms = KMSKeyManager()
        assert len(kms.derive_key("t1")) == 32

    def test_key_id_is_16_hex_chars(self):
        kms = KMSKeyManager()
        kid = kms.key_id("tenant_A")
        assert len(kid) == 16
        assert all(c in "0123456789abcdef" for c in kid)

    def test_rotate_changes_key_id(self):
        kms = KMSKeyManager()
        kid_before = kms.key_id("tenant_X")
        kms.rotate("tenant_X", b"new_secret_42")
        kid_after = kms.key_id("tenant_X")
        assert kid_before != kid_after


class TestDataHygieneFilter:

    @pytest.fixture
    def hygiene(self):
        return DataHygieneFilter(min_quality_score=0.3, require_opt_in=True)

    def test_clean_text_passes(self, hygiene):
        r = hygiene.check("깨끗한 드라마 씬 텍스트", quality_score=0.9, opt_in=True)
        assert r.passed
        assert r.violations == []

    def test_pii_detected(self, hygiene):
        r = hygiene.check("전화번호 010-1234", quality_score=0.9, opt_in=True)
        assert not r.passed
        assert DataHygieneViolation.PII_DETECTED in r.violations

    def test_low_quality_rejected(self, hygiene):
        r = hygiene.check("텍스트", quality_score=0.1, opt_in=True)
        assert not r.passed
        assert DataHygieneViolation.QUALITY_TOO_LOW in r.violations

    def test_no_opt_in_rejected(self, hygiene):
        r = hygiene.check("텍스트", quality_score=0.9, opt_in=False)
        assert not r.passed
        assert DataHygieneViolation.OPT_IN_REQUIRED in r.violations

    def test_invalid_license_rejected(self, hygiene):
        r = hygiene.check("텍스트", quality_score=0.9, opt_in=True, license_type="proprietary")
        assert not r.passed
        assert DataHygieneViolation.LICENSE_VIOLATION in r.violations

    def test_multiple_violations(self, hygiene):
        r = hygiene.check("주민번호 890101", quality_score=0.1, opt_in=False)
        assert len(r.violations) >= 2

    def test_violation_codes_as_strings(self, hygiene):
        r = hygiene.check("전화번호", quality_score=0.1, opt_in=False)
        codes = r.violation_codes
        assert all(isinstance(c, str) for c in codes)


class TestTenantRAGRegistry:

    def test_register_new_tenant(self):
        reg = TenantRAGRegistry()
        cfg = reg.register("t1")
        assert cfg.tenant_id == "t1"
        assert reg.tenant_count == 1

    def test_register_idempotent(self):
        reg = TenantRAGRegistry()
        c1 = reg.register("t1")
        c2 = reg.register("t1")
        assert c1.kms_key_id == c2.kms_key_id
        assert reg.tenant_count == 1

    def test_verify_isolation(self):
        reg = TenantRAGRegistry()
        reg.register("t1")
        reg.register("t2")
        assert reg.verify_isolation("t1", "t2")

    def test_verify_isolation_same_tenant_false(self):
        reg = TenantRAGRegistry()
        reg.register("t1")
        assert not reg.verify_isolation("t1", "t1")


class TestTenantIsolationV2:

    @pytest.fixture
    def iso(self):
        return TenantIsolationV2()

    def test_collection_name_includes_prefix(self, iso):
        iso.register_tenant("studio_A")
        col = iso.collection_name("studio_A", "scenes")
        assert "scenes" in col
        assert col.startswith("t_")

    def test_different_tenants_different_collections(self, iso):
        col_a = iso.collection_name("studio_A", "scenes")
        col_b = iso.collection_name("studio_B", "scenes")
        assert col_a != col_b

    def test_auto_register_on_collection_name(self, iso):
        _ = iso.collection_name("new_tenant", "docs")
        assert iso.tenant_count >= 1

    def test_kms_key_differs_per_tenant(self, iso):
        k1 = iso.kms_key_id("t1")
        k2 = iso.kms_key_id("t2")
        assert k1 != k2

    def test_verify_isolation_two_tenants(self, iso):
        iso.register_tenant("tA")
        iso.register_tenant("tB")
        assert iso.verify_isolation("tA", "tB")

    def test_hygiene_clean(self, iso):
        r = iso.check_hygiene("이준혁이 병원을 걷는다", quality_score=0.8)
        assert r.passed

    def test_hygiene_pii_blocked(self, iso):
        r = iso.check_hygiene("계좌번호 1234-5678", quality_score=0.8)
        assert not r.passed
