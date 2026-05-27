"""V659 ReaderFeedbackCollector + Gate G68 테스트 (ADR-119) — 33 TC."""
from __future__ import annotations

import pytest

from literary_system.feedback import (
    ConsentError,
    ConsentLevel,
    FeedbackCollectionError,
    FeedbackType,
    PIIPurgePolicy,
    ReaderFeedbackCollector,
)
from literary_system.gates.feedback_collection_gate import run_g68


@pytest.fixture
def col():
    return ReaderFeedbackCollector(required_consent=ConsentLevel.ANONYMOUS)


def _fill(col, n=10):
    for i in range(n):
        col.collect(f"r_{i}", f"씬 {i}번 피드백입니다. 감동적이었습니다.", 4.0 + (i % 10) * 0.1)


# ── TC-01~06: 기본 수집 ───────────────────────────────────────────────────

class TestCollect:
    def test_collect_returns_anonymized(self, col):                        # TC-01
        fb = col.collect("reader_1", "좋은 씬이었습니다.", 4.5)
        assert fb.hashed_reader_id != "reader_1"

    def test_reader_id_hashed(self, col):                                  # TC-02
        fb = col.collect("reader_1", "테스트 피드백입니다.", 3.0)
        assert len(fb.hashed_reader_id) == 16

    def test_score_stored(self, col):                                      # TC-03
        fb = col.collect("r", "좋은 장면이었습니다.", 4.2)
        assert fb.score == 4.2

    def test_feedback_type_stored(self, col):                              # TC-04
        fb = col.collect("r", "감동적인 씬이었습니다.", 5.0, FeedbackType.EMOTIONAL_IMPACT)
        assert fb.feedback_type == FeedbackType.EMOTIONAL_IMPACT

    def test_count_increments(self, col):                                  # TC-05
        col.collect("r1", "피드백입니다.", 3.5)
        col.collect("r2", "또 다른 피드백입니다.", 4.0)
        assert col.count() == 2

    def test_pii_removed_flag(self, col):                                  # TC-06
        fb = col.collect("r", "좋은 장면입니다.", 4.0)
        assert fb.pii_removed is True


# ── TC-07~12: PII 마스킹 ──────────────────────────────────────────────────

class TestPIIMasking:
    def test_email_masked(self, col):                                      # TC-07
        fb = col.collect("r", "이메일은 test@example.com 입니다.", 3.0)
        assert "@" not in fb.text
        assert "[EMAIL]" in fb.text

    def test_phone_masked(self, col):                                      # TC-08
        fb = col.collect("r", "전화는 010-1234-5678 입니다.", 3.0)
        assert "010" not in fb.text
        assert "[PHONE]" in fb.text

    def test_name_title_masked(self, col):                                 # TC-09
        fb = col.collect("r", "김철수씨가 잘 하셨습니다.", 4.0)
        assert "[NAME]" in fb.text

    def test_clean_text_unchanged(self, col):                              # TC-10
        original = "씬의 감동이 대단했습니다."
        fb = col.collect("r", original, 4.0)
        assert fb.text == original

    def test_multiple_pii_all_masked(self, col):                           # TC-11
        fb = col.collect(
            "r",
            "연락처는 hong@test.kr 또는 010-9999-1111 입니다.",
            3.0,
        )
        assert "@" not in fb.text
        assert "010" not in fb.text

    def test_rrno_masked(self, col):                                       # TC-12
        fb = col.collect("r", "주민번호는 900101-1234567 입니다.", 3.0)
        assert "900101" not in fb.text


# ── TC-13~17: 동의 검증 ────────────────────────────────────────────────────

