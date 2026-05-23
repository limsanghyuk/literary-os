"""
V610 MultiWorkCIM v2.0 업그레이드 테스트

T01~T06: CIMVersion 열거형
T07~T11: ProjectCIM.to_v2() 마이그레이션
T12~T17: MultiWorkCIM.upgrade_to_v2() 변환
T18~T20: create_multi_work_cim() 팩토리
T21~T22: get_cim_version() 헬퍼 + stats() version 키

ADR-070 | SP-B.3 V610
"""

from __future__ import annotations

import pytest

from literary_system.multiwork.multi_work_cim import (
    CIMEntry,
    CIMVersion,
    MultiWorkCIM,
    ProjectCIM,
    create_multi_work_cim,
    get_cim_version,
)
from literary_system.multiwork.multi_work_cim_v2 import (
    CIMEntryV2,
    MultiWorkCIMV2,
    ProjectCIMV2,
)

# ══════════════════════════════════════════════════════════════════════════════
# T01~T06: CIMVersion 열거형
# ══════════════════════════════════════════════════════════════════════════════


class TestCIMVersion:
    def test_T01_current_returns_v2(self) -> None:
        """T01: CIMVersion.current()은 V2를 반환한다."""
        assert CIMVersion.current() == CIMVersion.V2

    def test_T02_v1_value(self) -> None:
        """T02: CIMVersion.V1 값은 'v1'이다."""
        assert CIMVersion.V1.value == "v1"

    def test_T03_v2_value(self) -> None:
        """T03: CIMVersion.V2 값은 'v2'이다."""
        assert CIMVersion.V2.value == "v2"

    def test_T04_from_str_v1(self) -> None:
        """T04: from_str('v1')은 V1을 반환한다."""
        assert CIMVersion.from_str("v1") == CIMVersion.V1

    def test_T05_from_str_v2(self) -> None:
        """T05: from_str('v2')은 V2를 반환한다."""
        assert CIMVersion.from_str("v2") == CIMVersion.V2

    def test_T06_from_str_unknown_defaults_v2(self) -> None:
        """T06: from_str 알 수 없는 문자열은 V2를 기본값으로 반환한다."""
        assert CIMVersion.from_str("unknown") == CIMVersion.V2


# ══════════════════════════════════════════════════════════════════════════════
# T07~T11: ProjectCIM.to_v2()
# ══════════════════════════════════════════════════════════════════════════════


class TestProjectCIMToV2:
    def _make_project_cim(self) -> ProjectCIM:
        cim = ProjectCIM(project_id="proj_test", decay=0.9)
        cim.record_interaction("A", "B")
        cim.record_interaction("A", "B")
        cim.record_interaction("B", "C")
        return cim

    def test_T07_to_v2_returns_projectcimv2(self) -> None:
        """T07: to_v2()는 ProjectCIMV2 인스턴스를 반환한다."""
        v2 = self._make_project_cim().to_v2()
        assert isinstance(v2, ProjectCIMV2)

    def test_T08_to_v2_preserves_project_id(self) -> None:
        """T08: to_v2() 후 project_id가 보존된다."""
        v2 = self._make_project_cim().to_v2()
        assert v2.project_id == "proj_test"

    def test_T09_to_v2_preserves_weights(self) -> None:
        """T09: to_v2() 후 기존 weight가 보존된다."""
        v1 = self._make_project_cim()
        w_v1 = v1.weight("A", "B")
        v2 = v1.to_v2()
        assert abs(v2.weight("A", "B") - w_v1) < 1e-9

    def test_T10_to_v2_reward_weighted_half(self) -> None:
        """T10: 마이그레이션 기본값 reward_weighted_weight = weight × 0.5."""
        v1 = self._make_project_cim()
        v2 = v1.to_v2()
        for key, entry in v2._entries_v2.items():
            assert isinstance(entry, CIMEntryV2)
            expected = round(entry.weight * 0.5, 6)
            assert abs(entry.reward_weighted_weight - expected) < 1e-9

    def test_T11_to_v2_nondestructive(self) -> None:
        """T11: to_v2()는 비파괴적 — 원본 v1 인스턴스가 변경되지 않는다."""
        v1 = self._make_project_cim()
        orig_count = len(v1.entries)
        orig_weight = v1.weight("A", "B")
        _ = v1.to_v2()
        assert len(v1.entries) == orig_count
        assert abs(v1.weight("A", "B") - orig_weight) < 1e-9


