"""
test_v467_gate18_data_residency.py — V467 Gate18 + DataResidencyRouter 테스트

ADR-016: DataResidencyRouter
Gate18: SP3 Compliance·Governance·DataSovereignty 검증
"""
import pytest
from literary_system.compliance.data_residency_router import (
    DataResidencyRouter, TenantResidencyConfig,
    ResidencyPolicy, DataRegion, RouteResult, RouteDecision, RouteViolation,
)
from literary_system.gates.gate18_sp3_compliance import _gate_sp3_compliance_sovereignty


# ===========================================================================
# DataResidencyRouter 테스트
# ===========================================================================

class TestTenantResidencyConfig:

    def test_config_creation(self):
        cfg = TenantResidencyConfig(tenant_id="t1", policy=ResidencyPolicy.KR_ONLY)
        assert cfg.tenant_id == "t1"
        assert cfg.policy == ResidencyPolicy.KR_ONLY
        assert cfg.created_at  # 자동 설정

    def test_preferred_region_override(self):
        cfg = TenantResidencyConfig(
            tenant_id="t1",
            policy=ResidencyPolicy.KR_EU,
            preferred_region=DataRegion.EU_IE,
        )
        assert cfg.preferred_region == DataRegion.EU_IE


class TestDataResidencyRouterSetup:

    def _router(self):
        return DataResidencyRouter()

    def test_set_and_get_config(self):
        r = self._router()
        cfg = TenantResidencyConfig("t1", ResidencyPolicy.KR_ONLY)
        r.set_tenant_config(cfg)
        assert r.get_tenant_config("t1") is not None
        assert r.get_tenant_config("t1").policy == ResidencyPolicy.KR_ONLY

    def test_get_config_nonexistent(self):
        r = self._router()
        assert r.get_tenant_config("nope") is None


class TestRoutingDecisions:

    def _router_kr(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.KR_ONLY))
        return r

    # --- KR_ONLY ---
    def test_kr_only_seoul_allowed(self):
        r = self._router_kr()
        d = r.route("t1", DataRegion.KR_SEOUL)
        assert d.result == RouteResult.ROUTED
        assert d.routed_region == DataRegion.KR_SEOUL

    def test_kr_only_busan_allowed(self):
        r = self._router_kr()
        d = r.route("t1", DataRegion.KR_BUSAN)
        assert d.result == RouteResult.ROUTED

    def test_kr_only_eu_violation(self):
        r = self._router_kr()
        d = r.route("t1", DataRegion.EU_IE)
        assert d.result in (RouteResult.VIOLATION, RouteResult.FALLBACK)
        # 위반 기록
        violations = r.get_violations("t1")
        assert len(violations) == 1

    def test_kr_only_us_violation(self):
        r = self._router_kr()
        r.route("t1", DataRegion.US_VA)
        assert len(r.get_violations("t1")) == 1

    # --- EU_ONLY ---
    def test_eu_only_ie_allowed(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.EU_ONLY))
        d = r.route("t1", DataRegion.EU_IE)
        assert d.result == RouteResult.ROUTED

    def test_eu_only_de_allowed(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.EU_ONLY))
        d = r.route("t1", DataRegion.EU_DE)
        assert d.result == RouteResult.ROUTED

    def test_eu_only_kr_violation(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.EU_ONLY))
        d = r.route("t1", DataRegion.KR_SEOUL)
        assert d.result in (RouteResult.VIOLATION, RouteResult.FALLBACK)

    # --- KR_EU ---
    def test_kr_eu_both_allowed(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.KR_EU))
        d1 = r.route("t1", DataRegion.KR_SEOUL)
        d2 = r.route("t1", DataRegion.EU_DE)
        assert d1.result == RouteResult.ROUTED
        assert d2.result == RouteResult.ROUTED

    def test_kr_eu_us_violation(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.KR_EU))
        d = r.route("t1", DataRegion.US_OR)
        assert d.result in (RouteResult.VIOLATION, RouteResult.FALLBACK)

    # --- ANY ---
    def test_any_policy_all_allowed(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.ANY))
        for region in [DataRegion.KR_SEOUL, DataRegion.EU_IE, DataRegion.US_VA]:
            d = r.route("t1", region)
            assert d.result == RouteResult.ROUTED

    # --- 지역 미지정 (기본값 사용) ---
    def test_route_no_region_uses_default(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.KR_ONLY))
        d = r.route("t1", None)
        assert d.result == RouteResult.ROUTED
        assert d.routed_region in (DataRegion.KR_SEOUL, DataRegion.KR_BUSAN)

    def test_route_preferred_region(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig(
            "t1", ResidencyPolicy.KR_EU,
            preferred_region=DataRegion.EU_IE,
        ))
        d = r.route("t1", None)
        assert d.routed_region == DataRegion.EU_IE

    # --- 미설정 테넌트 ---
    def test_unconfigured_tenant_any_policy(self):
        r = DataResidencyRouter()
        d = r.route("unknown_tenant", DataRegion.US_VA)
        assert d.result == RouteResult.ROUTED  # ANY 정책 기본값

    # --- 폴백 비허용 ---
    def test_fallback_disabled_violation_result(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig(
            "t1", ResidencyPolicy.KR_ONLY, allow_fallback=False
        ))
        d = r.route("t1", DataRegion.EU_IE)
        assert d.result == RouteResult.VIOLATION

    def test_fallback_enabled_fallback_result(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig(
            "t1", ResidencyPolicy.KR_ONLY, allow_fallback=True
        ))
        d = r.route("t1", DataRegion.EU_IE)
        assert d.result == RouteResult.FALLBACK
        assert d.routed_region in (DataRegion.KR_SEOUL, DataRegion.KR_BUSAN)


