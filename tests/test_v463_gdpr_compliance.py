"""
test_v463_gdpr_compliance.py — V463 GDPR Compliance Module 테스트

ADR-011: GDPR/PIPA Dual Compliance
커버리지 목표:
  - PIAGenerator: 7개 위험 규칙 × 시나리오
  - DPOWorkflow: 상태 전이 전체
  - CrossBorderTransferAPI: 국가별 결정
  - DeletionCascade: 카스케이드 + dry_run + 법적 보존
"""
import pytest
from datetime import datetime, timedelta, timezone

from literary_system.compliance.pia_generator import (
    PIAGenerator, ProcessingActivity, DataCategory, LegalBasis,
    RiskLevel, PIAStatus, PIARiskItem,
)
from literary_system.compliance.dpo_workflow import (
    DPOWorkflow, DPORequest, DPOStatus, DPORequestType,
)
from literary_system.compliance.cross_border_api import (
    CrossBorderTransferAPI, TransferDecision, TransferBasis,
)
from literary_system.compliance.deletion_cascade import (
    DeletionCascade, DeletionScope, DeletionStatus,
)


# ===========================================================================
# PIAGenerator 테스트
# ===========================================================================

class TestPIAGenerator:

    def _gen(self) -> PIAGenerator:
        return PIAGenerator()

    def _activity(self, **kwargs) -> ProcessingActivity:
        defaults = dict(
            name="테스트 처리",
            purpose="서비스 개선",
            data_categories=[DataCategory.GENERAL],
            legal_basis=LegalBasis.CONSENT,
            recipients=[],
            retention_days=180,
            cross_border=False,
            automated_decision=False,
            children_data=False,
        )
        defaults.update(kwargs)
        return ProcessingActivity(**defaults)

    # --- 기본 생성 ---
    def test_generate_low_risk(self):
        gen = self._gen()
        act = self._activity()
        report = gen.generate("tenant_1", act)
        assert report.pia_id
        assert report.overall_risk == RiskLevel.LOW
        assert report.dpo_required is False
        assert report.status == PIAStatus.DRAFT
        assert report.checksum  # 체크섬 존재

    def test_generate_sensitive_data_high_risk(self):
        gen = self._gen()
        act = self._activity(data_categories=[DataCategory.HEALTH])
        report = gen.generate("tenant_1", act)
        assert report.overall_risk in (RiskLevel.HIGH, RiskLevel.VERY_HIGH)
        assert report.dpo_required is True
        assert report.status == PIAStatus.PENDING_DPO

    def test_generate_biometric_very_high(self):
        gen = self._gen()
        act = self._activity(
            data_categories=[DataCategory.BIOMETRIC],
            children_data=True,
        )
        report = gen.generate("tenant_1", act)
        assert report.overall_risk == RiskLevel.VERY_HIGH
        assert report.dpo_required is True
        # 두 가지 위험 규칙 적용 확인
        categories = [r.category for r in report.risk_items]
        assert any("민감" in c or "아동" in c for c in categories)

    def test_generate_cross_border_risk(self):
        gen = self._gen()
        act = self._activity(cross_border=True)
        report = gen.generate("tenant_1", act)
        assert any("국경" in r.category for r in report.risk_items)

    def test_generate_automated_decision_risk(self):
        gen = self._gen()
        act = self._activity(automated_decision=True)
        report = gen.generate("tenant_1", act)
        assert any("자동화" in r.category for r in report.risk_items)

    def test_generate_children_data_risk(self):
        gen = self._gen()
        act = self._activity(children_data=True)
        report = gen.generate("tenant_1", act)
        assert any("아동" in r.category for r in report.risk_items)

    def test_generate_long_retention_risk(self):
        gen = self._gen()
        act = self._activity(retention_days=365 * 4)
        report = gen.generate("tenant_1", act)
        assert any("보존" in r.category for r in report.risk_items)

    def test_generate_legitimate_interest_risk(self):
        gen = self._gen()
        act = self._activity(legal_basis=LegalBasis.LEGITIMATE_INTEREST)
        report = gen.generate("tenant_1", act)
        assert any("정당한 이익" in r.category for r in report.risk_items)

    def test_generate_many_recipients_risk(self):
        gen = self._gen()
        act = self._activity(recipients=["A", "B", "C", "D", "E", "F"])
        report = gen.generate("tenant_1", act)
        assert any("수신자" in r.category for r in report.risk_items)

    # --- 저장/조회 ---
    def test_get_report(self):
        gen = self._gen()
        act = self._activity()
        report = gen.generate("t1", act)
        fetched = gen.get_report(report.pia_id)
        assert fetched is not None
        assert fetched.pia_id == report.pia_id

    def test_list_reports_by_tenant(self):
        gen = self._gen()
        gen.generate("t1", self._activity(name="A"))
        gen.generate("t1", self._activity(name="B"))
        gen.generate("t2", self._activity(name="C"))
        assert len(gen.list_reports("t1")) == 2
        assert len(gen.list_reports("t2")) == 1

    def test_pending_dpo_reports(self):
        gen = self._gen()
        gen.generate("t1", self._activity())           # low risk → not pending
        gen.generate("t1", self._activity(data_categories=[DataCategory.HEALTH]))  # high → pending
        pending = gen.pending_dpo_reports()
        assert len(pending) == 1

    # --- to_dict 직렬화 ---
    def test_to_dict_keys(self):
        gen = self._gen()
        report = gen.generate("t1", self._activity())
        d = report.to_dict()
        for key in ("pia_id", "tenant_id", "activity", "risk_items",
                    "overall_risk", "dpo_required", "status", "created_at",
                    "recommendations", "checksum"):
            assert key in d

    # --- 위험 점수 로직 ---
    def test_risk_item_score(self):
        item = PIARiskItem("cat", "desc", likelihood=4, impact=5, mitigation="m")
        assert item.score == 20
        assert item.level == RiskLevel.VERY_HIGH

    def test_risk_item_medium(self):
        item = PIARiskItem("cat", "desc", likelihood=2, impact=4, mitigation="m")
        assert item.score == 8
        assert item.level == RiskLevel.MEDIUM


