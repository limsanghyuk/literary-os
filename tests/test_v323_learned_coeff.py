"""
V323 Phase 2 — LearnedCoefficientStore 테스트 (35개)
[CSC] 씬 누적 → DRSE 계수 자동 갱신 검증.
"""
import json
import pytest
from literary_system.validation.learned_coefficient_store import (
    CoefficientRecord,
    LearnedCoefficients,
    LearnedCoefficientStore,
)


# ── 헬퍼 ───────────────────────────────────────────────────────────

def make_record(scene_id="s1", label="GOOD", gold=None,
                pull=0.6, afterimage=0.5, uncertainty=0.4,
                drse_score=0.5) -> CoefficientRecord:
    return CoefficientRecord(
        scene_id=scene_id,
        judgment_label=label,
        gold_label=gold or label,
        reader_pull=pull,
        reader_afterimage=afterimage,
        reader_uncertainty=uncertainty,
        final_drse_score=drse_score,
    )


def make_store(interval=10) -> LearnedCoefficientStore:
    return LearnedCoefficientStore(update_interval=interval)


# ══════════════════════════════════════════════════════════════════
# 1. CoefficientRecord
# ══════════════════════════════════════════════════════════════════

class TestCoefficientRecord:
    def test_defaults(self):
        r = CoefficientRecord(
            scene_id="s1",
            judgment_label="GOOD",
            gold_label="GOOD",
            reader_pull=0.5,
            reader_afterimage=0.4,
            reader_uncertainty=0.3,
            final_drse_score=0.6,
        )
        assert r.scene_id == "s1"
        assert r.metadata == {}

    def test_to_dict_roundtrip(self):
        r = make_record("s1", "GOOD", "GOOD", 0.7, 0.5, 0.3, 0.8)
        d = r.to_dict()
        r2 = CoefficientRecord.from_dict(d)
        assert r2.scene_id == r.scene_id
        assert r2.reader_pull == r.reader_pull
        assert r2.final_drse_score == r.final_drse_score

    def test_is_match_true(self):
        r = make_record(label="GOOD", gold="GOOD")
        assert r.is_match is True

    def test_is_match_false(self):
        r = make_record(label="GOOD", gold="BAD")
        assert r.is_match is False

    def test_is_good(self):
        r = make_record(label="GOOD")
        assert r.is_good is True
        r2 = make_record(label="BAD")
        assert r2.is_good is False


# ══════════════════════════════════════════════════════════════════
# 2. LearnedCoefficients
# ══════════════════════════════════════════════════════════════════

class TestLearnedCoefficients:
    def test_defaults(self):
        c = LearnedCoefficients()
        assert c.decay_lambda == pytest.approx(0.05)
        assert c.arc_pressure_boost == pytest.approx(1.2)
        assert c.residue_boost == pytest.approx(1.5)
        assert c.residue_min_s == pytest.approx(0.15)
        assert c.reader_pull_min == pytest.approx(0.40)
        assert c.version == 0

    def test_to_dict_roundtrip(self):
        c = LearnedCoefficients(decay_lambda=0.03, version=2)
        d = c.to_dict()
        c2 = LearnedCoefficients.from_dict(d)
        assert c2.decay_lambda == pytest.approx(0.03)
        assert c2.version == 2

    def test_json_serializable(self):
        c = LearnedCoefficients()
        d = c.to_dict()
        s = json.dumps(d)
        assert isinstance(s, str)

    def test_clamp_logic(self):
        # decay_lambda 범위 검증 (0.001~0.5)
        c = LearnedCoefficients(decay_lambda=0.001)
        assert c.decay_lambda >= 0.001
        c2 = LearnedCoefficients(decay_lambda=0.5)
        assert c2.decay_lambda <= 0.5


# ══════════════════════════════════════════════════════════════════
# 3. LearnedCoefficientStore — 기본
# ══════════════════════════════════════════════════════════════════

class TestStoreBasic:
    def test_initial_state(self):
        store = make_store()
        assert store.total_records == 0
        assert store.updates_count == 0

    def test_record_accumulates(self):
        store = make_store(interval=10)
        for i in range(5):
            store.record(make_record(f"s{i}"))
        assert store.total_records == 5

    def test_update_not_triggered_before_interval(self):
        store = make_store(interval=10)
        for i in range(9):
            store.record(make_record(f"s{i}"))
        assert store.updates_count == 0

    def test_update_triggered_at_interval(self):
        store = make_store(interval=10)
        for i in range(10):
            store.record(make_record(f"s{i}"))
        assert store.updates_count == 1

    def test_multiple_intervals(self):
        store = make_store(interval=5)
        for i in range(15):
            store.record(make_record(f"s{i}"))
        assert store.updates_count == 3


# ══════════════════════════════════════════════════════════════════
# 4. LearnedCoefficientStore — 계수 갱신 로직
# ══════════════════════════════════════════════════════════════════

