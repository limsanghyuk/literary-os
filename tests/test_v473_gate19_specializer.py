"""
test_v473_gate19_specializer.py — Gate19 + ProseSpecializerAPI 테스트 (V473)

ADR-010: Graceful Degradation (FINETUNED→BASE→MOCK 폴백)
ADR-017: Canary Deployment (해시 기반 라우팅)
"""
import uuid
import pytest
from literary_system.finetune.prose_specializer_api import (
    ProseSpecializerAPI, ServeRequest, ServingTier, ABGroup,
)


def _make_request(style: str = "romance", ab_group=None) -> ServeRequest:
    return ServeRequest(
        request_id=str(uuid.uuid4()),
        prompt="사랑하는 두 사람을 묘사해주세요",
        style_hint=style,
        ab_group=ab_group,
    )


# ─────────────────────────────────────────────
# ProseSpecializerAPI: 기본 서빙
# ─────────────────────────────────────────────

class TestProseSpecializerAPIBasic:
    """기본 serve 동작"""

    def test_serve_returns_response(self):
        api = ProseSpecializerAPI()
        req = _make_request()
        resp = api.serve(req)
        assert resp is not None

    def test_serve_generated_text_not_empty(self):
        api = ProseSpecializerAPI()
        resp = api.serve(_make_request())
        assert resp.generated_text != ""

    def test_serve_request_id_matches(self):
        api = ProseSpecializerAPI()
        req = _make_request()
        resp = api.serve(req)
        assert resp.request_id == req.request_id

    def test_serve_has_latency(self):
        api = ProseSpecializerAPI()
        resp = api.serve(_make_request())
        assert resp.latency_ms >= 0

    def test_serve_has_served_at(self):
        api = ProseSpecializerAPI()
        resp = api.serve(_make_request())
        assert resp.served_at != ""

    def test_serve_no_active_version_uses_base(self):
        """활성 버전 없으면 BASE 폴백"""
        api = ProseSpecializerAPI(active_version_id=None, canary_pct=0)
        resp = api.serve(_make_request())
        assert resp.serving_tier == ServingTier.BASE


class TestProseSpecializerAPICanaryRouting:
    """카나리 트래픽 라우팅 (ADR-017)"""

    def test_canary_0pct_always_base(self):
        api = ProseSpecializerAPI(active_version_id="ver-x", canary_pct=0)
        for _ in range(5):
            resp = api.serve(_make_request())
            assert resp.serving_tier == ServingTier.BASE

    def test_canary_100pct_always_finetuned(self):
        api = ProseSpecializerAPI(active_version_id="ver-y", canary_pct=100)
        for _ in range(5):
            resp = api.serve(_make_request())
            assert resp.serving_tier == ServingTier.FINETUNED

    def test_ab_control_uses_base(self):
        api = ProseSpecializerAPI(active_version_id="ver-z", canary_pct=50)
        req = _make_request(ab_group=ABGroup.CONTROL)
        resp = api.serve(req)
        assert resp.serving_tier == ServingTier.BASE

    def test_ab_treatment_uses_finetuned(self):
        api = ProseSpecializerAPI(active_version_id="ver-z", canary_pct=50)
        req = _make_request(ab_group=ABGroup.TREATMENT)
        resp = api.serve(req)
        assert resp.serving_tier == ServingTier.FINETUNED

    def test_deterministic_routing_same_request_id(self):
        """같은 request_id → 항상 같은 라우팅 결과"""
        api = ProseSpecializerAPI(active_version_id="ver-det", canary_pct=50)
        req_id = str(uuid.uuid4())
        req = ServeRequest(request_id=req_id, prompt="테스트", style_hint="romance")
        resp1 = api.serve(req)
        resp2 = api.serve(req)
        assert resp1.serving_tier == resp2.serving_tier


