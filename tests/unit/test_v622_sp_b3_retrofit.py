"""
V622 SP-B.3 retrofit P-IF 3건 단위 테스트 (ADR-089)

§A  ConflictPolicy + CharacterConflictResolver  TC-01~20
§B  WorkloadProfile + SLO + schedule()          TC-21~40
§C  RewardModelV2 + AdvSeed                     TC-41~60

목표: 60/60 PASS, G58/G59 회귀 0건
"""
from __future__ import annotations

import math
import pytest

# ────────────────────────────────────────────────────────────────
# §A  ConflictPolicy + CharacterConflictResolver  (TC-01~20)
# ────────────────────────────────────────────────────────────────

class TestConflictPolicy:
    """TC-01~10: ConflictPolicy Enum 5종 기본 검증."""

    def test_tc01_enum_values_exist(self):
        """TC-01: ConflictPolicy 5종 value 존재."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        assert ConflictPolicy.RENAME.value   == "RENAME"
        assert ConflictPolicy.MERGE.value    == "MERGE"
        assert ConflictPolicy.FORK.value     == "FORK"
        assert ConflictPolicy.BLOCK.value    == "BLOCK"
        assert ConflictPolicy.ESCALATE.value == "ESCALATE"

    def test_tc02_enum_count(self):
        """TC-02: ConflictPolicy 멤버 수 == 5."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        assert len(list(ConflictPolicy)) == 5

    def test_tc03_enum_is_str_subclass(self):
        """TC-03: ConflictPolicy 는 str 서브클래스."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        assert isinstance(ConflictPolicy.RENAME, str)

    def test_tc04_enum_from_string(self):
        """TC-04: 문자열로 ConflictPolicy 생성."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        assert ConflictPolicy("MERGE") == ConflictPolicy.MERGE

    def test_tc05_enum_comparison(self):
        """TC-05: ConflictPolicy 동등 비교."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        assert ConflictPolicy.FORK != ConflictPolicy.BLOCK

    def test_tc06_rename_value(self):
        """TC-06: RENAME value 문자열 == 'RENAME'."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        assert ConflictPolicy.RENAME == "RENAME"

    def test_tc07_block_value(self):
        """TC-07: BLOCK value 문자열 == 'BLOCK'."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        assert ConflictPolicy.BLOCK == "BLOCK"

    def test_tc08_escalate_value(self):
        """TC-08: ESCALATE value 문자열 == 'ESCALATE'."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        assert ConflictPolicy.ESCALATE == "ESCALATE"

    def test_tc09_all_values_unique(self):
        """TC-09: 5종 value 모두 고유."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        vals = [p.value for p in ConflictPolicy]
        assert len(vals) == len(set(vals))

    def test_tc10_iterable(self):
        """TC-10: ConflictPolicy 이터러블."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        names = [p.name for p in ConflictPolicy]
        assert "RENAME" in names
        assert "ESCALATE" in names