class TestIsRegionAllowed:

    def test_allowed(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.EU_ONLY))
        assert r.is_region_allowed("t1", DataRegion.EU_IE) is True
        assert r.is_region_allowed("t1", DataRegion.KR_SEOUL) is False

    def test_unconfigured_always_allowed(self):
        r = DataResidencyRouter()
        assert r.is_region_allowed("unknown", DataRegion.US_VA) is True


class TestQueryMethods:

    def test_get_violations_by_tenant(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.KR_ONLY))
        r.set_tenant_config(TenantResidencyConfig("t2", ResidencyPolicy.EU_ONLY))
        r.route("t1", DataRegion.US_VA)
        r.route("t2", DataRegion.KR_SEOUL)
        assert len(r.get_violations("t1")) == 1
        assert len(r.get_violations("t2")) == 1
        assert len(r.get_violations()) == 2

    def test_get_decisions_by_tenant(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.KR_ONLY))
        r.route("t1", DataRegion.KR_SEOUL)
        r.route("t1", DataRegion.EU_IE)  # violation/fallback
        assert len(r.get_decisions("t1")) == 2

    def test_to_dict_decision(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t1", ResidencyPolicy.ANY))
        d = r.route("t1", DataRegion.KR_SEOUL)
        dd = d.to_dict()
        for k in ("decision_id", "tenant_id", "routed_region", "result", "policy", "reason"):
            assert k in dd

    def test_to_dict_violation(self):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig(
            "t1", ResidencyPolicy.KR_ONLY, allow_fallback=False
        ))
        r.route("t1", DataRegion.US_VA)
        v = r.get_violations("t1")[0]
        vd = v.to_dict()
        for k in ("violation_id", "tenant_id", "requested_region", "policy", "reason"):
            assert k in vd


class TestAllPolicies:
    """6개 정책 × 주요 지역 교차 검증"""

    def _check(self, policy: ResidencyPolicy, region: DataRegion, should_pass: bool):
        r = DataResidencyRouter()
        r.set_tenant_config(TenantResidencyConfig("t", policy, allow_fallback=False))
        d = r.route("t", region)
        if should_pass:
            assert d.result == RouteResult.ROUTED, f"{policy} × {region} should be ROUTED"
        else:
            assert d.result == RouteResult.VIOLATION, f"{policy} × {region} should be VIOLATION"

    def test_kr_only_regions(self):
        self._check(ResidencyPolicy.KR_ONLY, DataRegion.KR_SEOUL, True)
        self._check(ResidencyPolicy.KR_ONLY, DataRegion.KR_BUSAN, True)
        self._check(ResidencyPolicy.KR_ONLY, DataRegion.EU_IE, False)
        self._check(ResidencyPolicy.KR_ONLY, DataRegion.US_VA, False)

    def test_eu_only_regions(self):
        self._check(ResidencyPolicy.EU_ONLY, DataRegion.EU_IE, True)
        self._check(ResidencyPolicy.EU_ONLY, DataRegion.EU_DE, True)
        self._check(ResidencyPolicy.EU_ONLY, DataRegion.KR_SEOUL, False)
        self._check(ResidencyPolicy.EU_ONLY, DataRegion.US_OR, False)

    def test_us_only_regions(self):
        self._check(ResidencyPolicy.US_ONLY, DataRegion.US_VA, True)
        self._check(ResidencyPolicy.US_ONLY, DataRegion.US_OR, True)
        self._check(ResidencyPolicy.US_ONLY, DataRegion.KR_SEOUL, False)
        self._check(ResidencyPolicy.US_ONLY, DataRegion.EU_DE, False)

    def test_kr_eu_regions(self):
        self._check(ResidencyPolicy.KR_EU, DataRegion.KR_SEOUL, True)
        self._check(ResidencyPolicy.KR_EU, DataRegion.EU_IE, True)
        self._check(ResidencyPolicy.KR_EU, DataRegion.US_VA, False)

    def test_kr_us_regions(self):
        self._check(ResidencyPolicy.KR_US, DataRegion.KR_SEOUL, True)
        self._check(ResidencyPolicy.KR_US, DataRegion.US_VA, True)
        self._check(ResidencyPolicy.KR_US, DataRegion.EU_IE, False)


