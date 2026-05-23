"""
tests/test_v615_performance_slo_gate.py
Gate G60 — PerformanceSLOGate v1.0 단위 테스트 (V615, ADR-075)

20 Test Cases:
  TestConstants          (3 TC)  — SLO 임계값 상수 검증
  TestCheckpointResult   (3 TC)  — CheckpointResult 데이터 클래스
  TestG60GateResult      (5 TC)  — G60GateResult 데이터 클래스
  TestGateCheckpoints    (7 TC)  — 개별 체크포인트 검증
  TestRunG60Gate         (2 TC)  — run_g60_gate() 통합 실행
"""

import pytest
from literary_system.gates.performance_slo_gate import (
    CACHE_HIT_SLO,
    GPU_SLO_MB,
    P95_SLO_MS,
    CheckpointResult,
    G60GateResult,
    PerformanceSLOGate,
    run_g60_gate,
)


# ─────────────────────────────────────────────────────────────────────────────
# TestConstants
# ─────────────────────────────────────────────────────────────────────────────

class TestConstants:
    """V615-C1~C3: SLO 임계값 상수 검증"""

    def test_p95_slo_ms(self):
        """C1: P95 SLO ≤ 1500ms"""
        assert P95_SLO_MS == 1500.0

    def test_gpu_slo_mb(self):
        """C2: GPU SLO ≤ 8192MB"""
        assert GPU_SLO_MB == 8192.0

    def test_cache_hit_slo(self):
        """C3: CacheHit SLO ≥ 60%"""
        assert CACHE_HIT_SLO == 0.60


# ─────────────────────────────────────────────────────────────────────────────
# TestCheckpointResult
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckpointResult:
    """V615-R1~R3: CheckpointResult 데이터 클래스"""

    def test_passed_checkpoint(self):
        """R1: 통과 체크포인트 생성"""
        cp = CheckpointResult(name="CP-1:test", passed=True, detail="OK", elapsed_ms=1.5)
        assert cp.name == "CP-1:test"
        assert cp.passed is True
        assert cp.elapsed_ms == 1.5

    def test_failed_checkpoint(self):
        """R2: 실패 체크포인트 생성"""
        cp = CheckpointResult(name="CP-2:test", passed=False, detail="FAIL")
        assert cp.passed is False

    def test_to_dict(self):
        """R3: to_dict() 키 검증"""
        cp = CheckpointResult(name="CP-X", passed=True, detail="detail", elapsed_ms=2.0)
        d = cp.to_dict()
        assert set(d.keys()) == {"name", "passed", "detail", "elapsed_ms"}
        assert d["name"] == "CP-X"
        assert d["passed"] is True


# ─────────────────────────────────────────────────────────────────────────────
# TestG60GateResult
# ─────────────────────────────────────────────────────────────────────────────

class TestG60GateResult:
    """V615-G1~G5: G60GateResult 데이터 클래스"""

    def test_default_values(self):
        """G1: 기본값 검증"""
        r = G60GateResult()
        assert r.gate == "G60"
        assert r.total == 10
        assert r.gate_pass is False
        assert r.passed_count == 0

    def test_to_dict_keys(self):
        """G2: to_dict() 필수 키"""
        r = G60GateResult()
        d = r.to_dict()
        required = {"gate", "gate_name", "pass", "passed_count", "total",
                    "checkpoints", "elapsed_ms", "error"}
        assert required <= set(d.keys())

    def test_gate_name(self):
        """G3: gate_name 값"""
        r = G60GateResult()
        assert "PerformanceSLOGate" in r.gate_name

    def test_pass_field_in_dict(self):
        """G4: to_dict()['pass'] 필드"""
        r = G60GateResult(gate_pass=True, passed_count=10)
        d = r.to_dict()
        assert d["pass"] is True
        assert d["passed_count"] == 10

    def test_checkpoints_list(self):
        """G5: checkpoints 리스트 직렬화"""
        cp = CheckpointResult(name="CP-1", passed=True, detail="ok")
        r = G60GateResult(checkpoints=[cp], passed_count=1)
        d = r.to_dict()
        assert len(d["checkpoints"]) == 1
        assert d["checkpoints"][0]["name"] == "CP-1"


# ─────────────────────────────────────────────────────────────────────────────
# TestGateCheckpoints
# ─────────────────────────────────────────────────────────────────────────────

class TestGateCheckpoints:
    """V615-P1~P7: 개별 체크포인트 단위 검증"""

    @pytest.fixture
    def gate(self):
        return PerformanceSLOGate()

    def test_cp1_import(self, gate):
        """P1: CP-1 모듈 임포트"""
        cp = gate._run_cp("CP-1:module_import", gate._cp1_import)
        assert cp.passed, f"CP-1 실패: {cp.detail}"

    def test_cp2_kv_cache(self, gate):
        """P2: CP-2 KVCache LRU"""
        cp = gate._run_cp("CP-2:kv_cache_lru", gate._cp2_kv_cache)
        assert cp.passed, f"CP-2 실패: {cp.detail}"

    def test_cp3_quantization(self, gate):
        """P3: CP-3 INT8/INT4 양자화"""
        cp = gate._run_cp("CP-3:quantization_int8_int4", gate._cp3_quantization)
        assert cp.passed, f"CP-3 실패: {cp.detail}"

    def test_cp4_latency_profiler(self, gate):
        """P4: CP-4 P95 계산"""
        cp = gate._run_cp("CP-4:latency_profiler", gate._cp4_latency_profiler)
        assert cp.passed, f"CP-4 실패: {cp.detail}"
        assert "P95=" in cp.detail

    def test_cp5_gpu_monitor(self, gate):
        """P5: CP-5 GPU 모니터 키"""
        cp = gate._run_cp("CP-5:gpu_monitor", gate._cp5_gpu_monitor)
        assert cp.passed, f"CP-5 실패: {cp.detail}"

    def test_cp6_slo_report_structure(self, gate):
        """P6: CP-6 PerfSLOReport 구조"""
        cp = gate._run_cp("CP-6:slo_report_structure", gate._cp6_slo_report_structure)
        assert cp.passed, f"CP-6 실패: {cp.detail}"

    def test_cp10_cache_hit_threshold(self, gate):
        """P7: CP-10 CacheHit SLO 임계값"""
        cp = gate._run_cp("CP-10:cache_hit_threshold", gate._cp10_cache_hit_threshold)
        assert cp.passed, f"CP-10 실패: {cp.detail}"


# ─────────────────────────────────────────────────────────────────────────────
# TestRunG60Gate
# ─────────────────────────────────────────────────────────────────────────────

class TestRunG60Gate:
    """V615-I1~I2: run_g60_gate() 통합 실행"""

    def test_run_g60_gate_returns_dict(self):
        """I1: run_g60_gate() 반환 타입"""
        result = run_g60_gate()
        assert isinstance(result, dict)
        assert "pass" in result
        assert "checkpoints" in result
        assert result["gate"] == "G60"

    def test_run_g60_gate_all_pass(self):
        """I2: Gate G60 10/10 ALL PASS"""
        result = run_g60_gate()
        failed = [cp for cp in result["checkpoints"] if not cp["passed"]]
        assert result["pass"] is True, \
            f"Gate G60 FAIL — 실패 CP: {[cp['name'] + ': ' + cp['detail'] for cp in failed]}"
        assert result["passed_count"] == 10
        assert result["total"] == 10