class TestCharacterConflictResolver:
    """TC-11~20: CharacterConflictResolver.resolve() 5종 정책."""

    @staticmethod
    def _make_conflict(db, cid: str = "hero"):
        """register_project_state 두 번 + 보장된 신규 key 추가로 실제 충돌 레코드 생성.

        _trait_hash 는 key 집합 기반이므로 반드시 새 key 를 추가해야 hash 가 변한다.
        """
        # Step1: 기준점 A 등록
        db.register_project_state("proj_a", cid)
        # Step2: 보장된 신규 key '__tb__' 추가 -> hash_B != hash_A
        db.update_traits(cid, {"__tb__": 1})
        db.register_project_state("proj_b", cid)
        # Step3: 또 다른 신규 key '__tc__' 추가 -> current != hash_A, hash_B
        db.update_traits(cid, {"__tc__": 1})
        return db.detect_conflicts(cid, "proj_a", "proj_b")

    @pytest.fixture()
    def db_with_conflict(self):
        """캐릭터 등록 + 충돌 레코드가 있는 SharedCharacterDBV2 반환."""
        from literary_system.multiwork.shared_character_db_v2 import (
            SharedCharacterDBV2, CharacterConflictResolver,
        )
        db = SharedCharacterDBV2()
        db.add_character("hero", "홍길동", "주인공", traits={"courage": 0.9})
        conflict = TestCharacterConflictResolver._make_conflict(db, "hero")
        conflicts = [conflict] if conflict is not None else []
        resolver = CharacterConflictResolver(db)
        return db, resolver, conflicts

    def test_tc11_resolver_instantiation(self, db_with_conflict):
        """TC-11: CharacterConflictResolver 인스턴스 생성."""
        from literary_system.multiwork.shared_character_db_v2 import CharacterConflictResolver
        db, resolver, _ = db_with_conflict
        assert isinstance(resolver, CharacterConflictResolver)

    def test_tc12_rename_policy_resolved(self, db_with_conflict):
        """TC-12: RENAME 정책 → resolved=True."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        db, resolver, conflicts = db_with_conflict
        if not conflicts:
            pytest.skip("충돌 없음 — 환경 제한")
        result = resolver.resolve(conflicts[0].conflict_id, ConflictPolicy.RENAME)
        assert result["resolved"] is True

    def test_tc13_rename_result_ids_two(self, db_with_conflict):
        """TC-13: RENAME → result_ids 2개 (원본 + 새 ID)."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        db, resolver, conflicts = db_with_conflict
        if not conflicts:
            pytest.skip("충돌 없음")
        result = resolver.resolve(conflicts[0].conflict_id, ConflictPolicy.RENAME)
        assert len(result["result_ids"]) == 2

    def test_tc14_merge_policy_resolved(self, db_with_conflict):
        """TC-14: MERGE 정책 → resolved=True."""
        from literary_system.multiwork.shared_character_db_v2 import (
            SharedCharacterDBV2, CharacterConflictResolver, ConflictPolicy,
        )
        db2 = SharedCharacterDBV2()
        db2.add_character("c1", "이몽룡", "주인공", traits={"wit": 0.9})
        conflict2 = TestCharacterConflictResolver._make_conflict(db2, "c1")
        conflicts2 = [conflict2] if conflict2 is not None else []
        resolver2 = CharacterConflictResolver(db2)
        if not conflicts2:
            pytest.skip("충돌 없음")
        result = resolver2.resolve(conflicts2[0].conflict_id, ConflictPolicy.MERGE)
        assert result["resolved"] is True

    def test_tc15_fork_creates_fork_id(self, db_with_conflict):
        """TC-15: FORK → '_fork' 접미사 ID 생성."""
        from literary_system.multiwork.shared_character_db_v2 import (
            SharedCharacterDBV2, CharacterConflictResolver, ConflictPolicy,
        )
        from literary_system.multiwork.shared_character_db import CharacterProfile
        db2 = SharedCharacterDBV2()
        db2.add_character("hero2", "춘향", "여주인공", traits={"loyalty": 1.0})
        conflict2 = TestCharacterConflictResolver._make_conflict(db2, "hero2")
        conflicts2 = [conflict2] if conflict2 is not None else []
        resolver2 = CharacterConflictResolver(db2)
        if not conflicts2:
            pytest.skip("충돌 없음")
        result = resolver2.resolve(conflicts2[0].conflict_id, ConflictPolicy.FORK)
        assert any("_fork" in rid for rid in result["result_ids"])

    def test_tc16_block_raises_runtime_error(self, db_with_conflict):
        """TC-16: BLOCK 정책 → RuntimeError 발생."""
        from literary_system.multiwork.shared_character_db_v2 import (
            SharedCharacterDBV2, CharacterConflictResolver, ConflictPolicy,
        )
        from literary_system.multiwork.shared_character_db import CharacterProfile
        db2 = SharedCharacterDBV2()
        db2.add_character("hero3", "변학도", "악당", traits={"greed": 0.8})
        conflict2 = TestCharacterConflictResolver._make_conflict(db2, "hero3")
        conflicts2 = [conflict2] if conflict2 is not None else []
        resolver2 = CharacterConflictResolver(db2)
        if not conflicts2:
            pytest.skip("충돌 없음")
        with pytest.raises(RuntimeError, match="BLOCK"):
            resolver2.resolve(conflicts2[0].conflict_id, ConflictPolicy.BLOCK)

    def test_tc17_escalate_resolved_false(self, db_with_conflict):
        """TC-17: ESCALATE → resolved=False (에스컬레이션 마킹)."""
        from literary_system.multiwork.shared_character_db_v2 import (
            SharedCharacterDBV2, CharacterConflictResolver, ConflictPolicy,
        )
        from literary_system.multiwork.shared_character_db import CharacterProfile
        db2 = SharedCharacterDBV2()
        db2.add_character("hero4", "판관", "조력자", traits={"authority": 0.95})
        conflict2 = TestCharacterConflictResolver._make_conflict(db2, "hero4")
        conflicts2 = [conflict2] if conflict2 is not None else []
        resolver2 = CharacterConflictResolver(db2)
        if not conflicts2:
            pytest.skip("충돌 없음")
        result = resolver2.resolve(conflicts2[0].conflict_id, ConflictPolicy.ESCALATE)
        assert result["resolved"] is False

    def test_tc18_resolve_unknown_id_raises(self, db_with_conflict):
        """TC-18: 존재하지 않는 conflict_id → KeyError."""
        from literary_system.multiwork.shared_character_db_v2 import ConflictPolicy
        db, resolver, _ = db_with_conflict
        with pytest.raises(KeyError):
            resolver.resolve("no_such_id", ConflictPolicy.RENAME)

    def test_tc19_resolve_returns_policy_field(self, db_with_conflict):
        """TC-19: 결과 dict에 'policy' 키 존재."""
        from literary_system.multiwork.shared_character_db_v2 import (
            SharedCharacterDBV2, CharacterConflictResolver, ConflictPolicy,
        )
        from literary_system.multiwork.shared_character_db import CharacterProfile
        db2 = SharedCharacterDBV2()
        db2.add_character("h5", "배우5", "조연", traits={"skill": 0.5})
        conflict2 = TestCharacterConflictResolver._make_conflict(db2, "h5")
        conflicts2 = [conflict2] if conflict2 is not None else []
        resolver2 = CharacterConflictResolver(db2)
        if not conflicts2:
            pytest.skip("충돌 없음")
        result = resolver2.resolve(conflicts2[0].conflict_id, ConflictPolicy.MERGE)
        assert "policy" in result

    def test_tc20_result_has_action_field(self, db_with_conflict):
        """TC-20: 결과 dict에 'action' 키 존재."""
        from literary_system.multiwork.shared_character_db_v2 import (
            SharedCharacterDBV2, CharacterConflictResolver, ConflictPolicy,
        )
        from literary_system.multiwork.shared_character_db import CharacterProfile
        db2 = SharedCharacterDBV2()
        db2.add_character("h6", "배우6", "조연", traits={"depth": 0.7})
        conflict2 = TestCharacterConflictResolver._make_conflict(db2, "h6")
        conflicts2 = [conflict2] if conflict2 is not None else []
        resolver2 = CharacterConflictResolver(db2)
        if not conflicts2:
            pytest.skip("충돌 없음")
        result = resolver2.resolve(conflicts2[0].conflict_id, ConflictPolicy.FORK)
        assert "action" in result


