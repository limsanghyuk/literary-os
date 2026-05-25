"""
tests/unit/test_v629_phase_b_docs.py

V629 — Phase B 운영 문서 완성 + API 레퍼런스 + ATIA 메타데이터 외부 감사 패키지
ADR-096: 3종 모듈 검증

TC-01~20: TestOpsRunbook (ops_runbook.py)
TC-21~40: TestAPIReferenceGenerator (api_reference_generator.py)
TC-41~60: TestATIAMetadataAuditor (atia_metadata_auditor.py)

총 60 TC — LLM-0 원칙 준수
"""
import json
import math
import pytest
from typing import Any, Dict

from literary_system.ops.ops_runbook import (
    OpsRunbook,
    RunbookStep,
    RunbookResult,
    StepResult,
    StepStatus,
    RunbookSeverity,
    build_health_check_runbook,
)
from literary_system.docs.api_reference_generator import (
    APIReferenceGenerator,
    APIReferenceReport,
    EndpointSpec,
    HTTPMethod,
    ParamSpec,
    ResponseSpec,
)
from literary_system.audit.atia_metadata_auditor import (
    ATIAMetadataAuditor,
    ATIAMetadataRecord,
    ATIAAuditReport,
    ATIADimension,
    ATIARiskLevel,
    _risk_from_score,
)


# ======================================================================= #
# TC-01~20: TestOpsRunbook                                                 #
# ======================================================================= #

