"""
literary_system/docs/api_reference_generator.py

V629: APIReferenceGenerator — API 레퍼런스 자동 생성기
ADR-096 §2: Phase B API 레퍼런스 완성

등록된 엔드포인트 스펙을 수집하여 Markdown 및 OpenAPI 3.1 Fragment를 생성한다.
LLM-0 원칙: 외부 LLM 호출 없음.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class ParamSpec:
    """단일 파라미터 스펙."""
    name: str
    param_in: str          # "query" | "path" | "header" | "cookie"
    description: str = ""
    required: bool = False
    schema_type: str = "string"
    example: Any = None


@dataclass
class ResponseSpec:
    """단일 응답 스펙."""
    status_code: int
    description: str
    schema_ref: Optional[str] = None   # "$ref" 형식 (예: "#/components/schemas/OKResponse")
    example: Any = None


@dataclass
class EndpointSpec:
    """API 엔드포인트 스펙."""
    path: str
    method: HTTPMethod
    summary: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    params: List[ParamSpec] = field(default_factory=list)
    request_body_schema: Optional[str] = None   # JSON Schema ref
    responses: List[ResponseSpec] = field(default_factory=list)
    deprecated: bool = False
    operation_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.operation_id:
            clean = self.path.replace("/", "_").replace("{", "").replace("}", "").strip("_")
            self.operation_id = f"{self.method.value.lower()}_{clean}"

    def to_openapi_dict(self) -> Dict[str, Any]:
        """OpenAPI 3.1 operation 객체 반환."""
        op: Dict[str, Any] = {
            "summary": self.summary,
            "operationId": self.operation_id,
            "tags": self.tags,
            "deprecated": self.deprecated,
        }
        if self.description:
            op["description"] = self.description

        # parameters
        if self.params:
            op["parameters"] = [
                {
                    "name": p.name,
                    "in": p.param_in,
                    "description": p.description,
                    "required": p.required,
                    "schema": {"type": p.schema_type},
                    **({"example": p.example} if p.example is not None else {}),
                }
                for p in self.params
            ]

        # requestBody
        if self.request_body_schema:
            op["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": self.request_body_schema}
                    }
                },
            }

        # responses
        if self.responses:
            op["responses"] = {}
            for r in self.responses:
                resp: Dict[str, Any] = {"description": r.description}
                if r.schema_ref:
                    resp["content"] = {
                        "application/json": {
                            "schema": {"$ref": r.schema_ref}
                        }
                    }
                op["responses"][str(r.status_code)] = resp
        else:
            op["responses"] = {"200": {"description": "OK"}}

        return op


@dataclass
class APIReferenceReport:
    """API 레퍼런스 생성 보고서."""
    endpoint_count: int
    generated_at: str
    markdown: str
    openapi_fragment: str
    tag_list: List[str]

    @property
    def is_empty(self) -> bool:
        return self.endpoint_count == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint_count": self.endpoint_count,
            "generated_at": self.generated_at,
            "tag_list": self.tag_list,
            "openapi_fragment_length": len(self.openapi_fragment),
        }


class APIReferenceGenerator:
    """
    API 레퍼런스 생성기.

    EndpointSpec을 등록하고 Markdown / OpenAPI 3.1 Fragment를 생성한다.
    """

    def __init__(self, title: str = "Literary OS API Reference", version: str = "1.0.0") -> None:
        self.title = title
        self.version = version
        self._endpoints: List[EndpointSpec] = []

    # ------------------------------------------------------------------ #
    # 등록                                                                  #
    # ------------------------------------------------------------------ #

    def register(self, endpoint: EndpointSpec) -> "APIReferenceGenerator":
        """엔드포인트 등록 (체이닝 지원)."""
        self._endpoints.append(endpoint)
        return self

    def register_many(self, endpoints: List[EndpointSpec]) -> "APIReferenceGenerator":
        for ep in endpoints:
            self.register(ep)
        return self

    def endpoint_count(self) -> int:
        return len(self._endpoints)

    def collect_endpoints(self) -> List[EndpointSpec]:
        """등록된 엔드포인트 목록 반환."""
        return list(self._endpoints)

    # ------------------------------------------------------------------ #
    # 생성                                                                  #
    # ------------------------------------------------------------------ #

    def generate(self) -> APIReferenceReport:
        """Markdown + OpenAPI Fragment 생성."""
        md = self._build_markdown()
        frag = self._build_openapi_fragment()
        tags = sorted({t for ep in self._endpoints for t in ep.tags})
        return APIReferenceReport(
            endpoint_count=len(self._endpoints),
            generated_at=self._iso_now(),
            markdown=md,
            openapi_fragment=frag,
            tag_list=tags,
        )

    def generate_markdown(self) -> str:
        """Markdown 레퍼런스만 반환."""
        return self._build_markdown()

    def generate_openapi_fragment(self) -> str:
        """OpenAPI 3.1 Fragment(JSON) 반환."""
        return self._build_openapi_fragment()

    # ------------------------------------------------------------------ #
    # 내부                                                                  #
    # ------------------------------------------------------------------ #

    def _build_markdown(self) -> str:
        lines: List[str] = [
            f"# {self.title}",
            f"",
            f"**버전**: {self.version}  ",
            f"**생성일**: {self._iso_now()}  ",
            f"**엔드포인트 수**: {len(self._endpoints)}",
            f"",
            f"---",
            f"",
        ]
        # 태그별 그룹
        tag_map: Dict[str, List[EndpointSpec]] = {}
        for ep in self._endpoints:
            tag = ep.tags[0] if ep.tags else "General"
            tag_map.setdefault(tag, []).append(ep)

        for tag in sorted(tag_map.keys()):
            lines.append(f"## {tag}")
            lines.append("")
            for ep in tag_map[tag]:
                badge = f"`{ep.method.value}`"
                dep = " *(deprecated)*" if ep.deprecated else ""
                lines.append(f"### {badge} `{ep.path}`{dep}")
                lines.append("")
                lines.append(f"**요약**: {ep.summary}")
                if ep.description:
                    lines.append(f"")
                    lines.append(ep.description)
                if ep.params:
                    lines.append("")
                    lines.append("**파라미터**:")
                    lines.append("")
                    lines.append("| 이름 | 위치 | 필수 | 타입 | 설명 |")
                    lines.append("|------|------|------|------|------|")
                    for p in ep.params:
                        req = "✓" if p.required else ""
                        lines.append(f"| `{p.name}` | {p.param_in} | {req} | {p.schema_type} | {p.description} |")
                if ep.responses:
                    lines.append("")
                    lines.append("**응답**:")
                    lines.append("")
                    for r in ep.responses:
                        lines.append(f"- `{r.status_code}` — {r.description}")
                lines.append("")
        return "\n".join(lines)

    def _build_openapi_fragment(self) -> str:
        paths: Dict[str, Any] = {}
        for ep in self._endpoints:
            paths.setdefault(ep.path, {})[ep.method.value.lower()] = ep.to_openapi_dict()
        fragment = {
            "openapi": "3.1.0",
            "info": {"title": self.title, "version": self.version},
            "paths": paths,
        }
        return json.dumps(fragment, ensure_ascii=False, indent=2)

    @staticmethod
    def _iso_now() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