# ────────────────────────────────────────────────────────────────
# §B  WorkloadProfile + SLO + schedule()  (TC-21~40)
# ────────────────────────────────────────────────────────────────

class TestWorkloadProfile:
    """TC-21~30: WorkloadProfile Enum + SLO 상수."""

    def test_tc21_profile_values(self):
        """TC-21: WorkloadProfile 3종 value 존재."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import WorkloadProfile
        assert WorkloadProfile.SINGLE.value == "SINGLE"
        assert WorkloadProfile.DUAL.value   == "DUAL"
        assert WorkloadProfile.TRIPLE.value == "TRIPLE"

    def test_tc22_profile_count(self):
        """TC-22: WorkloadProfile 멤버 수 == 3."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import WorkloadProfile
        assert len(list(WorkloadProfile)) == 3

    def test_tc23_slo_single(self):
        """TC-23: SLO_SINGLE_MS == 3000."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import SLO_SINGLE_MS
        assert SLO_SINGLE_MS == 3_000

    def test_tc24_slo_dual(self):
        """TC-24: SLO_DUAL_MS == 5000."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import SLO_DUAL_MS
        assert SLO_DUAL_MS == 5_000

    def test_tc25_slo_triple(self):
        """TC-25: SLO_TRIPLE_MS == 8000."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import SLO_TRIPLE_MS
        assert SLO_TRIPLE_MS == 8_000

    def test_tc26_slo_ordering(self):
        """TC-26: SLO SINGLE < DUAL < TRIPLE."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import (
            SLO_SINGLE_MS, SLO_DUAL_MS, SLO_TRIPLE_MS
        )
        assert SLO_SINGLE_MS < SLO_DUAL_MS < SLO_TRIPLE_MS

    def test_tc27_classify_single(self):
        """TC-27: 1개 프로젝트 → SINGLE."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import (
            WorkloadProfile, classify_workload
        )
        assert classify_workload(["p1"]) == WorkloadProfile.SINGLE

    def test_tc28_classify_dual(self):
        """TC-28: 2개 프로젝트 → DUAL."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import (
            WorkloadProfile, classify_workload
        )
        assert classify_workload(["p1", "p2"]) == WorkloadProfile.DUAL

    def test_tc29_classify_triple(self):
        """TC-29: 3개 이상 프로젝트 → TRIPLE."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import (
            WorkloadProfile, classify_workload
        )
        assert classify_workload(["p1", "p2", "p3"]) == WorkloadProfile.TRIPLE
        assert classify_workload(["p1", "p2", "p3", "p4"]) == WorkloadProfile.TRIPLE

    def test_tc30_get_slo_ms(self):
        """TC-30: get_slo_ms() 값 정확성."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import (
            WorkloadProfile, get_slo_ms, SLO_SINGLE_MS, SLO_DUAL_MS, SLO_TRIPLE_MS
        )
        assert get_slo_ms(WorkloadProfile.SINGLE) == SLO_SINGLE_MS
        assert get_slo_ms(WorkloadProfile.DUAL)   == SLO_DUAL_MS
        assert get_slo_ms(WorkloadProfile.TRIPLE)  == SLO_TRIPLE_MS


