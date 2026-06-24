"""배선 PoC 회귀 가드 — P1~P4 + 16/24부작 + 결정성."""
import examples.wiring_poc as w


def test_16_episode_plumbing():
    ctx = w.run_wiring_poc(total_episodes=16)
    assert len(ctx.plans) == 16
    assert len(ctx.prose) == 16
    assert all(p.startswith("[FORMULA-FALLBACK") for p in ctx.prose)


def test_feedback_channel_alive():
    ctx = w.run_wiring_poc(total_episodes=16)
    # 갈등압력이 화간 변동 = 텐서 피드백 채널 생존
    assert len(set(round(c, 4) for c in ctx.conflict_trace)) >= 2
    assert ctx.tensor.conflict_pressure == ctx.conflict_trace[-1]


def test_24_episode_autonomy():
    ctx = w.run_wiring_poc(total_episodes=24)
    assert len(ctx.plans) == 24


def test_deterministic():
    a = w.run_wiring_poc(total_episodes=16).k_trace
    b = w.run_wiring_poc(total_episodes=16).k_trace
    assert a == b


def test_residue_derivation_never_empty():
    ctx = w.run_wiring_poc(total_episodes=16)
    assert len(ctx.residue_ids) >= 1