# ===========================================================================
# DPOWorkflow 테스트
# ===========================================================================

class TestDPOWorkflow:

    def _wf(self) -> DPOWorkflow:
        return DPOWorkflow()

    def _req(self, wf: DPOWorkflow, **kwargs) -> DPORequest:
        defaults = dict(
            tenant_id="t1",
            request_type=DPORequestType.PIA_REVIEW,
            title="테스트 요청",
            description="설명",
            requester="user_a",
        )
        defaults.update(kwargs)
        return wf.create_request(**defaults)

    # --- 생성 ---
    def test_create_request_pending(self):
        wf = self._wf()
        req = self._req(wf)
        assert req.request_id
        assert req.status == DPOStatus.PENDING
        assert len(req.audit_trail) == 1
        assert req.audit_trail[0]["event"] == "CREATED"

    def test_deadline_30_days(self):
        wf = self._wf()
        req = self._req(wf)
        created = datetime.fromisoformat(req.created_at)
        deadline = datetime.fromisoformat(req.deadline_at)
        assert (deadline - created).days == 30

    # --- 상태 전이 ---
    def test_start_review(self):
        wf = self._wf()
        req = self._req(wf)
        wf.start_review(req.request_id, "dpo_officer")
        assert req.status == DPOStatus.UNDER_REVIEW
        assert req.reviewer == "dpo_officer"

    def test_approve(self):
        wf = self._wf()
        req = self._req(wf)
        wf.start_review(req.request_id, "dpo_officer")
        wf.approve(req.request_id, "dpo_officer", "문제없음")
        assert req.status == DPOStatus.APPROVED
        assert req.decision_notes == "문제없음"

    def test_approve_with_conditions(self):
        wf = self._wf()
        req = self._req(wf)
        wf.start_review(req.request_id, "dpo_officer")
        conds = ["SCC 체결 선행", "암호화 적용"]
        wf.approve_with_conditions(req.request_id, "dpo_officer", conds)
        assert req.status == DPOStatus.CONDITIONALLY_APPROVED
        assert req.conditions == conds

    def test_reject(self):
        wf = self._wf()
        req = self._req(wf)
        wf.start_review(req.request_id, "dpo_officer")
        wf.reject(req.request_id, "dpo_officer", "법적 근거 불충분")
        assert req.status == DPOStatus.REJECTED

    def test_cannot_approve_without_review(self):
        wf = self._wf()
        req = self._req(wf)
        with pytest.raises(ValueError):
            wf.approve(req.request_id, "dpo_officer")

    # --- 에스컬레이션 ---
    def test_escalation(self):
        wf = self._wf()
        req = self._req(wf)
        # deadline을 과거로 조작
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        req.deadline_at = past
        escalated = wf.check_escalations()
        assert len(escalated) == 1
        assert req.status == DPOStatus.ESCALATED

    def test_no_escalation_if_completed(self):
        wf = self._wf()
        req = self._req(wf)
        wf.start_review(req.request_id, "dpo")
        wf.approve(req.request_id, "dpo")
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        req.deadline_at = past
        escalated = wf.check_escalations()
        assert len(escalated) == 0

    # --- 조회 ---
    def test_list_by_tenant(self):
        wf = self._wf()
        self._req(wf, tenant_id="t1")
        self._req(wf, tenant_id="t1")
        self._req(wf, tenant_id="t2")
        assert len(wf.list_by_tenant("t1")) == 2

    def test_list_pending(self):
        wf = self._wf()
        req1 = self._req(wf)
        req2 = self._req(wf)
        wf.start_review(req2.request_id, "dpo")
        wf.approve(req2.request_id, "dpo")
        pending = wf.list_pending()
        assert len(pending) == 1
        assert pending[0].request_id == req1.request_id

    # --- to_dict ---
    def test_to_dict(self):
        wf = self._wf()
        req = self._req(wf)
        d = req.to_dict()
        assert d["status"] == "pending"
        assert "audit_trail" in d