class TestConsent:
    def test_no_consent_raises(self, col):                                 # TC-13
        with pytest.raises(ConsentError):
            col.collect("r", "동의 없는 피드백입니다.", 3.0, consent=ConsentLevel.NONE)

    def test_anonymous_consent_accepted(self, col):                        # TC-14
        fb = col.collect("r", "익명 피드백입니다.", 4.0, consent=ConsentLevel.ANONYMOUS)
        assert fb is not None

    def test_higher_consent_accepted(self, col):                           # TC-15
        fb = col.collect("r", "가명 피드백입니다.", 4.0, consent=ConsentLevel.PSEUDONYMOUS)
        assert fb is not None

    def test_blocked_count_increments(self, col):                          # TC-16
        try:
            col.collect("r", "차단될 피드백입니다.", 3.0, consent=ConsentLevel.NONE)
        except ConsentError:
            pass
        report = col.gate_report()
        assert report["consent_blocked_count"] >= 1

    def test_score_out_of_range_raises(self, col):                         # TC-17
        with pytest.raises(FeedbackCollectionError):
            col.collect("r", "범위 초과 점수 피드백입니다.", 6.0)


# ── TC-18~22: 조회 ────────────────────────────────────────────────────────

class TestQuery:
    def test_get_feedback_all(self, col):                                  # TC-18
        _fill(col, 5)
        items = col.get_feedback()
        assert len(items) == 5

    def test_get_feedback_by_type(self, col):                              # TC-19
        col.collect("r1", "감동적입니다.", 4.0, FeedbackType.EMOTIONAL_IMPACT)
        col.collect("r2", "씬이 좋습니다.", 4.5, FeedbackType.SCENE_QUALITY)
        items = col.get_feedback(feedback_type=FeedbackType.EMOTIONAL_IMPACT)
        assert all(f.feedback_type == FeedbackType.EMOTIONAL_IMPACT for f in items)

    def test_get_feedback_min_score(self, col):                            # TC-20
        _fill(col, 5)
        col.collect("r_high", "최고의 피드백입니다.", 5.0)
        high = col.get_feedback(min_score=5.0)
        assert all(f.score >= 5.0 for f in high)

    def test_average_score(self, col):                                     # TC-21
        col.collect("r1", "좋습니다.", 3.0)
        col.collect("r2", "매우 좋습니다.", 5.0)
        avg = col.average_score()
        assert abs(avg - 4.0) < 0.01

    def test_average_score_empty(self, col):                               # TC-22
        assert col.average_score() == 0.0


# ── TC-23~27: 파기 ────────────────────────────────────────────────────────

class TestPurge:
    def test_purge_expired_zero(self, col):                                # TC-23
        _fill(col, 3)
        purged = col.purge_expired()
        assert purged == 0

    def test_purge_policy_attrs(self):                                     # TC-24
        policy = PIIPurgePolicy(retention_days=7)
        assert policy.retention_days == 7
        assert policy.auto_anonymize is True

    def test_purge_expired_removes_old(self):                              # TC-25
        import time as _time
        col = ReaderFeedbackCollector(PIIPurgePolicy(retention_days=0))
        col.collect("r", "오래된 피드백입니다.", 3.0)
        _time.sleep(0.01)
        purged = col.purge_expired()
        assert purged >= 1
        assert col.count() == 0

    def test_purge_keeps_recent(self, col):                                # TC-26
        _fill(col, 5)
        purged = col.purge_expired()
        assert purged == 0
        assert col.count() == 5

    def test_feedback_id_unique(self, col):                                # TC-27
        fb1 = col.collect("r1", "첫 번째 피드백입니다.", 3.0)
        fb2 = col.collect("r2", "두 번째 피드백입니다.", 4.0)
        assert fb1.feedback_id != fb2.feedback_id


# ── TC-28~33: Gate G68 ────────────────────────────────────────────────────

class TestGateG68:
    def test_gate_pass_with_10_feedbacks(self):                            # TC-28
        result = run_g68()
        assert result["passed"] is True

    def test_gate_pii_residual_zero(self):                                 # TC-29
        result = run_g68()
        assert result["pii_residual"] == 0

    def test_gate_feedback_count_ge_10(self):                              # TC-30
        result = run_g68()
        assert result["feedback_count"] >= 10

    def test_gate_pii_clean_rate_one(self):                                # TC-31
        result = run_g68()
        assert result["pii_clean_rate"] == 1.0

    def test_gate_fail_too_few(self):                                      # TC-32
        empty_col = ReaderFeedbackCollector()
        result = run_g68(empty_col)
        assert result["passed"] is False

    def test_gate_summary_string(self):                                    # TC-33
        result = run_g68()
        assert "G68" in result["summary"]
        assert "PASS" in result["summary"]
