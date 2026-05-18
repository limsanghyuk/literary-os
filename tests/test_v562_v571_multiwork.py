"""
tests/test_v562_v571_multiwork.py
Stage C MultiWorkOrchestrator 통합 테스트

V562: MultiWorkCore (이 파일에서 커버)
V563~V571: 후속 버전에서 추가
"""

import threading
import time
import pytest

from literary_system.multiwork import (
    WorkProject,
    WorkStatus,
    WorkSession,
    MultiWorkCore,
    ProjectConflict,
)


# =========================================================
# TestWorkProject — WorkProject 데이터클래스 / FSM
# =========================================================

class TestWorkProject:
    """WorkProject 생성·상태 전환 테스트 (7개)."""

    def test_default_status_is_draft(self):
        proj = WorkProject(
            project_id="p1",
            author_id="author_A",
            title="테스트 작품",
            genre="drama",
        )
        assert proj.status == WorkStatus.DRAFT

    def test_activate_from_draft(self):
        proj = WorkProject(project_id="p2", author_id="a", title="T", genre="g")
        proj.activate()
        assert proj.status == WorkStatus.ACTIVE

    def test_pause_from_active(self):
        proj = WorkProject(project_id="p3", author_id="a", title="T", genre="g")
        proj.activate()
        proj.pause()
        assert proj.status == WorkStatus.PAUSED

    def test_complete_from_active(self):
        proj = WorkProject(project_id="p4", author_id="a", title="T", genre="g")
        proj.activate()
        proj.complete()
        assert proj.status == WorkStatus.COMPLETED

    def test_archive_from_completed(self):
        proj = WorkProject(project_id="p5", author_id="a", title="T", genre="g")
        proj.activate()
        proj.complete()
        proj.archive()
        assert proj.status == WorkStatus.ARCHIVED

    def test_invalid_transition_raises(self):
        proj = WorkProject(project_id="p6", author_id="a", title="T", genre="g")
        with pytest.raises(ProjectConflict):
            proj.pause()  # DRAFT → PAUSED 불가

    def test_activate_from_paused(self):
        proj = WorkProject(project_id="p7", author_id="a", title="T", genre="g")
        proj.activate()
        proj.pause()
        proj.activate()  # PAUSED → ACTIVE 가능
        assert proj.status == WorkStatus.ACTIVE


# =========================================================
# TestWorkSession — WorkSession 기능
# =========================================================

class TestWorkSession:
    """WorkSession 에피소드 기록·예산 테스트 (6개)."""

    def _make_session(self, budget: int = -1) -> WorkSession:
        return WorkSession(
            session_id="s-001",
            project_id="proj-001",
            author_id="author_X",
            token_budget=budget,
        )

    def test_initial_episode_count_zero(self):
        s = self._make_session()
        assert s.episode_count == 0

    def test_record_episode_increments_count(self):
        s = self._make_session()
        s.record_episode()
        s.record_episode()
        assert s.episode_count == 2

    def test_token_budget_decreases(self):
        s = self._make_session(budget=1000)
        s.record_episode(tokens_used=300)
        assert s.token_budget == 700

    def test_budget_exhausted_true(self):
        s = self._make_session(budget=100)
        s.record_episode(tokens_used=100)
        assert s.is_budget_exhausted() is True

    def test_unlimited_budget_never_exhausted(self):
        s = self._make_session(budget=-1)
        s.record_episode(tokens_used=9999)
        assert s.is_budget_exhausted() is False

    def test_summary_contains_required_keys(self):
        s = self._make_session()
        sm = s.summary()
        for key in ("session_id", "project_id", "author_id", "episode_count"):
            assert key in sm


# =========================================================
# TestMultiWorkCoreBasic — 프로젝트 등록·조회·제거
# =========================================================

class TestMultiWorkCoreBasic:
    """MultiWorkCore 기본 CRUD 테스트 (8개)."""

    def setup_method(self):
        self.core = MultiWorkCore()

    def test_register_project_returns_work_project(self):
        proj = self.core.register_project("author1", "작품A", "drama")
        assert isinstance(proj, WorkProject)
        assert proj.author_id == "author1"
        assert proj.title == "작품A"
        assert proj.genre == "drama"

    def test_register_assigns_unique_id(self):
        p1 = self.core.register_project("a", "T1", "g")
        p2 = self.core.register_project("a", "T2", "g")
        assert p1.project_id != p2.project_id

    def test_register_duplicate_id_raises(self):
        self.core.register_project("a", "T", "g", project_id="fixed-id")
        with pytest.raises(ProjectConflict):
            self.core.register_project("b", "T2", "g", project_id="fixed-id")

    def test_get_project_returns_correct(self):
        proj = self.core.register_project("a", "T", "g")
        found = self.core.get_project(proj.project_id)
        assert found is proj

    def test_get_project_missing_returns_none(self):
        assert self.core.get_project("nonexistent") is None

    def test_list_projects_filter_by_author(self):
        self.core.register_project("alice", "A1", "drama")
        self.core.register_project("alice", "A2", "romance")
        self.core.register_project("bob", "B1", "fantasy")
        alices = self.core.list_projects(author_id="alice")
        assert len(alices) == 2

    def test_remove_draft_project(self):
        proj = self.core.register_project("a", "T", "g")
        result = self.core.remove_project(proj.project_id)
        assert result is True
        assert self.core.get_project(proj.project_id) is None

    def test_remove_active_project_raises(self):
        proj = self.core.register_project("a", "T", "g")
        self.core.open_session(proj.project_id)
        with pytest.raises(ProjectConflict):
            self.core.remove_project(proj.project_id)


