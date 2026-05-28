"""
tests/unit/test_v682_revenue_contiguous.py
==========================================
V682: TD-2 is_contiguous() + calculate_tiered() 테스트 (ADR-144)
TC-01 ~ TC-20
"""
from __future__ import annotations
import pytest
from literary_system.enterprise.revenue import (
    RevenueCalculator, RevenueTier, PartnerRevenueContract, RevenueModel
)

def _make_contract(tiers):
    return PartnerRevenueContract('c1','p1','P',RevenueModel.TIERED,tiers=tiers)

TIERS_OK = [RevenueTier(0,100,0.1), RevenueTier(100,500,0.15), RevenueTier(500,-1,0.2)]
TIERS_GAP = [RevenueTier(0,100,0.1), RevenueTier(200,500,0.15)]
TIERS_OVERLAP = [RevenueTier(0,150,0.1), RevenueTier(100,500,0.15)]

class TestIsContiguous:
    def test_contiguous_true(self):
        """TC-01: 연속 티어 → True."""
        assert RevenueCalculator.is_contiguous(TIERS_OK) is True
    def test_gap_false(self):
        """TC-02: 공백 구간 → False."""
        assert RevenueCalculator.is_contiguous(TIERS_GAP) is False
    def test_empty_true(self):
        """TC-03: 빈 리스트 → True."""
        assert RevenueCalculator.is_contiguous([]) is True
    def test_single_true(self):
        """TC-04: 단일 티어 → True."""
        assert RevenueCalculator.is_contiguous([RevenueTier(0,100,0.1)]) is True
    def test_overlap_false(self):
        """TC-05: 겹침 구간 → False (max≠next.min)."""
        assert RevenueCalculator.is_contiguous(TIERS_OVERLAP) is False
    def test_two_contiguous(self):
        """TC-06: 2-티어 연속."""
        assert RevenueCalculator.is_contiguous([RevenueTier(0,100,0.1), RevenueTier(100,-1,0.2)]) is True
    def test_unsorted_contiguous(self):
        """TC-07: 역순 입력도 정렬 후 검증."""
        tiers_rev = [RevenueTier(100,500,0.15), RevenueTier(0,100,0.1)]
        assert RevenueCalculator.is_contiguous(tiers_rev) is True

class TestCalculateTiered:
    def test_300_equals_40(self):
        """TC-08: 300 → 10+30=40."""
        v = RevenueCalculator.calculate_tiered(_make_contract(TIERS_OK), 300.0)
        assert abs(v - 40.0) < 0.01
    def test_600_equals_90(self):
        """TC-09: 600 → 10+60+20=90."""
        v = RevenueCalculator.calculate_tiered(_make_contract(TIERS_OK), 600.0)
        assert abs(v - 90.0) < 0.01
    def test_zero_revenue(self):
        """TC-10: 매출 0 → 분배금 0."""
        v = RevenueCalculator.calculate_tiered(_make_contract(TIERS_OK), 0.0)
        assert v == 0.0
    def test_noncont_raises_valueerror(self):
        """TC-11: 비연속 티어 → ValueError."""
        with pytest.raises(ValueError, match="Non-contiguous"):
            RevenueCalculator.calculate_tiered(_make_contract(TIERS_GAP), 300.0)
    def test_empty_tiers_returns_zero(self):
        """TC-12: 빈 티어 → 0."""
        v = RevenueCalculator.calculate_tiered(_make_contract([]), 300.0)
        assert v == 0.0
    def test_exactly_at_boundary(self):
        """TC-13: 경계값 100.0."""
        v = RevenueCalculator.calculate_tiered(_make_contract(TIERS_OK), 100.0)
        assert abs(v - 10.0) < 0.001  # 100*0.1=10
    def test_infinite_last_tier(self):
        """TC-14: max=-1(unlimited) 마지막 티어."""
        tiers = [RevenueTier(0,100,0.1), RevenueTier(100,-1,0.5)]
        v = RevenueCalculator.calculate_tiered(_make_contract(tiers), 600.0)
        assert abs(v - (10.0 + 500*0.5)) < 0.01

class TestCalculatePartnerShareTiered:
    def test_tiered_delegates_to_calculate_tiered(self):
        """TC-15: calculate_partner_share TIERED → calculate_tiered 위임."""
        v = RevenueCalculator.calculate_partner_share(_make_contract(TIERS_OK), 300.0)
        assert abs(v - 40.0) < 0.01
    def test_noncont_raises_in_partner_share(self):
        """TC-16: 비연속 티어 → ValueError (partner_share 경유)."""
        with pytest.raises(ValueError):
            RevenueCalculator.calculate_partner_share(_make_contract(TIERS_GAP), 300.0)

class TestErrorMessage:
    def test_valueerror_contains_contract_id(self):
        """TC-17: ValueError 메시지에 contract_id 포함."""
        try:
            RevenueCalculator.calculate_tiered(_make_contract(TIERS_GAP), 100.0)
        except ValueError as e:
            assert 'c1' in str(e)
    def test_valueerror_contains_tier_ranges(self):
        """TC-18: ValueError 메시지에 티어 범위 포함."""
        try:
            RevenueCalculator.calculate_tiered(_make_contract(TIERS_GAP), 100.0)
        except ValueError as e:
            assert '100' in str(e) or '200' in str(e)

class TestBoundaryValues:
    def test_very_small_revenue(self):
        """TC-19: 매우 소액 0.01."""
        v = RevenueCalculator.calculate_tiered(_make_contract(TIERS_OK), 0.01)
        assert 0.0 <= v <= 0.01
    def test_large_revenue(self):
        """TC-20: 대용량 1M."""
        tiers_large = [RevenueTier(0,1000,0.1), RevenueTier(1000,-1,0.05)]
        v = RevenueCalculator.calculate_tiered(_make_contract(tiers_large), 1_000_000.0)
        expected = 1000*0.1 + 999_000*0.05
        assert abs(v - expected) < 0.01