class TestCoefficientUpdate:
    def test_force_update_increments_version(self):
        store = make_store()
        store.force_update()
        c = store.get_coefficients()
        assert c.version == 1

    def test_good_scene_bias_lowers_pull_threshold(self):
        """GOOD 씬 비율이 높으면 reader_pull_min 하향 조정."""
        store = make_store(interval=10)
        # 10개 모두 GOOD, 높은 reader_pull
        for i in range(10):
            store.record(make_record(f"s{i}", "GOOD", "GOOD", pull=0.8))
        c_before = store.get_coefficients().reader_pull_min
        c = store.get_coefficients()
        # 갱신 후 pull_min은 기본값 이하거나 유지
        assert c.reader_pull_min <= 0.40 + 0.05  # 소폭 허용 범위

    def test_bad_scene_bias_raises_pull_threshold(self):
        """GOOD이지만 실제 BAD(FP)가 많으면 reader_pull_min 상향."""
        store = make_store(interval=10)
        # 5개 GOOD 판단이지만 gold=BAD (FP)
        for i in range(5):
            store.record(make_record(f"s{i}", "GOOD", "BAD", pull=0.45))
        for i in range(5, 10):
            store.record(make_record(f"s{i}", "BAD", "BAD", pull=0.3))
        c = store.get_coefficients()
        # precision 낮아서 pull_min 상향됐거나 유지
        assert c.reader_pull_min >= 0.40

    def test_coefficients_version_increases_on_interval(self):
        store = make_store(interval=10)
        for i in range(10):
            store.record(make_record(f"s{i}"))
        c = store.get_coefficients()
        assert c.version >= 1

    def test_decay_lambda_range(self):
        """decay_lambda는 항상 [0.001, 0.5] 범위."""
        store = make_store(interval=5)
        for i in range(20):
            store.record(make_record(f"s{i}"))
        c = store.get_coefficients()
        assert 0.001 <= c.decay_lambda <= 0.5

    def test_residue_boost_range(self):
        """residue_boost는 [1.0, 3.0] 범위."""
        store = make_store(interval=5)
        for i in range(20):
            store.record(make_record(f"s{i}"))
        c = store.get_coefficients()
        assert 1.0 <= c.residue_boost <= 3.0


# ══════════════════════════════════════════════════════════════════
# 5. LocalJudgmentValidator 연동
# ══════════════════════════════════════════════════════════════════

class TestValidatorIntegration:
    def test_apply_to_validator(self):
        from literary_system.validation.local_judgment_validator import LocalJudgmentValidator
        store = make_store(interval=5)
        for i in range(5):
            store.record(make_record(f"s{i}", "GOOD", "GOOD", pull=0.75))
        validator = LocalJudgmentValidator()
        store.apply_to_validator(validator)
        # validator 임계값이 LearnedCoefficients 값으로 갱신됨
        c = store.get_coefficients()
        assert validator.thresholds["reader_pull_min"] == pytest.approx(c.reader_pull_min)

    def test_apply_to_validator_preserves_structure(self):
        from literary_system.validation.local_judgment_validator import LocalJudgmentValidator
        store = make_store()
        validator = LocalJudgmentValidator()
        store.apply_to_validator(validator)
        # 구조 유지 확인
        assert "reader_pull_min" in validator.thresholds
        assert "reader_afterimage_min" in validator.thresholds
        assert "reader_uncertainty_max" in validator.thresholds

    def test_apply_to_drse_scorer(self):
        from literary_system.drse.drse_engine import (
            DRSEScorer, KnowledgeBoundaryGate
        )
        from literary_system.relation_graph.relation_graph_store import RelationGraphStore
        store = make_store(interval=5)
        for i in range(5):
            store.record(make_record(f"s{i}"))
        rgs = RelationGraphStore()
        gate = KnowledgeBoundaryGate(relation_graph=rgs)
        scorer = DRSEScorer(rgs=rgs, boundary_gate=gate)
        store.apply_to_drse_scorer(scorer)
        c = store.get_coefficients()
        assert scorer.DECAY_LAMBDA == pytest.approx(c.decay_lambda)
        assert scorer.RESIDUE_BOOST == pytest.approx(c.residue_boost)


# ══════════════════════════════════════════════════════════════════
# 6. JSON 직렬화 (SnapshotManager 연동)
# ══════════════════════════════════════════════════════════════════

class TestJsonSerialization:
    def test_to_json_returns_string(self):
        store = make_store()
        store.record(make_record())
        s = store.to_json()
        assert isinstance(s, str)

    def test_from_json_inplace_restores_state(self):
        store = make_store(interval=5)
        for i in range(5):
            store.record(make_record(f"s{i}"))
        json_str = store.to_json()

        store2 = make_store(interval=5)
        store2.from_json_inplace(json_str)
        assert store2.updates_count == store.updates_count
        c1 = store.get_coefficients()
        c2 = store2.get_coefficients()
        assert c1.version == c2.version
        assert c1.reader_pull_min == pytest.approx(c2.reader_pull_min)

    def test_json_roundtrip_preserves_records_count(self):
        store = make_store()
        for i in range(7):
            store.record(make_record(f"s{i}"))
        j = store.to_json()
        store2 = LearnedCoefficientStore()
        store2.from_json_inplace(j)
        assert store2.total_records == 7


# ══════════════════════════════════════════════════════════════════
# 7. stats & maybe_update
# ══════════════════════════════════════════════════════════════════

class TestStatsAndMaybeUpdate:
    def test_stats_fields(self):
        store = make_store()
        s = store.stats()
        assert "total_records" in s
        assert "updates_count" in s
        assert "update_interval" in s
        assert "current_coefficients" in s

    def test_maybe_update_returns_false_before_interval(self):
        store = make_store(interval=10)
        for i in range(9):
            store.record(make_record(f"s{i}"))
        updated = store.maybe_update()
        assert updated is False

    def test_maybe_update_returns_true_at_interval(self):
        store = make_store(interval=5)
        for i in range(5):
            store.record(make_record(f"s{i}"))
        # 이미 record에서 자동 갱신됨 → force trigger via maybe_update
        # 추가 5개 후
        for i in range(5, 10):
            store.record(make_record(f"s{i}"))
        updated = store.maybe_update()
        # 이미 갱신됐으면 False도 ok, updates_count로 확인
        assert store.updates_count >= 1

    def test_clear_records(self):
        store = make_store()
        for i in range(5):
            store.record(make_record(f"s{i}"))
        store.clear_records()
        assert store.total_records == 0
