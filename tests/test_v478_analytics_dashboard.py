"""
tests/test_v478_analytics_dashboard.py
V478 — AnalyticsDashboard + PublicAPIDoc 테스트
"""
import pytest
from literary_system.ops.analytics_dashboard import (
    AnalyticsDashboard, AnalyticsEvent, CohortReport, NPSResult, PublicAPIDoc,
)


# ──────────────────────────────────────────────────────────────────────────────
# AnalyticsDashboard
# ──────────────────────────────────────────────────────────────────────────────
class TestAnalyticsDashboard:
    def test_track_event_returns_event(self):
        dash = AnalyticsDashboard()
        evt = dash.track_event("login", "usr_001")
        assert isinstance(evt, AnalyticsEvent)
        assert evt.name == "login"

    def test_event_id_sequential(self):
        dash = AnalyticsDashboard()
        e1 = dash.track_event("a", "u1")
        e2 = dash.track_event("b", "u1")
        assert e1.event_id != e2.event_id

    def test_event_count(self):
        dash = AnalyticsDashboard()
        dash.track_event("a", "u1")
        dash.track_event("b", "u2")
        assert dash.event_count() == 2

    def test_events_by_name(self):
        dash = AnalyticsDashboard()
        dash.track_event("click", "u1")
        dash.track_event("click", "u2")
        dash.track_event("view", "u1")
        assert len(dash.events_by_name("click")) == 2
        assert len(dash.events_by_name("view")) == 1

    def test_unique_users(self):
        dash = AnalyticsDashboard()
        dash.track_event("a", "u1")
        dash.track_event("b", "u1")
        dash.track_event("a", "u2")
        assert dash.unique_users() == 2

    def test_event_properties(self):
        dash = AnalyticsDashboard()
        evt = dash.track_event("page_view", "u1", {"page": "/home"})
        assert evt.properties["page"] == "/home"

    def test_compute_nps_basic(self):
        dash = AnalyticsDashboard()
        nps = dash.compute_nps([10, 9, 8, 6, 3])
        assert isinstance(nps, NPSResult)
        assert -100 <= nps.score <= 100

    def test_nps_promoters(self):
        dash = AnalyticsDashboard()
        nps = dash.compute_nps([10, 9, 10])
        assert nps.promoters == 3
        assert nps.score == pytest.approx(100.0)

    def test_nps_detractors(self):
        dash = AnalyticsDashboard()
        nps = dash.compute_nps([0, 1, 2])
        assert nps.detractors == 3
        assert nps.score == pytest.approx(-100.0)

    def test_nps_empty_raises(self):
        dash = AnalyticsDashboard()
        with pytest.raises(ValueError):
            dash.compute_nps([])

    def test_nps_invalid_score_raises(self):
        dash = AnalyticsDashboard()
        with pytest.raises(ValueError):
            dash.compute_nps([11])

    def test_nps_mixed(self):
        dash = AnalyticsDashboard()
        # 2 promoters, 1 passive, 2 detractors → (2-2)/5 * 100 = 0
        nps = dash.compute_nps([10, 9, 8, 5, 4])
        assert nps.score == pytest.approx(0.0)

    def test_summary_keys(self):
        dash = AnalyticsDashboard()
        dash.track_event("login", "u1")
        s = dash.summary()
        assert "total_events" in s
        assert "unique_users" in s
        assert "event_breakdown" in s

    def test_cohort_no_events_returns_empty(self):
        dash = AnalyticsDashboard()
        r = dash.cohort_analysis(window_days=30)
        assert isinstance(r, CohortReport)
        assert r.total_users == 0


# ──────────────────────────────────────────────────────────────────────────────
# PublicAPIDoc
# ──────────────────────────────────────────────────────────────────────────────
class TestPublicAPIDoc:
    def test_generate_openapi_version(self):
        doc = PublicAPIDoc()
        spec = doc.generate_openapi()
        assert spec["openapi"] == "3.1.0"

    def test_generate_openapi_title(self):
        doc = PublicAPIDoc()
        spec = doc.generate_openapi()
        assert "Literary OS" in spec["info"]["title"]

    def test_generate_openapi_paths_count(self):
        doc = PublicAPIDoc()
        spec = doc.generate_openapi()
        assert len(spec["paths"]) >= 10

    def test_generate_openapi_has_security(self):
        doc = PublicAPIDoc()
        spec = doc.generate_openapi()
        assert "security" in spec
        assert len(spec["security"]) > 0

    def test_generate_openapi_bearer_scheme(self):
        doc = PublicAPIDoc()
        spec = doc.generate_openapi()
        schemes = spec["components"]["securitySchemes"]
        assert "BearerAuth" in schemes
        assert schemes["BearerAuth"]["type"] == "http"

    def test_generate_openapi_has_tags(self):
        doc = PublicAPIDoc()
        spec = doc.generate_openapi()
        assert len(spec["tags"]) > 0

    def test_endpoint_count(self):
        doc = PublicAPIDoc()
        assert doc.endpoint_count() >= 10

    def test_all_paths_have_responses(self):
        doc = PublicAPIDoc()
        spec = doc.generate_openapi()
        for path, methods in spec["paths"].items():
            for method, op in methods.items():
                assert "responses" in op, f"No responses for {method} {path}"

    def test_generate_openapi_has_generate_endpoint(self):
        doc = PublicAPIDoc()
        spec = doc.generate_openapi()
        assert "/api/v2/generate" in spec["paths"]

    def test_generate_openapi_has_health_endpoint(self):
        doc = PublicAPIDoc()
        spec = doc.generate_openapi()
        assert "/api/v2/health" in spec["paths"]
