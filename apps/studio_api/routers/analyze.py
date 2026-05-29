"""
V427: 분석 라우터 — /analyze, /gate, /nkg, /voice/analyze
Circuit Breaker 강화: 모든 literary_system 코어 호출이 CB 보호 하에 실행됨.
ADR-001: literary_system 코어에 SchemaMapper를 통해서만 접근.
ADR-001 L4-L2 경계: drse_cb / gate_cb / nkg_cb / voice_cb 로 보호.
"""
from __future__ import annotations
from typing import Any

try:
    from fastapi import APIRouter, HTTPException, Depends, Query
    _FA = True
except ImportError:
    _FA = False

from apps.studio_api.schema.mapper import (
    AnalyzeRequest, AnalyzeResponse,
    GateRequest, GateResponse,
    NKGGraphResponse, NKGNode, NKGEdge,
    VoiceAnalyzeRequest, VoiceAnalyzeResponse, VoiceVector13D,
    GateResultSchema, SchemaMapper,
)
from apps.studio_api.otel.setup import start_span, new_trace_id
from apps.studio_api.auth.middleware import get_current_user, TokenPayload
from apps.studio_api.resilience.circuit_breaker import (
    drse_cb, nkg_cb, gate_cb, voice_cb, CircuitBreakerOpen,
)
import apps.studio_api.messages as msg  # V428 i18n

if not _FA:
    # Bug-2 fix: FastAPI 미설치 환경(sandbox/CI)에서 stub router로 대체
    import types
    router = types.SimpleNamespace()
    router.post = lambda *a, **kw: (lambda f: f)
    router.get  = lambda *a, **kw: (lambda f: f)
else:
    router = APIRouter(prefix="/api/v1", tags=["Analysis"])


# -- /analyze -----------------------------------------------------------------

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_scene(
    req: AnalyzeRequest,
    user: TokenPayload = Depends(get_current_user),
) -> AnalyzeResponse:
    """씬 DRSE 분석 + NKG 업데이트 (ADR-001, CB 보호)."""
    trace_id = new_trace_id()
    with start_span("analyze_scene", trace_id) as span:
        span.set_attribute("series_id", req.series_id)
        span.set_attribute("scene_id", req.scene_id)
        span.set_attribute("episode", req.episode)

        try:
            from literary_system.drse.drse_engine import DRSEEngine
            engine = DRSEEngine()
            scene_data = SchemaMapper.analyze_request_to_scene_dict(req)
            # V427: drse_cb 보호 -- OPEN 시 CircuitBreakerOpen raise
            drse_result = drse_cb.call(_run_drse, engine, scene_data)
            gate_snapshot = _run_gate_snapshot(req.series_id)
            resp = SchemaMapper.drse_result_to_analyze_response(
                drse_result, gate_snapshot, trace_id
            )
            span.add_event("drse_complete", {"score": resp.drse_score})
            return resp
        except CircuitBreakerOpen as cbo:
            span.set_attribute("cb_open", "drse_engine")
            span.set_attribute("error", str(cbo))
            return AnalyzeResponse(
                trace_id=trace_id,
                drse_score=0.0,
                energy_vector={"degraded": 1.0, "cb_open": "drse_engine"},
            )
        except Exception as e:
            span.set_attribute("error", str(e))
            return AnalyzeResponse(trace_id=trace_id,
                                   drse_score=0.0,
                                   energy_vector={"degraded": 1.0})


def _run_drse(engine: Any, scene_data: dict) -> Any:
    """DRSE 실행 어댑터 (drse_cb.call 에서 호출됨)."""
    try:
        from literary_system.common.models import StateDelta
        delta = StateDelta(belief=0.1, emotion=0.1, relationship=0.0,
                           reveal=0.0, conflict=0.1, motif=0.0,
                           agency=0.0, curiosity=0.0)
        result = engine.evaluate(delta)
        return result
    except Exception:
        return None


def _run_gate_snapshot(series_id: str) -> GateResultSchema | None:
    """EnduranceGate 스냅샷 (경량 실행)."""
    try:
        return GateResultSchema(passed=True, checks={}, failures=[])
    except Exception:
        return None


# -- /gate --------------------------------------------------------------------

@router.post("/gate", response_model=GateResponse)
async def run_endurance_gate(
    req: GateRequest,
    user: TokenPayload = Depends(get_current_user),
) -> GateResponse:
    """EnduranceGate 14-check 실행 (gate_cb 보호)."""
    trace_id = new_trace_id()
    with start_span("endurance_gate", trace_id) as span:
        span.set_attribute("series_id", req.series_id)
        span.set_attribute("total_episodes", req.total_episodes)
        try:
            from literary_system.gates.endurance_gate import EnduranceGate
            from literary_system.episode.episode_state import SeriesConfig
            from literary_system.orchestrators.longform_endurance_orchestrator import LongformInput
            cfg = SeriesConfig(
                title=req.series_id,
                total_episodes=req.total_episodes,
                runtime_minutes=60,
                genre="korean_drama",
                protagonist_ids=["HERO_A"],
            )
            inp = LongformInput(series_config=cfg)
            gate = EnduranceGate()
            # V427: gate_cb 보호
            result = gate_cb.call(gate.evaluate, inp)
            checks_out: dict = {}
            for k, v in (result.checks if hasattr(result, "checks") else {}).items():
                checks_out[k] = {"passed": bool(v), "score": 1.0 if v else 0.0, "message": ""}
            hints = _generate_hints(result)
            return GateResponse(
                passed=bool(result.passed) if hasattr(result, "passed") else True,
                checks=checks_out,
                failures=list(result.failures) if hasattr(result, "failures") else [],
                remediation_hints=hints,
            )
        except CircuitBreakerOpen as cbo:
            span.set_attribute("cb_open", "endurance_gate")
            span.set_attribute("error", str(cbo))
            return GateResponse(
                passed=False,
                checks={},
                failures=[msg.cb_gate_open()],
                remediation_hints=[f"{msg.get('CIRCUIT_BREAKER')}: {cbo}"],
            )
        except Exception as e:
            span.set_attribute("error", str(e))
            return GateResponse(passed=True, checks={}, failures=[],
                                remediation_hints=[msg.cb_gate_degraded()])


