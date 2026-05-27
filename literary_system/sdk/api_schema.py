"""OpenAPI 3.1 스키마 생성기 (ADR-117).

PublicSDK의 4개 엔드포인트에 대한 OpenAPI 3.1 스펙을
dict 또는 YAML/JSON 문자열로 반환한다.
"""
from __future__ import annotations

import json
from typing import Any

__all__ = ["build_openapi_schema", "get_openapi_yaml", "get_openapi_json"]

_VERSION = "1.0.0"
_TITLE = "Literary OS PublicSDK API"
_DESCRIPTION = (
    "Korean literary scene analysis, repair, prediction and generation API.\n"
    "All endpoints accept and return JSON. offline_mode=true 기본 동작."
)


def build_openapi_schema() -> dict[str, Any]:
    """OpenAPI 3.1 스펙 dict를 반환한다."""
    return {
        "openapi": "3.1.0",
        "info": {
            "title": _TITLE,
            "version": _VERSION,
            "description": _DESCRIPTION,
            "contact": {"email": "api@literary-os.io"},
            "license": {"name": "Apache 2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
        },
        "servers": [
            {"url": "http://localhost:8080", "description": "로컬 개발"},
            {"url": "https://api.literary-os.io/v1", "description": "프로덕션"},
        ],
        "paths": {
            "/analyze": _path_analyze(),
            "/repair": _path_repair(),
            "/predict": _path_predict(),
            "/generate": _path_generate(),
            "/health": _path_health(),
        },
        "components": {
            "schemas": _schemas(),
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                },
                "ApiKeyHeader": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                },
            },
        },
        "security": [{"BearerAuth": []}, {"ApiKeyHeader": []}],
    }


def get_openapi_json(indent: int = 2) -> str:
    """OpenAPI 스펙을 JSON 문자열로 반환."""
    return json.dumps(build_openapi_schema(), ensure_ascii=False, indent=indent)


def get_openapi_yaml() -> str:
    """OpenAPI 스펙을 YAML 문자열로 반환 (PyYAML 미사용)."""
    def _dict_to_yaml(obj: Any, indent: int = 0) -> str:
        pad = "  " * indent
        if isinstance(obj, dict):
            lines = []
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    lines.append(f"{pad}{k}:")
                    lines.append(_dict_to_yaml(v, indent + 1))
                else:
                    lines.append(f"{pad}{k}: {_yaml_scalar(v)}")
            return "\n".join(lines)
        elif isinstance(obj, list):
            lines = []
            for item in obj:
                if isinstance(item, (dict, list)):
                    lines.append(f"{pad}-")
                    lines.append(_dict_to_yaml(item, indent + 1))
                else:
                    lines.append(f"{pad}- {_yaml_scalar(item)}")
            return "\n".join(lines)
        return f"{pad}{_yaml_scalar(obj)}"

    def _yaml_scalar(v: Any) -> str:
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        s = str(v)
        if any(c in s for c in (':', '{', '}', '[', ']', '#', '&', '*', '!', '|', '>', "'", '"', '\n')):
            return f'"{s}"'
        return s

    return "---\n" + _dict_to_yaml(build_openapi_schema())


# ── 경로 정의 ──────────────────────────────────────────────────────────────