# =========================================================
# TestMultiWorkCoreSessions — 세션 격리 및 동시성
# =========================================================

class TestMultiWorkCoreSessions:
    """세션 생성·격리·동시성 테스트 (8개)."""

    def setup_method(self):
        self.core = MultiWorkCore(max_concurrent=3)

    def test_open_session_activates_project(self):
        proj = self.core.register_project("a", "T", "g")
        session = self.core.open_session(proj.project_id)
        assert isinstance(session, WorkSession)
        assert proj.status == WorkStatus.ACTIVE

    def test_session_bound_to_project(self):
        proj = self.core.register_project("a", "T", "g")
        session = self.core.open_session(proj.project_id)
        assert session.project_id == proj.project_id

    def test_duplicate_session_raises(self):
        proj = self.core.register_project("a", "T", "g")
        self.core.open_session(proj.project_id)
        with pytest.raises(ProjectConflict):
            self.core.open_session(proj.project_id)

    def test_max_concurrent_limit(self):
        projects = [
            self.core.register_project("a", f"T{i}", "g") for i in range(3)
        ]
        for p in projects:
            self.core.open_session(p.project_id)
        extra = self.core.register_project("a", "Extra", "g")
        with pytest.raises(ProjectConflict):
            self.core.open_session(extra.project_id)

    def test_close_session_pauses_project(self):
        proj = self.core.register_project("a", "T", "g")
        self.core.open_session(proj.project_id)
        self.core.close_session(proj.project_id)
        assert proj.status == WorkStatus.PAUSED

    def test_close_session_mark_completed(self):
        proj = self.core.register_project("a", "T", "g")
        self.core.open_session(proj.project_id)
        self.core.close_session(proj.project_id, mark_completed=True)
        assert proj.status == WorkStatus.COMPLETED

    def test_active_session_count(self):
        p1 = self.core.register_project("a", "T1", "g")
        p2 = self.core.register_project("a", "T2", "g")
        self.core.open_session(p1.project_id)
        self.core.open_session(p2.project_id)
        assert self.core.active_session_count() == 2
        self.core.close_session(p1.project_id)
        assert self.core.active_session_count() == 1

    def test_get_session_after_close_returns_none(self):
        proj = self.core.register_project("a", "T", "g")
        self.core.open_session(proj.project_id)
        self.core.close_session(proj.project_id)
        assert self.core.get_session(proj.project_id) is None


# =========================================================
# TestMultiWorkCoreSharedAssets — 공유 자산 인터페이스
# =========================================================

class TestMultiWorkCoreSharedAssets:
    """공유 자산 등록·연결 테스트 (6개)."""

    def setup_method(self):
        self.core = MultiWorkCore()

    def test_register_and_get_shared_asset(self):
        self.core.register_shared_asset("char:홍길동", {"name": "홍길동", "role": "주인공"})
        asset = self.core.get_shared_asset("char:홍길동")
        assert asset["name"] == "홍길동"

    def test_list_shared_asset_keys(self):
        self.core.register_shared_asset("char:A", {})
        self.core.register_shared_asset("world:왕국", {})
        keys = self.core.list_shared_asset_keys()
        assert "char:A" in keys
        assert "world:왕국" in keys

    def test_link_character_asset_to_project(self):
        proj = self.core.register_project("a", "T", "fantasy")
        self.core.register_shared_asset("char:엘프", {"name": "엘프"})
        self.core.link_asset_to_project(proj.project_id, "char:엘프", "character")
        assert "char:엘프" in proj.shared_character_refs

    def test_link_world_asset_to_project(self):
        proj = self.core.register_project("a", "T", "fantasy")
        self.core.register_shared_asset("world:중간계", {})
        self.core.link_asset_to_project(proj.project_id, "world:중간계", "world")
        assert "world:중간계" in proj.shared_world_refs

    def test_link_missing_asset_raises(self):
        proj = self.core.register_project("a", "T", "g")
        with pytest.raises(ProjectConflict):
            self.core.link_asset_to_project(proj.project_id, "nonexistent", "character")

    def test_link_deduplicated(self):
        proj = self.core.register_project("a", "T", "g")
        self.core.register_shared_asset("char:X", {})
        self.core.link_asset_to_project(proj.project_id, "char:X", "character")
        self.core.link_asset_to_project(proj.project_id, "char:X", "character")
        assert proj.shared_character_refs.count("char:X") == 1


