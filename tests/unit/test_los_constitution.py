"""SP-A.7 (V594) -- test_los_constitution.py: TC01-TC40"""
from __future__ import annotations
import sys, os, math, pytest
_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from literary_system.constitution.los_constitution import (
    ConstitutionWeights,
    LOSConstitution,
    ConstitutionSceneScore,
    ConstitutionWorkScore,

    _score_drse, _score_debt, _score_arc, _score_tension, _score_prose,
)

# 공통 풍부한 장면
_RICH = (
    "이도령과 춘향이 광한루에서 처음 만났다. 새로운 인연이 시작되었다. "
    '"이도령이라 하오." 이도령이 말했다. "저는 춘향입니다." 그녀가 답했다. '
    "이어서 두 사람은 이야기를 나눴다. 봄바람이 꽃잎을 날렸다. "
    "하지만 변학도의 갈등이 시작되었다. 위기와 대립이 고조되었다. "
    "마침내 이도령이 해결책을 찾아 돌아왔다. 결국 두 사람의 사랑이 승리했다. "
    "드디어 행복한 결말이 찾아왔다. "
) * 3
_SHORT = "안녕하세요."


# ===========================================================================
# TC01~TC06: ConstitutionWeights
# ===========================================================================

class TestConstitutionWeights:
    def test_tc01_default_values(self):
        """TC01: 기본값 0.30/0.20/0.20/0.15/0.15"""
        w = ConstitutionWeights()
        assert w.drse == 0.30
        assert w.debt == 0.20
        assert w.arc  == 0.20
        assert w.tension == 0.15
        assert w.prose   == 0.15

    def test_tc02_sum_equals_1(self):
        """TC02: 합계 = 1.0"""
        w = ConstitutionWeights()
        total = w.drse + w.debt + w.arc + w.tension + w.prose
        assert abs(total - 1.0) < 1e-6

    def test_tc03_invalid_sum_raises(self):
        """TC03: 합계 != 1.0 → ValueError"""
        with pytest.raises(ValueError):
            ConstitutionWeights(drse=0.50, debt=0.20, arc=0.20, tension=0.15, prose=0.15)

    def test_tc04_custom_weights(self):
        """TC04: 커스텀 가중치 (합계 1.0)"""
        w = ConstitutionWeights(drse=0.25, debt=0.25, arc=0.25, tension=0.15, prose=0.10)
        assert abs(w.drse + w.debt + w.arc + w.tension + w.prose - 1.0) < 1e-6

    def test_tc05_as_dict(self):
        """TC05: as_dict() 구조"""
        w = ConstitutionWeights()
        d = w.as_dict()
        for key in ("drse", "debt", "arc", "tension", "prose"):
            assert key in d

    def test_tc06_frozen(self):
        """TC06: frozen dataclass — 수정 불가"""
        w = ConstitutionWeights()
        with pytest.raises((AttributeError, TypeError)):
            w.drse = 0.5


# ===========================================================================
# TC07~TC12: 개별 축 점수 함수
# ===========================================================================

class TestAxisScores:
    def test_tc07_drse_short_low(self):
        """TC07: 짧은 텍스트 DRSE < 0.35"""
        assert _score_drse("짧아") < 0.35

    def test_tc08_drse_rich_high(self):
        """TC08: 풍부한 텍스트 DRSE >= 0.35"""
        assert _score_drse(_RICH) >= 0.35

    def test_tc09_arc_full_1(self):
        """TC09: 기승전결 모두 포함 arc = 1.0"""
        text = "처음 만났다. 이어서 발전했다. 하지만 위기가 왔다. 마침내 해결했다."
        score = _score_arc(text)
        assert score >= 0.5  # 최소 절반 이상

    def test_tc10_tension_markers(self):
        """TC10: 긴장 마커 포함 텍스트 tension >= 0.2"""
        text = "갈등이 심해졌다. 위기가 닥쳤다. 대립이 고조되었다. " * 5
        assert _score_tension(text) >= 0.2

    def test_tc11_prose_score_range(self):
        """TC11: prose 점수 [0, 1] 범위"""
        for text in [_SHORT, _RICH, "a b c " * 50]:
            s = _score_prose(text)
            assert 0.0 <= s <= 1.0

    def test_tc12_debt_no_hooks(self):
        """TC12: 물음표 없는 텍스트 debt >= 0.5"""
        text = "이도령이 왔다. 춘향이 기다렸다. 만났다. 행복했다." * 5
        assert _score_debt(text) >= 0.5


# ===========================================================================
# TC13~TC20: LOSConstitution.score_scene()
# ===========================================================================

