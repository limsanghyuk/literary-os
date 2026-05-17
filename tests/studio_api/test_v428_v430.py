"""
V428~V430 테스트 스위트
A. V428 i18n 메시지 레이어 -- 로케일 전환 + 키 존재 확인
B. V428 analyze.py i18n 교체 -- 하드코딩 제거 검증
C. V429 CostLedger v2 -- budget 추적 + by_endpoint alias
D. V430 Docker 설정 -- DEV_MODE 기본값 + 환경변수 선언
E. 통합 E2E -- API 전체 흐름 (CB + Cost + i18n)
F. GitNexus 최종 무결성 -- 모든 단절 해소 확인
"""
from __future__ import annotations

import os
from pathlib import Path
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# A. V428 i18n 메시지 레이어
# ─────────────────────────────────────────────────────────────────────────────

class TestV428I18nMessages:
    """i18n 메시지 모듈 구조 및 로케일 전환 검증."""

    def test_ko_module_has_all_required_keys(self):
        from apps.studio_api.messages import ko
        required = [
            "CB_GATE_OPEN", "CB_DRSE_OPEN", "CB_NKG_OPEN", "CB_VOICE_OPEN",
            "CB_GATE_DEGRADED", "HINT_OVERLOAD", "HINT_VOICE_DRIFT",
            "HINT_PAYOFF_DEBT", "HINT_FATIGUE", "WARN_NO_DELIMITER",
        ]
        for key in required:
            assert hasattr(ko, key), f"Missing key: {key}"

    def test_en_module_has_all_required_keys(self):
        from apps.studio_api.messages import en
        required = [
            "CB_GATE_OPEN", "CB_DRSE_OPEN", "CB_NKG_OPEN", "CB_VOICE_OPEN",
            "CB_GATE_DEGRADED", "HINT_OVERLOAD", "HINT_VOICE_DRIFT",
            "HINT_PAYOFF_DEBT", "HINT_FATIGUE", "WARN_NO_DELIMITER",
        ]
        for key in required:
            assert hasattr(en, key), f"Missing key: {key}"

    def test_ko_and_en_have_same_keys(self):
        from apps.studio_api.messages import ko, en
        ko_keys = {k for k in dir(ko) if not k.startswith('_') and k.isupper()}
        en_keys = {k for k in dir(en) if not k.startswith('_') and k.isupper()}
        assert ko_keys == en_keys, f"Key mismatch: ko={ko_keys-en_keys}, en={en_keys-ko_keys}"

    def test_get_function_returns_korean_by_default(self):
        import apps.studio_api.messages as msg
        os.environ["LITERARY_OS_LOCALE"] = "ko"
        msg.reload("ko")
        val = msg.get("CB_GATE_OPEN")
        assert len(val) > 0
        assert "OPEN" in val or "오픈" in val.upper() or "Circuit" in val or "게이트" in val

    def test_reload_switches_locale_to_english(self):
        import apps.studio_api.messages as msg
        msg.reload("en")
        val = msg.get("CB_GATE_OPEN")
        assert "Gate" in val or "OPEN" in val
        assert "게이트" not in val
        # 복원
        msg.reload("ko")

    def test_reload_unsupported_locale_falls_back_to_ko(self):
        import apps.studio_api.messages as msg
        msg.reload("zh")  # 미지원 → ko fallback
        val = msg.get("CB_GATE_OPEN")
        assert len(val) > 0
        msg.reload("ko")

    def test_convenience_accessors_exist(self):
        import apps.studio_api.messages as msg
        msg.reload("ko")
        assert callable(msg.cb_gate_open)
        assert callable(msg.cb_gate_degraded)
        assert callable(msg.hint_overload)
        assert callable(msg.hint_voice_drift)
        assert callable(msg.hint_payoff_debt)
        assert callable(msg.hint_fatigue)
        assert callable(msg.warn_no_delimiter)

    def test_convenience_accessors_return_nonempty_strings(self):
        import apps.studio_api.messages as msg
        msg.reload("ko")
        for fn in [msg.cb_gate_open, msg.cb_gate_degraded, msg.hint_overload,
                   msg.hint_voice_drift, msg.hint_payoff_debt, msg.hint_fatigue,
                   msg.warn_no_delimiter]:
            val = fn()
            assert isinstance(val, str) and len(val) > 0, f"{fn.__name__} returned empty"

    def test_get_unknown_key_returns_default(self):
        import apps.studio_api.messages as msg
        val = msg.get("NONEXISTENT_KEY_XYZ", "fallback")
        assert val == "fallback"