class TestOpsRunbook:
    """OpsRunbook 20 TC."""

    # --- 헬퍼 -----------------------------------------------------------

    @staticmethod
    def _ok_step(name: str, val: Any = True) -> RunbookStep:
        return RunbookStep(
            name=name,
            description=f"{name} 단계",
            action_fn=lambda ctx, v=val: v,
        )

    @staticmethod
    def _fail_step(name: str) -> RunbookStep:
        return RunbookStep(
            name=name,
            description=f"{name} 실패 단계",
            action_fn=lambda ctx: (_ for _ in ()).throw(RuntimeError(f"{name} 실패")),
        )

    @staticmethod
    def _rollback_tracking_step(name: str, log: list) -> RunbookStep:
        def act(ctx: Dict) -> str:
            return "done"

        def rb(ctx: Dict) -> None:
            log.append(f"rolled_back:{name}")

        return RunbookStep(name=name, description=name, action_fn=act, rollback_fn=rb)

    # TC-01: 빈 런북 생성
    def test_tc01_create_empty_runbook(self):
        rb = OpsRunbook("test_rb")
        assert rb.step_count() == 0
        assert rb.name == "test_rb"

    # TC-02: 단계 추가 체이닝
    def test_tc02_add_step_chaining(self):
        rb = OpsRunbook("chain_rb")
        result = rb.add_step(self._ok_step("s1")).add_step(self._ok_step("s2"))
        assert result is rb
        assert rb.step_count() == 2

    # TC-03: 단순 성공 실행
    def test_tc03_execute_success(self):
        rb = OpsRunbook("success_rb")
        rb.add_step(self._ok_step("s1")).add_step(self._ok_step("s2"))
        res = rb.execute()
        assert res.success is True
        assert res.steps_succeeded == 2
        assert res.steps_failed == 0

    # TC-04: 실패 단계 — stop_on_failure=True
    def test_tc04_execute_stop_on_failure(self):
        rb = OpsRunbook("fail_rb")
        rb.add_step(self._ok_step("s1"))
        rb.add_step(self._fail_step("s2"))
        rb.add_step(self._ok_step("s3"))
        res = rb.execute(stop_on_failure=True)
        assert res.success is False
        assert res.failed_step == "s2"
        # s3 는 실행되지 않아야 함
        names = [r.step_name for r in res.step_results]
        assert "s3" not in names

    # TC-05: 실패 단계 — stop_on_failure=False (계속 실행)
    def test_tc05_execute_continue_on_failure(self):
        rb = OpsRunbook("continue_rb")
        rb.add_step(self._ok_step("s1"))
        rb.add_step(self._fail_step("s2"))
        rb.add_step(self._ok_step("s3"))
        res = rb.execute(stop_on_failure=False)
        assert res.success is False
        assert res.steps_executed == 3
        assert res.steps_succeeded == 2

    # TC-06: 롤백 역순 호출 검증
    def test_tc06_rollback_reverse_order(self):
        log = []
        rb = OpsRunbook("rollback_rb")
        rb.add_step(self._rollback_tracking_step("s1", log))
        rb.add_step(self._rollback_tracking_step("s2", log))
        rb.add_step(self._fail_step("s3"))
        rb.execute(stop_on_failure=True)
        assert log == ["rolled_back:s2", "rolled_back:s1"]

    # TC-07: dry_run — skip_on_dry_run=True 단계 건너뜀
    def test_tc07_dry_run_skip(self):
        rb = OpsRunbook("dry_rb")
        rb.add_step(self._ok_step("s1"))
        rb.add_step(RunbookStep(
            name="deploy",
            description="배포",
            action_fn=lambda ctx: "deployed",
            skip_on_dry_run=True,
        ))
        res = rb.execute(dry_run=True)
        assert res.success is True
        statuses = {r.step_name: r.status for r in res.step_results}
        assert statuses["deploy"] == StepStatus.SKIPPED

    # TC-08: 컨텍스트 공유
    def test_tc08_context_sharing(self):
        rb = OpsRunbook("ctx_rb")
        rb.add_step(RunbookStep("writer", "쓰기", action_fn=lambda ctx: ctx.update({"value": 42}) or 42))
        rb.add_step(RunbookStep("reader", "읽기", action_fn=lambda ctx: ctx.get("value")))
        ctx: Dict[str, Any] = {}
        res = rb.execute(context=ctx)
        assert res.success is True
        # 컨텍스트에 결과 저장 확인
        assert ctx.get("__result_reader") == 42

    # TC-09: validate — 중복 이름 감지
    def test_tc09_validate_duplicate_names(self):
        rb = OpsRunbook("dup_rb")
        rb.add_step(self._ok_step("same"))
        rb.add_step(self._ok_step("same"))
        errors = rb.validate()
        assert any("중복" in e for e in errors)

    # TC-10: validate — 빈 런북
    def test_tc10_validate_empty(self):
        rb = OpsRunbook("empty_rb")
        errors = rb.validate()
        assert any("단계" in e for e in errors)

    # TC-11: to_dict 직렬화
    def test_tc11_to_dict(self):
        rb = OpsRunbook("dict_rb", "설명")
        rb.add_step(self._ok_step("s1"))
        d = rb.to_dict()
        assert d["name"] == "dict_rb"
        assert d["step_count"] == 1
        assert len(d["steps"]) == 1

    # TC-12: StepResult.succeeded / failed 프로퍼티
    def test_tc12_step_result_properties(self):
        ok = StepResult("s1", StepStatus.SUCCESS)
        fail = StepResult("s2", StepStatus.FAILED)
        assert ok.succeeded is True
        assert ok.failed is False
        assert fail.succeeded is False
        assert fail.failed is True

    # TC-13: RunbookResult.all_passed
    def test_tc13_runbook_result_all_passed(self):
        rb = OpsRunbook("allpass_rb")
        rb.add_step(self._ok_step("s1"))
        res = rb.execute()
        assert res.all_passed is True

    # TC-14: RunbookResult.summary 문자열
    def test_tc14_runbook_result_summary(self):
        rb = OpsRunbook("summary_rb")
        rb.add_step(self._ok_step("s1"))
        res = rb.execute()
        s = res.summary()
        assert "SUCCESS" in s
        assert "summary_rb" in s

    # TC-15: 표준 헬스체크 런북 팩토리
    def test_tc15_build_health_check_runbook(self):
        rb = build_health_check_runbook()
        assert rb.name == "health_check"
        assert rb.step_count() == 3

    # TC-16: 헬스체크 런북 실행
    def test_tc16_health_check_runbook_execute(self):
        rb = build_health_check_runbook()
        res = rb.execute()
        assert res.success is True
        assert res.steps_succeeded == 3

    # TC-17: RunbookSeverity 열거형
    def test_tc17_severity_enum(self):
        assert RunbookSeverity.CRITICAL.value == "critical"
        assert RunbookSeverity.LOW.value == "low"

    # TC-18: elapsed_ms 측정 (0 이상)
    def test_tc18_elapsed_ms(self):
        rb = OpsRunbook("timing_rb")
        rb.add_step(self._ok_step("s1"))
        res = rb.execute()
        assert res.total_elapsed_ms >= 0

    # TC-19: steps() 반환은 복사본 (원본 보호)
    def test_tc19_steps_returns_copy(self):
        rb = OpsRunbook("copy_rb")
        rb.add_step(self._ok_step("s1"))
        lst = rb.steps()
        lst.append(self._ok_step("injected"))
        assert rb.step_count() == 1

    # TC-20: 다중 실패 — steps_failed 카운트
    def test_tc20_multiple_failures_count(self):
        rb = OpsRunbook("multifail_rb")
        for i in range(3):
            rb.add_step(self._fail_step(f"f{i}"))
        res = rb.execute(stop_on_failure=False)
        assert res.steps_failed == 3
        assert res.success is False


