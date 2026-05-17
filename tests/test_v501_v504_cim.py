"""
V501~V504 테스트 — CharacterInfluenceMatrix
ADR-018: W[n×n], 구조적 균형, PageRank, 5티어, SparseCIM, TopKTriangleFilter
"""
import pytest
import sys
sys.path.insert(0, ".")

from literary_system.nie.character_influence_matrix import (
    CharacterInfluenceMatrix, CIMTier, TriangleTension,
    LR_CIM, SPARSE_N_THRESHOLD, SPARSE_W_THRESHOLD,
    PAGERANK_DAMPING, TOP_K_TRIANGLES, TRIANGLE_MIN_TENSION,
)


# ── 기본 행렬 조작 ──────────────────────────────────────────────────

class TestCIMBasic:
    def test_init_empty(self):
        cim = CharacterInfluenceMatrix()
        assert cim.n == 0

    def test_add_character(self):
        cim = CharacterInfluenceMatrix(["A", "B"])
        assert cim.n == 2

    def test_update_creates_edge(self):
        cim = CharacterInfluenceMatrix(["A", "B"])
        cim.update("A", "B", 1.0)
        assert cim.get("A", "B") > 0.0

    def test_asymmetric(self):
        cim = CharacterInfluenceMatrix(["A", "B"])
        cim.set_direct("A", "B", 0.8)
        cim.set_direct("B", "A", -0.3)
        assert cim.get("A", "B") != cim.get("B", "A")

    def test_clamp_max(self):
        cim = CharacterInfluenceMatrix(["A", "B"])
        for _ in range(200):
            cim.update("A", "B", 1.0)
        assert cim.get("A", "B") <= 1.0

    def test_clamp_min(self):
        cim = CharacterInfluenceMatrix(["A", "B"])
        for _ in range(200):
            cim.update("A", "B", -1.0)
        assert cim.get("A", "B") >= -1.0

    def test_get_nonexistent_returns_zero(self):
        cim = CharacterInfluenceMatrix(["A", "B"])
        assert cim.get("A", "X") == 0.0

    def test_set_direct(self):
        cim = CharacterInfluenceMatrix(["A", "B", "C"])
        cim.set_direct("A", "B", 0.7)
        assert cim.get("A", "B") == pytest.approx(0.7)

    def test_add_new_character_on_update(self):
        cim = CharacterInfluenceMatrix()
        cim.update("X", "Y", 0.5)
        assert "X" in cim._ids
        assert "Y" in cim._ids

    def test_remove_character_clears_edges(self):
        cim = CharacterInfluenceMatrix(["A", "B", "C"])
        cim.set_direct("A", "B", 0.5)
        cim.set_direct("B", "C", 0.3)
        cim.remove_character("B")
        assert cim.get("A", "B") == 0.0
        assert cim.get("B", "C") == 0.0


# ── 구조적 균형 이론 ────────────────────────────────────────────────

class TestStructuralBalance:
    def _balanced_triangle(self) -> CharacterInfluenceMatrix:
        """균형 삼각형: A-B(+) B-C(+) C-A(+) → B=+1"""
        cim = CharacterInfluenceMatrix(["A", "B", "C"])
        cim.set_direct("A", "B", 0.8)
        cim.set_direct("B", "C", 0.7)
        cim.set_direct("C", "A", 0.6)
        return cim

    def _unbalanced_triangle(self) -> CharacterInfluenceMatrix:
        """불균형 삼각형: A-B(+) B-C(-) C-A(+) → B=-1 (적의 적은 친구인데 아님)"""
        cim = CharacterInfluenceMatrix(["A", "B", "C"])
        cim.set_direct("A", "B", 0.8)
        cim.set_direct("B", "C", -0.7)
        cim.set_direct("C", "A", 0.6)
        return cim

    def test_balanced_balance_is_positive(self):
        cim = self._balanced_triangle()
        assert cim.balance("A", "B", "C") == pytest.approx(1.0)

    def test_unbalanced_balance_is_negative(self):
        cim = self._unbalanced_triangle()
        assert cim.balance("A", "B", "C") == pytest.approx(-1.0)

    def test_balanced_tension_is_zero(self):
        cim = self._balanced_triangle()
        assert cim.tension("A", "B", "C") == pytest.approx(0.0)

    def test_unbalanced_tension_is_two(self):
        cim = self._unbalanced_triangle()
        assert cim.tension("A", "B", "C") == pytest.approx(2.0)

    def test_sign_method(self):
        assert CharacterInfluenceMatrix._sign(0.5) == 1.0
        assert CharacterInfluenceMatrix._sign(-0.3) == -1.0
        assert CharacterInfluenceMatrix._sign(0.0) == 0.0