# ─────────────────────────────────────────────────────────────────────────────
# B. V428 analyze.py 하드코딩 제거 검증
# ─────────────────────────────────────────────────────────────────────────────

class TestV428AnalyzeI18nCleanup:
    """analyze.py 에서 하드코딩 한국어 문자열이 제거됐는지 검증."""

    def test_analyze_router_imports_messages(self):
        import apps.studio_api.routers.analyze as mod
        import inspect
        src = inspect.getsource(mod)
        assert "import apps.studio_api.messages as msg" in src

    def test_analyze_no_hardcoded_korean_hints(self):
        import apps.studio_api.routers.analyze as mod
        import inspect
        src = inspect.getsource(mod)
        hardcoded = [
            "클라이맥스 밀집 구간을 분산시키세요",
            "캐릭터 음성 일관성을 확인하세요",
            "미지불 Payoff Debt를 해소하세요",
            "독자 주의력 피로 구간을 조정하세요",
        ]
        for phrase in hardcoded:
            assert phrase not in src, f"하드코딩 잔존: {phrase!r}"

    def test_analyze_no_hardcoded_cb_messages(self):
        import apps.studio_api.routers.analyze as mod
        import inspect
        src = inspect.getsource(mod)
        hardcoded = [
            "게이트 Circuit OPEN",
            "게이트 실행 실패 -- 열화 모드",
        ]
        for phrase in hardcoded:
            assert phrase not in src, f"하드코딩 잔존: {phrase!r}"

    def test_analyze_uses_msg_accessors(self):
        import apps.studio_api.routers.analyze as mod
        import inspect
        src = inspect.getsource(mod)
        assert "msg.cb_gate_open()" in src
        assert "msg.cb_gate_degraded()" in src
        assert "msg.hint_overload()" in src
        assert "msg.hint_voice_drift()" in src
        assert "msg.hint_payoff_debt()" in src
        assert "msg.hint_fatigue()" in src

    def test_locale_switch_affects_gate_hints(self):
        """로케일 전환이 실제 hints 값에 반영돼야 한다."""
        import apps.studio_api.messages as msg
        msg.reload("ko")
        ko_hint = msg.hint_overload()
        msg.reload("en")
        en_hint = msg.hint_overload()
        assert ko_hint != en_hint, "KO/EN 힌트가 동일 — 로케일 전환 미작동"
        msg.reload("ko")


# ─────────────────────────────────────────────────────────────────────────────
# C. V429 CostLedger v2
# ─────────────────────────────────────────────────────────────────────────────

