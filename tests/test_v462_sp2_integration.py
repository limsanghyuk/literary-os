"""
Literary OS V462 -- SP2 통합 테스트

검증 범위:
  - V457: TenantManager + KMSKeyStore
  - V458: TenantRouter + QuotaEnforcer + TenantContextMiddleware
  - V459: BillingEngine (Stripe + TossPayments)
  - V460: TenantAuditLog (hash chain) + ProductionMonitor (SLO)
  - V461: DRController (RPO 1h + ADR-018 태그 롤백) + Gate16
  - V462: Release Gate 14+2=16 ALL PASS

LLM-0: 모든 외부 호출은 fn 주입 mock 사용.
"""
from __future__ import annotations

import pytest
import datetime as dt

# ── 공통 픽스처 ───────────────────────────────────────────────────────────────

@pytest.fixture
def mgr():
    from literary_system.tenant import TenantManager, TenantRegion
    m = TenantManager()
    m.create_tenant("sp2_kr", "KR테스트사", region=TenantRegion.KR,
                    max_tokens_per_month=10_000, max_cost_usd_per_month=100.0)
    m.create_tenant("sp2_eu", "EU테스트사", region=TenantRegion.EU)
    m.create_tenant("sp2_us", "US테스트사", region=TenantRegion.US)
    return m


@pytest.fixture
def router(mgr):
    from literary_system.tenant import TenantRouter
    return TenantRouter(mgr)


@pytest.fixture
def quota(mgr):
    from literary_system.tenant import QuotaEnforcer
    return QuotaEnforcer(mgr)


@pytest.fixture
def billing_engine():
    from literary_system.billing import BillingEngine
    return BillingEngine()


@pytest.fixture
def audit_log():
    from literary_system.tenant import TenantAuditLog
    return TenantAuditLog()


@pytest.fixture
def monitor():
    from literary_system.tenant import ProductionMonitor, SLOTier
    return ProductionMonitor(tier=SLOTier.BETA)


@pytest.fixture
def dr():
    from literary_system.dr import DRController, DRPolicy
    return DRController(policy=DRPolicy(rpo_minutes=60))


# ══════════════════════════════════════════════════════════════════════════════
# V457: TenantManager + KMSKeyStore
# ══════════════════════════════════════════════════════════════════════════════

class TestV457TenantManager:
    """TenantManager CRUD 및 KMS 키 관리."""

    def test_create_tenant_kr(self, mgr):
        t = mgr.get_tenant("sp2_kr")
        assert t.tenant_id == "sp2_kr"
        from literary_system.tenant import TenantRegion
        assert t.region == TenantRegion.KR

    def test_data_residency_endpoint_by_region(self, mgr):
        t_kr = mgr.get_tenant("sp2_kr")
        t_eu = mgr.get_tenant("sp2_eu")
        t_us = mgr.get_tenant("sp2_us")
        assert "kr-data" in t_kr.data_residency_endpoint
        assert "eu-data" in t_eu.data_residency_endpoint
        assert "us-data" in t_us.data_residency_endpoint

    def test_kms_key_provisioned_on_create(self, mgr):
        key = mgr.get_tenant_key("sp2_kr")
        assert key.version == 1
        assert key.key_id.startswith("kms-sp2_kr-")

    def test_kms_key_rotation_increments_version(self, mgr):
        rotated = mgr.rotate_tenant_key("sp2_kr")
        assert rotated.version == 2

    def test_kms_key_derive_data_key(self, mgr):
        key = mgr.get_tenant_key("sp2_eu")
        dk = key.derive_data_key("encryption")
        assert len(dk) == 32

    def test_duplicate_tenant_raises(self, mgr):
        from literary_system.tenant import TenantAlreadyExistsError, TenantRegion
        with pytest.raises(TenantAlreadyExistsError):
            mgr.create_tenant("sp2_kr", "중복", region=TenantRegion.KR)

    def test_not_found_raises(self, mgr):
        from literary_system.tenant import TenantNotFoundError
        with pytest.raises(TenantNotFoundError):
            mgr.get_tenant("nonexistent_xyz")

    def test_suspend_and_restore(self, mgr):
        from literary_system.tenant import TenantStatus, TenantInactiveError
        mgr.suspend_tenant("sp2_kr")
        assert mgr.get_tenant("sp2_kr").status == TenantStatus.SUSPENDED
        with pytest.raises(TenantInactiveError):
            mgr.require_active_tenant("sp2_kr")
        mgr.restore_tenant("sp2_kr")
        assert mgr.get_tenant("sp2_kr").is_active

    def test_logical_delete(self, mgr):
        from literary_system.tenant import TenantStatus, TenantInactiveError
        mgr.delete_tenant("sp2_us")
        assert mgr.get_tenant("sp2_us").status == TenantStatus.DELETED
        with pytest.raises(TenantInactiveError):
            mgr.require_active_tenant("sp2_us")

    def test_list_tenants_by_region(self, mgr):
        from literary_system.tenant import TenantRegion
        kr_tenants = mgr.list_tenants(region=TenantRegion.KR)
        assert any(t.tenant_id == "sp2_kr" for t in kr_tenants)

    def test_summary(self, mgr):
        s = mgr.summary()
        assert s["total_tenants"] >= 3
        assert s["kms_keys_provisioned"] >= 3


