"""
test_v609_multi_work_cim_v2.py — V609 MultiWorkCIMV2 단위 테스트 (22 TC)

T01: VERSION 및 타입 확인
T02: v1 init_project / record 호환
T03: record_v2 기본 상호작용 (reward 명시)
T04: record_v2 reward=None → char_db 평균 사용
T05: record_v2 char_db=None → 기본 reward 0.5
T06: reward_weighted_weight 계산 확인
T07: snapshot_project CIMSnapshot 반환
T08: 빈 프로젝트 스냅샷 (entries 0)
T09: restore_project 복원 정확성
T10: 잘못된 snapshot_id → KeyError
T11: 프로젝트 불일치 restore → KeyError
T12: list_project_snapshots 순서 보존
T13: inter_project_cim_score 공유 캐릭터 없음 → cosine=0.0, compatible=True
T14: inter_project_cim_score 단일 공유 캐릭터 (쌍 없음) → compatible=True
T15: inter_project_cim_score 공유 캐릭터 있음 cosine ∈ [0,1]
T16: inter_project_cim_score is_compatible False (큰 차이)
T17: reward_weighted_global_weight 계산
T18: global_weight v1 호환 (reward 없는 경우)
T19: export_state_v2 7-key 구조 확인
T20: export → import_state_v2 라운드트립
T21: import_state_v2 버전 불일치 → ValueError
T22: status_v2 version='2.0.0' 포함
"""

from __future__ import annotations

import pytest

from literary_system.multiwork.multi_work_cim_v2 import (
    CIMEntryV2,
    CIMSnapshot,
    InterProjectCIMScore,
    MultiWorkCIMV2,
    ProjectCIMV2,
)
from literary_system.multiwork.shared_character_db_v2 import SharedCharacterDBV2

# ─────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────

def _make_db_with_rewards(chars_rewards: dict) -> SharedCharacterDBV2:
    """캐릭터와 보상 점수를 가진 SharedCharacterDBV2 생성."""
    db = SharedCharacterDBV2()
    for cid, rewards in chars_rewards.items():
        db.add_character(character_id=cid, name=cid, role="주연")
        for r in rewards:
            db.record_reward(cid, r)
    return db


def _cim_v2(char_db=None, threshold=0.30) -> MultiWorkCIMV2:
    return MultiWorkCIMV2(decay=0.95, char_db=char_db, conflict_threshold=threshold)


# ─────────────────────────────────────────────────────────────────
# T01 ~ T06: 기본 타입 / 기록
# ─────────────────────────────────────────────────────────────────

class TestBasicTypes:
    def test_t01_version_and_type(self):
        cim = _cim_v2()
        assert cim.VERSION == "2.0.0"
        assert isinstance(cim, MultiWorkCIMV2)

    def test_t02_v1_compat_init_record(self):
        cim = _cim_v2()
        cim.init_project("P1")
        # v1 record 호환
        cim.record("P1", "A", "B")
        w = cim.global_weight("A", "B")
        assert w > 0.0

    def test_t03_record_v2_explicit_reward(self):
        cim = _cim_v2()
        cim.init_project("P1")
        cim.record_v2("P1", "A", "B", reward=0.8)
        pcim = cim.get_project_cim_v2("P1")
        assert pcim is not None
        rw = pcim.reward_weight("A", "B")
        assert rw > 0.0

    def test_t04_record_v2_none_reward_uses_char_db(self):
        db = _make_db_with_rewards({"A": [0.9, 0.9], "B": [0.7, 0.7]})
        cim = _cim_v2(char_db=db)
        cim.init_project("P1")
        cim.record_v2("P1", "A", "B", reward=None)  # char_db에서 조회
        pcim = cim.get_project_cim_v2("P1")
        rw = pcim.reward_weight("A", "B")
        assert rw > 0.0

    def test_t05_record_v2_no_char_db_default_reward(self):
        cim = _cim_v2(char_db=None)
        cim.init_project("P1")
        cim.record_v2("P1", "A", "B", reward=None)  # 기본 0.5
        pcim = cim.get_project_cim_v2("P1")
        # reward 0.5이면 reward_weighted_weight = weight * 0.5 > 0
        rw = pcim.reward_weight("A", "B")
        assert rw > 0.0
        # v1 weight보다 작아야 함
        w = pcim.weight("A", "B")
        assert rw < w + 1e-9  # rw ≤ w (reward ≤ 1.0)

    def test_t06_reward_weighted_weight_formula(self):
        """reward_weighted_weight = weight * clamp(reward, 0, 1)"""
        entry = CIMEntryV2(char_a="A", char_b="B")
        entry.update_with_reward(0.95, 0.8)
        assert entry.count == 1
        import math
        expected_w = 1.0 - math.exp(-0.95 * 1)
        expected_rw = expected_w * 0.8
        assert abs(entry.weight - expected_w) < 1e-6
        assert abs(entry.reward_weighted_weight - expected_rw) < 1e-5