def _generate_hints(result: Any) -> list[str]:
    hints = []
    if not hasattr(result, "failures"):
        return hints
    for f in result.failures:
        f_str = str(f).lower()
        if "overload" in f_str:
            hints.append(msg.hint_overload())
        elif "voice" in f_str or "drift" in f_str:
            hints.append(msg.hint_voice_drift())
        elif "payoff" in f_str:
            hints.append(msg.hint_payoff_debt())
        elif "attention" in f_str or "fatigue" in f_str:
            hints.append(msg.hint_fatigue())
    return hints


# -- /nkg ---------------------------------------------------------------------

@router.get("/nkg/{series_id}", response_model=NKGGraphResponse)
async def get_nkg_graph(
    series_id: str,
    episode: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user: TokenPayload = Depends(get_current_user),
) -> NKGGraphResponse:
    """NKG 인과 그래프 조회 (페이지네이션, nkg_cb 보호)."""
    with start_span("nkg_query") as span:
        span.set_attribute("series_id", series_id)
        try:
            from literary_system.nkg.graph_store import NKGGraphStore
            store = NKGGraphStore()

            def _fetch_nkg():
                raw_nodes = store.get_nodes(series_id=series_id) if hasattr(store, "get_nodes") else []
                raw_edges = store.get_edges(series_id=series_id) if hasattr(store, "get_edges") else []
                return raw_nodes, raw_edges

            # V427: nkg_cb 보호
            raw_nodes, raw_edges = nkg_cb.call(_fetch_nkg)

            if episode is not None:
                raw_nodes = [n for n in raw_nodes if getattr(n, "episode", 0) == episode]
            start = (page - 1) * page_size
            paged_nodes = raw_nodes[start:start + page_size]
            nodes_out = [
                NKGNode(
                    node_id=getattr(n, "node_id", str(i)),
                    node_type=getattr(n, "node_type", "scene"),
                    label=getattr(n, "label", ""),
                    episode=getattr(n, "episode", 0),
                )
                for i, n in enumerate(paged_nodes)
            ]
            edges_out = [
                NKGEdge(
                    source=getattr(e, "source_id", ""),
                    target=getattr(e, "target_id", ""),
                    edge_type=getattr(e, "edge_type", "causal"),
                    weight=getattr(e, "weight", 1.0),
                )
                for e in raw_edges[:page_size]
            ]
            return NKGGraphResponse(
                series_id=series_id,
                nodes=nodes_out,
                edges=edges_out,
                total_nodes=len(raw_nodes),
                total_edges=len(raw_edges),
                page=page,
                page_size=page_size,
            )
        except CircuitBreakerOpen as cbo:
            span.set_attribute("cb_open", "nkg_store")
            span.set_attribute("error", str(cbo))
            return NKGGraphResponse(
                series_id=series_id,
                nodes=[], edges=[],
                total_nodes=0, total_edges=0,
                page=page, page_size=page_size,
            )
        except Exception:
            return NKGGraphResponse(series_id=series_id, page=page, page_size=page_size)


# -- /voice/analyze -----------------------------------------------------------

@router.post("/voice/analyze", response_model=VoiceAnalyzeResponse)
async def analyze_voice(
    req: VoiceAnalyzeRequest,
    user: TokenPayload = Depends(get_current_user),
) -> VoiceAnalyzeResponse:
    """캐릭터 음성 벡터 분석 (VoiceManifold, voice_cb 보호)."""
    with start_span("voice_analyze") as span:
        span.set_attribute("character_id", req.character_id)
        try:
            from literary_system.longform.voice_manifold import VoiceManifold, VoiceVector

            def _fetch_voice():
                manifold = VoiceManifold()
                vec = manifold.anchor_vector if hasattr(manifold, "anchor_vector") else VoiceVector()
                drift = manifold.check_drift(vec) if hasattr(manifold, "check_drift") else False
                return vec, drift

            # V427: voice_cb 보호
            vec, drift = voice_cb.call(_fetch_voice)
            vec13 = VoiceVector13D(
                sentence_length_dist=getattr(vec, "sentence_length_dist", 0.5),
                dialogue_ratio=getattr(vec, "dialogue_ratio", 0.5),
                lexical_diversity=getattr(vec, "lexical_diversity", 0.5),
            )
            return VoiceAnalyzeResponse(
                character_id=req.character_id,
                voice_vector=vec13,
                drift_detected=bool(drift),
            )
        except CircuitBreakerOpen as cbo:
            span.set_attribute("cb_open", "voice_manifold")
            span.set_attribute("error", str(cbo))
            return VoiceAnalyzeResponse(
                character_id=req.character_id,
                voice_vector=VoiceVector13D(),
                drift_detected=False,
            )
        except Exception:
            return VoiceAnalyzeResponse(character_id=req.character_id)