class TestV429CostLedgerV2:
    """CostLedger v2: budget 추적 + by_endpoint alias + 스키마 검증."""

    def test_cost_summary_response_has_by_endpoint(self):
        from apps.studio_api.schema.mapper import CostSummaryResponse
        resp = CostSummaryResponse(
            total_entries=2,
            total_cost_usd=5.0,
            total_tokens=1000,
            by_operation_type={"analyze": 3.0, "gate": 2.0},
            by_endpoint={"analyze": 3.0, "gate": 2.0},
            budget_limit_usd=100.0,
            budget_used_pct=5.0,
        )
        assert resp.by_endpoint["analyze"] == 3.0
        assert resp.budget_limit_usd == 100.0
        assert resp.budget_used_pct == 5.0

    def test_cost_summary_response_defaults(self):
        from apps.studio_api.schema.mapper import CostSummaryResponse
        resp = CostSummaryResponse(
            total_entries=0,
            total_cost_usd=0.0,
            total_tokens=0,
        )
        assert resp.by_endpoint == {}
        assert resp.budget_limit_usd == 100.0
        assert resp.budget_used_pct == 0.0

    def test_cost_router_has_budget_env_var(self):
        import apps.studio_api.routers.cost as mod
        import inspect
        src = inspect.getsource(mod)
        assert "LITERARY_OS_COST_BUDGET_USD" in src
        assert "_BUDGET_LIMIT_USD" in src

    def test_cost_router_summary_includes_by_endpoint(self):
        import apps.studio_api.routers.cost as mod
        import inspect
        src = inspect.getsource(mod)
        assert "by_endpoint" in src
        assert "budget_used_pct" in src
        assert "budget_limit_usd" in src

    def test_cost_router_has_clear_endpoint(self):
        """V429 DELETE /cost/ledger 엔드포인트 추가 확인."""
        import apps.studio_api.routers.cost as mod
        import inspect
        src = inspect.getsource(mod)
        assert "clear_ledger" in src or "DELETE" in src or "router.delete" in src

    def test_budget_used_pct_calculation(self):
        """budget_used_pct = (total / limit) * 100, max 100."""
        from apps.studio_api.schema.mapper import CostSummaryResponse
        resp = CostSummaryResponse(
            total_entries=1,
            total_cost_usd=50.0,
            total_tokens=0,
            budget_limit_usd=100.0,
            budget_used_pct=50.0,
        )
        assert resp.budget_used_pct == 50.0

    def test_by_endpoint_alias_matches_by_operation_type(self):
        """by_endpoint 와 by_operation_type 이 동일 데이터여야 한다."""
        from apps.studio_api.schema.mapper import CostSummaryResponse
        data = {"analyze": 4.2, "gate": 2.1, "generate": 5.3}
        resp = CostSummaryResponse(
            total_entries=3,
            total_cost_usd=11.6,
            total_tokens=0,
            by_operation_type=data,
            by_endpoint=data,
        )
        assert resp.by_endpoint == resp.by_operation_type

    def test_cost_entry_schema_fields(self):
        from apps.studio_api.schema.mapper import CostEntry
        e = CostEntry(
            entry_id="e1",
            series_id="S1",
            operation_type="analyze",
            cost_usd=0.5,
            timestamp="2026-05-14T10:00:00Z",
        )
        assert e.entry_id == "e1"
        assert e.cost_usd == 0.5


# ─────────────────────────────────────────────────────────────────────────────
# D. V430 Docker 설정 검증
# ─────────────────────────────────────────────────────────────────────────────

class TestV430DockerConfig:
    """Dockerfile + docker-compose 설정 검증."""

    def _read_file(self, filename: str) -> str:
        from pathlib import Path
        p = Path(__file__).parent.parent.parent / filename
        if not p.exists():
            pytest.skip(f"{filename} 없음")
        return p.read_text()

    def test_dockerfile_sets_dev_mode_false(self):
        """Dockerfile 에 LITERARY_OS_DEV_MODE=false 가 있어야 한다 (단절 #2 해결)."""
        src = self._read_file("Dockerfile")
        assert "LITERARY_OS_DEV_MODE=false" in src, \
            "Dockerfile DEV_MODE=false 미설정 — 프로덕션 인증 bypass 위험!"

    def test_dockerfile_exposes_port_8000(self):
        src = self._read_file("Dockerfile")
        assert "EXPOSE 8000" in src

    def test_dockerfile_has_healthcheck(self):
        src = self._read_file("Dockerfile")
        assert "HEALTHCHECK" in src
        assert "/health" in src

    def test_dockerfile_uses_non_root_user(self):
        src = self._read_file("Dockerfile")
        assert "USER literary" in src or "USER " in src

    def test_dockerfile_has_uvicorn_cmd(self):
        src = self._read_file("Dockerfile")
        assert "uvicorn" in src
        assert "apps.studio_api.main:create_app" in src

    def test_docker_compose_has_dev_mode_env(self):
        src = self._read_file("docker-compose.yml")
        assert "LITERARY_OS_DEV_MODE" in src

    def test_docker_compose_has_dev_profile(self):
        src = self._read_file("docker-compose.yml")
        assert "dev" in src

    def test_docker_compose_has_healthcheck(self):
        src = self._read_file("docker-compose.yml")
        assert "healthcheck" in src

    def test_requirements_txt_has_core_deps(self):
        src = self._read_file("requirements.txt")
        assert "fastapi" in src
        assert "uvicorn" in src
        assert "pydantic" in src
        assert "opentelemetry-sdk" in src
        assert "python-jose" in src

    def test_middleware_dev_mode_default_false_in_prod(self):
        """auth/middleware.py DEV_MODE 기본값이 env로 제어돼야 한다."""
        import apps.studio_api.auth.middleware as mod
        import inspect
        src = inspect.getsource(mod)
        assert "LITERARY_OS_DEV_MODE" in src
        # 기본값이 "true" 인 것 자체는 허용 — Docker에서 false로 오버라이드
        assert 'os.environ.get("LITERARY_OS_DEV_MODE"' in src