# ─────────────────────────────────────────────────────────────────
# T07 ~ T12: 스냅샷
# ─────────────────────────────────────────────────────────────────

class TestSnapshots:
    def test_t07_snapshot_returns_cim_snapshot(self):
        cim = _cim_v2()
        cim.init_project("P1")
        cim.record_v2("P1", "A", "B", reward=0.7)
        snap = cim.snapshot_project("P1", label="after_scene1")
        assert isinstance(snap, CIMSnapshot)
        assert snap.project_id == "P1"
        assert snap.label == "after_scene1"
        assert "entries_v2" in snap.data

    def test_t08_snapshot_empty_project(self):
        cim = _cim_v2()
        cim.init_project("P2")
        snap = cim.snapshot_project("P2")
        assert snap.data["entries"] == {}
        assert snap.data["entries_v2"] == {}

    def test_t09_restore_project(self):
        cim = _cim_v2()
        cim.init_project("P1")
        cim.record_v2("P1", "A", "B", reward=0.9)
        snap = cim.snapshot_project("P1")
        # 추가 기록
        cim.record_v2("P1", "A", "C", reward=0.5)
        # 복원
        cim.restore_project("P1", snap.snapshot_id)
        pcim = cim.get_project_cim_v2("P1")
        # 복원 후 A-C 상호작용 없어야 함
        assert pcim.weight("A", "C") == 0.0
        # A-B는 복원되어야 함
        assert pcim.weight("A", "B") > 0.0

    def test_t10_restore_invalid_snapshot_id(self):
        cim = _cim_v2()
        cim.init_project("P1")
        with pytest.raises(KeyError, match="Snapshot not found"):
            cim.restore_project("P1", "nonexistent-snap-id")

    def test_t11_restore_wrong_project_id(self):
        cim = _cim_v2()
        cim.init_project("P1")
        cim.init_project("P2")
        snap = cim.snapshot_project("P1")
        with pytest.raises(KeyError):
            cim.restore_project("P2", snap.snapshot_id)  # P1 스냅샷을 P2에 복원

    def test_t12_list_snapshots_order(self):
        cim = _cim_v2()
        cim.init_project("P1")
        snap1 = cim.snapshot_project("P1", label="s1")
        cim.record_v2("P1", "A", "B", reward=0.5)
        snap2 = cim.snapshot_project("P1", label="s2")
        snaps = cim.list_project_snapshots("P1")
        assert len(snaps) == 2
        assert snaps[0].snapshot_id == snap1.snapshot_id
        assert snaps[1].snapshot_id == snap2.snapshot_id


# ─────────────────────────────────────────────────────────────────
# T13 ~ T16: InterProjectCIMScore
# ─────────────────────────────────────────────────────────────────

class TestInterProjectScore:
    def test_t13_no_shared_chars(self):
        cim = _cim_v2()
        cim.init_project("PA")
        cim.init_project("PB")
        score = cim.inter_project_cim_score("PA", "PB", shared_chars=[])
        assert score.cosine_similarity == 0.0
        assert score.is_compatible is True

    def test_t14_single_shared_char_no_pairs(self):
        """공유 캐릭터 1명이면 쌍이 없으므로 cosine=1.0, compatible=True."""
        cim = _cim_v2()
        cim.init_project("PA")
        cim.init_project("PB")
        score = cim.inter_project_cim_score("PA", "PB", shared_chars=["A"])
        assert score.is_compatible is True

    def test_t15_cosine_similarity_range(self):
        cim = _cim_v2()
        cim.init_project("PA")
        cim.init_project("PB")
        for _ in range(3):
            cim.record_v2("PA", "A", "B", reward=0.8)
        for _ in range(3):
            cim.record_v2("PB", "A", "B", reward=0.7)
        score = cim.inter_project_cim_score("PA", "PB", shared_chars=["A", "B"])
        assert 0.0 <= score.cosine_similarity <= 1.0
        assert score.weight_delta_max >= 0.0

    def test_t16_incompatible_projects(self):
        """PA에 많은 상호작용, PB에 없으면 delta_max > threshold → 비호환."""
        cim = _cim_v2(threshold=0.30)
        cim.init_project("PA")
        cim.init_project("PB")
        # PA: 많은 상호작용
        for _ in range(20):
            cim.record_v2("PA", "A", "B", reward=0.9)
        # PB: 상호작용 없음 → weight=0
        score = cim.inter_project_cim_score("PA", "PB", shared_chars=["A", "B"])
        assert score.weight_delta_max > 0.30
        assert score.is_compatible is False