# ══════════════════════════════════════════════════════════════════════════════
# V458: TenantRouter + QuotaEnforcer
# ══════════════════════════════════════════════════════════════════════════════

class TestV458TenantRouterQuota:
    """리전 라우팅 및 할당량 강제."""

    def test_kr_routes_to_kr_endpoint(self, router):
        r = router.route("sp2_kr")
        assert "kr-api" in r.endpoint
        assert r.latency_hint_ms == 20

    def test_eu_routes_to_eu_endpoint(self, router):
        r = router.route("sp2_eu")
        assert "eu-api" in r.endpoint
        assert r.latency_hint_ms == 80

    def test_us_routes_to_us_endpoint(self, router):
        r = router.route("sp2_us")
        assert "us-api" in r.endpoint
        assert r.latency_hint_ms == 120

    def test_latency_order_kr_lt_eu_lt_us(self, router):
        r_kr = router.route("sp2_kr")
        r_eu = router.route("sp2_eu")
        r_us = router.route("sp2_us")
        assert r_kr.latency_hint_ms < r_eu.latency_hint_ms < r_us.latency_hint_ms

    def test_routing_key_contains_region(self, router):
        r = router.route("sp2_kr")
        assert "KR" in r.routing_key

    def test_quota_normal_usage(self, quota):
        snap = quota.check_and_record("sp2_kr", tokens=100, cost_usd=0.01)
        assert snap.tokens_used == 100
        assert snap.request_count == 1

    def test_quota_token_exceeded(self, mgr):
        from literary_system.tenant import QuotaEnforcer, QuotaExceededError, TenantRegion
        mgr.create_tenant("sp2_lim", "제한사", region=TenantRegion.KR,
                          max_tokens_per_month=100, max_cost_usd_per_month=10.0)
        q = QuotaEnforcer(mgr)
        q.check_and_record("sp2_lim", tokens=80, cost_usd=0.01)
        with pytest.raises(QuotaExceededError) as exc_info:
            q.check_and_record("sp2_lim", tokens=30, cost_usd=0.01)
        assert exc_info.value.quota_type == "tokens"

    def test_quota_cost_exceeded(self, mgr):
        from literary_system.tenant import QuotaEnforcer, QuotaExceededError, TenantRegion
        mgr.create_tenant("sp2_cost", "비용사", region=TenantRegion.EU,
                          max_tokens_per_month=1_000_000, max_cost_usd_per_month=5.0)
        q = QuotaEnforcer(mgr)
        q.check_and_record("sp2_cost", tokens=10, cost_usd=4.0)
        with pytest.raises(QuotaExceededError) as exc_info:
            q.check_and_record("sp2_cost", tokens=10, cost_usd=2.0)
        assert exc_info.value.quota_type == "cost_usd"

    def test_quota_remaining(self, mgr):
        from literary_system.tenant import QuotaEnforcer, TenantRegion
        mgr.create_tenant("sp2_rem", "잔량사", region=TenantRegion.KR,
                          max_tokens_per_month=1000, max_cost_usd_per_month=10.0)
        q = QuotaEnforcer(mgr)
        q.check_and_record("sp2_rem", tokens=300, cost_usd=3.0)
        rem = q.remaining_quota("sp2_rem")
        assert rem["tokens_remaining"] == 700
        assert abs(rem["cost_usd_remaining"] - 7.0) < 0.001

    def test_quota_reset(self, mgr):
        from literary_system.tenant import QuotaEnforcer
        q = QuotaEnforcer(mgr)
        q.check_and_record("sp2_kr", tokens=500, cost_usd=1.0)
        q.reset_usage("sp2_kr")
        snap = q.get_usage("sp2_kr")
        assert snap.tokens_used == 0

    def test_middleware_execute(self, mgr, quota, router):
        from literary_system.tenant import TenantContextMiddleware
        mw = TenantContextMiddleware(mgr, quota, router)
        ctx = mw.build_context("sp2_kr")
        result = mw.execute(ctx, lambda c: f"ok:{c.tenant_id}", tokens=10, cost_usd=0.001)
        assert result == "ok:sp2_kr"

    def test_middleware_quota_blocks_execution(self, mgr):
        from literary_system.tenant import (
            TenantContextMiddleware, TenantRouter, QuotaEnforcer,
            QuotaExceededError, TenantRegion
        )
        mgr.create_tenant("sp2_blk", "블락사", region=TenantRegion.KR,
                          max_tokens_per_month=10, max_cost_usd_per_month=1.0)
        q  = QuotaEnforcer(mgr)
        r  = TenantRouter(mgr)
        mw = TenantContextMiddleware(mgr, q, r)
        ctx = mw.build_context("sp2_blk")
        with pytest.raises(QuotaExceededError):
            mw.execute(ctx, lambda c: "should_not_run", tokens=100, cost_usd=0.001)


