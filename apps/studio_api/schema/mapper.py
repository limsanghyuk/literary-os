"""
V420: SchemaMapper — Pydantic v2 ↔ literary_system 데이터클래스 양방향 변환.
ADR-001 준수: L4 API Gateway가 L2 Narrative Core에 접근하는 유일한 컨트랙트 레이어.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


# ── 공통 ─────────────────────────────────────────────────────────────────────

class CostBreakdown(BaseModel):
    model_config = ConfigDict(extra="ignore")
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    cost_krw: float = 0.0


class GateCheckResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    passed: bool = True
    score: float = 1.0
    message: str = ""


class GateResultSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")
    passed: bool
    checks: dict[str, Any] = Field(default_factory=dict)
    failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ── /analyze 요청/응답 ────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    series_id: str
    scene_id: str
    content: str = Field(..., max_length=16384)
    characters: list[str] = Field(default_factory=list)
    episode: int = Field(default=1, ge=1, le=24)
    delta_only: bool = True


class NKGEdgeDelta(BaseModel):
    source: str
    target: str
    edge_type: str
    weight: float = 1.0


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    drse_score: float = 0.0
    energy_vector: dict[str, Any] = Field(default_factory=dict)
    energy_delta: dict[str, float] = Field(default_factory=dict)
    nkg_updated: bool = False
    nkg_delta_edges: list[NKGEdgeDelta] = Field(default_factory=list)
    gate_snapshot: GateResultSchema | None = None
    cost: CostBreakdown = Field(default_factory=CostBreakdown)
    trace_id: str = ""


# ── /gate 요청/응답 ───────────────────────────────────────────────────────────

class GateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    series_id: str
    total_episodes: int = Field(default=16, ge=1, le=24)


class GateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    passed: bool
    checks: dict[str, Any] = Field(default_factory=dict)
    failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    overload_ratio: float = 0.0
    mid_sag: float = 0.0
    finale_risk: float = 0.0
    remediation_hints: list[str] = Field(default_factory=list)


# ── /nkg 응답 ────────────────────────────────────────────────────────────────

class NKGNode(BaseModel):
    node_id: str
    node_type: str
    label: str
    episode: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class NKGEdge(BaseModel):
    source: str
    target: str
    edge_type: str
    weight: float = 1.0


class NKGGraphResponse(BaseModel):
    series_id: str
    nodes: list[NKGNode] = Field(default_factory=list)
    edges: list[NKGEdge] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    page: int = 1
    page_size: int = 50


# ── /import 요청/응답 ─────────────────────────────────────────────────────────

class ImportRequest(BaseModel):
    """
    V420 stub: 텍스트 페이로드 기반 임포트.
    V423 ManuscriptImporter v2에서 content_base64 + streaming으로 교체.
    """
    model_config = ConfigDict(extra="ignore")
    series_id: str
    format: str = Field(default="txt", pattern="^(txt|md|docx|pdf)$")
    content: str = Field(default="", max_length=1_000_000)
    filename: str = ""  # 선택적 원본 파일명


class ImportResponse(BaseModel):
    series_id: str
    format: str = "txt"
    scene_count: int = 0
    imported_scene_ids: list[str] = Field(default_factory=list)
    characters: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ── /export 요청/응답 ─────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    series_id: str
    format: str = Field(default="docx", pattern="^(docx|pdf|txt|md)$")
    scene_ids: list[str] = Field(default_factory=list)


class ExportResponse(BaseModel):
    series_id: str = ""
    format: str = ""
    scene_count: int = 0
    content: str = ""
    download_url: str | None = None
    filename: str = ""
    size_bytes: int = 0


# ── /voice/analyze 요청/응답 ─────────────────────────────────────────────────

class VoiceAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    series_id: str
    character_id: str
    scene_ids: list[str] = Field(default_factory=list)


class VoiceVector13D(BaseModel):
    sentence_length_dist: float = 0.5
    dialogue_ratio: float = 0.5
    lexical_diversity: float = 0.5
    rhythm_signature: float = 0.5
    withheld_answer_rate: float = 0.5
    expository_ratio: float = 0.5
    speech_level_variance: float = 0.5
    emotional_suppression: float = 0.5
    indirect_expression: float = 0.5
    confrontation_avoidance: float = 0.5
    pause_frequency: float = 0.5
    metaphor_density: float = 0.5
    scene_boundary_sharpness: float = 0.5


class VoiceAnalyzeResponse(BaseModel):
    character_id: str
    voice_vector: VoiceVector13D = Field(default_factory=VoiceVector13D)
    drift_detected: bool = False
    drift_score: float = 0.0
    anchor_delta: dict[str, float] = Field(default_factory=dict)


# ── /cost/ledger 응답 ─────────────────────────────────────────────────────────

# ── /cost/ledger 요청 및 집계 ─────────────────────────────────────────────────

class CostLedgerRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    series_id: str
    operation_type: str  # analyze | generate | gate | import | export
    cost_usd: float = Field(ge=0.0)
    token_count: int | None = None
    model: str | None = None


class CostEntry(BaseModel):
    entry_id: str
    series_id: str
    operation_type: str
    cost_usd: float
    token_count: int | None = None
    model: str | None = None
    recorded_by: str = ""
    timestamp: str = ""


class CostSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    total_entries: int
    total_cost_usd: float
    total_tokens: int
    by_operation_type: dict[str, float] = Field(default_factory=dict)
    entries: list["CostEntry"] = Field(default_factory=list)
    # V429: budget 추적 + dashboard alias
    budget_limit_usd: float = 100.0
    budget_used_pct: float = 0.0   # 0.0~100.0
    by_endpoint: dict[str, float] = Field(default_factory=dict)  # alias for dashboard


# ── /jobs/{id} 응답 (확장) ────────────────────────────────────────────────────

class JobStatusResponse(BaseModel):
    job_id: str
    status: str = "pending"  # pending | running | completed | failed | cancelled
    progress: int = 0  # 0-100
    result: dict | None = None
    error: str | None = None
    created_at: str = ""
    updated_at: str = ""


class CostLedgerResponse(BaseModel):
    period: str = "monthly"
    total_usd: float = 0.0
    total_krw: float = 0.0
    budget_usd: float = 0.0
    usage_ratio: float = 0.0
    by_provider: dict[str, float] = Field(default_factory=dict)
    by_model: dict[str, float] = Field(default_factory=dict)
    budget_status: str = "ok"  # ok | warn | blocked


# ── /jobs/{id} 응답 ───────────────────────────────────────────────────────────

class JobStatus(BaseModel):
    job_id: str
    status: str = "queued"  # queued | running | done | failed
    progress: float = 0.0
    result_url: str | None = None
    error: str | None = None


# ── 헬스체크 응답 ─────────────────────────────────────────────────────────────

class ProviderHealth(BaseModel):
    available: bool = True
    latency_ms: float = 0.0


class HealthResponse(BaseModel):
    status: str = "ok"  # ok | degraded | down
    version: str = "V420"
    providers: dict[str, ProviderHealth] = Field(default_factory=dict)
    uptime_seconds: float = 0.0


# ── SchemaMapper ──────────────────────────────────────────────────────────────

class SchemaMapper:
    """
    Pydantic v2 스키마 ↔ literary_system 내부 데이터클래스 양방향 변환.
    L4(API Gateway) ↔ L2(Narrative Core) 경계의 단일 책임 모듈.
    """

    @staticmethod
    def analyze_request_to_scene_dict(req: AnalyzeRequest) -> dict[str, Any]:
        """AnalyzeRequest → literary_system 씬 처리용 dict"""
        return {
            "series_id": req.series_id,
            "scene_id": req.scene_id,
            "content": req.content,
            "characters": req.characters,
            "episode": req.episode,
        }

    @staticmethod
    def gate_result_to_response(gate_result: Any) -> GateResultSchema:
        """literary_system GateResult → GateResultSchema"""
        if gate_result is None:
            return GateResultSchema(passed=True)
        try:
            checks = gate_result.checks if hasattr(gate_result, "checks") else {}
            failures = gate_result.failures if hasattr(gate_result, "failures") else []
            passed = gate_result.passed if hasattr(gate_result, "passed") else True
            return GateResultSchema(passed=passed, checks=checks, failures=list(failures))
        except Exception:
            return GateResultSchema(passed=True)

    @staticmethod
    def drse_result_to_analyze_response(
        drse_result: Any,
        gate_snapshot: GateResultSchema | None = None,
        trace_id: str = "",
    ) -> AnalyzeResponse:
        """DRSE 분석 결과 → AnalyzeResponse"""
        resp = AnalyzeResponse(trace_id=trace_id)
        if drse_result is None:
            return resp
        try:
            if hasattr(drse_result, "overall_score"):
                resp.drse_score = float(drse_result.overall_score)
            if hasattr(drse_result, "energy_vector"):
                ev = drse_result.energy_vector
                if hasattr(ev, "__dict__"):
                    resp.energy_vector = {k: float(v) for k, v in vars(ev).items()
                                          if not k.startswith("_")}
        except Exception:
            pass
        resp.gate_snapshot = gate_snapshot
        return resp
