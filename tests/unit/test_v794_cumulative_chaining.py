"""SP-E.10.3 — 누적 어댑터 체이닝 오케스트레이터(V794). CumulativeLoopC 상태기계.

검증: ①체이닝 링크(라운드 k의 init_adapter == 직전 채택 어댑터) ②adopt 승격 /
rollback 시 current_adapter 불변 ③base-anchored KL 원장 기록 ④5연속 클린 → Exit v14.0.0.
실 GPU 학습 비수행 — measured_w1/kl/ci/adapter_path는 외부 산출을 모사 주입.
"""
import os
import tempfile
import pytest

from literary_system.learning.loopc_closure import (
    CumulativeLoopC, CumulativeRoundResult)
from literary_system.learning.first_training_kit import make_smoke_dataset


@pytest.fixture
def pairs_path():
    fd, p = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    make_smoke_dataset(p, n=4)
    yield p
    os.unlink(p)


def _submit(loop, pairs_path, idx, *, decision="adopt", ci=0.64, lrate=0.40):
    """adopt면 w1을 w0보다 높게(0.9), rollback이면 낮게(0.0) 주입. kl<τ, c3=중립(PASS)."""
    measured_w1 = 0.9 if decision == "adopt" else 0.0
    return loop.submit_round(
        pairs_path=pairs_path, measured_w1=measured_w1, kl=0.10,
        w1_ci_lower=ci, length_rule_rate=lrate, n_pairs=250,
        adapter_path=f"/adapters/r{idx}", base_anchored_kl=0.05 * idx)


def test_first_round_inits_from_base(pairs_path):
    loop = CumulativeLoopC()
    assert loop.current_adapter is None
    res = _submit(loop, pairs_path, 1)
    assert isinstance(res, CumulativeRoundResult)
    assert res.init_adapter is None            # 첫 라운드 = base만
    assert res.decision == "adopt"
    assert res.current_adapter == "/adapters/r1"   # 승격됨


def test_chaining_link_carries_prior_adapter(pairs_path):
    loop = CumulativeLoopC()
    _submit(loop, pairs_path, 1)
    res2 = _submit(loop, pairs_path, 2)
    # 라운드2의 시작점 = 라운드1 채택 어댑터 → 누적 체이닝
    assert res2.init_adapter == "/adapters/r1"
    assert res2.current_adapter == "/adapters/r2"


def test_rollback_keeps_current_adapter(pairs_path):
    loop = CumulativeLoopC()
    _submit(loop, pairs_path, 1)               # adopt → r1
    res2 = _submit(loop, pairs_path, 2, decision="rollback")
    assert res2.decision == "rollback"
    assert res2.init_adapter == "/adapters/r1"  # 직전 채택에서 출발
    assert res2.current_adapter == "/adapters/r1"  # 폐기 → 불변(r2 미승격)
    res3 = _submit(loop, pairs_path, 3)         # 다음 라운드도 r1에서 출발
    assert res3.init_adapter == "/adapters/r1"


def test_base_anchored_kl_recorded(pairs_path):
    loop = CumulativeLoopC()
    res = _submit(loop, pairs_path, 1)
    assert res.ledger_record["base_anchored_kl"] == pytest.approx(0.05)
    assert loop.ledger[0]["base_anchored_kl"] == pytest.approx(0.05)


def test_five_consecutive_clean_triggers_exit(pairs_path):
    loop = CumulativeLoopC()
    out = None
    for i in range(1, 6):
        out = _submit(loop, pairs_path, i)
    assert out.decision == "adopt"
    assert out.exit is True
    assert out.graduation["graduated"] is True
    assert out.graduation["exit_version"] == "v14.0.0"
    assert out.graduation["consecutive_adopt"] == 5


def test_four_clean_not_yet_exit(pairs_path):
    loop = CumulativeLoopC()
    out = None
    for i in range(1, 5):
        out = _submit(loop, pairs_path, i)
    assert out.exit is False
    assert out.graduation["graduated"] is False


def test_rollback_in_window_blocks_exit(pairs_path):
    loop = CumulativeLoopC()
    _submit(loop, pairs_path, 1)
    _submit(loop, pairs_path, 2, decision="rollback")  # 스트릭 끊김
    out = None
    for i in range(3, 7):                                # 이후 4 adopt(< 5)
        out = _submit(loop, pairs_path, i)
    assert out.exit is False
    assert out.graduation["consecutive_adopt"] == 4


def test_to_dict_roundtrips(pairs_path):
    loop = CumulativeLoopC()
    d = _submit(loop, pairs_path, 1).to_dict()
    for k in ("round_idx", "decision", "init_adapter", "adapter_path",
              "current_adapter", "report", "ledger_record", "graduation", "exit"):
        assert k in d