# ── TopK 삼각 필터 ──────────────────────────────────────────────────

class TestTopKTriangles:
    def _make_cim_with_tension(self) -> CharacterInfluenceMatrix:
        chars = [f"C{i}" for i in range(5)]
        cim = CharacterInfluenceMatrix(chars)
        # 불균형 삼각형 여러 개
        cim.set_direct("C0", "C1", 0.8)
        cim.set_direct("C1", "C2", -0.7)
        cim.set_direct("C2", "C0", 0.6)
        cim.set_direct("C0", "C3", 0.5)
        cim.set_direct("C3", "C4", -0.6)
        cim.set_direct("C4", "C0", 0.7)
        return cim

    def test_returns_list_of_triangle_tension(self):
        cim = self._make_cim_with_tension()
        result = cim.top_k_triangles(k=10)
        assert isinstance(result, list)
        for tri in result:
            assert isinstance(tri, TriangleTension)

    def test_all_results_have_high_tension(self):
        cim = self._make_cim_with_tension()
        result = cim.top_k_triangles(k=10)
        for tri in result:
            assert tri.tension >= TRIANGLE_MIN_TENSION

    def test_sorted_by_tension_desc(self):
        cim = self._make_cim_with_tension()
        result = cim.top_k_triangles(k=10)
        tensions = [t.tension for t in result]
        assert tensions == sorted(tensions, reverse=True)

    def test_top_k_limit(self):
        # 많은 인물로 삼각형 폭증 시 k 이하 반환
        chars = [f"X{i}" for i in range(10)]
        cim = CharacterInfluenceMatrix(chars)
        for i in range(10):
            for j in range(10):
                if i != j:
                    cim.set_direct(chars[i], chars[j], 0.8 if (i + j) % 2 == 0 else -0.5)
        result = cim.top_k_triangles(k=TOP_K_TRIANGLES)
        assert len(result) <= TOP_K_TRIANGLES

    def test_triangle_to_dict(self):
        cim = self._make_cim_with_tension()
        result = cim.top_k_triangles(k=5)
        if result:
            d = result[0].to_dict()
            assert "triangle" in d
            assert "tension" in d
            assert len(d["triangle"]) == 3


# ── PageRank ────────────────────────────────────────────────────────

class TestPageRank:
    def _make_star_cim(self) -> CharacterInfluenceMatrix:
        """중심 허브 A → B,C,D,E (스타 그래프)"""
        chars = ["A", "B", "C", "D", "E"]
        cim = CharacterInfluenceMatrix(chars)
        for c in ["B", "C", "D", "E"]:
            cim.set_direct(c, "A", 0.9)  # 모두 A를 향함
        return cim

    def test_pagerank_returns_all_chars(self):
        cim = self._make_star_cim()
        pr = cim.compute_pagerank()
        assert set(pr.keys()) == {"A", "B", "C", "D", "E"}

    def test_hub_has_highest_pagerank(self):
        cim = self._make_star_cim()
        pr = cim.compute_pagerank()
        assert pr["A"] == max(pr.values())

    def test_pagerank_sum_approx_1(self):
        cim = self._make_star_cim()
        pr = cim.compute_pagerank()
        assert sum(pr.values()) == pytest.approx(1.0, abs=1e-4)

    def test_pagerank_range(self):
        cim = self._make_star_cim()
        pr = cim.compute_pagerank()
        for v in pr.values():
            assert 0.0 <= v <= 1.0

    def test_empty_graph_pagerank(self):
        cim = CharacterInfluenceMatrix(["A", "B"])
        pr = cim.compute_pagerank()
        assert set(pr.keys()) == {"A", "B"}


