"""
Gate 18 — SP3 Compliance Sovereignty (V467)

SP3 Compliance 모듈 4종 생존 검증:
  1. PIAGenerator (pia_generator.py)
  2. EUAIActGovernance (eu_ai_act.py)
  3. PIIScannerV2 (pii_scanner_v2.py)
  4. AuditTrailDB + hash chain (audit_trail_db.py)
  5. DataResidencyRouter + 정책 검증 (data_residency_router.py)
"""
from __future__ import annotations


def _gate_sp3_compliance_sovereignty() -> dict:
    """SP3 Compliance·Governance·Data Sovereignty 핵심 모듈 생존 검증 (Gate 18)."""
    verified: list[str] = []
    errors: list[str] = []

    # --- 1. PIAGenerator ---
    try:
        from literary_system.compliance.pia_generator import (
            DataCategory,
            LegalBasis,
            PIAGenerator,
            ProcessingActivity,
            RiskLevel,
        )
        gen = PIAGenerator()
        act = ProcessingActivity(
            name="gate_check", purpose="compliance_test",
            data_categories=[DataCategory.HEALTH],
            legal_basis=LegalBasis.CONSENT,
        )
        report = gen.generate("gate_tenant", act)
        assert report.dpo_required is True
        assert report.overall_risk in (RiskLevel.HIGH, RiskLevel.VERY_HIGH)
        assert report.checksum
        verified.append("PIAGenerator[HIGH_RISK+DPO]")
    except Exception as e:
        errors.append(f"PIAGenerator: {e}")

    # --- 2. EUAIActGovernance ---
    try:
        from literary_system.compliance.eu_ai_act import (
            AIRiskCategory,
            AISystemProfile,
            EUAIActGovernance,
            TransparencyObligation,
        )
        gov = EUAIActGovernance()
        profile = AISystemProfile(
            system_id="gate_sys", name="test", purpose="test",
            generates_synthetic_content=True, interacts_with_users=True,
        )
        clf = gov.classify_system(profile)
        assert clf.risk_category == AIRiskCategory.LIMITED_RISK
        assert TransparencyObligation.AI_WATERMARK in clf.transparency_obligations
        rec = gov.apply_watermark("t1", "gate_sys", "c001", "test content")
        assert gov.verify_watermark(rec.record_id, "test content", "c001", "gate_sys")
        verified.append("EUAIActGovernance[LIMITED_RISK+WATERMARK]")
    except Exception as e:
        errors.append(f"EUAIActGovernance: {e}")

    # --- 3. PIIScannerV2 ---
    try:
        from literary_system.compliance.pii_scanner_v2 import MaskMode, PIIScannerV2, PIIType
        scanner = PIIScannerV2(mask_mode=MaskMode.PARTIAL)
        result = scanner.scan("연락처: 010-1234-5678, 이메일: test@example.com")
        assert result.pii_found
        types = {m.pii_type for m in result.matches}
        assert PIIType.EMAIL in types
        assert PIIType.PHONE_KR in types
        assert "010-1234-5678" not in result.sanitized_text
        verified.append(f"PIIScannerV2[{len(result.matches)} matches masked]")
    except Exception as e:
        errors.append(f"PIIScannerV2: {e}")

    # --- 4. AuditTrailDB hash chain ---
    try:
        from literary_system.compliance.audit_trail_db import AuditEventType, AuditSeverity, AuditTrailDB
        db = AuditTrailDB()
        r1 = db.log("gate_t", AuditEventType.CONSENT_GRANTED, "user", "api", "GRANT")
        r2 = db.log("gate_t", AuditEventType.PERSONAL_DATA_ACCESS, "sys", "table", "SELECT")
        r3 = db.log("gate_t", AuditEventType.DELETION_CASCADE, "engine", "all", "DELETE")
        assert r2.prev_hash == r1.record_hash
        assert r3.prev_hash == r2.record_hash
        report = db.verify_chain("gate_t")
        assert report.valid
        assert report.total_records == 3
        verified.append("AuditTrailDB[3 records, chain OK]")
    except Exception as e:
        errors.append(f"AuditTrailDB: {e}")

    # --- 5. DataResidencyRouter ---
    try:
        from literary_system.compliance.data_residency_router import (
            DataRegion,
            DataResidencyRouter,
            ResidencyPolicy,
            RouteResult,
            TenantResidencyConfig,
        )
        router = DataResidencyRouter()
        # KR-only 테넌트 설정
        router.set_tenant_config(TenantResidencyConfig(
            tenant_id="kr_tenant", policy=ResidencyPolicy.KR_ONLY
        ))
        # 허용 지역
        d1 = router.route("kr_tenant", DataRegion.KR_SEOUL)
        assert d1.result == RouteResult.ROUTED
        # 위반 지역
        d2 = router.route("kr_tenant", DataRegion.US_VA)
        assert d2.result in (RouteResult.VIOLATION, RouteResult.FALLBACK)
        violations = router.get_violations("kr_tenant")
        assert len(violations) == 1
        verified.append("DataResidencyRouter[KR_ONLY policy, violation detected]")
    except Exception as e:
        errors.append(f"DataResidencyRouter: {e}")

    if errors:
        return {
            "pass": False,
            "verified": verified,
            "errors": errors,
            "summary": f"Gate18 FAIL: {'; '.join(errors)}",
        }

    return {
        "pass": True,
        "modules_verified": len(verified),
        "symbols_verified": verified,
        "summary": f"Gate18 PASS: SP3 Compliance/Governance/DataSovereignty ALL OK ({len(verified)}/5)",
    }
