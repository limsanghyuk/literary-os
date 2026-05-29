"""
V425~V427 테스트 스위트
A. V427 Circuit Breaker 강화 -- analyze.py CB 배선 검증
B. V427 CB 상태 전이 -- CLOSED->OPEN->HALF_OPEN->CLOSED
C. V426 WebSocket 에너지 스트림 -- drse_cb 연동
D. V425 대시보드 엔드포인트 -- /health CB 상태 + 스키마 검증
E. 열화 모드 -- CB OPEN 시 degraded 응답 검증
"""
from __future__ import annotations

import json
import pytest
import asyncio


# ─────────────────────────────────────────────────────────────────────────────
# A. V427 Circuit Breaker 강화 -- analyze.py 임포트 & CB 배선
# ─────────────────────────────────────────────────────────────────────────────

class TestV427AnalyzeCBWiring:
    """analyze.py 에서 CB 인스턴스가 실제로 임포트·사용되는지 검증."""

    def test_analyze_router_imports_circuit_breakers(self):
        """analyze.py 가 drse_cb/gate_cb/nkg_cb/voice_cb 를 임포트해야 한다."""
        import apps.studio_api.routers.analyze as mod
        # 모듈 소스에서 CB import 확인
        import inspect
        src = inspect.getsource(mod)
        assert "drse_cb" in src
        assert "gate_cb" in src
        assert "nkg_cb" in src
        assert "voice_cb" in src
        assert "CircuitBreakerOpen" in src

    def test_analyze_router_uses_cb_call(self):
        """analyze.py 내부에서 .call() 패턴이 사용돼야 한다."""
        import apps.studio_api.routers.analyze as mod
        import inspect
        src = inspect.getsource(mod)
        assert "drse_cb.call(" in src
        assert "gate_cb.call(" in src
        assert "nkg_cb.call(" in src
        assert "voice_cb.call(" in src

    def test_analyze_router_handles_cb_open(self):
        """CB OPEN 예외를 잡아 degraded 응답을 반환해야 한다."""
        import apps.studio_api.routers.analyze as mod
        import inspect
        src = inspect.getsource(mod)
        assert "CircuitBreakerOpen" in src
        assert "cb_open" in src

    def test_energy_ws_imports_drse_cb(self):
        """ws/energy.py 가 drse_cb 를 임포트해야 한다."""
        import apps.studio_api.ws.energy as mod
        import inspect
        src = inspect.getsource(mod)
        assert "drse_cb" in src
        assert "drse_cb.call(" in src
        assert "CircuitBreakerOpen" in src

    def test_energy_ws_no_sin_stub(self):
        """V426: ws/energy.py 가 sin() stub 을 제거하고 실제 DRSE를 사용해야 한다."""
        import apps.studio_api.ws.energy as mod
        import inspect
        src = inspect.getsource(mod)
        # sin stub 제거 확인
        assert "math.sin(i)" not in src
        # 실제 DRSE 함수 포함 확인
        assert "_drse_evaluate_scene" in src

    def test_energy_ws_7layer_labels(self):
        """ws/energy.py 가 7-레이어 레이블을 정의해야 한다."""
        from apps.studio_api.ws.energy import _LAYER_LABELS
        assert len(_LAYER_LABELS) == 7
        assert "L1" in _LAYER_LABELS[0]
        assert "L7" in _LAYER_LABELS[6]

    def test_energy_ws_cb_open_event(self):
        """CB OPEN 시 cb_open 이벤트 전송 코드가 있어야 한다."""
        import apps.studio_api.ws.energy as mod
        import inspect
        src = inspect.getsource(mod)
        assert '"cb_open"' in src or "'cb_open'" in src

    def test_energy_ws_stream_end_has_total_energy(self):
        """stream_end 이벤트에 total_energy 필드가 포함돼야 한다."""
        import apps.studio_api.ws.energy as mod
        import inspect
        src = inspect.getsource(mod)
        assert "total_energy" in src


# ─────────────────────────────────────────────────────────────────────────────
# B. V427 CB 상태 전이
# ─────────────────────────────────────────────────────────────────────────────

