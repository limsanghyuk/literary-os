"""V657 OpenAPI 3.1 스키마 테스트 (ADR-117) — 33 TC."""
from __future__ import annotations

import json

import pytest

from literary_system.sdk.api_schema import (
    build_openapi_schema,
    get_openapi_json,
    get_openapi_yaml,
)


@pytest.fixture
def schema():
    return build_openapi_schema()


# ── TC-01~06: 최상위 스펙 구조 ─────────────────────────────────────────────

class TestTopLevel:
    def test_openapi_version(self, schema):                                # TC-01
        assert schema["openapi"] == "3.1.0"

    def test_info_title(self, schema):                                     # TC-02
        assert "Literary OS" in schema["info"]["title"]

    def test_info_version(self, schema):                                   # TC-03
        assert schema["info"]["version"] == "1.0.0"

    def test_servers_nonempty(self, schema):                               # TC-04
        assert len(schema["servers"]) >= 1

    def test_paths_defined(self, schema):                                  # TC-05
        assert "/analyze" in schema["paths"]
        assert "/repair" in schema["paths"]
        assert "/predict" in schema["paths"]
        assert "/generate" in schema["paths"]
        assert "/health" in schema["paths"]

    def test_security_schemes(self, schema):                               # TC-06
        schemes = schema["components"]["securitySchemes"]
        assert "BearerAuth" in schemes
        assert "ApiKeyHeader" in schemes


# ── TC-07~12: /analyze 경로 ────────────────────────────────────────────────

class TestAnalyzePath:
    def test_post_method(self, schema):                                    # TC-07
        assert "post" in schema["paths"]["/analyze"]

    def test_request_body_required(self, schema):                          # TC-08
        assert schema["paths"]["/analyze"]["post"]["requestBody"]["required"] is True

    def test_200_response(self, schema):                                   # TC-09
        assert "200" in schema["paths"]["/analyze"]["post"]["responses"]

    def test_400_response(self, schema):                                   # TC-10
        assert "400" in schema["paths"]["/analyze"]["post"]["responses"]

    def test_429_response(self, schema):                                   # TC-11
        assert "429" in schema["paths"]["/analyze"]["post"]["responses"]

    def test_operation_id(self, schema):                                   # TC-12
        assert schema["paths"]["/analyze"]["post"]["operationId"] == "analyze"


# ── TC-13~17: /generate 경로 ──────────────────────────────────────────────

class TestGeneratePath:
    def test_post_method(self, schema):                                    # TC-13
        assert "post" in schema["paths"]["/generate"]

    def test_operation_id(self, schema):                                   # TC-14
        assert schema["paths"]["/generate"]["post"]["operationId"] == "generate"

    def test_request_body_required(self, schema):                          # TC-15
        assert schema["paths"]["/generate"]["post"]["requestBody"]["required"] is True

    def test_200_response_exists(self, schema):                            # TC-16
        assert "200" in schema["paths"]["/generate"]["post"]["responses"]

    def test_tags_set(self, schema):                                       # TC-17
        tags = schema["paths"]["/generate"]["post"]["tags"]
        assert "Generation" in tags


# ── TC-18~22: /health 경로 ────────────────────────────────────────────────

class TestHealthPath:
    def test_get_method(self, schema):                                     # TC-18
        assert "get" in schema["paths"]["/health"]

    def test_no_auth_required(self, schema):                               # TC-19
        security = schema["paths"]["/health"]["get"].get("security", None)
        assert security == []

    def test_200_response(self, schema):                                   # TC-20
        assert "200" in schema["paths"]["/health"]["get"]["responses"]

    def test_operation_id(self, schema):                                   # TC-21
        assert schema["paths"]["/health"]["get"]["operationId"] == "health"

    def test_tags_set(self, schema):                                       # TC-22
        assert "System" in schema["paths"]["/health"]["get"]["tags"]


# ── TC-23~28: 컴포넌트 스키마 ─────────────────────────────────────────────

class TestComponentSchemas:
    def test_quality_score_schema(self, schema):                           # TC-23
        qs = schema["components"]["schemas"]["QualityScore"]
        for axis in ["coherence", "emotion", "style", "character", "tension"]:
            assert axis in qs["properties"]

    def test_analyze_request_required(self, schema):                       # TC-24
        req = schema["components"]["schemas"]["AnalyzeRequest"]
        assert "text" in req["required"]

    def test_generate_request_required(self, schema):                      # TC-25
        req = schema["components"]["schemas"]["GenerateRequest"]
        for field in ["title", "characters", "setting", "conflict"]:
            assert field in req["required"]

    def test_error_response_schema(self, schema):                          # TC-26
        err = schema["components"]["schemas"]["ErrorResponse"]
        assert "code" in err["properties"]
        assert "message" in err["properties"]

    def test_scene_prediction_schema(self, schema):                        # TC-27
        sp = schema["components"]["schemas"]["ScenePrediction"]
        assert "rank" in sp["properties"]
        assert "probability" in sp["properties"]

    def test_repair_result_schema(self, schema):                           # TC-28
        rr = schema["components"]["schemas"]["RepairResult"]
        assert "improved" in rr["properties"]
        assert "applied_fixes" in rr["properties"]


# ── TC-29~33: JSON / YAML 직렬화 ─────────────────────────────────────────

class TestSerialization:
    def test_get_openapi_json_valid(self):                                  # TC-29
        j = get_openapi_json()
        parsed = json.loads(j)
        assert parsed["openapi"] == "3.1.0"

    def test_get_openapi_json_indent(self):                                 # TC-30
        j = get_openapi_json(indent=4)
        assert "    " in j  # 4칸 들여쓰기 확인

    def test_get_openapi_yaml_starts_with_separator(self):                 # TC-31
        y = get_openapi_yaml()
        assert y.startswith("---")

    def test_get_openapi_yaml_contains_paths(self):                        # TC-32
        y = get_openapi_yaml()
        assert "paths:" in y

    def test_schema_roundtrip(self):                                       # TC-33
        original = build_openapi_schema()
        j = get_openapi_json()
        recovered = json.loads(j)
        assert recovered["info"]["title"] == original["info"]["title"]
        assert set(recovered["paths"].keys()) == set(original["paths"].keys())