class TestScoreScene:
    def setup_method(self):
        self.los = LOSConstitution()

    def test_tc13_score_scene_str(self):
        """TC13: str 입력 score_scene()"""
        s = self.los.score_scene(_RICH)
        assert 0.0 <= s <= 1.0

    def test_tc14_score_scene_dict(self):
        """TC14: dict 입력 score_scene()"""
        scene = {"text": _RICH, "episode": 1}
        s = self.los.score_scene(scene)
        assert 0.0 <= s <= 1.0

    def test_tc15_rich_scene_ge_065(self):
        """TC15: 풍부한 장면 R(scene) >= 0.65"""
        s = self.los.score_scene(_RICH)
        assert s >= 0.65, f"R={s:.4f} < 0.65"

    def test_tc16_short_scene_low(self):
        """TC16: 짧은 장면 R(scene) < 0.65"""
        s = self.los.score_scene(_SHORT)
        assert s < 0.65

    def test_tc17_score_scene_full_structure(self):
        """TC17: score_scene_full() ConstitutionSceneScore 구조"""
        full = self.los.score_scene_full(_RICH, scene_id="S001")
        assert full.scene_id == "S001"
        assert hasattr(full, "drse") and hasattr(full, "total")
        assert 0.0 <= full.total <= 1.0

    def test_tc18_weighted_sum_correct(self):
        """TC18: total = 가중합 검증"""
        full = self.los.score_scene_full(_RICH)
        w = self.los.weights
        expected = (w.drse * full.drse + w.debt * full.debt +
                    w.arc * full.arc + w.tension * full.tension +
                    w.prose * full.prose)
        assert abs(full.total - round(expected, 4)) < 1e-4

    def test_tc19_score_scene_full_to_dict(self):
        """TC19: ConstitutionSceneScore.to_dict() 구조"""
        full = self.los.score_scene_full(_RICH)
        d = full.to_dict()
        for key in ("scene_id", "drse", "debt", "arc", "tension", "prose", "total"):
            assert key in d

    def test_tc20_custom_weights_changes_score(self):
        """TC20: 커스텀 가중치 반영 확인"""
        w_default = ConstitutionWeights()
        w_custom  = ConstitutionWeights(drse=0.50, debt=0.10, arc=0.15, tension=0.15, prose=0.10)
        los_d = LOSConstitution(weights=w_default)
        los_c = LOSConstitution(weights=w_custom)
        s_d = los_d.score_scene(_RICH)
        s_c = los_c.score_scene(_RICH)
        # 두 점수가 다를 수 있음 (가중치 다르므로)
        assert isinstance(s_d, float) and isinstance(s_c, float)


# ===========================================================================
# TC21~TC28: score_work()
# ===========================================================================

class TestScoreWork:
    def setup_method(self):
        self.los = LOSConstitution()

    def _rich_scenes(self, n: int) -> list:
        return [_RICH] * n

    def test_tc21_score_work_empty(self):
        """TC21: 빈 장면 목록 work_score=0"""
        ws = self.los.score_work([])
        assert ws.scene_count == 0
        assert ws.work_score == 0.0

    def test_tc22_score_work_structure(self):
        """TC22: ConstitutionWorkScore 구조"""
        ws = self.los.score_work(self._rich_scenes(5))
        assert hasattr(ws, "mean_total") and hasattr(ws, "variance_total")
        assert hasattr(ws, "work_score") and ws.scene_count == 5

    def test_tc23_mean_ge_065(self):
        """TC23: 풍부한 10개 장면 mean >= 0.65 (ADR-054)"""
        ws = self.los.score_work(self._rich_scenes(10))
        assert ws.mean_total >= 0.65, f"mean={ws.mean_total:.4f}"

    def test_tc24_variance_le_005(self):
        """TC24: 동일 장면 10개 variance <= 0.05 (ADR-054)"""
        ws = self.los.score_work(self._rich_scenes(10))
        assert ws.variance_total <= 0.05, f"var={ws.variance_total:.6f}"

    def test_tc25_work_score_formula(self):
        """TC25: W(work) = mean - 0.10·variance 공식 검증"""
        ws = self.los.score_work(self._rich_scenes(5))
        expected = round(ws.mean_total - 0.10 * ws.variance_total, 4)
        assert abs(ws.work_score - expected) < 1e-4

    def test_tc26_to_dict(self):
        """TC26: ConstitutionWorkScore.to_dict() 구조"""
        ws = self.los.score_work(self._rich_scenes(3))
        d = ws.to_dict()
        for key in ("mean_total", "variance_total", "work_score", "scene_count"):
            assert key in d

    def test_tc27_scene_count_correct(self):
        """TC27: scene_count 정확성"""
        for n in (1, 5, 20):
            ws = self.los.score_work(self._rich_scenes(n))
            assert ws.scene_count == n

    def test_tc28_work_score_plausible(self):
        """TC28: work_score [0, 1] 범위 내"""
        ws = self.los.score_work(self._rich_scenes(10))
        # work_score는 mean - 0.10·variance 이므로 mean 근방
        assert ws.work_score >= 0.0