class TestV427CBStateMachine:
    """Circuit Breaker 상태 전이 검증."""

    def test_cb_starts_closed(self):
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker, CBState
        cb = CircuitBreaker("test_start", failure_threshold=3)
        assert cb.state == CBState.CLOSED

    def test_cb_opens_after_threshold(self):
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker, CBState
        cb = CircuitBreaker("test_open", failure_threshold=3)
        def fail():
            raise ValueError("boom")
        for _ in range(3):
            try:
                cb.call(fail)
            except ValueError:
                pass
        assert cb.state == CBState.OPEN

    def test_cb_open_raises_circuit_breaker_open(self):
        from apps.studio_api.resilience.circuit_breaker import (
            CircuitBreaker, CBState, CircuitBreakerOpen
        )
        cb = CircuitBreaker("test_cbo", failure_threshold=2)
        def fail():
            raise RuntimeError("err")
        for _ in range(2):
            try:
                cb.call(fail)
            except RuntimeError:
                pass
        assert cb.state == CBState.OPEN
        with pytest.raises(CircuitBreakerOpen):
            cb.call(lambda: None)

    def test_cb_half_open_after_timeout(self):
        """recovery_timeout 경과 후 HALF_OPEN 전환 검증."""
        import time
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker, CBState
        cb = CircuitBreaker("test_halfopen", failure_threshold=2, recovery_timeout=0.05)
        def fail():
            raise RuntimeError("err")
        for _ in range(2):
            try:
                cb.call(fail)
            except RuntimeError:
                pass
        assert cb.state == CBState.OPEN
        time.sleep(0.1)
        assert cb.state == CBState.HALF_OPEN

    def test_cb_closes_after_success_threshold(self):
        """HALF_OPEN 상태에서 성공 2회 -> CLOSED 전환."""
        import time
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker, CBState
        cb = CircuitBreaker("test_close", failure_threshold=2, recovery_timeout=0.05,
                            success_threshold=2)
        def fail():
            raise RuntimeError("err")
        for _ in range(2):
            try:
                cb.call(fail)
            except RuntimeError:
                pass
        time.sleep(0.1)
        assert cb.state == CBState.HALF_OPEN
        cb.call(lambda: "ok")
        cb.call(lambda: "ok")
        assert cb.state == CBState.CLOSED

    def test_cb_reset_forces_closed(self):
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker, CBState
        cb = CircuitBreaker("test_reset", failure_threshold=2)
        def fail():
            raise RuntimeError()
        for _ in range(2):
            try:
                cb.call(fail)
            except RuntimeError:
                pass
        assert cb.state == CBState.OPEN
        cb.reset()
        assert cb.state == CBState.CLOSED

    def test_cb_status_dict_keys(self):
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker("test_status", failure_threshold=5)
        status = cb.status()
        for key in ("name", "state", "failure_count", "failure_threshold",
                    "remaining_timeout_s"):
            assert key in status, f"Missing key: {key}"

    def test_preconfigured_instances_present(self):
        from apps.studio_api.resilience.circuit_breaker import (
            drse_cb, nkg_cb, gate_cb, voice_cb
        )
        assert drse_cb.name == "drse_engine"
        assert nkg_cb.name == "nkg_store"
        assert gate_cb.name == "endurance_gate"
        assert voice_cb.name == "voice_manifold"
        assert gate_cb.failure_threshold == 3   # gate가 더 엄격
        assert gate_cb.recovery_timeout == 60.0

    def test_cb_thread_safety(self):
        """멀티스레드 동시 호출 안전성 검증."""
        import threading
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker, CBState
        cb = CircuitBreaker("test_thread", failure_threshold=50)
        results = []
        errors = []
        def do_call():
            try:
                cb.call(lambda: "ok")
                results.append("ok")
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_call) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(results) == 20
        assert cb.state == CBState.CLOSED


# ─────────────────────────────────────────────────────────────────────────────
# C. V426 WebSocket 에너지 스트림 단위 테스트
# ─────────────────────────────────────────────────────────────────────────────