# ══════════════════════════════════════════════════════════════════════════════
# V459: BillingEngine
# ══════════════════════════════════════════════════════════════════════════════

class TestV459BillingEngine:
    """PG 다중화 결제 엔진."""

    def test_kr_uses_toss(self, billing_engine):
        from literary_system.billing import InvoiceLineItem, PaymentGatewayType
        items = [InvoiceLineItem("테스트", 1.0, 10.0)]
        rec = billing_engine.create_and_charge("t_kr", "KR", "2026-05", items)
        assert rec.gateway == PaymentGatewayType.TOSS

    def test_eu_uses_stripe(self, billing_engine):
        from literary_system.billing import InvoiceLineItem, PaymentGatewayType
        items = [InvoiceLineItem("테스트", 1.0, 10.0)]
        rec = billing_engine.create_and_charge("t_eu", "EU", "2026-05", items)
        assert rec.gateway == PaymentGatewayType.STRIPE

    def test_us_uses_stripe(self, billing_engine):
        from literary_system.billing import InvoiceLineItem, PaymentGatewayType
        items = [InvoiceLineItem("테스트", 1.0, 10.0)]
        rec = billing_engine.create_and_charge("t_us", "US", "2026-05", items)
        assert rec.gateway == PaymentGatewayType.STRIPE

    def test_krw_conversion(self, billing_engine):
        from literary_system.billing import InvoiceLineItem
        items = [InvoiceLineItem("1 USD", 1.0, 1.0)]
        rec = billing_engine.create_and_charge("t_conv", "KR", "2026-05", items)
        assert rec.amount_krw == 1350  # 1 USD * 1350

    def test_multi_line_items(self, billing_engine):
        from literary_system.billing import InvoiceLineItem
        items = [
            InvoiceLineItem("API", 1.0, 10.0),
            InvoiceLineItem("스토리지", 5.0, 2.0),
        ]
        rec = billing_engine.create_and_charge("t_multi", "EU", "2026-05", items)
        assert rec.amount_usd == 20.0

    def test_refund_changes_status(self, billing_engine):
        from literary_system.billing import InvoiceLineItem, PaymentStatus
        items = [InvoiceLineItem("환불테스트", 1.0, 5.0)]
        rec = billing_engine.create_and_charge("t_ref", "KR", "2026-05", items)
        refunded = billing_engine.refund(rec.record_id)
        assert refunded.status == PaymentStatus.REFUNDED

    def test_total_revenue_excludes_refunds(self, billing_engine):
        from literary_system.billing import InvoiceLineItem
        items = [InvoiceLineItem("수익", 1.0, 50.0)]
        rec1 = billing_engine.create_and_charge("t_rev1", "EU", "2026-05", items)
        rec2 = billing_engine.create_and_charge("t_rev2", "KR", "2026-05", items)
        billing_engine.refund(rec1.record_id)
        assert billing_engine.total_revenue_usd() == 50.0

    def test_gateway_txid_not_empty(self, billing_engine):
        from literary_system.billing import InvoiceLineItem
        items = [InvoiceLineItem("txid테스트", 1.0, 1.0)]
        rec = billing_engine.create_and_charge("t_txid", "KR", "2026-05", items)
        assert rec.gateway_txid != ""

    def test_payment_gateway_error_propagation(self):
        from literary_system.billing import (
            BillingEngine, InvoiceLineItem, PaymentGatewayRouter,
            StripeAdapter, TossPaymentsAdapter, PaymentGatewayError
        )

        def fail_fn(**kwargs):
            raise RuntimeError("PG 연결 실패")

        router = PaymentGatewayRouter(
            stripe_adapter=StripeAdapter(charge_fn=fail_fn),
            toss_adapter=TossPaymentsAdapter(charge_fn=fail_fn),
        )
        engine = BillingEngine(pg_router=router)
        items = [InvoiceLineItem("실패테스트", 1.0, 1.0)]
        with pytest.raises(PaymentGatewayError):
            engine.create_and_charge("t_fail", "KR", "2026-05", items)

    def test_invoice_list_by_tenant(self, billing_engine):
        from literary_system.billing import InvoiceLineItem
        items = [InvoiceLineItem("청구서목록", 1.0, 3.0)]
        billing_engine.create_and_charge("t_inv_list", "EU", "2026-05", items)
        billing_engine.create_and_charge("t_inv_list", "EU", "2026-06", items)
        invoices = billing_engine._invoicer.list_invoices("t_inv_list")
        assert len(invoices) == 2


