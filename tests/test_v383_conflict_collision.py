"""V383 — ConflictCollisionCalculus 테스트."""
import pytest
from literary_system.physics.conflict_collision import ConflictCollisionCalculus, ConflictCollisionResult


@pytest.fixture
def calc():
    return ConflictCollisionCalculus()


class TestConflictCollisionBasic:
    def test_returns_result_type(self, calc):
        r = calc.calculate(['A', 'B'], [('A', 'B')], {'A': 0.8, 'B': 0.6})
        assert isinstance(r, ConflictCollisionResult)

    def test_intensity_range(self, calc):
        r = calc.calculate(['A', 'B', 'C'], [('A', 'B'), ('B', 'C')], {'A': 0.8, 'B': 0.7, 'C': 0.6})
        assert 0.0 <= r.conflict_intensity <= 1.0

    def test_no_characters_stagnation(self, calc):
        r = calc.calculate([], [], {})
        assert r.stagnation_warning is True
        assert r.conflict_intensity == 0.0

    def test_no_conflict_edges_stagnation(self, calc):
        r = calc.calculate(['A', 'B'], [], {'A': 0.8, 'B': 0.6})
        assert r.stagnation_warning is True
        assert r.conflict_intensity == 0.0

    def test_collision_pairs_returned(self, calc):
        r = calc.calculate(['A', 'B'], [('A', 'B')], {'A': 1.0, 'B': 1.0})
        assert ('A', 'B') in r.collision_pairs

    def test_only_scene_chars_counted(self, calc):
        # C는 씬에 없는 캐릭터 → 충돌 쌍에서 제외
        r = calc.calculate(['A', 'B'], [('A', 'C')], {'A': 0.9, 'B': 0.5, 'C': 0.8})
        assert r.collision_pairs == []
        assert r.stagnation_warning is True

    def test_high_weight_high_intensity(self, calc):
        r = calc.calculate(['A', 'B'], [('A', 'B')], {'A': 1.0, 'B': 1.0})
        assert r.conflict_intensity > 0.0

    def test_stagnation_below_threshold(self, calc):
        r = calc.calculate(['A', 'B'], [('A', 'B')], {'A': 0.05, 'B': 0.05})
        # 매우 낮은 가중치 → intensity < 0.1 → stagnation
        assert r.stagnation_warning is True

    def test_deterministic(self, calc):
        args = (['A', 'B'], [('A', 'B')], {'A': 0.7, 'B': 0.8})
        r1 = calc.calculate(*args)
        r2 = calc.calculate(*args)
        assert r1.conflict_intensity == r2.conflict_intensity

    def test_llm_not_called(self, calc):
        # ConflictCollisionCalculus는 LLM을 전혀 호출하지 않음
        # → generate 메서드 없음 확인
        assert not hasattr(calc, 'generate')

    def test_multiple_pairs(self, calc):
        chars = ['A', 'B', 'C']
        edges = [('A', 'B'), ('A', 'C'), ('B', 'C')]
        weights = {'A': 0.8, 'B': 0.7, 'C': 0.6}
        r = calc.calculate(chars, edges, weights)
        assert len(r.collision_pairs) == 3
        assert r.conflict_intensity > 0.0

    def test_missing_weight_defaults(self, calc):
        # cluster_weights에 없는 캐릭터 → 기본값 0.5
        r = calc.calculate(['A', 'B'], [('A', 'B')], {})
        assert r.conflict_intensity > 0.0

    def test_intensity_clamp_upper(self, calc):
        chars = ['A', 'B']
        edges = [('A', 'B')]
        weights = {'A': 100.0, 'B': 100.0}
        r = calc.calculate(chars, edges, weights)
        assert r.conflict_intensity <= 1.0

    def test_intensity_clamp_lower(self, calc):
        r = calc.calculate(['A', 'B'], [('A', 'B')], {'A': 0.0, 'B': 0.0})
        assert r.conflict_intensity >= 0.0
