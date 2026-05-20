"""
tests/test_v580_async_performance.py
V580 AsyncDiscipline + PerformanceBaseline 검증 테스트 (25 TC)

그룹:
  A. AsyncDiscipline 기본 (TC01~05)
  B. G38 탐지 로직 (TC06~10)
  C. PerformanceBaseline 기본 (TC11~15)
  D. G39 벤치마크 개별 (TC16~20)
  E. 레지스트리 통합 (TC21~25)
"""
import ast
import json
import hashlib
import re
import time
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ─── 공통 임포트 ────────────────────────────────────────────────────────────────
from literary_system.gates.release_gate import (
    _gate_async_discipline_g38,
    _gate_performance_baseline_g39,
    GATES,
)
from literary_system.gates.gate_registry import GATE_REGISTRY, get_gate, validate_registry


# ════════════════════════════════════════════════════════════════════════════════
# 그룹 A: AsyncDiscipline 기본
# ════════════════════════════════════════════════════════════════════════════════

class TestAsyncDisciplineBasic:
    """TC01~05: G38 AsyncDiscipline 기본 동작"""

    def test_tc01_gate_returns_dict(self):
        """TC01: G38 반환값이 dict 타입"""
        result = _gate_async_discipline_g38()
        assert isinstance(result, dict)

    def test_tc02_gate_has_required_keys(self):
        """TC02: G38 반환값에 필수 키 포함"""
        result = _gate_async_discipline_g38()
        assert "pass" in result
        assert "violation_count" in result
        assert "details" in result

    def test_tc03_gate_passes(self):
        """TC03: G38 현재 코드베이스에서 PASS"""
        result = _gate_async_discipline_g38()
        assert result["pass"] is True

    def test_tc04_violation_count_zero(self):
        """TC04: asyncio.get_event_loop() 위반 0건"""
        result = _gate_async_discipline_g38()
        assert result["violation_count"] == 0

    def test_tc05_details_contains_pass_message(self):
        """TC05: details 메시지에 PASS 문구 포함"""
        result = _gate_async_discipline_g38()
        assert "PASS" in result["details"]


# ════════════════════════════════════════════════════════════════════════════════
# 그룹 B: G38 탐지 로직 — AST 기반 정확성
# ════════════════════════════════════════════════════════════════════════════════

class TestAsyncDisciplineDetection:
    """TC06~10: AST 기반 get_event_loop 탐지 정밀도"""

    def _has_get_event_loop_call(self, source: str) -> bool:
        """AST로 asyncio.get_event_loop() 실제 호출 존재 여부"""
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "get_event_loop"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "asyncio"):
                return True
        return False

    def test_tc06_ast_detects_direct_call(self):
        """TC06: asyncio.get_event_loop() 직접 호출 탐지"""
        src = "import asyncio\nloop = asyncio.get_event_loop()\n"
        assert self._has_get_event_loop_call(src) is True

    def test_tc07_ast_ignores_string_literal(self):
        """TC07: 문자열 내 'asyncio.get_event_loop()' 무시"""
        src = 'x = "asyncio.get_event_loop()"\n'
        assert self._has_get_event_loop_call(src) is False

    def test_tc08_ast_ignores_comment(self):
        """TC08: 주석 내 asyncio.get_event_loop() 무시"""
        src = "# asyncio.get_event_loop() deprecated\nx = 1\n"
        assert self._has_get_event_loop_call(src) is False

    def test_tc09_ast_allows_get_running_loop(self):
        """TC09: asyncio.get_running_loop() 는 위반 아님"""
        src = "import asyncio\nloop = asyncio.get_running_loop()\n"
        assert self._has_get_event_loop_call(src) is False

    def test_tc10_ast_allows_asyncio_run(self):
        """TC10: asyncio.run() 은 위반 아님"""
        src = "import asyncio\nasyncio.run(main())\n"
        assert self._has_get_event_loop_call(src) is False


# ════════════════════════════════════════════════════════════════════════════════
# 그룹 C: PerformanceBaseline 기본
# ════════════════════════════════════════════════════════════════════════════════