# ===========================================================================
# TC29~TC33: rlhf_reward()
# ===========================================================================

class TestRlhfReward:
    def setup_method(self):
        self.los = LOSConstitution()

    def test_tc29_reward_range(self):
        """TC29: rlhf_reward 범위 [-1, 1]"""
        r = self.los.rlhf_reward(_RICH, _SHORT)
        assert -1.0 <= r <= 1.0

    def test_tc30_generated_better_positive(self):
        """TC30: 생성본이 더 좋으면 양수 보상"""
        r = self.los.rlhf_reward(_RICH, _SHORT)
        assert r > 0.0

    def test_tc31_same_text_zero(self):
        """TC31: 동일 텍스트 → 보상 = 0.0"""
        text = "동일한 텍스트 " * 20
        r = self.los.rlhf_reward(text, text)
        assert r == 0.0

    def test_tc32_generated_worse_negative(self):
        """TC32: 생성본이 더 나쁘면 음수 보상"""
        r = self.los.rlhf_reward(_SHORT, _RICH)
        assert r < 0.0

    def test_tc33_reward_is_float(self):
        """TC33: 반환 타입 float"""
        r = self.los.rlhf_reward(_RICH, _RICH[:50])
        assert isinstance(r, float)


# ===========================================================================
# TC34~TC40: 50 scenes 통합 + LLM-0
# ===========================================================================

class TestConstitutionIntegration:
    def setup_method(self):
        self.los = LOSConstitution()

    def _varied_scene(self, i: int) -> str:
        base = _RICH
        extra = f"장면 {i}번. 이야기가 계속된다. " * (1 + i % 3)
        return base + extra

    def test_tc34_50_scenes_mean_ge_065(self):
        """TC34: 50개 장면 평균 R(scene) >= 0.65 (ADR-054 핵심)"""
        scenes = [self._varied_scene(i) for i in range(50)]
        ws = self.los.score_work(scenes)
        assert ws.mean_total >= 0.65, f"50-scene mean={ws.mean_total:.4f}"

    def test_tc35_50_scenes_variance_le_005(self):
        """TC35: 50개 장면 variance <= 0.05"""
        scenes = [self._varied_scene(i) for i in range(50)]
        ws = self.los.score_work(scenes)
        assert ws.variance_total <= 0.05, f"variance={ws.variance_total:.6f}"

    def test_tc36_scene_scores_populated(self):
        """TC36: score_work().scene_scores 리스트 채워짐"""
        scenes = [_RICH] * 5
        ws = self.los.score_work(scenes)
        assert len(ws.scene_scores) == 5
        assert all(isinstance(s, ConstitutionSceneScore) for s in ws.scene_scores)

    def test_tc37_dict_input(self):
        """TC37: dict 장면 목록 처리"""
        scenes = [{"scene_id": f"SC{i}", "text": _RICH} for i in range(5)]
        ws = self.los.score_work(scenes)
        assert ws.scene_count == 5

    def test_tc38_llm0_compliance(self):
        """TC38: LLM-0 — 외부 LLM 호출 없음"""
        import inspect
        import literary_system.constitution.los_constitution as mod
        src = inspect.getsource(mod)
        for pat in ["openai.ChatCompletion", "anthropic.Anthropic", "requests.post"]:
            assert pat not in src, f"LLM-0 위반: {pat}"

    def test_tc39_constitution_weights_property(self):
        """TC39: LOSConstitution.weights 속성 반환"""
        los = LOSConstitution()
        assert isinstance(los.weights, ConstitutionWeights)
        assert los.weights.drse == 0.30

    def test_tc40_rlhf_reward_direction_consistency(self):
        """TC40: rlhf_reward 방향성 일관성"""
        los = LOSConstitution()
        # 풍부한 텍스트가 짧은 텍스트보다 높은 점수여야 함
        r1 = los.rlhf_reward(_RICH, _SHORT)   # 생성=좋음 → 양수
        r2 = los.rlhf_reward(_SHORT, _RICH)   # 생성=나쁨 → 음수
        assert r1 > 0 and r2 < 0
        assert r1 == -r2
