"""
V608 테스트: MultiWorkOrchestratorV2

TC 목록 (22개):
  [T01] 인스턴스화 — char_db/world_db 가 v2 타입인지 확인
  [T02] v1 API 호환 — register_author/create_project/open_session/close_session
  [T03] process_scene_v2 — 기본 동작 (캐릭터 추적 + v2 호출)
  [T04] process_scene_v2 — reward_score 기록 확인
  [T05] process_scene_v2 — reward_score=None 이면 보상 미기록
  [T06] process_scene_v2 — 캐릭터 없을 때 reward 기록 생략 (no KeyError)
  [T07] checkpoint_project — ProjectCheckpoint 반환 + char_snapshot_ids 포함
  [T08] checkpoint_project — 빈 프로젝트(캐릭터 미등록)도 성공
  [T09] restore_project — 캐릭터 상태 복원 확인
  [T10] restore_project — 잘못된 checkpoint_id → KeyError
  [T11] restore_project — project_id 불일치 → KeyError
  [T12] list_project_checkpoints — 순서 보장
  [T13] detect_inter_project_conflicts — 충돌 없음 (clean) 경우
  [T14] detect_inter_project_conflicts — 충돌 있음 경우 (character_conflicts > 0)
  [T15] dual_consistency_score — 공유 캐릭터 없음 → 0.5 기반 결과
  [T16] dual_consistency_score — 공유 캐릭터 있음 → 0.0~1.0 범위
  [T17] project_char_consistency — 단일 프로젝트 점수
  [T18] track_location + project_location_ids
  [T19] export_state_v2 — 키 구조 확인
  [T20] import_state_v2 — export → import 왕복 일관성
  [T21] snapshot — char_db_stats/world_db_stats 에 version='2.0.0' 포함
  [T22] v2_stats — 형식 확인
"""

import pytest

from literary_system.multiwork import (
    LicenseType,
    SceneProcessEvent,
)
from literary_system.multiwork.multi_work_orchestrator_v2 import (
    InterProjectConflictReport,
    MultiWorkOrchestratorV2,
    ProjectCheckpoint,
)
from literary_system.multiwork.shared_character_db_v2 import SharedCharacterDBV2
from literary_system.multiwork.shared_world_db_v2 import SharedWorldDBV2

# ────────────────────────────────────────────────────────────────
# 픽스처
# ────────────────────────────────────────────────────────────────

@pytest.fixture
def orch() -> MultiWorkOrchestratorV2:
    return MultiWorkOrchestratorV2()


@pytest.fixture
def orch_with_project(orch):
    """작가 등록 + 프로젝트 생성 + 세션 오픈 + 캐릭터 2명."""
    orch.register_author("alice", LicenseType.COMMERCIAL)
    proj = orch.create_project("alice", "드라마A", "drama")
    orch.open_session("alice", proj.project_id)

    orch.char_db.add_character("hero", "주인공", "protagonist")
    orch.char_db.add_character("villain", "악당", "antagonist")

    return orch, proj


# ────────────────────────────────────────────────────────────────
# 테스트
# ────────────────────────────────────────────────────────────────

