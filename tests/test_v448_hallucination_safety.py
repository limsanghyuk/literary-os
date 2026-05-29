"""
V448 테스트: HallucinationDetector + SafetyGate
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from literary_system.quality.hallucination_safety import (
    HallucinationDetector,
    HallucinationFlag,
    HallucinationReport,
    SafetyGate,
    SafetyViolation,
    SafetyResult,
    _default_hallucination_check,
    _default_safety_check,
)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def clean_text():
    return "오늘 날씨가 맑고 바람이 없었다. 주인공은 창문 밖을 바라보았다."

@pytest.fixture
def hallucination_text():
    return "연구에 따르면 이 약은 100% 효과적이다. 무조건 맞다고 할 수 있다."

@pytest.fixture
def safety_text_pii():
    return "고객 연락처: 010-1234-5678"

@pytest.fixture
def safety_text_violence():
    return "이 문서에는 살인 방법에 대한 내용이 포함되어 있다."

@pytest.fixture
def detector():
    return HallucinationDetector()

@pytest.fixture
def gate():
    return SafetyGate()


# ──────────────────────────────────────────────
# TestDefaultHallucinationCheck
# ──────────────────────────────────────────────

class TestDefaultHallucinationCheck:
    def test_clean_text_returns_empty(self, clean_text):
        flags = _default_hallucination_check(clean_text)
        assert flags == []

    def test_false_authority_detected(self):
        text = "연구에 따르면 이것이 사실이다."
        flags = _default_hallucination_check(text)
        assert any(label == "false_authority" for label, _, _, _ in flags)

    def test_absolute_claim_detected(self):
        text = "무조건 맞다."
        flags = _default_hallucination_check(text)
        assert len(flags) >= 1

    def test_returns_4_tuple(self):
        text = "연구에 따르면 효과적이다."
        flags = _default_hallucination_check(text)
        if flags:
            pattern, matched, position, severity = flags[0]
            assert isinstance(pattern, str)
            assert isinstance(matched, str)
            assert isinstance(position, int)
            assert severity in ("low", "medium", "high")

    def test_multiple_patterns_detected(self):
        text = "연구에 따르면 무조건 맞다."
        flags = _default_hallucination_check(text)
        # May detect both false_authority and absolute_claim
        assert isinstance(flags, list)


# ──────────────────────────────────────────────
# TestHallucinationDetectorInit
# ──────────────────────────────────────────────

class TestHallucinationDetectorInit:
    def test_default_init(self):
        det = HallucinationDetector()
        assert det.min_severity == "low"
        assert det.check_fn is not None

    def test_custom_check_fn(self):
        custom_fn = lambda text: [("test_pattern", "test", 0, "high")]
        det = HallucinationDetector(check_fn=custom_fn)
        assert det.check_fn is custom_fn

    def test_min_severity_high(self):
        det = HallucinationDetector(min_severity="high")
        assert det.min_severity == "high"

    def test_initial_reports_empty(self):
        det = HallucinationDetector()
        assert det._reports == []

    def test_checked_by_rule_based(self, detector):
        report = detector.detect("t001", "무해한 텍스트")
        assert report.checked_by == "rule_based"

    def test_checked_by_custom(self):
        custom_fn = lambda text: []
        det = HallucinationDetector(check_fn=custom_fn)
        report = det.detect("t001", "텍스트")
        assert report.checked_by == "custom"


# ──────────────────────────────────────────────
# TestHallucinationDetect
# ──────────────────────────────────────────────

class TestHallucinationDetect:
    def test_clean_text_not_flagged(self, detector, clean_text):
        report = detector.detect("t001", clean_text)
        assert not report.flagged
        assert report.severity == "none"

    def test_hallucination_text_flagged(self, detector, hallucination_text):
        report = detector.detect("t002", hallucination_text)
        assert report.flagged
        assert report.severity in ("medium", "high")

    def test_report_has_trace_id(self, detector, clean_text):
        report = detector.detect("my_trace", clean_text)
        assert report.trace_id == "my_trace"

    def test_flags_are_immutable(self, detector, hallucination_text):
        report = detector.detect("t003", hallucination_text)
        for flag in report.flags:
            assert isinstance(flag, HallucinationFlag)
            # frozen=True means attributes are read-only
            with pytest.raises((AttributeError, TypeError)):
                flag.severity = "low"

    def test_to_dict_structure(self, detector, hallucination_text):
        report = detector.detect("t004", hallucination_text)
        d = report.to_dict()
        assert "trace_id" in d
        assert "flagged" in d
        assert "severity" in d
        assert "flag_count" in d
        assert "flags" in d
        assert "checked_by" in d

    def test_min_severity_filter(self):
        det = HallucinationDetector(min_severity="high")
        custom_fn = lambda text: [
            ("p1", "x", 0, "low"),
            ("p2", "y", 1, "high"),
        ]
        det.check_fn = custom_fn
        report = det.detect("t005", "텍스트")
        # low severity should be filtered
        flag_severities = [f.severity for f in report.flags]
        assert "low" not in flag_severities

    def test_report_stored_in_internal_list(self, detector, clean_text):
        before = len(detector._reports)
        detector.detect("t006", clean_text)
        assert len(detector._reports) == before + 1


# ──────────────────────────────────────────────
# TestHallucinationDetectBatch
# ──────────────────────────────────────────────

class TestHallucinationDetectBatch:
    def _make_records(self, texts):
        """간단한 mock TraceRecord 목록 생성."""
        class MockRecord:
            def __init__(self, tid, txt):
                self.trace_id = tid
                self.render_output = {"scene": txt}
        return [MockRecord(f"t{i}", t) for i, t in enumerate(texts)]

    def test_batch_returns_list(self, detector):
        records = self._make_records(["무해한 텍스트", "또 다른 텍스트"])
        reports = detector.detect_batch(records)
        assert isinstance(reports, list)
        assert len(reports) == 2

    def test_batch_each_is_report(self, detector):
        records = self._make_records(["텍스트"])
        reports = detector.detect_batch(records)
        assert isinstance(reports[0], HallucinationReport)

    def test_batch_flagged_reports(self, detector, hallucination_text):
        records = self._make_records(["무해한 텍스트", hallucination_text])
        detector.detect_batch(records)
        flagged = detector.flagged_reports()
        assert len(flagged) >= 1


# ──────────────────────────────────────────────
# TestHallucinationStats
# ──────────────────────────────────────────────

class TestHallucinationStats:
    def test_stats_keys(self, detector, clean_text):
        detector.detect("t001", clean_text)
        s = detector.stats()
        assert "total_checked" in s
        assert "flagged_count" in s
        assert "pass_rate" in s
        assert "severity_dist" in s

    def test_stats_zero_on_empty(self):
        det = HallucinationDetector()
        s = det.stats()
        assert s["total_checked"] == 0
        assert s["pass_rate"] == 1.0

    def test_stats_counts(self, hallucination_text):
        det = HallucinationDetector()
        det.detect("t1", "무해한 텍스트")
        det.detect("t2", hallucination_text)
        s = det.stats()
        assert s["total_checked"] == 2
        assert s["flagged_count"] >= 1


# ──────────────────────────────────────────────
# TestDefaultSafetyCheck
# ──────────────────────────────────────────────

class TestDefaultSafetyCheck:
    def test_clean_text_empty(self, clean_text):
        results = _default_safety_check(clean_text)
        assert results == []

    def test_pii_detected(self, safety_text_pii):
        results = _default_safety_check(safety_text_pii)
        assert any(cat == "pii" for cat, _, _ in results)

    def test_violence_detected(self, safety_text_violence):
        results = _default_safety_check(safety_text_violence)
        assert any(cat == "violence" for cat, _, _ in results)

    def test_returns_3_tuple(self, safety_text_pii):
        results = _default_safety_check(safety_text_pii)
        if results:
            cat, matched, pos = results[0]
            assert isinstance(cat, str)
            assert isinstance(matched, str)
            assert isinstance(pos, int)


# ──────────────────────────────────────────────
# TestSafetyGateInit
# ──────────────────────────────────────────────

class TestSafetyGateInit:
    def test_default_init(self):
        gate = SafetyGate()
        assert gate.gate_fn is not None
        assert "pii" in gate.blocked_categories

    def test_custom_gate_fn(self):
        custom_fn = lambda text: []
        gate = SafetyGate(gate_fn=custom_fn)
        assert gate.gate_fn is custom_fn

    def test_custom_blocked_categories(self):
        gate = SafetyGate(blocked_categories={"custom_cat"})
        assert "custom_cat" in gate.blocked_categories

    def test_initial_results_empty(self):
        gate = SafetyGate()
        assert gate._results == []


# ──────────────────────────────────────────────
# TestSafetyGateCheck
# ──────────────────────────────────────────────

class TestSafetyGateCheck:
    def test_clean_text_passes(self, gate, clean_text):
        result = gate.check("t001", clean_text)
        assert not result.blocked
        assert result.action == "pass"

    def test_pii_text_blocked(self, gate, safety_text_pii):
        result = gate.check("t002", safety_text_pii)
        assert result.blocked
        assert result.action == "block"

    def test_violence_text_blocked(self, gate, safety_text_violence):
        result = gate.check("t003", safety_text_violence)
        assert result.blocked
        assert result.action == "block"

    def test_result_has_trace_id(self, gate, clean_text):
        result = gate.check("my_trace", clean_text)
        assert result.trace_id == "my_trace"

    def test_violations_are_immutable(self, gate, safety_text_pii):
        result = gate.check("t004", safety_text_pii)
        for v in result.violations:
            assert isinstance(v, SafetyViolation)
            with pytest.raises((AttributeError, TypeError)):
                v.category = "changed"

    def test_to_dict_structure(self, gate, safety_text_pii):
        result = gate.check("t005", safety_text_pii)
        d = result.to_dict()
        assert "trace_id" in d
        assert "blocked" in d
        assert "action" in d
        assert "violation_count" in d
        assert "violations" in d
        assert "checked_by" in d

    def test_custom_gate_fn(self):
        custom_fn = lambda text: [("custom", "match", 0)]
        gate = SafetyGate(
            gate_fn=custom_fn,
            blocked_categories={"custom"},
        )
        result = gate.check("t006", "어떤 텍스트")
        assert result.blocked
        assert result.checked_by == "custom"

    def test_result_stored(self, gate, clean_text):
        before = len(gate._results)
        gate.check("t007", clean_text)
        assert len(gate._results) == before + 1


# ──────────────────────────────────────────────
# TestSafetyGateBatch
# ──────────────────────────────────────────────

class TestSafetyGateBatch:
    def _make_records(self, texts):
        class MockRecord:
            def __init__(self, tid, txt):
                self.trace_id = tid
                self.render_output = {"scene": txt}
        return [MockRecord(f"t{i}", t) for i, t in enumerate(texts)]

    def test_batch_returns_list(self, gate):
        records = self._make_records(["무해한 텍스트", "다른 텍스트"])
        results = gate.check_batch(records)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_batch_blocked_results(self, gate, safety_text_pii):
        records = self._make_records(["무해한 텍스트", safety_text_pii])
        gate.check_batch(records)
        blocked = gate.blocked_results()
        assert len(blocked) >= 1


# ──────────────────────────────────────────────
# TestSafetyGateStats
# ──────────────────────────────────────────────

class TestSafetyGateStats:
    def test_stats_keys(self, gate, clean_text):
        gate.check("t001", clean_text)
        s = gate.stats()
        assert "total_checked" in s
        assert "blocked_count" in s
        assert "warned_count" in s
        assert "pass_count" in s
        assert "block_rate" in s

    def test_stats_zero_on_empty(self):
        g = SafetyGate()
        s = g.stats()
        assert s["total_checked"] == 0
        assert s["block_rate"] == 0.0

    def test_stats_counts(self, safety_text_pii):
        g = SafetyGate()
        g.check("t1", "무해한 텍스트")
        g.check("t2", safety_text_pii)
        s = g.stats()
        assert s["total_checked"] == 2
        assert s["blocked_count"] >= 1
        assert s["pass_count"] >= 1
