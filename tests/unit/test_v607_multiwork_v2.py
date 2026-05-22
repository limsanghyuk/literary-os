"""
tests/unit/test_v607_multiwork_v2.py
V607: SharedCharacterDB v2.0 + SharedWorldDB v2.0 단위 테스트 (27 TC)
"""
import math
import time
import pytest
from literary_system.multiwork import (
    SharedCharacterDBV2, CharacterSnapshot, RewardTrace, ConflictRecord,
    SharedWorldDBV2, WorldSnapshot, LocationConflict,
)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def char_db():
    return SharedCharacterDBV2()

@pytest.fixture
def world_db():
    return SharedWorldDBV2()

@pytest.fixture
def populated_char_db(char_db):
    char_db.add_character("c1", "이준영", "주인공", traits={"용감함": True})
    return char_db

@pytest.fixture
def populated_world_db(world_db):
    world_db.add_location("loc1", "서울역", "한국의 중앙역")
    return world_db


# ──────────────────────────────────────────────
# TC-01 ~ TC-04: 버전 확인 및 상속 보장
# ──────────────────────────────────────────────

class TestVersionAndInheritance:
    def test_tc01_char_db_version(self, char_db):
        """TC-01: SharedCharacterDBV2.VERSION == '2.0.0'"""
        assert char_db.VERSION == "2.0.0"

    def test_tc02_world_db_version(self, world_db):
        """TC-02: SharedWorldDBV2.VERSION == '2.0.0'"""
        assert world_db.VERSION == "2.0.0"

    def test_tc03_char_db_inherits_v1(self, populated_char_db):
        """TC-03: v1 API (get_character) 정상 동작 보장"""
        profile = populated_char_db.get_character("c1")
        assert profile is not None
        assert profile.name == "이준영"

    def test_tc04_world_db_inherits_v1(self, populated_world_db):
        """TC-04: v1 API (get_location) 정상 동작 보장"""
        loc = populated_world_db.get_location("loc1")
        assert loc is not None
        assert loc.name == "서울역"


# ──────────────────────────────────────────────
# TC-05 ~ TC-09: CharacterSnapshot 체크포인트 / 복원
# ──────────────────────────────────────────────

class TestCharacterSnapshot:
    def test_tc05_checkpoint_returns_snapshot_id(self, populated_char_db):
        """TC-05: checkpoint() → 유효한 snapshot_id 반환"""
        sid = populated_char_db.checkpoint("c1", label="초기 상태")
        assert isinstance(sid, str) and len(sid) > 0

    def test_tc06_list_snapshots(self, populated_char_db):
        """TC-06: list_snapshots() → 체크포인트 목록 반환"""
        populated_char_db.checkpoint("c1", label="s1")
        populated_char_db.checkpoint("c1", label="s2")
        snaps = populated_char_db.list_snapshots("c1")
        assert len(snaps) >= 2
        assert all(isinstance(s, CharacterSnapshot) for s in snaps)

    def test_tc07_restore_reverts_traits(self, populated_char_db):
        """TC-07: restore() → 저장 당시 traits로 복원"""
        sid = populated_char_db.checkpoint("c1", label="원본")
        # traits 수정
        populated_char_db.update_traits("c1", {"용감함": False, "비겁함": True})
        assert populated_char_db.get_character("c1").traits.get("비겁함") is True
        # 복원
        populated_char_db.restore("c1", sid)
        char = populated_char_db.get_character("c1")
        assert "용감함" in char.traits
        assert char.traits.get("비겁함") is None

    def test_tc08_snapshot_checksum_stable(self, populated_char_db):
        """TC-08: 동일 스냅샷 → 체크섬 동일"""
        sid = populated_char_db.checkpoint("c1", label="cs1")
        snap = populated_char_db.get_snapshot(sid)
        assert snap is not None
        assert snap.checksum() == snap.checksum()

    def test_tc09_restore_invalid_snapshot_raises(self, populated_char_db):
        """TC-09: 존재하지 않는 snapshot_id 복원 시 KeyError"""
        with pytest.raises(KeyError):
            populated_char_db.restore("c1", "nonexistent-snap-id-000")


# ──────────────────────────────────────────────
# TC-10 ~ TC-13: RewardTrace (RLHF 보상 이력)
# ──────────────────────────────────────────────