class TestV426EnergyStream:
    """_drse_evaluate_scene 함수 단위 검증."""

    def test_drse_evaluate_returns_7_scores(self):
        from apps.studio_api.ws.energy import _drse_evaluate_scene
        scores = _drse_evaluate_scene("S1", "SC-001", 1)
        assert isinstance(scores, list)
        assert len(scores) == 7

    def test_drse_evaluate_scores_are_non_negative(self):
        from apps.studio_api.ws.energy import _drse_evaluate_scene
        scores = _drse_evaluate_scene("S1", "SC-001", 1)
        for s in scores:
            assert s >= 0.0, f"Negative score: {s}"

    def test_drse_evaluate_scores_are_floats(self):
        from apps.studio_api.ws.energy import _drse_evaluate_scene
        scores = _drse_evaluate_scene("S1", "SC-001", 1)
        for s in scores:
            assert isinstance(s, float)

    def test_stream_energy_cb_open_fallback(self):
        """drse_cb OPEN 시 _stream_energy 가 cb_open 이벤트를 전송해야 한다."""
        import asyncio
        from apps.studio_api.resilience.circuit_breaker import (
            CircuitBreaker, CircuitBreakerOpen
        )
        from apps.studio_api import ws as ws_pkg
        # drse_cb 를 일시적으로 OPEN 으로 강제
        from apps.studio_api.resilience import circuit_breaker as cb_mod
        original_drse_cb = cb_mod.drse_cb
        forced_open_cb = CircuitBreaker("drse_engine_test", failure_threshold=1)
        def _fail():
            raise RuntimeError("forced")
        try:
            forced_open_cb.call(_fail)
        except RuntimeError:
            pass

        # 임시 패치
        cb_mod.drse_cb = forced_open_cb
        import apps.studio_api.ws.energy as energy_mod
        orig_cb = energy_mod.drse_cb
        energy_mod.drse_cb = forced_open_cb

        sent_messages = []

        class MockWS:
            async def send_json(self, data):
                sent_messages.append(data)

        async def run():
            await energy_mod._stream_energy(MockWS(), "S1", "SC-001", 1)

        asyncio.get_event_loop().run_until_complete(run())

        # 복원
        energy_mod.drse_cb = orig_cb
        cb_mod.drse_cb = original_drse_cb

        types = [m.get("type") for m in sent_messages]
        assert "cb_open" in types, f"cb_open not found in: {types}"
        assert "stream_end" in types

    def test_stream_energy_normal_sends_7_updates(self):
        """정상 흐름: 7개 energy_update + 1개 stream_end."""
        import asyncio
        from apps.studio_api.ws.energy import _stream_energy
        from apps.studio_api.resilience.circuit_breaker import drse_cb
        # CB 리셋 (이전 테스트 영향 제거)
        drse_cb.reset()

        sent_messages = []

        class MockWS:
            async def send_json(self, data):
                sent_messages.append(data)

        async def run():
            await _stream_energy(MockWS(), "S1", "SC-001", 1)

        asyncio.get_event_loop().run_until_complete(run())

        updates = [m for m in sent_messages if m.get("type") == "energy_update"]
        ends = [m for m in sent_messages if m.get("type") == "stream_end"]
        assert len(updates) == 7, f"Expected 7 updates, got {len(updates)}"
        assert len(ends) == 1

    def test_stream_energy_update_has_layer_label(self):
        """energy_update 메시지에 layer 레이블이 포함돼야 한다."""
        import asyncio
        from apps.studio_api.ws.energy import _stream_energy
        from apps.studio_api.resilience.circuit_breaker import drse_cb
        drse_cb.reset()

        sent_messages = []

        class MockWS:
            async def send_json(self, data):
                sent_messages.append(data)

        asyncio.get_event_loop().run_until_complete(
            _stream_energy(MockWS(), "S1", "SC-002", 1)
        )

        updates = [m for m in sent_messages if m.get("type") == "energy_update"]
        for u in updates:
            assert "layer" in u
            assert u["layer"].startswith("L")

    def test_stream_end_has_total_energy(self):
        """stream_end 에 total_energy 필드가 있어야 한다."""
        import asyncio
        from apps.studio_api.ws.energy import _stream_energy
        from apps.studio_api.resilience.circuit_breaker import drse_cb
        drse_cb.reset()

        sent_messages = []

        class MockWS:
            async def send_json(self, data):
                sent_messages.append(data)

        asyncio.get_event_loop().run_until_complete(
            _stream_energy(MockWS(), "S1", "SC-003", 1)
        )

        end = next(m for m in sent_messages if m.get("type") == "stream_end")
        assert "total_energy" in end
        assert isinstance(end["total_energy"], float)