# ══════════════════════════════════════════════════════════════════════════════
# V460: TenantAuditLog + ProductionMonitor
# ══════════════════════════════════════════════════════════════════════════════

class TestV460AuditLogMonitor:
    """hash chain 감사 로그 및 SLO 모니터링."""

    def test_audit_append_and_count(self, audit_log):
        from literary_system.tenant import AuditEventType
        audit_log.append("t001", AuditEventType.TENANT_CREATED, "system", "생성")
        audit_log.append("t001", AuditEventType.KMS_KEY_PROVISIONED, "system", "KMS")
        assert audit_log.count("t001") == 2

    def test_audit_hash_chain_valid(self, audit_log):
        from literary_system.tenant import AuditEventType
        for evt in [
            AuditEventType.TENANT_CREATED,
            AuditEventType.BILLING_CHARGED,
            AuditEventType.CONFIG_CHANGED,
            AuditEventType.ACCESS_GRANTED,
        ]:
            audit_log.append("t002", evt, "actor", evt.value)
        result = audit_log.verify_chain("t002")
        assert result["valid"] is True
        assert result["checked"] == 4

    def test_audit_hash_chain_tamper_detected(self, audit_log):
        from literary_system.tenant import AuditEventType
        audit_log.append("t003", AuditEventType.TENANT_CREATED, "s", "생성")
        # 수동으로 첫 레코드 hash 변조 시뮬레이션
        from literary_system.tenant.audit_log import AuditRecord
        old = audit_log._records[0]
        tampered = AuditRecord(
            record_id=old.record_id,
            tenant_id=old.tenant_id,
            event_type=old.event_type,
            actor=old.actor,
            description="TAMPERED",
            payload=old.payload,
            created_at=old.created_at,
            prev_hash=old.prev_hash,
            record_hash="bad_hash_000",
        )
        audit_log._records[0] = tampered
        result = audit_log.verify_chain("t003")
        assert result["valid"] is False

    def test_audit_filter_by_event_type(self, audit_log):
        from literary_system.tenant import AuditEventType
        audit_log.append("t004", AuditEventType.BILLING_CHARGED, "s", "결제1")
        audit_log.append("t004", AuditEventType.BILLING_CHARGED, "s", "결제2")
        audit_log.append("t004", AuditEventType.ACCESS_DENIED, "s", "접근 거부")
        billing = audit_log.get_records("t004", event_type=AuditEventType.BILLING_CHARGED)
        assert len(billing) == 2

    def test_monitor_slo_pass_all_fast(self, monitor):
        from literary_system.tenant import RequestSample, RequestOutcome
        for i in range(30):
            monitor.record(RequestSample("t_fast", 100.0, RequestOutcome.SUCCESS))
        report = monitor.get_slo_report("t_fast", window_minutes=60)
        assert report.p95_ok is True
        assert report.avail_ok is True
        assert report.overall_ok is True

    def test_monitor_slo_fail_p95(self, monitor):
        from literary_system.tenant import RequestSample, RequestOutcome
        for i in range(100):
            lat = 500.0 if i < 90 else 5000.0
            monitor.record(RequestSample("t_slow", lat, RequestOutcome.SUCCESS))
        report = monitor.get_slo_report("t_slow", window_minutes=60)
        assert report.p95_ok is False

    def test_monitor_slo_fail_availability(self, monitor):
        from literary_system.tenant import RequestSample, RequestOutcome
        for i in range(100):
            outcome = RequestOutcome.SUCCESS if i < 80 else RequestOutcome.ERROR
            monitor.record(RequestSample("t_err", 200.0, outcome))
        report = monitor.get_slo_report("t_err", window_minutes=60)
        assert report.avail_ok is False

    def test_monitor_alerts_fired_on_breach(self, monitor):
        from literary_system.tenant import RequestSample, RequestOutcome, AlertSeverity
        for i in range(20):
            lat = 200.0 if i < 18 else 8000.0
            monitor.record(RequestSample("t_alert", lat, RequestOutcome.SUCCESS))
        monitor.get_slo_report("t_alert", window_minutes=60)
        alerts = monitor.get_alerts("t_alert", severity=AlertSeverity.CRITICAL)
        assert len(alerts) >= 1

    def test_monitor_global_report(self, monitor):
        from literary_system.tenant import RequestSample, RequestOutcome
        for tid in ["t_g1", "t_g2"]:
            for _ in range(10):
                monitor.record(RequestSample(tid, 300.0, RequestOutcome.SUCCESS))
        global_r = monitor.get_global_report(window_minutes=60)
        assert global_r["total_tenants"] >= 2

    def test_monitor_db_callback(self):
        from literary_system.tenant import TenantAuditLog, AuditEventType
        captured = []
        log = TenantAuditLog(db_fn=lambda rec: captured.append(rec))
        log.append("t_cb", AuditEventType.TENANT_CREATED, "sys", "콜백테스트")
        assert len(captured) == 1
        assert captured[0]["event_type"] == "TENANT_CREATED"