# =========================================================
# TestMultiWorkCoreStats — 통계 및 상태
# =========================================================

class TestMultiWorkCoreStats:
    """통계 반환 테스트 (4개)."""

    def setup_method(self):
        self.core = MultiWorkCore()

    def test_stats_initial(self):
        s = self.core.stats()
        assert s["total_projects"] == 0
        assert s["active_sessions"] == 0
        assert s["max_concurrent"] == MultiWorkCore.MAX_CONCURRENT

    def test_stats_after_register(self):
        self.core.register_project("a", "T1", "g")
        self.core.register_project("a", "T2", "g")
        s = self.core.stats()
        assert s["total_projects"] == 2
        assert s["by_status"]["draft"] == 2

    def test_stats_after_session_open(self):
        proj = self.core.register_project("a", "T", "g")
        self.core.open_session(proj.project_id)
        s = self.core.stats()
        assert s["active_sessions"] == 1
        assert s["by_status"].get("active", 0) == 1

    def test_stats_shared_assets_count(self):
        self.core.register_shared_asset("char:A", {})
        self.core.register_shared_asset("world:B", {})
        s = self.core.stats()
        assert s["shared_assets"] == 2


# =========================================================
# TestMultiWorkCoreThreadSafety — Thread-safe 연산
# =========================================================