# ===========================================================================
# CrossBorderTransferAPI 테스트
# ===========================================================================

class TestCrossBorderTransferAPI:

    def _api(self) -> CrossBorderTransferAPI:
        return CrossBorderTransferAPI()

    def _eval(self, api, source="EU", target="US", categories=None):
        return api.evaluate_transfer(
            tenant_id="t1",
            source_region=source,
            target_country=target,
            data_categories=categories or ["general"],
            purpose="analytics",
            recipient="partner_corp",
        )

    # --- 적정성 결정 국가 ---
    def test_eu_to_kr_adequacy(self):
        api = self._api()
        req = self._eval(api, source="EU", target="KR")
        assert req.decision == TransferDecision.ALLOWED
        assert req.basis == TransferBasis.ADEQUACY_DECISION

    def test_eu_to_jp_adequacy(self):
        api = self._api()
        req = self._eval(api, source="EU", target="JP")
        assert req.decision == TransferDecision.ALLOWED

    # --- SCC 국가 ---
    def test_eu_to_us_scc(self):
        api = self._api()
        req = self._eval(api, source="EU", target="US")
        assert req.decision == TransferDecision.ALLOWED_WITH_SAFEGUARDS
        assert req.basis == TransferBasis.SCC
        assert len(req.safeguards) > 0

    def test_eu_to_us_sensitive_requires_dpo(self):
        api = self._api()
        req = self._eval(api, source="EU", target="US", categories=["health"])
        assert req.decision == TransferDecision.REQUIRES_DPO

    # --- 금지 국가 ---
    def test_prohibited_country_denied(self):
        api = self._api()
        req = self._eval(api, source="EU", target="KP")
        assert req.decision == TransferDecision.DENIED
        assert req.basis == TransferBasis.DENIED

    # --- 한국 소스 ---
    def test_kr_to_us_scc(self):
        api = self._api()
        req = self._eval(api, source="KR", target="US")
        assert req.decision in (TransferDecision.ALLOWED_WITH_SAFEGUARDS, TransferDecision.REQUIRES_DPO)

    def test_kr_to_us_sensitive_dpo(self):
        api = self._api()
        req = self._eval(api, source="KR", target="US", categories=["sensitive"])
        assert req.decision == TransferDecision.REQUIRES_DPO

    # --- 조회 ---
    def test_list_by_tenant(self):
        api = self._api()
        self._eval(api)
        self._eval(api)
        assert len(api.list_by_tenant("t1")) == 2

    def test_list_denied(self):
        api = self._api()
        self._eval(api, target="US")
        self._eval(api, target="KP")
        denied = api.list_denied()
        assert len(denied) == 1

    def test_list_requires_dpo(self):
        api = self._api()
        self._eval(api, target="US", categories=["health"])
        self._eval(api, target="US", categories=["general"])
        requires = api.list_requires_dpo()
        assert len(requires) == 1

    # --- to_dict ---
    def test_to_dict(self):
        api = self._api()
        req = self._eval(api)
        d = req.to_dict()
        for k in ("request_id", "tenant_id", "decision", "basis", "safeguards"):
            assert k in d