class TestRewardTrace:
    def test_tc10_record_and_mean(self, populated_char_db):
        """TC-10: record_reward() → get_reward_trace().mean() 일치"""
        scores = [0.5, 0.7, 0.9]
        for s in scores:
            populated_char_db.record_reward("c1", s)
        trace = populated_char_db.get_reward_trace("c1")
        assert trace is not None
        assert abs(trace.mean() - sum(scores) / len(scores)) < 1e-9

    def test_tc11_reward_trend_positive(self, populated_char_db):
        """TC-11: 보상 상승 추세 → trend() > 0"""
        for s in [0.1, 0.2, 0.3, 0.4, 0.5, 0.9, 1.0]:
            populated_char_db.record_reward("c1", s)
        trace = populated_char_db.get_reward_trace("c1")
        assert trace.trend() > 0

    def test_tc12_reward_trend_single_score(self, populated_char_db):
        """TC-12: 보상 1개 → trend() == 0.0"""
        populated_char_db.record_reward("c1", 0.5)
        trace = populated_char_db.get_reward_trace("c1")
        assert trace.trend() == 0.0

    def test_tc13_no_trace_before_record(self, char_db):
        """TC-13: 기록 없는 캐릭터 → get_reward_trace() None"""
        char_db.add_character("cx", "미스터리", "조연")
        assert char_db.get_reward_trace("cx") is None


# ──────────────────────────────────────────────
# TC-14 ~ TC-16: consistency_score
# ──────────────────────────────────────────────

class TestConsistencyScore:
    def test_tc14_score_range(self, populated_char_db):
        """TC-14: consistency_score() → [0, 1] 범위"""
        for s in [0.6, 0.7, 0.8]:
            populated_char_db.record_reward("c1", s)
        score = populated_char_db.consistency_score("c1")
        assert 0.0 <= score <= 1.0

    def test_tc15_stable_higher_than_volatile(self, populated_char_db):
        """TC-15: 안정적 보상 → consistency_score() 상대적으로 높음"""
        for s in [0.75, 0.76, 0.75, 0.76]:
            populated_char_db.record_reward("c1", s)
        stable_score = populated_char_db.consistency_score("c1")

        db2 = SharedCharacterDBV2()
        db2.add_character("c1", "테스트", "역할")
        for s in [-5.0, 0.0, 5.0, -5.0]:
            db2.record_reward("c1", s)
        volatile_score = db2.consistency_score("c1")
        assert stable_score >= volatile_score

    def test_tc16_no_rewards_gives_valid_score(self, populated_char_db):
        """TC-16: 보상 없을 때 consistency_score() → 유효한 float"""
        score = populated_char_db.consistency_score("c1")
        assert isinstance(score, float) and not math.isnan(score)


# ──────────────────────────────────────────────
# TC-17 ~ TC-19: ConflictRecord 충돌 감지
# ──────────────────────────────────────────────

class TestConflictDetection:
    def _setup_diverged_projects(self, char_db):
        """두 프로젝트가 다른 시점을 기준으로 캐릭터를 수정하는 시나리오."""
        char_db.add_character("c2", "김민지", "조연", traits={"지혜로움": True})
        # A가 기준점 등록 (traits = {지혜로움})
        char_db.register_project_state("proj_A", "c2")
        # traits 추가 후 B 기준점 등록 (A와 다른 기준)
        char_db.update_traits("c2", {"탐정": True})
        char_db.register_project_state("proj_B", "c2")
        # 또 다른 변경 → 현재 상태가 A 기준점과도, B 기준점과도 다름
        char_db.update_traits("c2", {"지도자": True})

    def test_tc17_detect_conflict(self, char_db):
        """TC-17: 두 프로젝트가 다른 기준에서 수정 → ConflictRecord 반환"""
        self._setup_diverged_projects(char_db)
        record = char_db.detect_conflicts("c2", "proj_A", "proj_B")
        assert record is not None
        assert isinstance(record, ConflictRecord)
        assert record.character_id == "c2"

    def test_tc18_resolve_conflict(self, char_db):
        """TC-18: resolve_conflict() → resolved=True"""
        self._setup_diverged_projects(char_db)
        record = char_db.detect_conflicts("c2", "proj_A", "proj_B")
        assert record is not None
        result = char_db.resolve_conflict(record.conflict_id)
        assert result is True

    def test_tc19_list_conflicts_unresolved(self, char_db):
        """TC-19: list_conflicts(resolved=False) → 미해결 충돌만"""
        self._setup_diverged_projects(char_db)
        char_db.detect_conflicts("c2", "proj_A", "proj_B")
        unresolved = char_db.list_conflicts(resolved=False)
        assert len(unresolved) >= 1
        assert all(not c.resolved for c in unresolved)