class TestPerformanceBaselineBasic:
    """TC11~15: G39 PerformanceBaseline 기본 동작"""

    def test_tc11_gate_returns_dict(self):
        """TC11: G39 반환값이 dict 타입"""
        result = _gate_performance_baseline_g39()
        assert isinstance(result, dict)

    def test_tc12_gate_has_required_keys(self):
        """TC12: G39 반환값에 필수 키 포함"""
        result = _gate_performance_baseline_g39()
        assert "pass" in result
        assert "benchmarks" in result
        assert "regression_count" in result
        assert "details" in result

    def test_tc13_gate_passes(self):
        """TC13: G39 현재 환경에서 PASS"""
        result = _gate_performance_baseline_g39()
        assert result["pass"] is True

    def test_tc14_regression_count_zero(self):
        """TC14: 성능 회귀 0건"""
        result = _gate_performance_baseline_g39()
        assert result["regression_count"] == 0

    def test_tc15_benchmarks_list_has_three_entries(self):
        """TC15: 벤치마크 항목 정확히 3개"""
        result = _gate_performance_baseline_g39()
        assert len(result["benchmarks"]) == 3


# ════════════════════════════════════════════════════════════════════════════════
# 그룹 D: G39 벤치마크 개별 검증
# ════════════════════════════════════════════════════════════════════════════════

class TestPerformanceBenchmarks:
    """TC16~20: 벤치마크 항목별 세부 검증"""

    @pytest.fixture(scope="class")
    def bench_result(self):
        return _gate_performance_baseline_g39()

    def test_tc16_json_benchmark_present(self, bench_result):
        """TC16: json_roundtrip_1000 벤치마크 존재"""
        names = [b["name"] for b in bench_result["benchmarks"]]
        assert "json_roundtrip_1000" in names

    def test_tc17_sha256_benchmark_present(self, bench_result):
        """TC17: sha256_10000 벤치마크 존재"""
        names = [b["name"] for b in bench_result["benchmarks"]]
        assert "sha256_10000" in names

    def test_tc18_regex_benchmark_present(self, bench_result):
        """TC18: regex_5000 벤치마크 존재"""
        names = [b["name"] for b in bench_result["benchmarks"]]
        assert "regex_5000" in names

    def test_tc19_each_benchmark_has_timing(self, bench_result):
        """TC19: 각 벤치마크에 elapsed_ms, limit_ms 포함"""
        for b in bench_result["benchmarks"]:
            assert "elapsed_ms" in b
            assert "limit_ms" in b
            assert b["elapsed_ms"] >= 0
            assert b["limit_ms"] > 0

    def test_tc20_each_benchmark_passes(self, bench_result):
        """TC20: 각 벤치마크 개별 PASS"""
        for b in bench_result["benchmarks"]:
            assert b["pass"] is True, (
                f"{b['name']}: {b['elapsed_ms']}ms > {b['limit_ms']}ms"
            )


# ════════════════════════════════════════════════════════════════════════════════
# 그룹 E: 레지스트리 통합 검증
# ════════════════════════════════════════════════════════════════════════════════

class TestRegistryIntegration:
    """TC21~25: Gate Registry G38/G39 통합 검증"""

    @pytest.fixture(scope="class")
    def registry(self):
        return GATE_REGISTRY

    def test_tc21_g38_in_gates_list(self):
        """TC21: GATES 리스트에 async_discipline_g38 포함"""
        ids = [g[0] for g in GATES]
        assert "async_discipline_g38" in ids

    def test_tc22_g39_in_gates_list(self):
        """TC22: GATES 리스트에 performance_baseline_g39 포함"""
        ids = [g[0] for g in GATES]
        assert "performance_baseline_g39" in ids

    def test_tc23_g38_registry_metadata(self, registry):
        """TC23: registry에서 G38 메타데이터 조회 가능"""
        entry = registry.get("async_discipline_g38")
        assert entry is not None
        assert entry.adr_ref == "ADR-036"
        assert entry.version_added == "V580"
        assert entry.layer == "L1"

    def test_tc24_g39_registry_metadata(self, registry):
        """TC24: registry에서 G39 메타데이터 조회 가능"""
        entry = registry.get("performance_baseline_g39")
        assert entry is not None
        assert entry.adr_ref == "ADR-039"
        assert entry.version_added == "V580"
        assert entry.layer == "L1"

    def test_tc25_total_gates_39(self):
        """TC25: 전체 Gates 수 40개 (G1~G40 포함, V582 sql_real_adapter G41 추가)"""
        assert len(GATES) == 40  # V582: G41 추가로 40개