# ===========================================================================
# DeletionCascade 테스트
# ===========================================================================

class TestDeletionCascade:

    def _dc(self, **kwargs) -> DeletionCascade:
        return DeletionCascade(dry_run=True, **kwargs)

    # --- 요청 생성 ---
    def test_create_request(self):
        dc = self._dc()
        req = dc.create_request("t1", "user_1", DeletionScope.FULL, "탈퇴")
        assert req.request_id
        assert req.status == DeletionStatus.PENDING
        assert req.scope == DeletionScope.FULL

    def test_deadline_30_days(self):
        dc = self._dc()
        req = dc.create_request("t1", "u1", DeletionScope.FULL, "reason")
        created = datetime.fromisoformat(req.created_at)
        deadline = datetime.fromisoformat(req.deadline_at)
        assert (deadline - created).days == 30

    # --- 실행 (dry_run) ---
    def test_execute_full_dry_run(self):
        dc = self._dc()
        req = dc.create_request("t1", "u1", DeletionScope.FULL, "탈퇴")
        result = dc.execute(req.request_id)
        assert result.status in (
            DeletionStatus.COMPLETED, DeletionStatus.PARTIALLY_COMPLETED
        )
        assert len(result.targets) > 0
        assert result.certificate_id is not None

    def test_execute_has_legal_hold_layers(self):
        dc = self._dc()
        req = dc.create_request("t1", "u1", DeletionScope.FULL, "탈퇴")
        result = dc.execute(req.request_id)
        # billing_records와 audit_logs는 quarantined > 0
        billing = next((t for t in result.targets if t.layer == "billing_records"), None)
        audit = next((t for t in result.targets if t.layer == "audit_logs"), None)
        assert billing is not None and billing.quarantined > 0
        assert audit is not None and audit.quarantined > 0

    def test_execute_data_only_no_account(self):
        dc = self._dc()
        req = dc.create_request("t1", "u1", DeletionScope.DATA_ONLY, "데이터 삭제")
        result = dc.execute(req.request_id)
        layers = [t.layer for t in result.targets]
        assert "tenant_account" not in layers

    def test_partial_completed_status(self):
        dc = self._dc()
        req = dc.create_request("t1", "u1", DeletionScope.FULL, "탈퇴")
        result = dc.execute(req.request_id)
        # dry_run에서는 legal hold → PARTIALLY_COMPLETED
        assert result.status == DeletionStatus.PARTIALLY_COMPLETED

    def test_certificate_issued(self):
        dc = self._dc()
        req = dc.create_request("t1", "u1", DeletionScope.FULL, "탈퇴")
        result = dc.execute(req.request_id)
        assert result.certificate_id is not None
        assert "DEL-CERT" in result.certificate_id

    # --- 커스텀 핸들러 ---
    def test_custom_handler(self):
        handled = {}

        def handler(tenant_id: str, subject_id: str) -> int:
            handled["called"] = True
            return 5

        dc = DeletionCascade(
            layer_handlers={"sessions": handler},
            dry_run=False,
        )
        req = dc.create_request("t1", "u1", DeletionScope.DATA_ONLY, "test")
        result = dc.execute(req.request_id)
        assert handled.get("called") is True
        sessions_target = next(t for t in result.targets if t.layer == "sessions")
        assert sessions_target.deleted == 5

    # --- 기한 초과 ---
    def test_overdue_requests(self):
        dc = self._dc()
        req = dc.create_request("t1", "u1", DeletionScope.FULL, "탈퇴")
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        req.deadline_at = past
        overdue = dc.overdue_requests()
        assert len(overdue) == 1

    # --- 조회 ---
    def test_list_by_tenant(self):
        dc = self._dc()
        dc.create_request("t1", "u1", DeletionScope.FULL, "r")
        dc.create_request("t1", "u2", DeletionScope.FULL, "r")
        dc.create_request("t2", "u3", DeletionScope.FULL, "r")
        assert len(dc.list_by_tenant("t1")) == 2

    # --- to_dict ---
    def test_to_dict_after_execute(self):
        dc = self._dc()
        req = dc.create_request("t1", "u1", DeletionScope.FULL, "탈퇴")
        dc.execute(req.request_id)
        d = req.to_dict()
        assert "targets" in d
        assert "certificate_id" in d
        assert d["certificate_id"] is not None