def _path_analyze() -> dict:
    return {
        "post": {
            "summary": "씬 텍스트 품질 분석",
            "description": "5축(coherence/emotion/style/character/tension) 품질 점수와 이슈 목록을 반환.",
            "operationId": "analyze",
            "tags": ["Analysis"],
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AnalyzeRequest"}}},
            },
            "responses": {
                "200": {"description": "분석 성공", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AnalyzeResult"}}}},
                "400": {"description": "입력 오류", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                "429": {"description": "RPM 초과", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
            },
        }
    }


def _path_repair() -> dict:
    return {
        "post": {
            "summary": "이슈 기반 텍스트 수정",
            "operationId": "repair",
            "tags": ["Repair"],
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/RepairRequest"}}},
            },
            "responses": {
                "200": {"description": "수정 성공", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/RepairResult"}}}},
                "400": {"description": "입력 오류", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
            },
        }
    }


def _path_predict() -> dict:
    return {
        "post": {
            "summary": "다음 씬 예측",
            "operationId": "predict",
            "tags": ["Prediction"],
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PredictRequest"}}},
            },
            "responses": {
                "200": {"description": "예측 성공", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PredictResult"}}}},
                "400": {"description": "입력 오류", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
            },
        }
    }


def _path_generate() -> dict:
    return {
        "post": {
            "summary": "씬 생성",
            "description": "DirectorAgent 기반 씬 생성. max_rounds ≤ 3.",
            "operationId": "generate",
            "tags": ["Generation"],
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/GenerateRequest"}}},
            },
            "responses": {
                "200": {"description": "생성 성공", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/GenerateResult"}}}},
                "400": {"description": "입력 오류", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
            },
        }
    }


def _path_health() -> dict:
    return {
        "get": {
            "summary": "헬스 체크",
            "operationId": "health",
            "tags": ["System"],
            "security": [],
            "responses": {
                "200": {"description": "정상", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/HealthResponse"}}}},
            },
        }
    }


# ── 컴포넌트 스키마 ────────────────────────────────────────────────────────

def _schemas() -> dict:
    return {
        "QualityScore": {
            "type": "object",
            "description": "씬 품질 5축 점수",
            "properties": {
                "coherence":  {"type": "number", "format": "float", "minimum": 0, "maximum": 1},
                "emotion":    {"type": "number", "format": "float", "minimum": 0, "maximum": 1},
                "style":      {"type": "number", "format": "float", "minimum": 0, "maximum": 1},
                "character":  {"type": "number", "format": "float", "minimum": 0, "maximum": 1},
                "tension":    {"type": "number", "format": "float", "minimum": 0, "maximum": 1},
                "overall":    {"type": "number", "format": "float", "minimum": 0, "maximum": 1, "readOnly": True},
            },
            "required": ["coherence", "emotion", "style", "character", "tension"],
        },
        "AnalyzeRequest": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text":    {"type": "string", "minLength": 10, "maxLength": 50000, "description": "분석할 씬 텍스트"},
                "context": {"type": "string", "default": "", "description": "이전 씬 맥락"},
                "lang":    {"type": "string", "default": "ko", "enum": ["ko", "en"]},
            },
        },
        "AnalyzeResult": {
            "type": "object",
            "properties": {
                "quality":        {"$ref": "#/components/schemas/QualityScore"},
                "issues":         {"type": "array", "items": {"type": "string"}},
                "patterns":       {"type": "array", "items": {"type": "string"}},
                "word_count":     {"type": "integer"},
                "sentence_count": {"type": "integer"},
                "passed":         {"type": "boolean"},
                "meta":           {"type": "object"},
            },
        },
        "RepairRequest": {
            "type": "object",
            "required": ["text", "issues"],
            "properties": {
                "text":         {"type": "string", "minLength": 10},
                "issues":       {"type": "array", "items": {"type": "string"}},
                "target_score": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.75},
                "lang":         {"type": "string", "default": "ko"},
            },
        },
        "RepairResult": {
            "type": "object",
            "properties": {
                "original_text":  {"type": "string"},
                "repaired_text":  {"type": "string"},
                "applied_fixes":  {"type": "array", "items": {"type": "string"}},
                "score_before":   {"type": "number"},
                "score_after":    {"type": "number"},
                "improved":       {"type": "boolean"},
                "meta":           {"type": "object"},
            },
        },
        "PredictRequest": {
            "type": "object",
            "required": ["context"],
            "properties": {
                "context":    {"type": "string", "minLength": 10},
                "n":          {"type": "integer", "minimum": 1, "maximum": 10, "default": 3},
                "style_hint": {"type": "string", "default": ""},
                "lang":       {"type": "string", "default": "ko"},
            },
        },
        "ScenePrediction": {
            "type": "object",
            "properties": {
                "rank":        {"type": "integer"},
                "synopsis":    {"type": "string"},
                "emotion_arc": {"type": "string"},
                "probability": {"type": "number"},
            },
        },
        "PredictResult": {
            "type": "object",
            "properties": {
                "predictions":    {"type": "array", "items": {"$ref": "#/components/schemas/ScenePrediction"}},
                "context_tokens": {"type": "integer"},
                "meta":           {"type": "object"},
            },
        },
        "GenerateRequest": {
            "type": "object",
            "required": ["title", "characters", "setting", "conflict"],
            "properties": {
                "title":      {"type": "string", "minLength": 1},
                "characters": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                "setting":    {"type": "string", "minLength": 1},
                "conflict":   {"type": "string"},
                "tone":       {"type": "string", "default": "dramatic", "enum": ["dramatic", "lyrical", "thriller", "comedic"]},
                "max_rounds": {"type": "integer", "minimum": 1, "maximum": 3, "default": 3},
                "lang":       {"type": "string", "default": "ko"},
            },
        },
        "GenerateResult": {
            "type": "object",
            "properties": {
                "scene_text":        {"type": "string"},
                "quality":           {"$ref": "#/components/schemas/QualityScore"},
                "rounds_used":       {"type": "integer"},
                "director_blueprint":{"type": "object"},
                "passed_critic":     {"type": "boolean"},
                "meta":              {"type": "object"},
            },
        },
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "code":    {"type": "string"},
                "message": {"type": "string"},
            },
        },
        "HealthResponse": {
            "type": "object",
            "properties": {
                "status":      {"type": "string", "example": "ok"},
                "version":     {"type": "string"},
                "sdk_version": {"type": "string"},
            },
        },
    }