class TestMultiWorkCoreThreadSafety:
    """멀티스레드 환경에서의 안전성 테스트 (3개)."""

    def test_concurrent_register_no_duplicate(self):
        """50개 스레드가 동시에 프로젝트를 등록해도 ID 중복 없음."""
        core = MultiWorkCore()
        results = []
        errors = []

        def register(i):
            try:
                proj = core.register_project(f"author_{i}", f"작품_{i}", "drama")
                results.append(proj.project_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=register, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 50
        assert len(set(results)) == 50  # 모두 고유

    def test_concurrent_open_session_respects_limit(self):
        """동시 세션 한도(5)를 초과하면 정확히 ProjectConflict 발생."""
        core = MultiWorkCore(max_concurrent=5)
        projects = [
            core.register_project(f"a{i}", f"T{i}", "g") for i in range(10)
        ]
        successes = []
        failures = []

        def open_session(proj):
            try:
                core.open_session(proj.project_id)
                successes.append(proj.project_id)
            except ProjectConflict:
                failures.append(proj.project_id)

        threads = [threading.Thread(target=open_session, args=(p,)) for p in projects]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(successes) == 5
        assert len(failures) == 5

    def test_concurrent_close_and_reopen(self):
        """세션 닫기 후 재오픈이 안전하게 동작."""
        core = MultiWorkCore(max_concurrent=2)
        proj = core.register_project("a", "T", "g")
        core.open_session(proj.project_id)
        core.close_session(proj.project_id)
        # PAUSED → 재활성화
        session2 = core.open_session(proj.project_id)
        assert session2.project_id == proj.project_id
        assert proj.status == WorkStatus.ACTIVE


# =========================================================
# TestMultiWorkCoreIntegration — 시나리오 통합 테스트
# =========================================================

class TestMultiWorkCoreIntegration:
    """작가별 N작품 동시 처리 시나리오 (4개)."""

    def test_author_manages_three_concurrent_projects(self):
        """작가 한 명이 3개 작품을 동시에 처리하는 시나리오."""
        core = MultiWorkCore()
        # 3개 작품 등록
        drama = core.register_project("writer_kim", "드라마 작품", "drama")
        fantasy = core.register_project("writer_kim", "판타지 작품", "fantasy")
        romance = core.register_project("writer_kim", "로맨스 작품", "romance")

        # 모두 세션 오픈
        s_drama = core.open_session(drama.project_id)
        s_fantasy = core.open_session(fantasy.project_id)
        s_romance = core.open_session(romance.project_id)

        # 각 세션에서 에피소드 처리
        for _ in range(5):
            s_drama.record_episode(tokens_used=100)
        for _ in range(3):
            s_fantasy.record_episode(tokens_used=200)
        s_romance.record_episode(tokens_used=50)

        assert s_drama.episode_count == 5
        assert s_fantasy.episode_count == 3
        assert s_romance.episode_count == 1

        # 드라마 완료
        core.close_session(drama.project_id, mark_completed=True)
        assert drama.status == WorkStatus.COMPLETED
        assert core.active_session_count() == 2

    def test_shared_character_across_projects(self):
        """동일 캐릭터가 두 작품에 공유되는 시나리오."""
        core = MultiWorkCore()
        p1 = core.register_project("writer", "작품1", "drama")
        p2 = core.register_project("writer", "작품2", "fantasy")

        core.register_shared_asset("char:주인공", {"name": "김영수", "role": "주인공"})
        core.link_asset_to_project(p1.project_id, "char:주인공", "character")
        core.link_asset_to_project(p2.project_id, "char:주인공", "character")

        assert "char:주인공" in p1.shared_character_refs
        assert "char:주인공" in p2.shared_character_refs

        # 공유 자산 내용 동일
        a1 = core.get_shared_asset("char:주인공")
        assert a1["name"] == "김영수"

    def test_project_lifecycle_full(self):
        """프로젝트 전체 생명주기: DRAFT→ACTIVE→PAUSED→ACTIVE→COMPLETED→ARCHIVED."""
        core = MultiWorkCore()
        proj = core.register_project("a", "T", "g")
        assert proj.status == WorkStatus.DRAFT

        core.open_session(proj.project_id)
        assert proj.status == WorkStatus.ACTIVE

        core.close_session(proj.project_id)  # PAUSED
        assert proj.status == WorkStatus.PAUSED

        core.open_session(proj.project_id)  # ACTIVE again
        assert proj.status == WorkStatus.ACTIVE

        core.close_session(proj.project_id, mark_completed=True)
        assert proj.status == WorkStatus.COMPLETED

        proj.archive()
        assert proj.status == WorkStatus.ARCHIVED

    def test_list_projects_filter_by_status(self):
        """상태별 프로젝트 필터링 시나리오."""
        core = MultiWorkCore()
        for i in range(3):
            p = core.register_project("a", f"T{i}", "g")
            if i > 0:  # T1, T2만 활성화
                s = core.open_session(p.project_id)

        drafts = core.list_projects(status=WorkStatus.DRAFT)
        active = core.list_projects(status=WorkStatus.ACTIVE)

        assert len(drafts) == 1
        assert len(active) == 2


# =========================================================
# TestSharedCharacterDB — V563
# =========================================================

class TestSharedCharacterDB:
    """SharedCharacterDB CRUD·관계·아크 테스트 (9개)."""

    def setup_method(self):
        from literary_system.multiwork import SharedCharacterDB, RelationType
        self.db = SharedCharacterDB()
        self.RelationType = RelationType

    def test_add_and_get_character(self):
        char = self.db.add_character("c1", "홍길동", "주인공",
                                     genre_tags=["drama"])
        found = self.db.get_character("c1")
        assert found is char
        assert found.name == "홍길동"

    def test_add_duplicate_raises(self):
        self.db.add_character("c2", "A", "조연")
        with pytest.raises(KeyError):
            self.db.add_character("c2", "B", "악당")

    def test_list_characters_filter_genre(self):
        self.db.add_character("c3", "X", "주인공", genre_tags=["drama"])
        self.db.add_character("c4", "Y", "조연", genre_tags=["fantasy"])
        drama = self.db.list_characters(genre="drama")
        assert len(drama) == 1 and drama[0].character_id == "c3"

    def test_update_traits(self):
        self.db.add_character("c5", "Z", "악당")
        self.db.update_traits("c5", {"hair": "black", "height": 180})
        char = self.db.get_character("c5")
        assert char.traits["hair"] == "black"

    def test_link_to_project(self):
        self.db.add_character("c6", "A", "주인공")
        self.db.link_to_project("c6", "proj-001")
        char = self.db.get_character("c6")
        assert "proj-001" in char.project_refs

    def test_add_relation(self):
        self.db.add_character("c7", "A", "주인공")
        self.db.add_character("c8", "B", "조연")
        rel = self.db.add_relation("c7", "c8", self.RelationType.ALLY, weight=0.8)
        assert rel.relation_type == self.RelationType.ALLY
        assert rel.weight == 0.8

    def test_neighbors(self):
        self.db.add_character("c9", "A", "주인공")
        self.db.add_character("c10", "B", "악당")
        self.db.add_character("c11", "C", "조연")
        self.db.add_relation("c9", "c10", self.RelationType.ENEMY)
        self.db.add_relation("c9", "c11", self.RelationType.ALLY)
        allies = self.db.neighbors("c9", self.RelationType.ALLY)
        assert len(allies) == 1 and allies[0].to_id == "c11"

    def test_record_arc_and_cumulative(self):
        self.db.add_character("c12", "A", "주인공")
        self.db.record_arc("c12", "scene-1", 0.3)
        self.db.record_arc("c12", "scene-2", -0.1)
        char = self.db.get_character("c12")
        assert abs(char.cumulative_arc() - 0.2) < 1e-9

    def test_remove_character_cleans_relations(self):
        self.db.add_character("c13", "A", "주인공")
        self.db.add_character("c14", "B", "조연")
        self.db.add_relation("c13", "c14", self.RelationType.ALLY)
        self.db.remove_character("c13")
        assert self.db.get_character("c13") is None
        assert self.db.get_relation("c13", "c14") is None


# =========================================================
# TestSharedWorldDB — V564
# =========================================================

class TestSharedWorldDB:
    """SharedWorldDB CRUD 테스트 (8개)."""

    def setup_method(self):
        from literary_system.multiwork import SharedWorldDB
        self.db = SharedWorldDB()

    def test_add_and_get_location(self):
        loc = self.db.add_location("loc1", "서울", "대한민국 수도")
        assert self.db.get_location("loc1") is loc

    def test_location_hierarchy(self):
        self.db.add_location("parent", "대륙", "큰 대륙")
        child = self.db.add_location("child", "왕국", "소국", parent_id="parent")
        children = self.db.children_of("parent")
        assert len(children) == 1 and children[0].location_id == "child"

    def test_remove_location_with_children_fails(self):
        self.db.add_location("p", "대륙", "")
        self.db.add_location("c", "왕국", "", parent_id="p")
        result = self.db.remove_location("p")
        assert result is False

    def test_add_faction_and_member(self):
        self.db.add_location("loc_x", "X", "")
        fac = self.db.add_faction("f1", "왕국군", "선한 군대", alignment="good")
        self.db.add_member_to_faction("f1", "char_001")
        found = self.db.get_faction("f1")
        assert "char_001" in found.member_ids

    def test_list_factions_by_alignment(self):
        self.db.add_faction("f2", "악의 군단", "", alignment="evil")
        self.db.add_faction("f3", "중립 상인", "", alignment="neutral")
        evil = self.db.list_factions(alignment="evil")
        assert len(evil) == 1

    def test_timeline_event(self):
        ev = self.db.add_event("e1", 10.0, "전쟁 발발", "두 왕국 간 전쟁")
        assert self.db.get_event("e1") is ev

    def test_events_in_range_sorted(self):
        self.db.add_event("e2", 5.0, "조약", "")
        self.db.add_event("e3", 15.0, "혁명", "")
        self.db.add_event("e4", 10.0, "전투", "")
        events = self.db.events_in_range(0.0, 20.0)
        timestamps = [e.timestamp for e in events]
        assert timestamps == sorted(timestamps)

    def test_lore_crud(self):
        entry = self.db.add_lore("lore1", "magic", "마법 체계", "기원을 알 수 없는 마법")
        assert self.db.get_lore("lore1") is entry
        by_cat = self.db.list_lore(category="magic")
        assert len(by_cat) == 1


# =========================================================
# TestGenreTransferLearning — V565
# =========================================================

class TestGenreTransferLearning:
    """GenreTransferLearning 전이·거리·이력 테스트 (8개)."""

    def setup_method(self):
        from literary_system.multiwork import GenreTransferLearning
        self.gtl = GenreTransferLearning()

    def test_default_profiles_loaded(self):
        genres = self.gtl.list_genres()
        for g in ("drama", "romance", "fantasy", "thriller"):
            assert g in genres

    def test_get_profile(self):
        profile = self.gtl.get_profile("drama")
        assert profile is not None
        assert "tension_base" in profile.params

    def test_register_custom_profile(self):
        self.gtl.register_profile("custom_genre", {"tension_base": 0.5})
        assert self.gtl.get_profile("custom_genre") is not None

    def test_register_duplicate_raises(self):
        with pytest.raises(KeyError):
            self.gtl.register_profile("drama", {"tension_base": 0.9})

    def test_transfer_alpha_0_equals_target(self):
        result = self.gtl.transfer("fantasy", "drama", alpha=0.0)
        drama = self.gtl.get_profile("drama")
        for k in drama.params:
            if k in result.params:
                assert abs(result.params[k] - drama.params[k]) < 1e-6

    def test_transfer_alpha_1_equals_source(self):
        result = self.gtl.transfer("fantasy", "drama", alpha=1.0)
        fantasy = self.gtl.get_profile("fantasy")
        for k in fantasy.params:
            if k in result.params:
                assert abs(result.params[k] - fantasy.params[k]) < 1e-6

    def test_transfer_records_history(self):
        self.gtl.transfer("romance", "drama", alpha=0.3, project_id="proj-X")
        history = self.gtl.transfer_history(project_id="proj-X")
        assert len(history) == 1
        assert history[0].source_genre == "romance"

    def test_genre_distance_self_is_zero(self):
        d = self.gtl.genre_distance("drama", "drama")
        assert d == 0.0

    def test_most_similar_genre(self):
        similar, dist = self.gtl.most_similar_genre("drama")
        assert isinstance(similar, str)
        assert dist >= 0.0


# =========================================================
# TestProjectIsolationManager — V566
# =========================================================

class TestProjectIsolationManager:
    """ProjectIsolationManager 격리·감사 테스트 (9개)."""

    def setup_method(self):
        from literary_system.multiwork import (
            ProjectIsolationManager, IsolationPolicy, IsolationViolation
        )
        self.mgr = ProjectIsolationManager()
        self.IsolationPolicy = IsolationPolicy
        self.IsolationViolation = IsolationViolation

    def _register(self, pid, **kwargs):
        policy = self.IsolationPolicy(project_id=pid, **kwargs)
        self.mgr.register_policy(policy)

    def test_write_and_read_private(self):
        self._register("p1")
        self.mgr.write("p1", "key1", "value1")
        assert self.mgr.read_private("p1", "key1") == "value1"

    def test_read_missing_key_returns_default(self):
        self._register("p2")
        val = self.mgr.read_private("p2", "missing", default="fallback")
        assert val == "fallback"

    def test_blocked_key_write_raises(self):
        self._register("p3", blocked_keys={"secret"})
        with pytest.raises(self.IsolationViolation):
            self.mgr.write("p3", "secret", "data")

    def test_blocked_key_read_raises(self):
        self._register("p4", blocked_keys={"secret"})
        with pytest.raises(self.IsolationViolation):
            self.mgr.read_private("p4", "secret")

    def test_shared_read_allowed(self):
        self._register("p5", allow_shared_read=True)
        shared = {"char:hero": {"name": "Hero"}}
        val = self.mgr.read_shared("p5", "char:hero", shared)
        assert val["name"] == "Hero"

    def test_shared_read_disabled_raises(self):
        self._register("p6", allow_shared_read=False)
        with pytest.raises(self.IsolationViolation):
            self.mgr.read_shared("p6", "anything", {"anything": 1})

    def test_cross_project_allowed(self):
        self._register("requester", allowed_projects={"owner"})
        self._register("owner")
        self.mgr.write("owner", "data", 42)
        val = self.mgr.cross_project_read("requester", "owner", "data")
        assert val == 42

    def test_cross_project_not_whitelisted_raises(self):
        self._register("req2")
        self._register("own2")
        self.mgr.write("own2", "secret", "X")
        with pytest.raises(self.IsolationViolation):
            self.mgr.cross_project_read("req2", "own2", "secret")

    def test_audit_log_records_violations(self):
        self._register("p7", blocked_keys={"bad"})
        try:
            self.mgr.write("p7", "bad", "val")
        except self.IsolationViolation:
            pass
        violations = self.mgr.violation_count("p7")
        assert violations >= 1


# =========================================================
# TestStageC_Integration — V562~V566 통합 시나리오
# =========================================================

class TestStageC_Integration:
    """V562~V566 교차 통합 시나리오 (5개)."""

    def setup_method(self):
        from literary_system.multiwork import (
            MultiWorkCore, SharedCharacterDB, SharedWorldDB,
            GenreTransferLearning, ProjectIsolationManager,
            IsolationPolicy, RelationType
        )
        self.core = MultiWorkCore()
        self.char_db = SharedCharacterDB()
        self.world_db = SharedWorldDB()
        self.gtl = GenreTransferLearning()
        self.iso = ProjectIsolationManager()
        self.RelationType = RelationType
        self.IsolationPolicy = IsolationPolicy

    def test_full_multiwork_pipeline(self):
        """캐릭터·월드 공유 + 프로젝트 격리 통합 시나리오."""
        # 프로젝트 등록
        p1 = self.core.register_project("writer", "드라마 시즌1", "drama")
        p2 = self.core.register_project("writer", "드라마 시즌2", "drama")

        # 공유 캐릭터 등록
        hero = self.char_db.add_character("hero", "김주인공", "주인공",
                                          genre_tags=["drama"])
        self.char_db.link_to_project("hero", p1.project_id)
        self.char_db.link_to_project("hero", p2.project_id)

        # MultiWorkCore 공유 자산 등록
        self.core.register_shared_asset("char:hero", hero.to_dict())
        self.core.link_asset_to_project(p1.project_id, "char:hero", "character")
        self.core.link_asset_to_project(p2.project_id, "char:hero", "character")

        assert "char:hero" in p1.shared_character_refs
        assert "char:hero" in p2.shared_character_refs

    def test_genre_transfer_applied_to_project(self):
        """장르 전이 결과를 프로젝트 세션 컨텍스트에 저장."""
        proj = self.core.register_project("writer", "하이브리드 작품", "drama")
        session = self.core.open_session(proj.project_id)

        # fantasy → drama 30% 전이
        transferred = self.gtl.transfer("fantasy", "drama", alpha=0.3,
                                        project_id=proj.project_id)
        session.context["style_params"] = transferred.params

        assert "tension_base" in session.context["style_params"]
        assert transferred.source_genre == "fantasy"

    def test_isolation_guards_project_context(self):
        """격리 정책이 사설 컨텍스트를 보호."""
        p1 = self.core.register_project("a", "A", "drama")
        p2 = self.core.register_project("b", "B", "drama")

        self.iso.register_policy(self.IsolationPolicy(p1.project_id))
        self.iso.register_policy(self.IsolationPolicy(p2.project_id))

        self.iso.write(p1.project_id, "plot_secret", "반전 결말")

        from literary_system.multiwork import IsolationViolation
        with pytest.raises(IsolationViolation):
            self.iso.cross_project_read(p2.project_id, p1.project_id, "plot_secret")

    def test_character_arc_tracked_across_sessions(self):
        """두 세션에서 캐릭터 아크 누적 기록."""
        hero = self.char_db.add_character("hero2", "이주인공", "주인공")
        self.char_db.record_arc("hero2", "ep1-sc1", 0.2)
        self.char_db.record_arc("hero2", "ep2-sc3", 0.3)
        self.char_db.record_arc("hero2", "ep2-sc5", -0.1)

        assert abs(hero.cumulative_arc() - 0.4) < 1e-9
        assert len(hero.arc_history) == 3

    def test_world_shared_across_two_dramas(self):
        """동일 세계관을 두 드라마 프로젝트가 공유."""
        self.world_db.add_location("city", "서울", "수도")
        self.world_db.add_faction("police", "경찰청", "법 집행", alignment="good")

        p1 = self.core.register_project("w", "형사 드라마", "drama")
        p2 = self.core.register_project("w", "법정 드라마", "drama")

        self.world_db.link_location_to_project("city", p1.project_id)
        self.world_db.link_location_to_project("city", p2.project_id)
        self.world_db.link_faction_to_project("police", p1.project_id)

        city = self.world_db.get_location("city")
        assert p1.project_id in city.project_refs
        assert p2.project_id in city.project_refs

        police = self.world_db.get_faction("police")
        assert p1.project_id in police.project_refs


# =========================================================
# TestMultiWorkCIM — V567
# =========================================================

class TestMultiWorkCIM:
    """MultiWorkCIM 프로젝트별 격리·집계 테스트 (7개)."""

    def setup_method(self):
        from literary_system.multiwork import MultiWorkCIM
        self.cim = MultiWorkCIM(decay=0.95)

    def test_init_project(self):
        cim = self.cim.init_project("p1")
        assert cim.project_id == "p1"

    def test_init_duplicate_raises(self):
        self.cim.init_project("p2")
        with pytest.raises(KeyError):
            self.cim.init_project("p2")

    def test_record_interaction_updates_weight(self):
        self.cim.init_project("p3")
        self.cim.record("p3", "hero", "villain")
        cim = self.cim.get_project_cim("p3")
        w = cim.weight("hero", "villain")
        assert w > 0.0

    def test_weight_increases_with_count(self):
        self.cim.init_project("p4")
        for _ in range(5):
            self.cim.record("p4", "A", "B")
        cim = self.cim.get_project_cim("p4")
        w5 = cim.weight("A", "B")
        self.cim.record("p4", "A", "B")
        w6 = cim.weight("A", "B")
        assert w6 > w5

    def test_self_interaction_ignored(self):
        self.cim.init_project("p5")
        self.cim.record("p5", "hero", "hero")
        cim = self.cim.get_project_cim("p5")
        assert len(cim.entries) == 0

    def test_global_weight_aggregates(self):
        self.cim.init_project("pa")
        self.cim.init_project("pb")
        self.cim.record("pa", "X", "Y")
        self.cim.record("pb", "X", "Y")
        gw = self.cim.global_weight("X", "Y")
        assert gw > 0.0

    def test_aggregate_warm_start(self):
        self.cim.init_project("pc")
        self.cim.record("pc", "A", "B")
        result = self.cim.aggregate_warm_start(["A", "B"], project_ids=["pc"])
        assert "A" in result and "B" in result["A"]


# =========================================================
# TestAuthorLicenseAPI — V568
# =========================================================

class TestAuthorLicenseAPI:
    """AuthorLicenseAPI 발급·검증·사용량 테스트 (8개)."""

    def setup_method(self):
        from literary_system.multiwork import AuthorLicenseAPI, LicenseType, LicenseScope, LicenseViolation
        self.api = AuthorLicenseAPI()
        self.LicenseType = LicenseType
        self.LicenseScope = LicenseScope
        self.LicenseViolation = LicenseViolation

    def test_issue_license(self):
        lic = self.api.issue_license("lic1", "alice", self.LicenseType.COMMERCIAL)
        assert lic.is_active()
        assert lic.author_id == "alice"

    def test_issue_duplicate_raises(self):
        self.api.issue_license("lic2", "bob", self.LicenseType.PERSONAL)
        with pytest.raises(KeyError):
            self.api.issue_license("lic2", "bob", self.LicenseType.PERSONAL)

    def test_get_active_license(self):
        self.api.issue_license("lic3", "carol", self.LicenseType.ENTERPRISE)
        lic = self.api.get_active_license("carol")
        assert lic is not None
        assert lic.license_type == self.LicenseType.ENTERPRISE

    def test_validate_scope_allowed(self):
        self.api.issue_license("lic4", "dave", self.LicenseType.COMMERCIAL)
        # 예외 없이 통과
        self.api.validate_scope("dave", self.LicenseScope.MULTI_WORK)

    def test_validate_scope_denied(self):
        self.api.issue_license("lic5", "eve", self.LicenseType.PERSONAL)
        with pytest.raises(self.LicenseViolation):
            self.api.validate_scope("eve", self.LicenseScope.FINE_TUNE)

    def test_project_creation_limit(self):
        self.api.issue_license("lic6", "frank", self.LicenseType.PERSONAL)
        lic = self.api.get_active_license("frank")
        # PERSONAL: max 3 프로젝트
        for _ in range(3):
            self.api.record_project_created("frank")
        with pytest.raises(self.LicenseViolation):
            self.api.validate_project_creation("frank")

    def test_revoke_license(self):
        self.api.issue_license("lic7", "grace", self.LicenseType.RESEARCH)
        self.api.revoke_license("lic7")
        lic = self.api.get_active_license("grace")
        assert lic is None

    def test_stats(self):
        self.api.issue_license("lic8", "henry", self.LicenseType.COMMERCIAL)
        s = self.api.stats()
        assert s["total_licenses"] >= 1
        assert s["active_licenses"] >= 1


# =========================================================
# TestMultiWorkOrchestrator — V570
# =========================================================

class TestMultiWorkOrchestrator:
    """MultiWorkOrchestrator 통합 오케스트레이터 테스트 (7개)."""

    def setup_method(self):
        from literary_system.multiwork import (
            MultiWorkOrchestrator, LicenseType, SceneProcessEvent
        )
        self.orch = MultiWorkOrchestrator()
        self.LicenseType = LicenseType
        self.SceneProcessEvent = SceneProcessEvent

    def test_register_author_and_create_project(self):
        self.orch.register_author("writer1", self.LicenseType.COMMERCIAL)
        proj = self.orch.create_project("writer1", "드라마", "drama")
        assert proj.title == "드라마"

    def test_open_and_close_session(self):
        self.orch.register_author("writer2", self.LicenseType.COMMERCIAL)
        proj = self.orch.create_project("writer2", "판타지", "fantasy")
        session = self.orch.open_session("writer2", proj.project_id)
        assert session.project_id == proj.project_id
        self.orch.close_session("writer2", proj.project_id)

    def test_process_scene_records_cim_and_arc(self):
        self.orch.register_author("writer3", self.LicenseType.COMMERCIAL)
        # 캐릭터 등록
        self.orch.char_db.add_character("hero3", "주인공", "주인공")
        self.orch.char_db.add_character("villain3", "악당", "악당")
        proj = self.orch.create_project("writer3", "테스트", "drama")
        self.orch.open_session("writer3", proj.project_id)
        event = self.SceneProcessEvent(
            project_id=proj.project_id,
            scene_id="s-001",
            characters_present=["hero3", "villain3"],
            arc_deltas={"hero3": 0.3, "villain3": -0.2},
            tokens_used=200,
        )
        self.orch.process_scene(event)
        # CIM 확인
        cim = self.orch.cim.get_project_cim(proj.project_id)
        assert cim.weight("hero3", "villain3") > 0
        # 아크 확인
        hero = self.orch.char_db.get_character("hero3")
        assert len(hero.arc_history) == 1

    def test_process_scene_no_session_raises(self):
        from literary_system.multiwork import ProjectConflict
        self.orch.register_author("writer4", self.LicenseType.COMMERCIAL)
        proj = self.orch.create_project("writer4", "T", "drama")
        # 세션 열지 않고 씬 처리 시도
        with pytest.raises(ProjectConflict):
            self.orch.process_scene(self.SceneProcessEvent(
                project_id=proj.project_id,
                scene_id="s-001",
                characters_present=[],
            ))

    def test_genre_transfer_stored_in_session(self):
        self.orch.register_author("writer5", self.LicenseType.COMMERCIAL)
        proj = self.orch.create_project("writer5", "하이브리드", "drama")
        self.orch.open_session("writer5", proj.project_id)
        params = self.orch.apply_genre_transfer("writer5", proj.project_id,
                                                 "fantasy", alpha=0.3)
        session = self.orch.core.get_session(proj.project_id)
        assert "style_params" in session.context
        assert "tension_base" in params

    def test_snapshot(self):
        snap = self.orch.snapshot()
        assert hasattr(snap, "core_stats")
        assert hasattr(snap, "cim_stats")
        assert hasattr(snap, "license_stats")
        assert snap.total_scenes_processed == 0

    def test_multiple_scene_processing(self):
        self.orch.register_author("writer6", self.LicenseType.ENTERPRISE)
        proj = self.orch.create_project("writer6", "대하드라마", "drama")
        self.orch.open_session("writer6", proj.project_id)
        for i in range(10):
            self.orch.process_scene(self.SceneProcessEvent(
                project_id=proj.project_id,
                scene_id=f"s-{i:03d}",
                characters_present=["A", "B"],
                tokens_used=100,
            ))
        snap = self.orch.snapshot()
        assert snap.total_scenes_processed == 10


# =========================================================
# TestGate31 — V569
# =========================================================

class TestGate31:
    """Gate31 MultiWork 생존 게이트 테스트 (3개)."""

    def test_gate31_passes(self):
        from literary_system.gates.release_gate import GATES
        gate31 = next((g for g in GATES if g[0] == "multiwork_gate31"), None)
        assert gate31 is not None, "Gate31 not found in GATES"
        result = gate31[2]()
        assert result["pass"] is True, f"Gate31 failed: {result}"

    def test_total_gate_count_gte_30(self):
        from literary_system.gates.release_gate import GATES
        assert len(GATES) >= 30

    def test_run_release_gate_version(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["version"] == "V571"
        assert result["pass"] is True