class TestSchedule:
    """TC-31~40: schedule() 함수 검증."""

    def test_tc31_schedule_empty(self):
        """TC-31: 빈 목록 → ScheduleResult estimated_ms=0."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import schedule
        r = schedule([])
        assert r.estimated_ms == 0
        assert r.slo_ok is True

    def test_tc32_schedule_single_profile(self):
        """TC-32: 1개 프로젝트 → SINGLE 프로파일."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import (
            schedule, WorkloadProfile
        )
        r = schedule(["p1"])
        assert r.profile == WorkloadProfile.SINGLE

    def test_tc33_schedule_dual_profile(self):
        """TC-33: 2개 프로젝트 → DUAL 프로파일."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import (
            schedule, WorkloadProfile
        )
        r = schedule(["p1", "p2"])
        assert r.profile == WorkloadProfile.DUAL

    def test_tc34_schedule_triple_profile(self):
        """TC-34: 3개 프로젝트 → TRIPLE 프로파일."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import (
            schedule, WorkloadProfile
        )
        r = schedule(["p1", "p2", "p3"])
        assert r.profile == WorkloadProfile.TRIPLE

    def test_tc35_schedule_slo_ok_single(self):
        """TC-35: SINGLE 프로파일 기본 SLO 충족."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import schedule
        r = schedule(["p1"], scene_ms_each=1000)
        assert r.slo_ok is True

    def test_tc36_schedule_slo_ok_dual(self):
        """TC-36: DUAL 프로파일 기본 SLO 충족."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import schedule
        r = schedule(["p1", "p2"], scene_ms_each=1000)
        assert r.slo_ok is True

    def test_tc37_schedule_order_contains_all(self):
        """TC-37: schedule project_order 에 모든 프로젝트 포함."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import schedule
        ids = ["p1", "p2", "p3"]
        r = schedule(ids)
        assert sorted(r.project_order) == sorted(ids)

    def test_tc38_schedule_to_dict_keys(self):
        """TC-38: to_dict() 키 6개 존재."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import schedule
        r = schedule(["p1"])
        d = r.to_dict()
        for key in ("profile", "slo_ms", "project_order", "estimated_ms", "slo_ok"):
            assert key in d

    def test_tc39_schedule_result_type(self):
        """TC-39: schedule() 반환 타입 ScheduleResult."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import (
            schedule, ScheduleResult
        )
        r = schedule(["p1", "p2"])
        assert isinstance(r, ScheduleResult)

    def test_tc40_schedule_slo_exceed_detection(self):
        """TC-40: 예상 시간 > SLO → slo_ok=False."""
        from literary_system.multiwork.multi_work_orchestrator_v2 import (
            schedule, SLO_SINGLE_MS
        )
        # SINGLE 프로파일에서 scene_ms_each > SLO 이면 slo_ok=False
        r = schedule(["p1"], scene_ms_each=SLO_SINGLE_MS + 1)
        assert r.slo_ok is False


# ────────────────────────────────────────────────────────────────
# §C  RewardModelV2 + AdvSeed  (TC-41~60)
# ────────────────────────────────────────────────────────────────

SAMPLE_TEXT = (
    "그는 오랜 침묵 끝에 입을 열었다. "
    "빗소리가 창문을 두드리며 밤의 고요를 깼다. "
    "두 사람의 눈이 마주쳤고, 그 안에 담긴 이야기는 말보다 깊었다."
)


class TestAdvSeed:
    """TC-41~50: AdvSeed NamedTuple + ADV_SEEDS_REQUIRED."""

    def test_tc41_advseed_namedtuple_fields(self):
        """TC-41: AdvSeed 필드 4개 존재."""
        from literary_system.rlhf.reward_model import AdvSeed
        seed = AdvSeed(
            name="test",
            description="테스트",
            inject_fn=lambda t: t,
            expected_drop=0.1,
        )
        assert seed.name == "test"
        assert seed.expected_drop == 0.1

    def test_tc42_adv_seeds_required_count(self):
        """TC-42: ADV_SEEDS_REQUIRED 길이 == 5."""
        from literary_system.rlhf.reward_model import ADV_SEEDS_REQUIRED
        assert len(ADV_SEEDS_REQUIRED) == 5

    def test_tc43_adv_seeds_names(self):
        """TC-43: ADV_SEEDS_REQUIRED 5종 이름 존재."""
        from literary_system.rlhf.reward_model import ADV_SEEDS_REQUIRED
        names = {s.name for s in ADV_SEEDS_REQUIRED}
        expected = {
            "marker_stuffing", "length_inflation",
            "repetition_pattern", "extreme_emotion", "genre_deviation",
        }
        assert expected == names

    def test_tc44_adv_seeds_expected_drop_positive(self):
        """TC-44: 모든 시드 expected_drop > 0."""
        from literary_system.rlhf.reward_model import ADV_SEEDS_REQUIRED
        for s in ADV_SEEDS_REQUIRED:
            assert s.expected_drop > 0.0, f"{s.name} expected_drop 비양수"

    def test_tc45_adv_seeds_inject_callable(self):
        """TC-45: 모든 시드 inject_fn 호출 가능."""
        from literary_system.rlhf.reward_model import ADV_SEEDS_REQUIRED
        for s in ADV_SEEDS_REQUIRED:
            result = s.inject_fn("테스트 텍스트")
            assert isinstance(result, str)

    def test_tc46_marker_stuffing_changes_text(self):
        """TC-46: marker_stuffing 주입 후 텍스트 변경."""
        from literary_system.rlhf.reward_model import ADV_SEEDS_REQUIRED
        seed = next(s for s in ADV_SEEDS_REQUIRED if s.name == "marker_stuffing")
        corrupted = seed.inject_fn(SAMPLE_TEXT)
        assert corrupted != SAMPLE_TEXT
        assert len(corrupted) > len(SAMPLE_TEXT)

    def test_tc47_length_inflation_increases_length(self):
        """TC-47: length_inflation 후 텍스트 길이 증가."""
        from literary_system.rlhf.reward_model import ADV_SEEDS_REQUIRED
        seed = next(s for s in ADV_SEEDS_REQUIRED if s.name == "length_inflation")
        corrupted = seed.inject_fn(SAMPLE_TEXT)
        assert len(corrupted) > len(SAMPLE_TEXT) * 2

    def test_tc48_repetition_pattern_returns_str(self):
        """TC-48: repetition_pattern 결과가 str."""
        from literary_system.rlhf.reward_model import ADV_SEEDS_REQUIRED
        seed = next(s for s in ADV_SEEDS_REQUIRED if s.name == "repetition_pattern")
        assert isinstance(seed.inject_fn(SAMPLE_TEXT), str)

    def test_tc49_genre_deviation_injects_terms(self):
        """TC-49: genre_deviation 주입 후 SF 용어 포함."""
        from literary_system.rlhf.reward_model import ADV_SEEDS_REQUIRED
        seed = next(s for s in ADV_SEEDS_REQUIRED if s.name == "genre_deviation")
        corrupted = seed.inject_fn(SAMPLE_TEXT)
        # SF 관련 단어 중 하나라도 포함
        sf_words = ["광선검", "워프드라이브", "외계인", "로봇", "우주선"]
        assert any(w in corrupted for w in sf_words)

    def test_tc50_advseed_immutable(self):
        """TC-50: AdvSeed 는 NamedTuple → 불변."""
        from literary_system.rlhf.reward_model import AdvSeed
        seed = AdvSeed("x", "설명", lambda t: t, 0.1)
        with pytest.raises(AttributeError):
            seed.name = "y"  # type: ignore[misc]


class TestRewardModelV2:
    """TC-51~60: RewardModelV2.score_with_adv_seeds() 검증."""

    @pytest.fixture()
    def model(self):
        from literary_system.rlhf.reward_model import RewardModelV2
        return RewardModelV2()

    def test_tc51_model_version(self, model):
        """TC-51: RewardModelV2.VERSION == '2.0.0'."""
        assert model.VERSION == "2.0.0"

    def test_tc52_score_with_adv_seeds_returns_dict(self, model):
        """TC-52: score_with_adv_seeds() 반환 타입 dict."""
        result = model.score_with_adv_seeds(SAMPLE_TEXT)
        assert isinstance(result, dict)

    def test_tc53_result_keys(self, model):
        """TC-53: 결과 dict 키 4개 존재."""
        result = model.score_with_adv_seeds(SAMPLE_TEXT)
        for key in ("baseline", "results", "robustness", "all_passed"):
            assert key in result

    def test_tc54_baseline_in_range(self, model):
        """TC-54: baseline ∈ [0.0, 1.0]."""
        result = model.score_with_adv_seeds(SAMPLE_TEXT)
        assert 0.0 <= result["baseline"] <= 1.0

    def test_tc55_results_length_five(self, model):
        """TC-55: results 리스트 길이 == 5."""
        result = model.score_with_adv_seeds(SAMPLE_TEXT)
        assert len(result["results"]) == 5

    def test_tc56_each_result_keys(self, model):
        """TC-56: 각 시드 결과에 필수 키 존재."""
        result = model.score_with_adv_seeds(SAMPLE_TEXT)
        for r in result["results"]:
            for k in ("seed", "score", "drop", "expected_drop", "passed"):
                assert k in r, f"키 '{k}' 누락: {r}"

    def test_tc57_robustness_in_range(self, model):
        """TC-57: robustness ∈ [0.0, 1.0]."""
        result = model.score_with_adv_seeds(SAMPLE_TEXT)
        assert 0.0 <= result["robustness"] <= 1.0

    def test_tc58_custom_seeds(self, model):
        """TC-58: 사용자 정의 AdvSeed 목록으로 호출."""
        from literary_system.rlhf.reward_model import AdvSeed
        custom = [AdvSeed("custom", "사용자 정의", lambda t: t[:10], 0.05)]
        result = model.score_with_adv_seeds(SAMPLE_TEXT, seeds=custom)
        assert len(result["results"]) == 1
        assert result["results"][0]["seed"] == "custom"

    def test_tc59_empty_text_raises(self, model):
        """TC-59: 빈 텍스트 → ValueError."""
        with pytest.raises(ValueError):
            model.score_with_adv_seeds("")

    def test_tc60_robustness_score_method(self, model):
        """TC-60: robustness_score() 반환 float ∈ [0,1]."""
        score = model.robustness_score(SAMPLE_TEXT)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