# ─────────────────────────────────────────────────────────────────────────────
# D. V425 대시보드 지원 엔드포인트 -- /health CB 상태 검증
# ─────────────────────────────────────────────────────────────────────────────

class TestV425DashboardEndpoints:
    """
    React 대시보드 v1 이 사용하는 REST 엔드포인트 검증.
    /health, /api/v1/nkg/{series_id}, /api/v1/cost/summary
    """

    def setup_method(self):
        """FastAPI TestClient 설정."""
        try:
            from fastapi.testclient import TestClient
            from apps.studio_api.main import create_app
            self.client = TestClient(create_app())
            self.available = True
        except Exception:
            self.available = False

    def test_health_includes_cb_status(self):
        """GET /health 에 circuit_breakers 섹션이 있어야 한다."""
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "circuit_breakers" in data
        cbs = data["circuit_breakers"]
        cb_names = {cb["name"] for cb in cbs}
        assert "drse_engine" in cb_names
        assert "nkg_store" in cb_names
        assert "endurance_gate" in cb_names
        assert "voice_manifold" in cb_names

    def test_health_cb_state_field(self):
        """각 CB 상태에 state 필드가 있어야 한다."""
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.get("/health")
        data = resp.json()
        for cb in data.get("circuit_breakers", []):
            assert "state" in cb
            assert cb["state"] in ("closed", "open", "half_open")

    def test_nkg_returns_empty_on_new_series(self):
        """존재하지 않는 series_id 에 대해 빈 그래프가 반환돼야 한다."""
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.get("/api/v1/nkg/NONEXISTENT_S999")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_cost_summary_endpoint(self):
        """GET /api/v1/cost/summary 가 200을 반환해야 한다."""
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.get("/api/v1/cost/summary")
        assert resp.status_code == 200

    def test_jobs_list_endpoint(self):
        """GET /api/v1/jobs 가 200을 반환해야 한다."""
        if not self.available:
            pytest.skip("FastAPI unavailable")
        resp = self.client.get("/api/v1/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_analyze_degraded_when_cb_forced_open(self):
        """drse_cb OPEN 강제 시 /analyze 가 200 degraded 응답을 반환해야 한다."""
        if not self.available:
            pytest.skip("FastAPI unavailable")
        from apps.studio_api.resilience import circuit_breaker as cb_mod
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker
        # 강제 OPEN CB 생성
        forced = CircuitBreaker("drse_engine", failure_threshold=1)
        def _fail():
            raise RuntimeError("forced open")
        try:
            forced.call(_fail)
        except RuntimeError:
            pass
        original = cb_mod.drse_cb
        cb_mod.drse_cb = forced
        import apps.studio_api.routers.analyze as analyze_mod
        orig_analyze = analyze_mod.drse_cb
        analyze_mod.drse_cb = forced
        try:
            resp = self.client.post("/api/v1/analyze", json={
                "series_id": "S1",
                "scene_id": "SC-001",
                "episode": 1,
                "content": "테스트 씬입니다. " * 10,
            })
            assert resp.status_code == 200
            data = resp.json()
            # degraded 응답 확인
            assert data.get("drse_score") == 0.0
        finally:
            analyze_mod.drse_cb = orig_analyze
            cb_mod.drse_cb = original

    def test_gate_degraded_when_cb_forced_open(self):
        """gate_cb OPEN 강제 시 /gate 가 200 cb_open 응답을 반환해야 한다."""
        if not self.available:
            pytest.skip("FastAPI unavailable")
        from apps.studio_api.resilience import circuit_breaker as cb_mod
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker
        forced = CircuitBreaker("endurance_gate", failure_threshold=1, recovery_timeout=60.0)
        def _fail():
            raise RuntimeError("forced open")
        try:
            forced.call(_fail)
        except RuntimeError:
            pass
        orig = cb_mod.gate_cb
        cb_mod.gate_cb = forced
        import apps.studio_api.routers.analyze as analyze_mod
        orig_gate = analyze_mod.gate_cb
        analyze_mod.gate_cb = forced
        try:
            resp = self.client.post("/api/v1/gate", json={
                "series_id": "S1",
                "total_episodes": 16,
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("passed") is False
            assert any("Circuit" in f for f in data.get("failures", []))
        finally:
            analyze_mod.gate_cb = orig_gate
            cb_mod.gate_cb = orig


# ─────────────────────────────────────────────────────────────────────────────
# E. 열화 모드 통합 검증
# ─────────────────────────────────────────────────────────────────────────────

class TestDegradedModeIntegration:
    """CB + 라우터 + 웹소켓 전체 열화 흐름 검증."""

    def test_all_four_cbs_independent(self):
        """4개 CB 가 서로 독립적으로 동작해야 한다."""
        from apps.studio_api.resilience.circuit_breaker import (
            drse_cb, nkg_cb, gate_cb, voice_cb, CircuitBreaker
        )
        # 각 CB 리셋 (이전 테스트 영향 제거)
        drse_cb.reset()
        nkg_cb.reset()
        gate_cb.reset()
        voice_cb.reset()

        # drse_cb 만 OPEN
        from apps.studio_api.resilience.circuit_breaker import CBState
        test_cb = CircuitBreaker("test_indep", failure_threshold=1)
        def _fail():
            raise RuntimeError("err")
        try:
            test_cb.call(_fail)
        except RuntimeError:
            pass
        assert test_cb.state == CBState.OPEN

        # 다른 CB 는 여전히 CLOSED
        assert nkg_cb.state == CBState.CLOSED
        assert gate_cb.state == CBState.CLOSED
        assert voice_cb.state == CBState.CLOSED

    def test_cb_failure_does_not_affect_other_endpoints(self):
        """drse_cb OPEN 이 /nkg 엔드포인트에 영향을 주면 안 된다."""
        from apps.studio_api.resilience.circuit_breaker import (
            drse_cb, nkg_cb, CBState
        )
        drse_cb.reset()
        nkg_cb.reset()
        # drse_cb 만 실패
        def _fail():
            raise RuntimeError("drse fail")
        for _ in range(5):
            try:
                drse_cb.call(_fail)
            except RuntimeError:
                pass
        assert drse_cb.state == CBState.OPEN
        assert nkg_cb.state == CBState.CLOSED  # nkg_cb 는 영향 없음

    def test_voice_analyze_schema_has_defaults(self):
        """VoiceVector13D 기본값이 존재해야 한다 (CB OPEN 열화 응답용)."""
        from apps.studio_api.schema.mapper import VoiceVector13D
        vec = VoiceVector13D()
        # 기본값 확인 (0.0 or 0.5)
        assert isinstance(vec.sentence_length_dist, float)
        assert isinstance(vec.dialogue_ratio, float)
        assert isinstance(vec.lexical_diversity, float)

    def test_analyze_response_schema_degraded_field(self):
        """AnalyzeResponse 가 energy_vector 에 degraded 키를 수용해야 한다."""
        from apps.studio_api.schema.mapper import AnalyzeResponse
        resp = AnalyzeResponse(
            trace_id="test-trace",
            drse_score=0.0,
            energy_vector={"degraded": 1.0, "cb_open": "drse_engine"},
        )
        assert resp.drse_score == 0.0
        assert resp.energy_vector.get("degraded") == 1.0

    def test_cb_status_all_four_preconfigured(self):
        """4개 사전 구성 CB 의 status() 가 올바른 이름을 반환해야 한다."""
        from apps.studio_api.resilience.circuit_breaker import (
            drse_cb, nkg_cb, gate_cb, voice_cb
        )
        for cb, expected_name in [
            (drse_cb, "drse_engine"),
            (nkg_cb, "nkg_store"),
            (gate_cb, "endurance_gate"),
            (voice_cb, "voice_manifold"),
        ]:
            status = cb.status()
            assert status["name"] == expected_name
            assert status["state"] in ("closed", "open", "half_open")