# ─────────────────────────────────────────────────────────────────
# T17 ~ T18: 전역 집계
# ─────────────────────────────────────────────────────────────────

class TestGlobalAggregation:
    def test_t17_reward_weighted_global_weight(self):
        cim = _cim_v2()
        cim.init_project("PA")
        cim.init_project("PB")
        cim.record_v2("PA", "A", "B", reward=1.0)
        cim.record_v2("PB", "A", "B", reward=0.0)  # reward=0 → rw=0
        rw = cim.reward_weighted_global_weight("A", "B")
        # PA는 rw>0, PB는 rw=0 → active=[rw_PA] → mean=rw_PA
        pa_cim = cim.get_project_cim_v2("PA")
        assert rw == pa_cim.reward_weight("A", "B")

    def test_t18_global_weight_v1_compat(self):
        cim = _cim_v2()
        cim.init_project("PA")
        cim.record("PA", "X", "Y")
        cim.record("PA", "X", "Y")
        w = cim.global_weight("X", "Y")
        assert w > 0.0


# ─────────────────────────────────────────────────────────────────
# T19 ~ T22: 직렬화 / 통계
# ─────────────────────────────────────────────────────────────────

class TestSerializationAndStats:
    def test_t19_export_state_v2_keys(self):
        cim = _cim_v2()
        cim.init_project("P1")
        cim.record_v2("P1", "A", "B", reward=0.6)
        state = cim.export_state_v2()
        required_keys = {
            "version", "exported_at", "decay",
            "conflict_threshold", "project_cims",
            "snapshots", "total_interactions",
        }
        assert required_keys == set(state.keys())
        assert state["version"] == "2.0.0"
        assert state["total_interactions"] == 1

    def test_t20_export_import_roundtrip(self):
        cim = _cim_v2()
        cim.init_project("PA")
        cim.init_project("PB")
        cim.record_v2("PA", "A", "B", reward=0.7)
        cim.record_v2("PB", "C", "D", reward=0.5)
        snap = cim.snapshot_project("PA", label="before")
        state = cim.export_state_v2()

        cim2 = _cim_v2()
        cim2.import_state_v2(state)
        assert cim2.get_project_cim_v2("PA") is not None
        assert cim2.get_project_cim_v2("PB") is not None
        pa_cim = cim2.get_project_cim_v2("PA")
        assert pa_cim.weight("A", "B") > 0.0
        # 스냅샷 복원
        snaps = cim2.list_project_snapshots("PA")
        assert len(snaps) == 1
        assert snaps[0].snapshot_id == snap.snapshot_id

    def test_t21_import_version_mismatch(self):
        cim = _cim_v2()
        state = cim.export_state_v2()
        state["version"] = "1.0.0"
        cim2 = _cim_v2()
        with pytest.raises(ValueError, match="Version mismatch"):
            cim2.import_state_v2(state)

    def test_t22_status_v2_fields(self):
        cim = _cim_v2()
        cim.init_project("P1")
        cim.record_v2("P1", "A", "B", reward=0.5)
        cim.snapshot_project("P1")
        st = cim.status_v2()
        assert st["version"] == "2.0.0"
        assert st["has_char_db"] is False
        assert "per_project_snapshots" in st
        assert st["per_project_snapshots"]["P1"] == 1
        assert "per_project_reward_pairs" in st
        assert st["per_project_reward_pairs"]["P1"] == 1