# ===========================================================================
# 통합 시나리오 — PIA → DPO → 이전 결정 → 삭제
# ===========================================================================

class TestV463Integration:

    def test_full_gdpr_flow(self):
        """PIA 고위험 → DPO 요청 → 조건부 승인 → 국경 이전 평가 → 삭제"""
        # 1. PIA 생성 (민감정보 + 국경 이전)
        gen = PIAGenerator()
        act = ProcessingActivity(
            name="글로벌 AI 추천",
            purpose="사용자 맞춤 소설 추천",
            data_categories=[DataCategory.BEHAVIORAL, DataCategory.SENSITIVE],
            legal_basis=LegalBasis.LEGITIMATE_INTEREST,
            recipients=["EU_partner", "US_partner", "SG_partner", "JP_partner",
                        "AU_partner", "IN_partner"],
            retention_days=365 * 2,
            cross_border=True,
            automated_decision=True,
            children_data=False,
        )
        pia = gen.generate("tenant_global", act)
        assert pia.dpo_required is True
        assert pia.overall_risk in (RiskLevel.HIGH, RiskLevel.VERY_HIGH)

        # 2. DPO 요청
        wf = DPOWorkflow()
        dpo_req = wf.create_request(
            tenant_id="tenant_global",
            request_type=DPORequestType.PIA_REVIEW,
            title="글로벌 AI 추천 PIA 검토",
            description=f"PIA ID: {pia.pia_id}",
            requester="privacy_team",
            related_pia_id=pia.pia_id,
        )
        wf.start_review(dpo_req.request_id, "chief_dpo")
        wf.approve_with_conditions(
            dpo_req.request_id, "chief_dpo",
            conditions=["SCC 체결 필수", "LIA 문서화", "자동화 결정 이의제기 API 구현"],
        )
        assert dpo_req.status == DPOStatus.CONDITIONALLY_APPROVED

        # 3. 국경 이전 평가
        transfer_api = CrossBorderTransferAPI()
        transfer = transfer_api.evaluate_transfer(
            tenant_id="tenant_global",
            source_region="KR",
            target_country="US",
            data_categories=["behavioral"],
            purpose="AI model training",
            recipient="US_partner",
        )
        assert transfer.decision != TransferDecision.DENIED

        # 4. 삭제 요청
        dc = DeletionCascade(dry_run=True)
        del_req = dc.create_request(
            "tenant_global", "user_123",
            DeletionScope.DATA_ONLY, "사용자 탈퇴 요청"
        )
        result = dc.execute(del_req.request_id)
        assert result.status != DeletionStatus.FAILED
        assert result.certificate_id is not None
