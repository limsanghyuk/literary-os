"""V407 — NarrativeMemoryStore 테스트 (25 tests)."""
import os
import tempfile
import pytest

from literary_system.memory.narrative_memory_store import (
    NarrativeMemoryStore, EpisodeMemory,
    EpisodeMemoryNotFound, SeriesNotFound,
)


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _make_memory(series_id="test_series", episode_idx=1) -> EpisodeMemory:
    return EpisodeMemory(
        series_id=series_id,
        episode_idx=episode_idx,
        created_at="2026-05-14T00:00:00",
        pipeline_state={"series_title": "테스트 드라마", "total_episodes": 16},
        narrative_tensor={"SP": 0.4, "RU": 0.1, "ET": 0.0, "RD": 0.9},
        nkg_snapshot_path="",
        debt_ledger_snapshot={"open": [], "paid": [], "defaulted": []},
        coefficient_snapshot={"conflict_weight": 0.20, "scene_energy_weight": 0.15},
    )


@pytest.fixture
def store(tmp_path):
    return NarrativeMemoryStore(memory_root=str(tmp_path / "memory"))


# ── EpisodeMemory 직렬화 테스트 ───────────────────────────────────────────────

class TestEpisodeMemorySerialization:
    def test_to_dict(self):
        mem = _make_memory()
        d = mem.to_dict()
        assert d["series_id"] == "test_series"
        assert d["episode_idx"] == 1

    def test_from_dict_roundtrip(self):
        mem = _make_memory()
        restored = EpisodeMemory.from_dict(mem.to_dict())
        assert restored.series_id == mem.series_id
        assert restored.episode_idx == mem.episode_idx
        assert restored.narrative_tensor == mem.narrative_tensor

    def test_episode_key(self):
        assert _make_memory(episode_idx=1).episode_key == "ep001"
        assert _make_memory(episode_idx=16).episode_key == "ep016"
        assert _make_memory(episode_idx=0).episode_key == "ep000"


# ── init_series 테스트 ────────────────────────────────────────────────────────

class TestInitSeries:
    def test_creates_metadata(self, store):
        store.init_series("drama1", {"title": "드라마1"})
        meta = store.get_series_metadata("drama1")
        assert meta["title"] == "드라마1"

    def test_duplicate_raises(self, store):
        store.init_series("drama2", {"title": "드라마2"})
        with pytest.raises(FileExistsError):
            store.init_series("drama2", {"title": "드라마2-dup"})

    def test_list_series_finds_initialized(self, store):
        store.init_series("series_a", {})
        store.init_series("series_b", {})
        found = store.list_series()
        assert "series_a" in found
        assert "series_b" in found

    def test_list_series_empty(self, store):
        assert store.list_series() == []


# ── save_episode 테스트 ───────────────────────────────────────────────────────

class TestSaveEpisode:
    def test_save_creates_file(self, store):
        mem = _make_memory()
        path = store.save_episode(mem)
        assert os.path.exists(path)

    def test_save_twice_raises(self, store):
        mem = _make_memory()
        store.save_episode(mem)
        with pytest.raises(FileExistsError):
            store.save_episode(_make_memory())  # 같은 series_id/episode_idx

    def test_save_different_episodes_ok(self, store):
        store.save_episode(_make_memory(episode_idx=1))
        store.save_episode(_make_memory(episode_idx=2))  # 오류 없어야 함

    def test_save_nkg_object(self, store):
        """nkg_object 있으면 pkl 파일 생성."""
        mem = _make_memory()
        fake_nkg = {"nodes": ["n1", "n2"]}  # dict으로 시뮬레이션
        store.save_episode(mem, nkg_object=fake_nkg)
        # nkg_snapshot_path 업데이트 확인
        assert mem.nkg_snapshot_path == "ep001_nkg.pkl"


# ── load_episode 테스트 ───────────────────────────────────────────────────────

class TestLoadEpisode:
    def test_load_roundtrip(self, store):
        mem = _make_memory(series_id="drama3", episode_idx=5)
        store.save_episode(mem)
        loaded = store.load_episode("drama3", 5)
        assert loaded.series_id == "drama3"
        assert loaded.episode_idx == 5
        assert loaded.narrative_tensor == mem.narrative_tensor

    def test_load_not_found_raises(self, store):
        with pytest.raises(EpisodeMemoryNotFound):
            store.load_episode("nonexistent", 1)

    def test_load_series_all_episodes(self, store):
        for i in [0, 1, 2, 3]:
            store.save_episode(_make_memory(series_id="drama4", episode_idx=i))
        memories = store.load_series("drama4")
        assert len(memories) == 4
        assert [m.episode_idx for m in memories] == [0, 1, 2, 3]

    def test_load_series_sorted(self, store):
        """저장 순서 상관없이 episode_idx 순 정렬."""
        for i in [3, 1, 0, 2]:
            store.save_episode(_make_memory(series_id="drama5", episode_idx=i))
        memories = store.load_series("drama5")
        assert [m.episode_idx for m in memories] == [0, 1, 2, 3]

    def test_get_latest_episode(self, store):
        for i in [0, 1, 2]:
            store.save_episode(_make_memory(series_id="drama6", episode_idx=i))
        latest = store.get_latest_episode("drama6")
        assert latest.episode_idx == 2

    def test_get_latest_episode_none_if_empty(self, store):
        assert store.get_latest_episode("nonexistent") is None

    def test_load_nkg_returns_object(self, store):
        mem = _make_memory(series_id="drama7", episode_idx=1)
        fake_nkg = {"graph": "data"}
        store.save_episode(mem, nkg_object=fake_nkg)
        loaded_nkg = store.load_nkg("drama7", 1)
        assert loaded_nkg == fake_nkg

    def test_load_nkg_none_if_not_saved(self, store):
        mem = _make_memory(series_id="drama8", episode_idx=1)
        store.save_episode(mem, nkg_object=None)
        assert store.load_nkg("drama8", 1) is None