# ======================================================================= #
# TC-21~40: TestAPIReferenceGenerator                                      #
# ======================================================================= #

class TestAPIReferenceGenerator:
    """APIReferenceGenerator 20 TC."""

    @staticmethod
    def _basic_ep(path: str = "/v1/test", method: HTTPMethod = HTTPMethod.GET) -> EndpointSpec:
        return EndpointSpec(path=path, method=method, summary="테스트 엔드포인트")

    # TC-21: 빈 생성기 생성
    def test_tc21_create_empty_generator(self):
        gen = APIReferenceGenerator()
        assert gen.endpoint_count() == 0

    # TC-22: 엔드포인트 등록 체이닝
    def test_tc22_register_chaining(self):
        gen = APIReferenceGenerator()
        result = gen.register(self._basic_ep())
        assert result is gen
        assert gen.endpoint_count() == 1

    # TC-23: register_many
    def test_tc23_register_many(self):
        gen = APIReferenceGenerator()
        eps = [self._basic_ep(f"/v1/ep{i}") for i in range(5)]
        gen.register_many(eps)
        assert gen.endpoint_count() == 5

    # TC-24: generate() 반환 타입
    def test_tc24_generate_returns_report(self):
        gen = APIReferenceGenerator()
        gen.register(self._basic_ep())
        rpt = gen.generate()
        assert isinstance(rpt, APIReferenceReport)
        assert rpt.endpoint_count == 1

    # TC-25: generate_markdown 포함 내용 확인
    def test_tc25_generate_markdown_content(self):
        gen = APIReferenceGenerator("My API", "2.0.0")
        gen.register(EndpointSpec("/v1/users", HTTPMethod.GET, "사용자 목록", tags=["users"]))
        md = gen.generate_markdown()
        assert "My API" in md
        assert "/v1/users" in md
        assert "GET" in md

    # TC-26: generate_openapi_fragment JSON 파싱 가능
    def test_tc26_openapi_fragment_valid_json(self):
        gen = APIReferenceGenerator()
        gen.register(self._basic_ep())
        frag = gen.generate_openapi_fragment()
        data = json.loads(frag)
        assert "paths" in data
        assert "/v1/test" in data["paths"]

    # TC-27: HTTPMethod 열거형
    def test_tc27_http_method_enum(self):
        assert HTTPMethod.GET.value == "GET"
        assert HTTPMethod.POST.value == "POST"
        assert HTTPMethod.DELETE.value == "DELETE"

    # TC-28: EndpointSpec.operation_id 자동 생성
    def test_tc28_operation_id_auto(self):
        ep = EndpointSpec("/v1/items/{id}", HTTPMethod.GET, "아이템 조회")
        assert ep.operation_id is not None
        assert "get" in ep.operation_id

    # TC-29: ParamSpec 포함 엔드포인트
    def test_tc29_param_spec_in_markdown(self):
        ep = EndpointSpec(
            path="/v1/search",
            method=HTTPMethod.GET,
            summary="검색",
            params=[ParamSpec("q", "query", "검색어", required=True)],
        )
        gen = APIReferenceGenerator()
        gen.register(ep)
        md = gen.generate_markdown()
        assert "q" in md

    # TC-30: ResponseSpec 포함 엔드포인트
    def test_tc30_response_spec_in_openapi(self):
        ep = EndpointSpec(
            path="/v1/create",
            method=HTTPMethod.POST,
            summary="생성",
            responses=[ResponseSpec(201, "생성 성공"), ResponseSpec(400, "잘못된 요청")],
        )
        gen = APIReferenceGenerator()
        gen.register(ep)
        frag = json.loads(gen.generate_openapi_fragment())
        op = frag["paths"]["/v1/create"]["post"]
        assert "201" in op["responses"]
        assert "400" in op["responses"]

    # TC-31: 태그 목록 집계
    def test_tc31_tag_list_aggregation(self):
        gen = APIReferenceGenerator()
        gen.register(EndpointSpec("/a", HTTPMethod.GET, "A", tags=["users"]))
        gen.register(EndpointSpec("/b", HTTPMethod.POST, "B", tags=["items"]))
        rpt = gen.generate()
        assert "users" in rpt.tag_list
        assert "items" in rpt.tag_list

    # TC-32: deprecated 엔드포인트 markdown 표시
    def test_tc32_deprecated_in_markdown(self):
        ep = EndpointSpec("/v1/old", HTTPMethod.GET, "구버전", deprecated=True)
        gen = APIReferenceGenerator()
        gen.register(ep)
        md = gen.generate_markdown()
        assert "deprecated" in md.lower()

    # TC-33: collect_endpoints 복사본 반환
    def test_tc33_collect_endpoints_copy(self):
        gen = APIReferenceGenerator()
        gen.register(self._basic_ep())
        lst = gen.collect_endpoints()
        lst.append(self._basic_ep("/injected"))
        assert gen.endpoint_count() == 1

    # TC-34: 빈 생성기 generate — is_empty
    def test_tc34_empty_report_is_empty(self):
        gen = APIReferenceGenerator()
        rpt = gen.generate()
        assert rpt.is_empty is True

    # TC-35: to_dict 직렬화
    def test_tc35_report_to_dict(self):
        gen = APIReferenceGenerator()
        gen.register(self._basic_ep())
        rpt = gen.generate()
        d = rpt.to_dict()
        assert d["endpoint_count"] == 1
        assert "generated_at" in d

    # TC-36: multiple tags per endpoint
    def test_tc36_multiple_tags_per_endpoint(self):
        ep = EndpointSpec("/multi", HTTPMethod.PUT, "멀티", tags=["a", "b", "c"])
        assert ep.tags == ["a", "b", "c"]

    # TC-37: OpenAPI 3.1 version 필드
    def test_tc37_openapi_version_field(self):
        gen = APIReferenceGenerator()
        gen.register(self._basic_ep())
        frag = json.loads(gen.generate_openapi_fragment())
        assert frag["openapi"] == "3.1.0"

    # TC-38: requestBody schema ref 포함
    def test_tc38_request_body_schema_ref(self):
        ep = EndpointSpec(
            "/v1/manuscript",
            HTTPMethod.POST,
            "원고 제출",
            request_body_schema="#/components/schemas/ManuscriptInput",
        )
        gen = APIReferenceGenerator()
        gen.register(ep)
        frag = json.loads(gen.generate_openapi_fragment())
        op = frag["paths"]["/v1/manuscript"]["post"]
        assert "requestBody" in op

    # TC-39: 커스텀 title/version 반영
    def test_tc39_custom_title_version(self):
        gen = APIReferenceGenerator("Custom API", "3.5.2")
        gen.register(self._basic_ep())
        frag = json.loads(gen.generate_openapi_fragment())
        assert frag["info"]["title"] == "Custom API"
        assert frag["info"]["version"] == "3.5.2"

    # TC-40: 파라미터 required 필드 OpenAPI 반영
    def test_tc40_param_required_in_openapi(self):
        ep = EndpointSpec(
            "/v1/req",
            HTTPMethod.GET,
            "필수 파라미터",
            params=[ParamSpec("token", "header", required=True)],
        )
        gen = APIReferenceGenerator()
        gen.register(ep)
        frag = json.loads(gen.generate_openapi_fragment())
        params = frag["paths"]["/v1/req"]["get"]["parameters"]
        assert params[0]["required"] is True