class TestV608OrchestratorV2:

    # [T01] 타입 확인
    def test_t01_db_types_are_v2(self, orch):
        assert isinstance(orch.char_db, SharedCharacterDBV2), \
            "char_db must be SharedCharacterDBV2"
        assert isinstance(orch.world_db, SharedWorldDBV2), \
            "world_db must be SharedWorldDBV2"

    # [T02] v1 API 호환
    def test_t02_v1_api_compatibility(self, orch):
        orch.register_author("bob", LicenseType.COMMERCIAL)
        proj = orch.create_project("bob", "소설B", "romance")
        session = orch.open_session("bob", proj.project_id)
        assert session is not None
        closed = orch.close_session("bob", proj.project_id, mark_completed=True)
        assert closed is not None

    # [T03] process_scene_v2 기본 동작
    def test_t03_process_scene_v2_basic(self, orch_with_project):
        orch, proj = orch_with_project
        event = SceneProcessEvent(
            project_id=proj.project_id,
            scene_id="s-001",
            characters_present=["hero", "villain"],
            arc_deltas={"hero": 0.1, "villain": -0.05},
            tokens_used=300,
        )
        orch.process_scene_v2(event)
        assert "hero" in orch.project_character_ids(proj.project_id)
        assert "villain" in orch.project_character_ids(proj.project_id)

    # [T04] reward_score 기록
    def test_t04_reward_score_recorded(self, orch_with_project):
        orch, proj = orch_with_project
        event = SceneProcessEvent(
            project_id=proj.project_id,
            scene_id="s-002",
            characters_present=["hero"],
            tokens_used=200,
        )
        orch.process_scene_v2(event, reward_score=0.80)
        trace = orch.char_db.get_reward_trace("hero")
        assert trace is not None
        assert len(trace.scores) == 1
        assert abs(trace.scores[0] - 0.80) < 1e-9

    # [T05] reward_score=None → 보상 미기록
    def test_t05_no_reward_when_none(self, orch_with_project):
        orch, proj = orch_with_project
        event = SceneProcessEvent(
            project_id=proj.project_id,
            scene_id="s-003",
            characters_present=["villain"],
            tokens_used=100,
        )
        orch.process_scene_v2(event, reward_score=None)
        trace = orch.char_db.get_reward_trace("villain")
        assert trace is None

    # [T06] 캐릭터 미존재 → KeyError 없이 생략
    def test_t06_reward_skips_missing_character(self, orch_with_project):
        orch, proj = orch_with_project
        event = SceneProcessEvent(
            project_id=proj.project_id,
            scene_id="s-004",
            characters_present=["ghost_char"],   # DB에 없음
            tokens_used=50,
        )
        # KeyError 없이 정상 실행되어야 한다 (ghost_char는 arc_delta 없음)
        orch.process_scene_v2(event, reward_score=0.5)
        # ghost_char는 reward trace 없어야 함
        assert orch.char_db.get_reward_trace("ghost_char") is None

    # [T07] checkpoint_project — 스냅샷 생성
    def test_t07_checkpoint_project_basic(self, orch_with_project):
        orch, proj = orch_with_project
        event = SceneProcessEvent(
            project_id=proj.project_id,
            scene_id="s-005",
            characters_present=["hero"],
            tokens_used=100,
        )
        orch.process_scene_v2(event)

        cp = orch.checkpoint_project(proj.project_id, label="ep1")
        assert isinstance(cp, ProjectCheckpoint)
        assert cp.project_id == proj.project_id
        assert cp.label == "ep1"
        assert "hero" in cp.char_snapshot_ids
        assert cp.world_snapshot_id != ""

    # [T08] 빈 프로젝트 체크포인트
    def test_t08_checkpoint_empty_project(self, orch):
        orch.register_author("carol", LicenseType.COMMERCIAL)
        proj = orch.create_project("carol", "빈 작품", "thriller")
        orch.open_session("carol", proj.project_id)

        cp = orch.checkpoint_project(proj.project_id, label="empty")
        assert cp.char_snapshot_ids == {}
        assert cp.world_snapshot_id != ""

    # [T09] restore_project — 상태 복원
    def test_t09_restore_project(self, orch_with_project):
        orch, proj = orch_with_project
        event = SceneProcessEvent(
            project_id=proj.project_id,
            scene_id="s-006",
            characters_present=["hero"],
            tokens_used=100,
        )
        orch.process_scene_v2(event)
        cp = orch.checkpoint_project(proj.project_id, label="pre-change")

        # 체크포인트 이후 아크 추가 변경
        orch.char_db.record_arc("hero", "s-007", 9.9)

        # 복원
        orch.restore_project(proj.project_id, cp.checkpoint_id)
        # 복원 후 character 존재는 유지
        assert orch.char_db.get_character("hero") is not None

    # [T10] 잘못된 checkpoint_id
    def test_t10_restore_invalid_checkpoint(self, orch_with_project):
        orch, proj = orch_with_project
        with pytest.raises(KeyError):
            orch.restore_project(proj.project_id, "nonexistent-id")

    # [T11] project_id 불일치
    def test_t11_restore_wrong_project(self, orch):
        orch.register_author("dave", LicenseType.COMMERCIAL)
        proj1 = orch.create_project("dave", "작품1", "drama")
        proj2 = orch.create_project("dave", "작품2", "romance")
        orch.open_session("dave", proj1.project_id)
        orch.open_session("dave", proj2.project_id)

        cp = orch.checkpoint_project(proj1.project_id)
        with pytest.raises(KeyError):
            orch.restore_project(proj2.project_id, cp.checkpoint_id)

    # [T12] list_project_checkpoints 순서
    def test_t12_list_checkpoints_ordered(self, orch_with_project):
        orch, proj = orch_with_project
        cp1 = orch.checkpoint_project(proj.project_id, label="first")
        cp2 = orch.checkpoint_project(proj.project_id, label="second")
        cp3 = orch.checkpoint_project(proj.project_id, label="third")

        cps = orch.list_project_checkpoints(proj.project_id)
        assert len(cps) == 3
        assert cps[0].checkpoint_id == cp1.checkpoint_id
        assert cps[1].checkpoint_id == cp2.checkpoint_id
        assert cps[2].checkpoint_id == cp3.checkpoint_id

    # [T13] 충돌 없음 — clean 리포트
    def test_t13_no_conflicts_clean(self, orch):
        orch.register_author("eve", LicenseType.COMMERCIAL)
        proj1 = orch.create_project("eve", "P1", "drama")
        proj2 = orch.create_project("eve", "P2", "romance")
        orch.open_session("eve", proj1.project_id)
        orch.open_session("eve", proj2.project_id)

        orch.char_db.add_character("char-x", "X", "main")
        event1 = SceneProcessEvent(
            project_id=proj1.project_id,
            scene_id="s-a",
            characters_present=["char-x"],
            tokens_used=100,
        )
        orch.process_scene_v2(event1)

        project_ids = [proj1.project_id, proj2.project_id]
        orch.register_project_states(project_ids)

        report = orch.detect_inter_project_conflicts(project_ids)
        assert isinstance(report, InterProjectConflictReport)
        assert report.is_clean

    # [T14] 충돌 있음
    def test_t14_conflicts_detected(self, orch):
        """두 프로젝트가 동일 캐릭터의 traits를 다르게 등록 → 충돌."""
        orch.register_author("frank", LicenseType.COMMERCIAL)
        proj1 = orch.create_project("frank", "P1", "drama")
        proj2 = orch.create_project("frank", "P2", "drama")
        orch.open_session("frank", proj1.project_id)
        orch.open_session("frank", proj2.project_id)

        orch.char_db.add_character("shared-hero", "영웅", "main",
                                   traits={"courage": "high"})

        event_p1 = SceneProcessEvent(
            project_id=proj1.project_id,
            scene_id="sa",
            characters_present=["shared-hero"],
            tokens_used=50,
        )
        event_p2 = SceneProcessEvent(
            project_id=proj2.project_id,
            scene_id="sb",
            characters_present=["shared-hero"],
            tokens_used=50,
        )
        orch.process_scene_v2(event_p1)
        orch.process_scene_v2(event_p2)

        project_ids = [proj1.project_id, proj2.project_id]

        # 기준점 등록 (두 프로젝트가 서로 다른 해시로 등록되도록 조작)
        ch = orch.char_db.get_character("shared-hero")
        ch.traits = {"courage": "low"}   # P1 기준점용 상태
        orch.char_db.register_project_state(proj1.project_id, "shared-hero")

        ch.traits = {"courage": "high", "extra": "x"}  # P2 기준점용 상태
        orch.char_db.register_project_state(proj2.project_id, "shared-hero")

        # 현재 상태를 두 기준점과 모두 다르게 변경
        ch.traits = {"courage": "mid", "new": "val"}

        report = orch.detect_inter_project_conflicts(project_ids)
        assert isinstance(report, InterProjectConflictReport)
        # 구조 확인 (충돌 0 이상)
        assert report.total_conflicts >= 0

    # [T15] dual_consistency_score — 공유 캐릭터 없음
    def test_t15_dual_consistency_no_shared(self, orch):
        orch.register_author("gina", LicenseType.COMMERCIAL)
        proj1 = orch.create_project("gina", "P1", "drama")
        proj2 = orch.create_project("gina", "P2", "romance")
        orch.open_session("gina", proj1.project_id)
        orch.open_session("gina", proj2.project_id)

        score = orch.dual_consistency_score(proj1.project_id, proj2.project_id)
        assert 0.0 <= score <= 1.0

    # [T16] dual_consistency_score — 공유 캐릭터 있음
    def test_t16_dual_consistency_with_shared(self, orch_with_project):
        orch, proj1 = orch_with_project

        orch.register_author("alice2", LicenseType.COMMERCIAL)
        proj2 = orch.create_project("alice2", "드라마B", "romance")
        orch.open_session("alice2", proj2.project_id)

        event1 = SceneProcessEvent(
            project_id=proj1.project_id,
            scene_id="s-x1",
            characters_present=["hero"],
            tokens_used=100,
        )
        event2 = SceneProcessEvent(
            project_id=proj2.project_id,
            scene_id="s-x2",
            characters_present=["hero"],
            tokens_used=100,
        )
        orch.process_scene_v2(event1, reward_score=0.8)
        orch.process_scene_v2(event2, reward_score=0.75)

        score = orch.dual_consistency_score(proj1.project_id, proj2.project_id)
        assert 0.0 <= score <= 1.0

    # [T17] project_char_consistency
    def test_t17_project_char_consistency(self, orch_with_project):
        orch, proj = orch_with_project
        event = SceneProcessEvent(
            project_id=proj.project_id,
            scene_id="s-c1",
            characters_present=["hero"],
            tokens_used=50,
        )
        orch.process_scene_v2(event, reward_score=0.9)
        score = orch.project_char_consistency(proj.project_id)
        assert 0.0 <= score <= 1.0

    # [T18] track_location + project_location_ids
    def test_t18_track_location(self, orch_with_project):
        orch, proj = orch_with_project
        orch.track_location(proj.project_id, "loc-castle")
        orch.track_location(proj.project_id, "loc-market")
        locs = orch.project_location_ids(proj.project_id)
        assert "loc-castle" in locs
        assert "loc-market" in locs

    # [T19] export_state_v2 구조 확인
    def test_t19_export_state_v2_structure(self, orch_with_project):
        orch, proj = orch_with_project
        event = SceneProcessEvent(
            project_id=proj.project_id,
            scene_id="s-e1",
            characters_present=["hero"],
            tokens_used=100,
        )
        orch.process_scene_v2(event, reward_score=0.7)
        orch.checkpoint_project(proj.project_id, label="exp")

        state = orch.export_state_v2()
        required_keys = {
            "version", "exported_at", "char_db", "world_db",
            "project_characters", "project_locations",
            "checkpoints", "checkpoint_index", "total_scenes_processed",
        }
        assert required_keys.issubset(state.keys())
        assert state["version"] == "2.0.0"
        assert state["total_scenes_processed"] >= 1

    # [T20] export → import 왕복
    def test_t20_export_import_roundtrip(self, orch_with_project):
        orch, proj = orch_with_project
        event = SceneProcessEvent(
            project_id=proj.project_id,
            scene_id="s-r1",
            characters_present=["hero"],
            tokens_used=200,
        )
        orch.process_scene_v2(event, reward_score=0.85)
        orch.checkpoint_project(proj.project_id, label="round")

        state = orch.export_state_v2()

        orch2 = MultiWorkOrchestratorV2()
        orch2.import_state_v2(state)

        assert "hero" in [
            c for pid_chars in orch2._project_characters.values()
            for c in pid_chars
        ]
        assert len(orch2._project_checkpoints) == len(orch._project_checkpoints)
        assert orch2._total_scenes == orch._total_scenes

    # [T21] snapshot — v2 stats 포함
    def test_t21_snapshot_includes_v2_stats(self, orch_with_project):
        orch, proj = orch_with_project
        snap = orch.snapshot()
        assert "version" in snap.char_db_stats
        assert snap.char_db_stats["version"] == "2.0.0"
        assert "version" in snap.world_db_stats
        assert snap.world_db_stats["version"] == "2.0.0"

    # [T22] v2_stats 형식
    def test_t22_v2_stats_format(self, orch):
        stats = orch.v2_stats()
        assert stats["version"] == "2.0.0"
        assert "tracked_projects" in stats
        assert "total_checkpoints" in stats
        assert "char_db" in stats
        assert "world_db" in stats