# ===========================================================================
# Gate18 직접 실행 테스트
# ===========================================================================

class TestGate18:

    def test_gate18_passes(self):
        """Gate18 SP3 Compliance 5종 모두 PASS"""
        result = _gate_sp3_compliance_sovereignty()
        assert result["pass"] is True
        assert result["modules_verified"] == 5

    def test_gate18_symbols_all_verified(self):
        result = _gate_sp3_compliance_sovereignty()
        symbols = result["symbols_verified"]
        assert any("PIAGenerator" in s for s in symbols)
        assert any("EUAIAct" in s for s in symbols)
        assert any("PIIScanner" in s for s in symbols)
        assert any("AuditTrail" in s for s in symbols)
        assert any("DataResidency" in s for s in symbols)

    def test_gate18_summary_message(self):
        result = _gate_sp3_compliance_sovereignty()
        assert "Gate18 PASS" in result["summary"]
        assert "5/5" in result["summary"]


# ===========================================================================
# 통합 시나리오
# ===========================================================================

class TestV467Integration:

    def test_multi_region_tenant_routing(self):
        """KR+EU 테넌트 — 지역별 라우팅 + 위반 시 폴백"""
        router = DataResidencyRouter()

        # KR-only 소기업 테넌트
        router.set_tenant_config(TenantResidencyConfig(
            "kr_small_biz", ResidencyPolicy.KR_ONLY, allow_fallback=True
        ))
        # EU-only 유럽 파트너
        router.set_tenant_config(TenantResidencyConfig(
            "eu_partner", ResidencyPolicy.EU_ONLY, allow_fallback=True
        ))
        # 글로벌 엔터프라이즈
        router.set_tenant_config(TenantResidencyConfig(
            "global_corp", ResidencyPolicy.ANY
        ))

        # KR 소기업: 국내 → OK, 미국 → fallback
        d1 = router.route("kr_small_biz", DataRegion.KR_SEOUL)
        d2 = router.route("kr_small_biz", DataRegion.US_VA)
        assert d1.result == RouteResult.ROUTED
        assert d2.result == RouteResult.FALLBACK
        assert d2.routed_region in (DataRegion.KR_SEOUL, DataRegion.KR_BUSAN)

        # EU 파트너: EU → OK, KR → fallback
        d3 = router.route("eu_partner", DataRegion.EU_DE)
        d4 = router.route("eu_partner", DataRegion.KR_BUSAN)
        assert d3.result == RouteResult.ROUTED
        assert d4.result == RouteResult.FALLBACK

        # 글로벌: 어디든 OK
        for region in DataRegion:
            if region == DataRegion.GLOBAL:
                continue
            d = router.route("global_corp", region)
            assert d.result == RouteResult.ROUTED

        # 위반 기록: kr_small_biz 1건, eu_partner 1건
        assert len(router.get_violations("kr_small_biz")) == 1
        assert len(router.get_violations("eu_partner")) == 1
        assert len(router.get_violations("global_corp")) == 0

    def test_gate18_full_sp3_stack(self):
        """Gate18 전체 SP3 스택 통합 검증"""
        result = _gate_sp3_compliance_sovereignty()
        assert result["pass"] is True
        assert result["modules_verified"] == 5
        print(f"\n  Gate18: {result['summary']}")