# ══════════════════════════════════════════════════════════════════════════════
# V461: DRController + ADR-018 롤백
# ══════════════════════════════════════════════════════════════════════════════

class TestV461DRController:
    """RPO 1h 스냅샷 및 태그 기반 롤백."""

    def test_take_snapshot_qdrant(self, dr):
        from literary_system.dr import DRComponent
        snap = dr.take_snapshot(DRComponent.QDRANT)
        assert snap.component == DRComponent.QDRANT
        assert snap.size_bytes > 0
        assert snap.checksum != ""

    def test_take_full_snapshot_all_components(self, dr):
        from literary_system.dr import DRComponent
        snaps = dr.take_full_snapshot()
        assert len(snaps) == len(DRComponent)
        for comp in DRComponent:
            assert snaps[comp.value] is not None

    def test_rpo_verification_pass_after_snapshot(self, dr):
        from literary_system.dr import DRComponent
        dr.take_snapshot(DRComponent.QDRANT)
        result = dr.verify_rpo(DRComponent.QDRANT)
        assert result["rpo_ok"] is True
        assert result["age_minutes"] < 1.0

    def test_rpo_all_ok_after_full_snapshot(self, dr):
        dr.take_full_snapshot()
        result = dr.verify_all_rpo()
        assert result["all_ok"] is True

    def test_rpo_fail_without_snapshot(self, dr):
        from literary_system.dr import DRComponent
        result = dr.verify_rpo(DRComponent.POSTGRES)
        assert result["rpo_ok"] is False
        assert "스냅샷 없음" in result["reason"]

    def test_restore_from_snapshot(self, dr):
        from literary_system.dr import DRComponent
        snap = dr.take_snapshot(DRComponent.REDIS)
        res = dr.restore(snap.snapshot_id)
        assert res.success is True
        assert res.rto_minutes <= 240

    def test_restore_unknown_snapshot_raises(self, dr):
        from literary_system.dr import DRRestoreError
        with pytest.raises(DRRestoreError):
            dr.restore("SNAP-NONEXISTENT-0000")

    def test_register_tag_captures_snapshots(self, dr):
        tag = dr.register_tag("SP2", "V461", "통합 테스트 태그")
        assert tag.subphase == "SP2"
        assert tag.version == "V461"
        assert tag.is_current is True
        assert len(tag.snapshot_ids) > 0

    def test_rollback_to_previous_tag(self, dr):
        tag1 = dr.register_tag("SP1", "V456", "이전 태그")
        tag2 = dr.register_tag("SP2", "V462", "현재 태그")
        assert tag2.is_current is True

        rb = dr.rollback_to_tag(tag1.tag_id)
        assert rb.success is True
        assert rb.to_tag == tag1.tag_id

    def test_current_tag_updates_after_rollback(self, dr):
        tag1 = dr.register_tag("SP1", "V456", "이전 SP")
        dr.register_tag("SP2", "V462", "현재 SP")
        dr.rollback_to_tag(tag1.tag_id)
        current = dr.get_current_tag()
        assert current.tag_id == tag1.tag_id

    def test_custom_restore_fn_injection(self):
        from literary_system.dr import DRController, DRComponent, DRPolicy
        calls = []

        def mock_restore(**kwargs):
            calls.append(kwargs)
            return {"success": True, "rto_minutes": 5.0}

        dr = DRController(
            policy=DRPolicy(rpo_minutes=60),
            restore_fn=mock_restore,
        )
        snap = dr.take_snapshot(DRComponent.QDRANT)
        res = dr.restore(snap.snapshot_id)
        assert res.success is True
        assert res.rto_minutes == 5.0
        assert len(calls) == 1

    def test_dr_summary(self, dr):
        dr.take_full_snapshot()
        dr.register_tag("SP2", "V462", "요약 테스트")
        s = dr.summary()
        assert s["snapshots"] >= 3
        assert s["tags"] >= 1
        assert s["current_tag"] == "V462"
        assert s["rpo_all_ok"] is True