class TestProseSpecializerAPIAB:
    """A/B 비교 테스트"""

    def test_compare_ab_returns_result(self):
        api = ProseSpecializerAPI(active_version_id="ver-ab", canary_pct=50)
        result = api.compare_ab("로맨틱한 장면을 묘사하라", style_hint="romance")
        assert result is not None

    def test_compare_ab_has_comparison_id(self):
        api = ProseSpecializerAPI(active_version_id="ver-ab", canary_pct=50)
        result = api.compare_ab("장면 묘사", style_hint="thriller")
        assert result.comparison_id != ""

    def test_compare_ab_has_control_and_treatment(self):
        api = ProseSpecializerAPI(active_version_id="ver-ab", canary_pct=50)
        result = api.compare_ab("SF 장면", style_hint="sf")
        assert result.control_response is not None
        assert result.treatment_response is not None

    def test_compare_ab_winner_valid(self):
        api = ProseSpecializerAPI(active_version_id="ver-ab", canary_pct=50)
        result = api.compare_ab("로맨스 장면", style_hint="romance")
        # winner는 CONTROL, TREATMENT, 또는 None(무승부)
        assert result.winner in (ABGroup.CONTROL, ABGroup.TREATMENT, None)

    def test_compare_ab_has_metrics(self):
        api = ProseSpecializerAPI(active_version_id="ver-ab", canary_pct=50)
        result = api.compare_ab("스릴러 장면", style_hint="thriller")
        assert isinstance(result.metrics, dict)
        assert len(result.metrics) > 0


class TestProseSpecializerAPIStats:
    """통계"""

    def test_stats_initial(self):
        api = ProseSpecializerAPI()
        stats = api.get_stats()
        assert stats["total_requests"] == 0

    def test_stats_after_serve(self):
        api = ProseSpecializerAPI()
        api.serve(_make_request())
        api.serve(_make_request())
        stats = api.get_stats()
        assert stats["total_requests"] == 2

    def test_stats_ab_comparisons(self):
        api = ProseSpecializerAPI(active_version_id="ver-stat", canary_pct=50)
        api.compare_ab("장면 묘사", style_hint="romance")
        stats = api.get_stats()
        assert stats["ab_comparisons"] == 1

    def test_set_active_version(self):
        api = ProseSpecializerAPI()
        api.set_active_version("ver-new", 10)
        stats = api.get_stats()
        assert stats["active_version_id"] == "ver-new"
        assert stats["canary_pct"] == 10


class TestProseSpecializerAPIStyles:
    """스타일별 생성"""

    def test_serve_romance_style(self):
        api = ProseSpecializerAPI(active_version_id="ver-style", canary_pct=100)
        resp = api.serve(_make_request("romance"))
        assert resp.generated_text != ""

    def test_serve_thriller_style(self):
        api = ProseSpecializerAPI(active_version_id="ver-style", canary_pct=100)
        resp = api.serve(_make_request("thriller"))
        assert resp.generated_text != ""

    def test_serve_sf_style(self):
        api = ProseSpecializerAPI(active_version_id="ver-style", canary_pct=100)
        resp = api.serve(_make_request("sf"))
        assert resp.generated_text != ""

    def test_token_count_positive(self):
        api = ProseSpecializerAPI(active_version_id="ver-tok", canary_pct=100)
        resp = api.serve(_make_request("romance"))
        assert resp.token_count >= 0


# ─────────────────────────────────────────────
# Gate19 통합 검증
# ─────────────────────────────────────────────

class TestGate19Integration:
    """Gate19 _gate_sp4_finetune() 전체 검증"""

    def test_gate19_passes(self):
        from literary_system.gates.gate19_sp4_finetune import _gate_sp4_finetune
        result = _gate_sp4_finetune()
        assert result["pass"] is True, f"Gate19 실패: {result.get('errors')}"

    def test_gate19_modules_verified(self):
        from literary_system.gates.gate19_sp4_finetune import _gate_sp4_finetune
        result = _gate_sp4_finetune()
        assert result["modules_verified"] >= 5

    def test_gate19_no_errors(self):
        from literary_system.gates.gate19_sp4_finetune import _gate_sp4_finetune
        result = _gate_sp4_finetune()
        assert len(result["errors"]) == 0, f"에러 발생: {result['errors']}"

    def test_gate19_symbols_verified(self):
        from literary_system.gates.gate19_sp4_finetune import _gate_sp4_finetune
        result = _gate_sp4_finetune()
        syms = result["symbols_verified"]
        assert any("FineTuneJobManager" in s for s in syms)
        assert any("ProseStyleDataset" in s for s in syms)
        assert any("ModelEvalHarness" in s for s in syms)
        assert any("SafetyRegressionSuite" in s for s in syms)
        assert any("ModelVersionManager" in s for s in syms)
        assert any("CanaryKPIMonitor" in s for s in syms)
        assert any("ProseSpecializerAPI" in s for s in syms)