# ══════════════════════════════════════════════════════════════════════════════
# T12~T17: MultiWorkCIM.upgrade_to_v2()
# ══════════════════════════════════════════════════════════════════════════════


class TestMultiWorkCIMUpgradeToV2:
    def _make_v1(self) -> MultiWorkCIM:
        cim = MultiWorkCIM(decay=0.9)
        cim.init_project("p1")
        cim.init_project("p2")
        cim.record("p1", "A", "B")
        cim.record("p1", "A", "B")
        cim.record("p2", "B", "C")
        return cim

    def test_T12_upgrade_returns_multiworkcimv2(self) -> None:
        """T12: upgrade_to_v2()는 MultiWorkCIMV2 인스턴스를 반환한다."""
        v2 = self._make_v1().upgrade_to_v2()
        assert isinstance(v2, MultiWorkCIMV2)

    def test_T13_upgrade_preserves_projects(self) -> None:
        """T13: upgrade_to_v2() 후 프로젝트 목록이 보존된다."""
        v2 = self._make_v1().upgrade_to_v2()
        assert set(v2._project_cims_v2.keys()) == {"p1", "p2"}

    def test_T14_upgrade_preserves_weights(self) -> None:
        """T14: upgrade_to_v2() 후 기존 프로젝트 weight가 유지된다."""
        v1 = self._make_v1()
        w_p1_ab = v1.get_project_cim("p1").weight("A", "B")
        v2 = v1.upgrade_to_v2()
        assert abs(v2.get_project_cim("p1").weight("A", "B") - w_p1_ab) < 1e-9

    def test_T15_upgrade_project_cims_are_v2(self) -> None:
        """T15: upgrade 후 모든 _project_cims 값이 ProjectCIMV2다."""
        v2 = self._make_v1().upgrade_to_v2()
        for pid, cim in v2._project_cims.items():
            assert isinstance(cim, ProjectCIMV2), f"{pid} is not ProjectCIMV2"

    def test_T16_upgrade_global_weight_consistent(self) -> None:
        """T16: upgrade 후 global_weight 결과가 v1과 동일하다."""
        v1 = self._make_v1()
        gw_v1 = v1.global_weight("B", "C")
        v2 = v1.upgrade_to_v2()
        gw_v2 = v2.global_weight("B", "C")
        assert abs(gw_v1 - gw_v2) < 1e-9

    def test_T17_upgrade_nondestructive(self) -> None:
        """T17: upgrade_to_v2()는 원본 v1 인스턴스를 변경하지 않는다."""
        v1 = self._make_v1()
        orig_weight = v1.global_weight("A", "B")
        _ = v1.upgrade_to_v2()
        # v1 여전히 작동
        v1.record("p1", "A", "B")
        assert v1.global_weight("A", "B") > orig_weight


# ══════════════════════════════════════════════════════════════════════════════
# T18~T20: create_multi_work_cim() 팩토리
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateMultiWorkCIM:
    def test_T18_factory_default_returns_v2(self) -> None:
        """T18: create_multi_work_cim() 기본값은 MultiWorkCIMV2를 반환한다."""
        cim = create_multi_work_cim()
        assert isinstance(cim, MultiWorkCIMV2)

    def test_T19_factory_v1_returns_multiworkcim(self) -> None:
        """T19: create_multi_work_cim('v1')은 MultiWorkCIM을 반환한다."""
        cim = create_multi_work_cim("v1")
        assert type(cim) is MultiWorkCIM

    def test_T20_factory_decay_propagated(self) -> None:
        """T20: create_multi_work_cim() decay 파라미터가 전파된다."""
        cim_v2 = create_multi_work_cim("v2", decay=0.85)
        assert cim_v2._decay == 0.85
        cim_v1 = create_multi_work_cim("v1", decay=0.75)
        assert cim_v1._decay == 0.75


# ══════════════════════════════════════════════════════════════════════════════
# T21~T22: get_cim_version() + stats() version 키
# ══════════════════════════════════════════════════════════════════════════════


class TestGetCIMVersion:
    def test_T21_get_version_v1(self) -> None:
        """T21: get_cim_version()은 MultiWorkCIM에 대해 V1을 반환한다."""
        cim = MultiWorkCIM()
        assert get_cim_version(cim) == CIMVersion.V1

    def test_T22_stats_contains_version_key(self) -> None:
        """T22: MultiWorkCIM.stats()에 version 키가 포함된다."""
        cim = MultiWorkCIM()
        s = cim.stats()
        assert "version" in s
        assert s["version"] == "1.0.0"