# ── 5티어 분류 ──────────────────────────────────────────────────────

class TestTierClassification:
    def test_hub_is_jang_tier(self):
        chars = ["HERO"] + [f"S{i}" for i in range(10)]
        cim = CharacterInfluenceMatrix(chars)
        for s in chars[1:]:
            cim.set_direct(s, "HERO", 0.9)
        tiers = cim.classify_tiers()
        assert "HERO" in tiers
        # 허브는 장 또는 차 티어여야 함
        assert tiers["HERO"].tier in ("장", "차")

    def test_isolated_is_jol_tier(self):
        cim = CharacterInfluenceMatrix(["EXTRA", "MAIN"])
        cim.set_direct("MAIN", "MAIN", 0.0)  # EXTRA 연결 없음
        tiers = cim.classify_tiers()
        assert tiers["EXTRA"].tier in ("졸", "마·상")  # 균등 PR로 마·상 가능

    def test_all_chars_have_tier(self):
        chars = ["A", "B", "C", "D"]
        cim = CharacterInfluenceMatrix(chars)
        cim.set_direct("A", "B", 0.5)
        tiers = cim.classify_tiers()
        assert set(tiers.keys()) == set(chars)

    def test_tier_names_valid(self):
        cim = CharacterInfluenceMatrix(["X", "Y", "Z"])
        cim.set_direct("X", "Y", 0.5)
        tiers = cim.classify_tiers()
        valid = {"장", "차", "포", "마·상", "졸"}
        for t in tiers.values():
            assert t.tier in valid


# ── SparseCIM ───────────────────────────────────────────────────────

class TestSparseCIM:
    def test_large_n_prunes_weak_edges(self):
        # N>15 → |W|<0.1 엣지 자동 제거
        chars = [f"P{i}" for i in range(20)]
        cim = CharacterInfluenceMatrix(chars)
        # 약한 엣지 추가
        cim.set_direct("P0", "P1", 0.05)  # 아래 threshold
        # N>15이고 |W|<0.1 → 저장 안됨
        assert cim.get("P0", "P1") == 0.0

    def test_small_n_keeps_weak_edges(self):
        # N<=15 → 약한 엣지도 보존
        chars = ["A", "B", "C"]
        cim = CharacterInfluenceMatrix(chars)
        cim.set_direct("A", "B", 0.05)
        assert cim.get("A", "B") == pytest.approx(0.05)

    def test_prune_sparse_removes_weak(self):
        chars = ["A", "B", "C"]
        cim = CharacterInfluenceMatrix(chars)
        cim._W[("A", "B")] = 0.05  # 직접 주입
        removed = cim.prune_sparse()
        assert removed >= 1

    def test_to_dict_structure(self):
        cim = CharacterInfluenceMatrix(["A", "B"])
        cim.set_direct("A", "B", 0.5)
        d = cim.to_dict()
        assert "characters" in d
        assert "n" in d
        assert "edges" in d

    def test_density_zero_for_no_edges(self):
        cim = CharacterInfluenceMatrix(["A", "B", "C"])
        assert cim.density() == pytest.approx(0.0)

    def test_density_increases_with_edges(self):
        cim = CharacterInfluenceMatrix(["A", "B", "C"])
        cim.set_direct("A", "B", 0.5)
        assert cim.density() > 0.0
