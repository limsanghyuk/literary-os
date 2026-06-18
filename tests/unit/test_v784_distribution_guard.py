"""test_v784 — M3 분포 음성 가드레일 (V784, ADR-245). TC01~13."""
from literary_system.critic.distribution_guard import (
    distribution_guard, GuardResult, compute_stats, apply_guard_to_reward, NORMAL_BANDS)
_NORMAL=('"왜 여기 왔어." 한도가 물었다. 세진은 멈췄다. 숨을 골랐다. '
         '복도의 불빛이 깜빡였다. 그는 벽에 붙어 발소리를 죽였다. '
         '"증거는 가져왔나." 침묵이 흘렀다. 세진이 천천히 봉투를 내밀었다. '
         '한도의 가슴이 서늘해졌다. 둘은 마주 섰고, 아무도 먼저 움직이지 않았다.')
_EMO=' '.join(["사랑 분노 슬픔 두려움 절망 환희 그리움 고통 눈물 심장 가슴 떨림"]*3)

def test_tc01_stats_keys():
    s=compute_stats(_NORMAL); assert set(s)=={"dialogue_ratio","emotion_word_rate","avg_sentence_len","scene_len_tokens"}
def test_tc02_normal_zero_penalty():
    g=distribution_guard(_NORMAL); assert g.penalty==0.0 and not g.pathologies
def test_tc03_normal_not_rejected():
    assert not distribution_guard(_NORMAL).rejected
def test_tc04_no_positive_reward():
    # 전형성 무보상: penalty는 절대 양수 아님
    assert distribution_guard(_NORMAL).penalty <= 0.0
def test_tc05_emotion_overload_penalized():
    g=distribution_guard(_EMO); assert g.penalty<0 and any(p["metric"]=="emotion_word_rate" for p in g.pathologies)
def test_tc06_no_dialogue_penalized():
    flat="그는 갔다 방에 있었다 사람이 있었다 시간이 지났다 상황이 전개됐다 회의가 길게 이어졌다 설명만 나열됐다 끝없이 계속됐다 그리고 또"
    g=distribution_guard(flat); assert any(p["metric"]=="dialogue_ratio" for p in g.pathologies)
def test_tc07_is_pathological_flag():
    assert distribution_guard(_EMO).is_pathological and not distribution_guard(_NORMAL).is_pathological
def test_tc08_reject_threshold():
    g=distribution_guard(_EMO,reject_threshold=-1.0); assert g.rejected
def test_tc09_apply_guard_normal_unchanged():
    # 정상 → base 그대로(보너스 없음·감점 없음)
    assert apply_guard_to_reward(0.7,_NORMAL)==0.7
def test_tc10_apply_guard_pathology_penalized():
    assert apply_guard_to_reward(0.7,_EMO) < 0.7
def test_tc11_rejected_strong_floor():
    assert apply_guard_to_reward(0.9,_EMO)==-9.99
def test_tc12_to_dict():
    assert "penalty" in distribution_guard(_NORMAL).to_dict()
def test_tc13_export():
    import literary_system.critic as C
    assert hasattr(C,"distribution_guard") and hasattr(C,"apply_guard_to_reward")
