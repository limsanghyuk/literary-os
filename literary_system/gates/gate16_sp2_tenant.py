"""
Literary OS V461 -- Gate16: SP2 Tenant/Billing/DR 생존 검증

검증 항목:
  1. TenantManager CRUD + KMS 키 발급
  2. TenantRouter 리전 라우팅 (KR/EU/US)
  3. QuotaEnforcer 한도 초과 차단
  4. BillingEngine PG 다중화 (Toss KR / Stripe EU)
  5. TenantAuditLog hash chain 무결성
  6. ProductionMonitor SLO 보고서 생성
  7. DRController RPO 1h 스냅샷 + ADR-018 태그 롤백
"""
from __future__ import annotations


def _gate_sp2_tenant_survival() -> dict:
    """Gate 16 -- SP2 핵심 모듈 생존 검증."""
    try:
        # ── 1. TenantManager ─────────────────────────────────────────────────
        from literary_system.tenant import (
            QuotaEnforcer,
            QuotaExceededError,
            TenantAlreadyExistsError,
            TenantInactiveError,
            TenantManager,
            TenantNotFoundError,
            TenantRegion,
            TenantRouter,
            TenantStatus,
        )

        mgr = TenantManager()
        t1 = mgr.create_tenant("g16_kr", "게이트KR사", region=TenantRegion.KR,
                                max_tokens_per_month=500, max_cost_usd_per_month=1.0)
        t2 = mgr.create_tenant("g16_eu", "게이트EU사", region=TenantRegion.EU)
        t3 = mgr.create_tenant("g16_us", "게이트US사", region=TenantRegion.US)

        assert t1.is_active
        assert t1.data_residency_endpoint == "https://kr-data.literary-os.internal"

        # KMS 키 발급 확인
        key = mgr.get_tenant_key("g16_kr")
        assert key.version == 1

        # 일시 정지 / 복원
        mgr.suspend_tenant("g16_kr")
        assert mgr.get_tenant("g16_kr").status == TenantStatus.SUSPENDED
        try:
            mgr.require_active_tenant("g16_kr")
            return {"pass": False, "reason": "정지 테넌트에서 TenantInactiveError 미발생"}
        except TenantInactiveError:
            pass
        mgr.restore_tenant("g16_kr")
        assert mgr.get_tenant("g16_kr").status == TenantStatus.ACTIVE

        # 중복 등록 차단
        try:
            mgr.create_tenant("g16_kr", "중복", region=TenantRegion.KR)
            return {"pass": False, "reason": "중복 테넌트에서 예외 미발생"}
        except TenantAlreadyExistsError:
            pass

        # ── 2. TenantRouter ──────────────────────────────────────────────────
        router = TenantRouter(mgr)
        r_kr = router.route("g16_kr")
        r_eu = router.route("g16_eu")
        r_us = router.route("g16_us")
        assert "kr-api" in r_kr.endpoint, f"KR 라우트 오류: {r_kr.endpoint}"
        assert "eu-api" in r_eu.endpoint, f"EU 라우트 오류: {r_eu.endpoint}"
        assert "us-api" in r_us.endpoint, f"US 라우트 오류: {r_us.endpoint}"
        assert r_kr.latency_hint_ms < r_eu.latency_hint_ms < r_us.latency_hint_ms

        # ── 3. QuotaEnforcer ─────────────────────────────────────────────────
        quota = QuotaEnforcer(mgr)
        quota.check_and_record("g16_kr", tokens=300, cost_usd=0.5)

        try:
            quota.check_and_record("g16_kr", tokens=300, cost_usd=0.1)
            return {"pass": False, "reason": "토큰 초과 시 QuotaExceededError 미발생"}
        except QuotaExceededError as e:
            assert e.quota_type == "tokens"

        remaining = quota.remaining_quota("g16_kr")
        assert remaining["tokens_remaining"] == 200

        # ── 4. BillingEngine ─────────────────────────────────────────────────
        from literary_system.billing import BillingEngine, InvoiceLineItem, PaymentGatewayType

        engine = BillingEngine()
        items = [InvoiceLineItem("API 사용", 1.0, 20.0)]

        rec_kr = engine.create_and_charge("g16_kr", "KR", "2026-05", items)
        assert rec_kr.gateway == PaymentGatewayType.TOSS
        assert rec_kr.amount_krw == 27000   # 20 USD * 1350

        rec_eu = engine.create_and_charge("g16_eu", "EU", "2026-05", items)
        assert rec_eu.gateway == PaymentGatewayType.STRIPE

        # 환불 확인
        from literary_system.billing import PaymentStatus
        refunded = engine.refund(rec_kr.record_id)
        assert refunded.status == PaymentStatus.REFUNDED

        # ── 5. TenantAuditLog hash chain ─────────────────────────────────────
        from literary_system.tenant import AuditEventType, TenantAuditLog

        log = TenantAuditLog()
        for evt in [
            AuditEventType.TENANT_CREATED,
            AuditEventType.KMS_KEY_PROVISIONED,
            AuditEventType.BILLING_CHARGED,
        ]:
            log.append("g16_kr", evt, actor="gate16", description=evt.value)

        chain_result = log.verify_chain("g16_kr")
        if not chain_result["valid"]:
            return {"pass": False, "reason": f"hash chain 무결성 실패: {chain_result}"}
        assert chain_result["checked"] == 3

        # ── 6. ProductionMonitor ─────────────────────────────────────────────
        from literary_system.tenant import ProductionMonitor, RequestOutcome, RequestSample, SLOTier

        monitor = ProductionMonitor(tier=SLOTier.BETA)
        for i in range(20):
            lat = 500.0 if i < 19 else 2500.0
            monitor.record(RequestSample("g16_kr", lat, RequestOutcome.SUCCESS))

        report = monitor.get_slo_report("g16_kr", window_minutes=60)
        assert report.total_requests == 20
        assert report.p95_latency_ms <= 3000.0, f"p95 이상: {report.p95_latency_ms}"
        assert report.availability_pct == 1.0

        # ── 7. DRController RPO + ADR-018 롤백 ───────────────────────────────
        from literary_system.dr import DRComponent, DRController, DRPolicy

        policy = DRPolicy(rpo_minutes=60, rto_minutes=240)
        dr = DRController(policy=policy)

        # 전체 스냅샷
        snaps = dr.take_full_snapshot()
        assert len(snaps) == len(DRComponent)

        # RPO 검증
        rpo_result = dr.verify_all_rpo()
        if not rpo_result["all_ok"]:
            return {"pass": False, "reason": f"RPO 검증 실패: {rpo_result}"}

        # ADR-018 태그 등록 + 롤백
        tag = dr.register_tag("SP2", "V461", "Gate16 테스트 태그")
        assert tag.is_current
        assert len(tag.snapshot_ids) > 0

        rb = dr.rollback_to_tag(tag.tag_id)
        if not rb.success:
            return {"pass": False, "reason": f"롤백 실패: {rb.message}"}

        return {
            "pass": True,
            "modules_verified": 7,
            "tenants_created": 3,
            "billing_records": 2,
            "audit_chain_ok": True,
            "rpo_all_ok": True,
            "rollback_ok": True,
            "summary": "Gate16 PASS: TenantManager/Router/Quota/Billing/AuditLog/Monitor/DR ALL OK",
        }

    except Exception as e:
        import traceback
        return {"pass": False, "reason": str(e), "trace": traceback.format_exc()[-500:]}
