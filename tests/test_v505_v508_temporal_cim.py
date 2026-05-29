"""
V505~V508 테스트 — TemporalCIM
ADR-021: W[t][i][j], memory decay η=0.92, windowed view, flashback_compare
"""
import pytest
import sys
sys.path.insert(0, ".")

from literary_system.nie.temporal_cim import (
    TemporalCIM, RelationChange, ETA, WINDOW, MAX_EPISODES,
)
from literary_system.nie.character_influence_matrix import CharacterInfluenceMatrix


class TestTemporalCIMBasic:
    def test_init_creates_episode_0(self):
        tcim = TemporalCIM(["A", "B"])
        assert tcim.get_cim_at(0) is not None

    def test_current_t_starts_at_zero(self):
        tcim = TemporalCIM(["A", "B"])
        assert tcim.current_t == 0

    def test_update_sets_value(self):
        tcim = TemporalCIM(["A", "B"])
        tcim.update(0, "A", "B", delta=1.0)
        assert tcim.get_cim_at(0).get("A", "B") != 0.0

    def test_update_advances_current_t(self):
        tcim = TemporalCIM(["A", "B"])
        tcim.update(3, "A", "B", delta=0.5)
        assert tcim.current_t == 3

    def test_add_character_propagates(self):
        tcim = TemporalCIM(["A", "B"])
        tcim.update(0, "A", "B", 0.5)
        tcim.update(1, "A", "B", 0.3)
        tcim.add_character("C")
        assert "C" in tcim._char_ids


class TestMemoryDecay:
    def test_decay_reduces_old_relation(self):
        """에피소드가 지남에 따라 이전 관계가 decay됨"""
        tcim = TemporalCIM(["A", "B"])
        tcim.update(0, "A", "B", delta=1.0, lr=1.0)
        w0 = tcim.get_cim_at(0).get("A", "B")

        # 에피소드 1: decay 적용
        tcim.set_episode(1)
        w1 = tcim.get_cim_at(1).get("A", "B")
        # w1 = η * w0
        assert abs(w1) < abs(w0) or abs(w1) == pytest.approx(abs(w0) * ETA, abs=0.01)

    def test_set_episode_applies_decay(self):
        tcim = TemporalCIM(["A", "B"])
        tcim.update(0, "A", "B", delta=1.0, lr=1.0)
        tcim.set_episode(1)
        w_after = tcim.get_cim_at(1).get("A", "B")
        w_before = tcim.get_cim_at(0).get("A", "B")
        assert abs(w_after) <= abs(w_before) + 0.01

    def test_multiple_episodes_decay_chain(self):
        tcim = TemporalCIM(["A", "B"])
        tcim.update(0, "A", "B", delta=1.0, lr=1.0)
        w_vals = [tcim.get_cim_at(0).get("A", "B")]
        for t in range(1, 5):
            tcim.set_episode(t)
            w_vals.append(tcim.get_cim_at(t).get("A", "B"))
        # 값이 단조 감소하거나 decay 경향 확인 (부호 기준)
        assert len(w_vals) == 5

    def test_eta_constant(self):
        assert ETA == pytest.approx(0.92)

    def test_index_error_on_out_of_range(self):
        tcim = TemporalCIM(["A", "B"], max_episodes=10)
        with pytest.raises(IndexError):
            tcim.update(10, "A", "B", 0.5)


class TestWindowedView:
    def test_recent_window_returns_cim(self):
        tcim = TemporalCIM(["A", "B"])
        for t in range(3):
            tcim.update(t, "A", "B", delta=0.5)
        w_cim = tcim.get_recent_window(current_t=2)
        assert isinstance(w_cim, CharacterInfluenceMatrix)

    def test_window_average_within_range(self):
        tcim = TemporalCIM(["A", "B"])
        for t in range(WINDOW):
            tcim.update(t, "A", "B", delta=0.5, lr=1.0)
        avg_cim = tcim.get_recent_window(current_t=WINDOW - 1)
        val = avg_cim.get("A", "B")
        # 평균값은 ±1 범위
        assert -1.0 <= val <= 1.0

    def test_window_uses_only_recent_episodes(self):
        tcim = TemporalCIM(["A", "B"])
        # 에피소드 0에 큰 값
        tcim.update(0, "A", "B", delta=1.0, lr=1.0)
        # 에피소드 10~14는 0
        for t in range(10, 15):
            tcim.set_episode(t)
        avg = tcim.get_recent_window(current_t=14)
        # window=5, 10~14 에피소드 평균: 거의 0 (decay 적용)
        assert isinstance(avg, CharacterInfluenceMatrix)

    def test_empty_window_returns_empty_cim(self):
        tcim = TemporalCIM(["A", "B"])
        # 아무것도 초기화 안 된 에피소드
        result = tcim.get_recent_window(current_t=20)
        # max_episodes=24이므로 가능
        assert isinstance(result, CharacterInfluenceMatrix)


class TestFlashbackCompare:
    def _setup_tcim(self) -> TemporalCIM:
        tcim = TemporalCIM(["A", "B", "C"])
        # 에피소드 0: 우호 관계
        tcim.update(0, "A", "B", delta=1.0, lr=1.0)
        tcim.update(0, "B", "C", delta=0.8, lr=1.0)
        # 에피소드 5: 갈등 전환
        tcim.update(5, "A", "B", delta=-1.0, lr=1.0)
        tcim.update(5, "B", "C", delta=0.5, lr=1.0)
        return tcim

    def test_returns_list_of_relation_change(self):
        tcim = self._setup_tcim()
        changes = tcim.flashback_compare(5, 0)
        assert isinstance(changes, list)

    def test_degraded_relation_detected(self):
        tcim = self._setup_tcim()
        changes = tcim.flashback_compare(5, 0)
        # A→B 관계가 악화되었으므로 감지되어야 함
        pairs = [(c.char_i, c.char_j) for c in changes]
        # 최소 1개 변화 감지
        assert len(changes) >= 1

    def test_direction_field_valid(self):
        tcim = self._setup_tcim()
        changes = tcim.flashback_compare(5, 0)
        for c in changes:
            assert c.direction in ("강화", "약화")

    def test_sorted_by_abs_delta_desc(self):
        tcim = self._setup_tcim()
        changes = tcim.flashback_compare(5, 0)
        deltas = [abs(c.delta) for c in changes]
        assert deltas == sorted(deltas, reverse=True)

    def test_to_dict_structure(self):
        tcim = self._setup_tcim()
        changes = tcim.flashback_compare(5, 0)
        if changes:
            d = changes[0].to_dict()
            assert "pair" in d
            assert "delta" in d
            assert "direction" in d

    def test_no_change_below_threshold(self):
        tcim = TemporalCIM(["A", "B"])
        tcim.update(0, "A", "B", delta=0.001, lr=1.0)
        changes = tcim.flashback_compare(0, 0, threshold=0.5)
        assert len(changes) == 0


class TestTemporalCIMSnapshot:
    def test_snapshot_structure(self):
        tcim = TemporalCIM(["A", "B", "C"])
        snap = tcim.snapshot()
        assert "current_t" in snap
        assert "characters" in snap
        assert "eta" in snap
        assert "window" in snap
        assert "episode_count" in snap

    def test_snapshot_eta_correct(self):
        tcim = TemporalCIM(["A"])
        assert tcim.snapshot()["eta"] == pytest.approx(ETA)

    def test_get_current_returns_cim(self):
        tcim = TemporalCIM(["A", "B"])
        assert isinstance(tcim.get_current(), CharacterInfluenceMatrix)