# ======================================================================= #
# TC-41~60: TestATIAMetadataAuditor                                        #
# ======================================================================= #

class TestATIAMetadataAuditor:
    """ATIAMetadataAuditor 20 TC."""

    @staticmethod
    def _make_record(name: str, t: float = 0.8, i: float = 0.8, a: float = 0.8) -> ATIAMetadataRecord:
        return ATIAMetadataRecord(
            module_name=name,
            version="1.0",
            transparency_score=t,
            interpretability_score=i,
            accountability_score=a,
        )

    # TC-41: 빈 감사자 생성
    def test_tc41_create_empty_auditor(self):
        auditor = ATIAMetadataAuditor("Literary OS", "1.0")
        assert auditor.record_count() == 0

    # TC-42: 레코드 등록 체이닝
    def test_tc42_register_chaining(self):
        auditor = ATIAMetadataAuditor()
        result = auditor.register(self._make_record("mod_a"))
        assert result is auditor
        assert auditor.record_count() == 1

    # TC-43: register_many
    def test_tc43_register_many(self):
        auditor = ATIAMetadataAuditor()
        recs = [self._make_record(f"mod_{i}") for i in range(4)]
        auditor.register_many(recs)
        assert auditor.record_count() == 4

    # TC-44: ATIAMetadataRecord 유효성 — 범위 초과 예외
    def test_tc44_record_score_out_of_range(self):
        with pytest.raises(ValueError):
            ATIAMetadataRecord("bad", "1.0", 1.5, 0.8, 0.8)

    # TC-45: ATIAMetadataRecord 유효성 — 음수 예외
    def test_tc45_record_score_negative(self):
        with pytest.raises(ValueError):
            ATIAMetadataRecord("bad", "1.0", -0.1, 0.8, 0.8)

    # TC-46: overall_score 가중치 계산
    def test_tc46_overall_score_weights(self):
        rec = ATIAMetadataRecord("m", "1.0", 1.0, 0.0, 0.0)
        # T=1.0, I=0.0, A=0.0 → 0.30*1 + 0.30*0 + 0.40*0 = 0.30
        assert abs(rec.overall_score - 0.30) < 1e-9

    # TC-47: risk_level — LOW (>=0.80)
    def test_tc47_risk_level_low(self):
        rec = self._make_record("high_score", 0.9, 0.9, 0.9)
        assert rec.risk_level == ATIARiskLevel.LOW

    # TC-48: risk_level — CRITICAL (<0.40)
    def test_tc48_risk_level_critical(self):
        rec = self._make_record("critical", 0.1, 0.1, 0.1)
        assert rec.risk_level == ATIARiskLevel.CRITICAL

    # TC-49: record.passed — 전체 0.60 이상 + 각 축 0.40 이상
    def test_tc49_record_passed_true(self):
        rec = self._make_record("ok", 0.7, 0.7, 0.7)
        assert rec.passed is True

    # TC-50: record.passed — 한 축 0.40 미만이면 False
    def test_tc50_record_passed_false_low_axis(self):
        rec = ATIAMetadataRecord("fail_axis", "1.0", 0.9, 0.9, 0.35)
        assert rec.passed is False

    # TC-51: compute_scores 평균
    def test_tc51_compute_scores_mean(self):
        auditor = ATIAMetadataAuditor()
        auditor.register(self._make_record("a", 0.6, 0.8, 1.0))
        auditor.register(self._make_record("b", 0.8, 0.6, 0.8))
        t, i, a = auditor.compute_scores()
        assert abs(t - 0.70) < 1e-9
        assert abs(i - 0.70) < 1e-9
        assert abs(a - 0.90) < 1e-9

    # TC-52: audit() 반환 타입
    def test_tc52_audit_returns_report(self):
        auditor = ATIAMetadataAuditor()
        auditor.register(self._make_record("m"))
        rpt = auditor.audit()
        assert isinstance(rpt, ATIAAuditReport)

    # TC-53: audit() — critical_modules 감지
    def test_tc53_critical_modules_detected(self):
        auditor = ATIAMetadataAuditor()
        auditor.register(self._make_record("bad", 0.1, 0.1, 0.1))
        rpt = auditor.audit()
        assert "bad" in rpt.critical_modules

    # TC-54: audit() — passed=False when critical exists
    def test_tc54_audit_fails_with_critical(self):
        auditor = ATIAMetadataAuditor()
        auditor.register(self._make_record("bad", 0.1, 0.1, 0.1))
        rpt = auditor.audit()
        assert rpt.passed is False

    # TC-55: export_package 두 파일 반환
    def test_tc55_export_package_keys(self):
        auditor = ATIAMetadataAuditor()
        auditor.register(self._make_record("m"))
        pkg = auditor.export_package()
        assert "audit_report.json" in pkg
        assert "audit_summary.md" in pkg

    # TC-56: export_package JSON 파싱 가능
    def test_tc56_export_package_json_valid(self):
        auditor = ATIAMetadataAuditor()
        auditor.register(self._make_record("m"))
        pkg = auditor.export_package()
        data = json.loads(pkg["audit_report.json"])
        assert "summary" in data
        assert "records" in data

    # TC-57: export_package Markdown 포함 내용
    def test_tc57_export_package_markdown_content(self):
        auditor = ATIAMetadataAuditor("Literary OS", "10.34.0")
        auditor.register(self._make_record("ops_runbook"))
        pkg = auditor.export_package()
        md = pkg["audit_summary.md"]
        assert "Literary OS" in md
        assert "ops_runbook" in md

    # TC-58: dimension_stats — 수치 검증
    def test_tc58_dimension_stats(self):
        auditor = ATIAMetadataAuditor()
        auditor.register(self._make_record("a", t=0.6, i=0.7, a=0.8))
        auditor.register(self._make_record("b", t=0.8, i=0.9, a=1.0))
        stats = auditor.dimension_stats(ATIADimension.TRANSPARENCY)
        assert abs(stats["min"] - 0.6) < 1e-9
        assert abs(stats["max"] - 0.8) < 1e-9
        assert abs(stats["mean"] - 0.7) < 1e-9

    # TC-59: lowest_scored_modules — 정렬 확인
    def test_tc59_lowest_scored_modules(self):
        auditor = ATIAMetadataAuditor()
        for score in [0.9, 0.5, 0.7, 0.3, 0.8]:
            auditor.register(self._make_record(f"mod_{score}", score, score, score))
        lowest = auditor.lowest_scored_modules(n=2)
        assert lowest[0].overall_score <= lowest[1].overall_score
        assert lowest[0].overall_score < 0.5

    # TC-60: _risk_from_score 경계값 테스트
    def test_tc60_risk_from_score_boundaries(self):
        assert _risk_from_score(0.80) == ATIARiskLevel.LOW
        assert _risk_from_score(0.79) == ATIARiskLevel.MEDIUM
        assert _risk_from_score(0.60) == ATIARiskLevel.MEDIUM
        assert _risk_from_score(0.59) == ATIARiskLevel.HIGH
        assert _risk_from_score(0.40) == ATIARiskLevel.HIGH
        assert _risk_from_score(0.39) == ATIARiskLevel.CRITICAL