# ──────────────────────────────────────────────
# TC-20 ~ TC-21: export / import 직렬화
# ──────────────────────────────────────────────

class TestCharacterSerialization:
    def test_tc20_export_import_roundtrip(self, populated_char_db):
        """TC-20: export_snapshot() → import_snapshot() → 캐릭터 수 유지"""
        populated_char_db.checkpoint("c1", label="export_test")
        populated_char_db.record_reward("c1", 0.8)
        data = populated_char_db.export_snapshot()
        db2 = SharedCharacterDBV2()
        count = db2.import_snapshot(data)
        assert count >= 1

    def test_tc21_status_keys(self, populated_char_db):
        """TC-21: status() → 필수 키 포함"""
        populated_char_db.record_reward("c1", 0.5)
        st = populated_char_db.status()
        for key in ("version", "characters", "snapshots",
                    "reward_traces", "conflicts_total", "conflicts_unresolved"):
            assert key in st, f"Missing key: {key}"


# ──────────────────────────────────────────────
# TC-22 ~ TC-25: SharedWorldDBV2
# ──────────────────────────────────────────────

class TestWorldDBV2:
    def test_tc22_world_checkpoint_restore(self, populated_world_db):
        """TC-22: 세계관 checkpoint() / restore() — description 복원"""
        sid = populated_world_db.checkpoint(label="초기 세계관")
        # location description 수정 (remove + re-add)
        populated_world_db.remove_location("loc1")
        populated_world_db.add_location("loc1", "서울역", "수정된 설명")
        assert populated_world_db.get_location("loc1").description == "수정된 설명"
        # 복원
        populated_world_db.restore(sid)
        restored = populated_world_db.get_location("loc1")
        assert restored.description == "한국의 중앙역"

    def test_tc23_world_consistency_score_range(self, populated_world_db):
        """TC-23: world consistency_score() → [0, 1]"""
        for i in range(4):
            populated_world_db.add_event(
                f"ev{i}", float(i * 3600), f"사건{i}", f"설명{i}",
                affected_locations=["loc1"],
            )
        score = populated_world_db.consistency_score()
        assert 0.0 <= score <= 1.0

    def test_tc24_world_location_conflict(self, populated_world_db):
        """TC-24: 로케이션 충돌 감지 → LocationConflict 반환"""
        # A 기준점
        populated_world_db.register_project_state("pA", "loc1")
        # description 변경 후 B 기준점
        populated_world_db.remove_location("loc1")
        populated_world_db.add_location("loc1", "서울역", "프로젝트A 수정 버전")
        populated_world_db.register_project_state("pB", "loc1")
        # 또 다른 변경 → 현재 상태 ≠ pA 기준 ≠ pB 기준
        populated_world_db.remove_location("loc1")
        populated_world_db.add_location("loc1", "서울역", "프로젝트B 독자 수정")
        conflict = populated_world_db.detect_location_conflicts("loc1", "pA", "pB")
        assert conflict is not None
        assert isinstance(conflict, LocationConflict)

    def test_tc25_world_export_import(self, populated_world_db):
        """TC-25: 세계관 export_snapshot() / import_snapshot() 라운드트립"""
        populated_world_db.checkpoint(label="export_test")
        data = populated_world_db.export_snapshot()
        assert isinstance(data, dict)
        new_db = SharedWorldDBV2()
        new_db.import_snapshot(data)
        st = new_db.status()
        assert "version" in st


# ──────────────────────────────────────────────
# TC-26 ~ TC-27: 경계 케이스
# ──────────────────────────────────────────────

class TestEdgeCases:
    def test_tc26_world_consistency_no_events(self, world_db):
        """TC-26: 이벤트 없을 때 consistency_score() → 0.5 (중립)"""
        score = world_db.consistency_score()
        assert score == 0.5

    def test_tc27_world_consistency_single_event(self, populated_world_db):
        """TC-27: 이벤트 1개일 때 consistency_score() → 0.5 (중립)"""
        populated_world_db.add_event("solo", 0.0, "단독", "단독 사건",
                                     affected_locations=["loc1"])
        score = populated_world_db.consistency_score()
        assert score == 0.5