# ══════════════════════════════════════════════════════════════════════════════
# V462: Gate16 + Release Gate
# ══════════════════════════════════════════════════════════════════════════════

class TestV462Gate16:
    """Gate16 SP2 생존 검증."""

    def test_gate16_pass(self):
        from literary_system.gates.gate16_sp2_tenant import _gate_sp2_tenant_survival
        result = _gate_sp2_tenant_survival()
        assert result.get("pass") is True, result.get("reason", "")

    def test_gate16_modules_verified_count(self):
        from literary_system.gates.gate16_sp2_tenant import _gate_sp2_tenant_survival
        result = _gate_sp2_tenant_survival()
        assert result.get("modules_verified", 0) >= 7

    def test_gate16_billing_records_created(self):
        from literary_system.gates.gate16_sp2_tenant import _gate_sp2_tenant_survival
        result = _gate_sp2_tenant_survival()
        assert result.get("billing_records", 0) >= 2

    def test_gate16_audit_chain_ok(self):
        from literary_system.gates.gate16_sp2_tenant import _gate_sp2_tenant_survival
        result = _gate_sp2_tenant_survival()
        assert result.get("audit_chain_ok") is True

    def test_gate16_rpo_ok(self):
        from literary_system.gates.gate16_sp2_tenant import _gate_sp2_tenant_survival
        result = _gate_sp2_tenant_survival()
        assert result.get("rpo_all_ok") is True


class TestV462ReleaseGate:
    """V462 통합 릴리스 게이트 검증."""

    def test_release_gate_version(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["version"] in ("V462", "V467", "V468", "V474", "V480", "V481", "V485", "V491", "V497", "V546", "V555", "V556", "V561", "V571")

    def test_release_gate_14_plus_gates(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["gates_checked"] >= 14

    def test_release_gate_gate16_present(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert "sp2_tenant_survival" in result["results"]

    def test_release_gate_gate16_pass(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["results"]["sp2_tenant_survival"].get("pass") is True

    def test_release_gate_overall_status(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["status"] == "pass", f"실패 게이트: {result.get('issues', [])}"