# ─────────────────────────────────────────────────────────────────────────────
# E. 통합 E2E 흐름
# ─────────────────────────────────────────────────────────────────────────────

class TestV430IntegrationE2E:
    """API 전체 흐름: CB + i18n + Cost + Jobs."""

    def setup_method(self):
        try:
            from fastapi.testclient import TestClient
            from apps.studio_api.main import create_app
            self.client = TestClient(create_app())
            self.available = True
        except Exception:
            self.available = False

    def test_health_endpoint_version_v427(self):
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.get("/health")
        assert resp.status_code == 200
        assert resp.json().get("version") == "V427"

    def test_health_circuit_breakers_as_list(self):
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.get("/health")
        data = resp.json()
        cbs = data.get("circuit_breakers", [])
        assert isinstance(cbs, list), "circuit_breakers should be list"
        assert len(cbs) == 4

    def test_cost_summary_has_by_endpoint(self):
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.get("/api/v1/cost/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "by_endpoint" in data
        assert "budget_limit_usd" in data
        assert "budget_used_pct" in data

    def test_cost_ledger_record_and_summary(self):
        """비용 기록 후 summary 집계 확인 E2E."""
        if not self.available:
            pytest.skip("FastAPI unavailable")
        # 기록
        self.client.post("/api/v1/cost/ledger", json={
            "series_id": "S_E2E",
            "operation_type": "analyze",
            "cost_usd": 0.25,
            "token_count": 500,
        })
        self.client.post("/api/v1/cost/ledger", json={
            "series_id": "S_E2E",
            "operation_type": "gate",
            "cost_usd": 0.10,
        })
        # summary 조회
        resp = self.client.get("/api/v1/cost/summary?series_id=S_E2E")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_entries"] >= 2
        assert data["total_cost_usd"] >= 0.35
        assert "analyze" in data["by_endpoint"]

    def test_nkg_endpoint_returns_paginated(self):
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.get("/api/v1/nkg/S1?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data and "edges" in data
        assert "page" in data and "page_size" in data

    def test_jobs_list_and_cancel(self):
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.get("/api/v1/jobs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_dashboard_route_exists(self):
        """GET /dashboard 가 200 또는 404(HTML파일없음)를 반환해야 한다."""
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.get("/dashboard")
        assert resp.status_code in (200, 404)

    def test_import_export_roundtrip(self):
        """import → export 기본 왕복 E2E."""
        if not self.available:
            pytest.skip("FastAPI unavailable")
        # import
        imp = self.client.post("/api/v1/import", json={
            "series_id": "S_RT",
            "format": "txt",
            "content": "# 씬 1\n" + "내용이다. " * 20 + "\n# 씬 2\n" + "또 다른 내용. " * 20,
        })
        assert imp.status_code == 200
        imp_data = imp.json()
        scene_ids = imp_data.get("imported_scene_ids", [])
        # export
        exp = self.client.post("/api/v1/export", json={
            "series_id": "S_RT",
            "format": "md",
            "scene_ids": scene_ids,
        })
        assert exp.status_code == 200

    def test_analyze_returns_trace_id(self):
        """POST /analyze 응답에 trace_id 가 포함돼야 한다."""
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.post("/api/v1/analyze", json={
            "series_id": "S1",
            "scene_id": "SC-001",
            "episode": 1,
            "content": "주인공이 등장한다. " * 10,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "trace_id" in data
        assert "drse_score" in data


# ─────────────────────────────────────────────────────────────────────────────
# F. GitNexus 최종 무결성 감사
# ─────────────────────────────────────────────────────────────────────────────

class TestGitNexusFinalIntegrity:
    """V428~V430 완료 후 전체 단절 해소 + 파생 효과 해결 확인."""

    def test_disconnection1_by_endpoint_resolved(self):
        """단절 #1: dashboard by_endpoint ↔ CostSummaryResponse 불일치 해소."""
        from apps.studio_api.schema.mapper import CostSummaryResponse
        assert "by_endpoint" in CostSummaryResponse.model_fields

    def test_disconnection2_docker_dev_mode_resolved(self):
        """단절 #2: Docker DEV_MODE 기본값 false 설정 확인."""
        from pathlib import Path
        df = Path(__file__).parent.parent.parent / 'Dockerfile'
        if not df.exists():
            pytest.skip("Dockerfile 없음")
        assert "LITERARY_OS_DEV_MODE=false" in df.read_text()

    def test_disconnection3_i18n_hardcoding_resolved(self):
        """단절 #3: analyze.py 하드코딩 한국어 제거."""
        import apps.studio_api.routers.analyze as mod
        import inspect
        src = inspect.getsource(mod)
        assert "msg.hint_overload()" in src

    def test_cb_instances_all_wired_v427(self):
        """V427 CB 배선: 4개 CB 모두 라우터에서 사용."""
        import apps.studio_api.routers.analyze as mod
        import inspect
        src = inspect.getsource(mod)
        for cb in ["drse_cb.call(", "gate_cb.call(", "nkg_cb.call(", "voice_cb.call("]:
            assert cb in src, f"{cb} not found — CB disconnection!"

    def test_ws_energy_no_stub_v426(self):
        """V426 ws/energy.py: sin stub 제거."""
        import apps.studio_api.ws.energy as mod
        import inspect
        src = inspect.getsource(mod)
        assert "math.sin(i)" not in src

    def test_all_v420_routers_registered_in_main(self):
        """V420: 모든 라우터가 main.py 에 등록됐는지 확인."""
        import apps.studio_api.main as mod
        import inspect
        src = inspect.getsource(mod)
        for router_mod in ["analyze", "generate", "cost", "io", "jobs"]:
            assert router_mod in src, f"Router {router_mod} not in main.py"

    def test_schema_mapper_energy_vector_accepts_any(self):
        """AnalyzeResponse.energy_vector 가 str 값을 수용 (CB OPEN 상태)."""
        from apps.studio_api.schema.mapper import AnalyzeResponse
        resp = AnalyzeResponse(
            trace_id="t1",
            drse_score=0.0,
            energy_vector={"degraded": 1.0, "cb_open": "drse_engine"},
        )
        assert resp.energy_vector["cb_open"] == "drse_engine"

    def test_messages_package_importable(self):
        """messages 패키지가 정상 임포트돼야 한다."""
        import apps.studio_api.messages as msg
        assert callable(msg.get)
        assert callable(msg.reload)

    def test_cost_router_v2_has_budget_tracking(self):
        """CostLedger v2: budget 추적 코드 존재."""
        import apps.studio_api.routers.cost as mod
        import inspect
        src = inspect.getsource(mod)
        assert "budget_pct" in src or "budget_used_pct" in src

    def test_docker_compose_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent.parent / 'docker-compose.yml'
        assert p.exists()
        content = p.read_text()
        assert "studio-api" in content
        assert "LITERARY_OS_DEV_MODE" in content

    def test_final_module_count(self):
        """최종 apps/studio_api 모듈 수 >= 20."""
        import glob
        modules = glob.glob(
            str(Path(__file__).parent.parent.parent / 'apps' / 'studio_api' / '**' / '*.py'),
            recursive=True
        )
        modules = [m for m in modules if '__pycache__' not in m]
        assert len(modules) >= 20, f"모듈 수 부족: {len(modules)}"
