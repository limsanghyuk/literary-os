#!/usr/bin/env python3
"""experiments/pertoken/remeasure_pertoken.py — Round#2 length-confound 재측정 (③, DESIGN-SGATE-v1).

두 가지를 한다.
 (1) 길이 편향 진단[GPU 불필요·항상 실행]: pairs JSONL의 draft/ref 길이 비대칭과
     '짧은 쪽=승자' 귀무모형 승률을 계산. 관측 W(ref 우세 ≈ 1-W1)와 비슷하면
     W가 길이 인공물일 위험이 큼을 경고.
 (2) per-token 재측정[logp ledger 있을 때만]: 집/GPU 학습이 남긴 logp ledger JSONL
     (행마다 draft.sumlogp/n_tokens, ref.sumlogp/n_tokens)을 소비해
     scheme=sum vs pertoken 두 W를 산출. 길이정규화로 W가 어떻게 바뀌는지 보여줌.

사용:
  python -m experiments.pertoken.remeasure_pertoken --pairs pairs_held.jsonl
  python -m experiments.pertoken.remeasure_pertoken --pairs pairs_held.jsonl --logp logp_held.jsonl
"""
from __future__ import annotations
import argparse, json, sys
from literary_system.learning.pertoken_winrate import (
    win_rate, length_diagnostic, char_len, ws_token_len)


def _load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                out.append(json.loads(ln))
    return out


def run(pairs_path: str, logp_path: str | None = None) -> dict:
    pairs = _load_jsonl(pairs_path)
    rep: dict = {"pairs_path": pairs_path, "n_pairs": len(pairs)}

    # (1) 길이 진단 — char + 공백토큰 두 척도
    diag_c = length_diagnostic(pairs, char_len)
    diag_t = length_diagnostic(pairs, ws_token_len)
    rep["length_diag_char"] = diag_c.to_dict()
    rep["length_diag_wstok"] = diag_t.to_dict()
    # 관측된 'ref 우세율'(winner=='ref' 비율) = 1 - W1_label
    n = len(pairs) or 1
    ref_obs = round(sum(1 for p in pairs if p.get("winner") == "ref") / n, 4)
    rep["observed_ref_winrate_label"] = ref_obs
    rep["length_artifact_gap_char"] = round(diag_c.null_winrate_shorter - ref_obs, 4)

    # (2) per-token 재측정 — logp ledger가 있을 때만
    if logp_path:
        logp = _load_jsonl(logp_path)
        rep["logp_path"] = logp_path
        rep["n_logp"] = len(logp)
        rep["W_sum"] = win_rate(logp, scheme="sum", target="draft")
        rep["W_pertoken"] = win_rate(logp, scheme="pertoken", target="draft")
        rep["W_shift_pertoken_minus_sum"] = round(rep["W_pertoken"] - rep["W_sum"], 4)
    else:
        rep["logp_path"] = None
        rep["note_logp"] = ("logp ledger 미제공 — per-token W 재측정은 집/GPU 산출 ledger 필요. "
                            "길이 진단(1)만 수행함.")
    return rep


def _print(rep: dict) -> None:
    dc = rep["length_diag_char"]
    print(f"[pairs] {rep['pairs_path']}  n={rep['n_pairs']}")
    print(f"[len/char ] draft={dc['draft_mean']}  ref={dc['ref_mean']}  "
          f"draft-ref={dc['draft_minus_ref']}  null(shorter→ref)={dc['null_winrate_shorter']}")
    dt = rep["length_diag_wstok"]
    print(f"[len/wstok] draft={dt['draft_mean']}  ref={dt['ref_mean']}  "
          f"draft-ref={dt['draft_minus_ref']}  null(shorter→ref)={dt['null_winrate_shorter']}")
    print(f"[observed ] ref승률(label)={rep['observed_ref_winrate_label']}  "
          f"길이설명력-관측 gap={rep['length_artifact_gap_char']}")
    if rep.get("logp_path"):
        print(f"[per-token] W_sum={rep['W_sum']}  W_pertoken={rep['W_pertoken']}  "
              f"Δ(pt-sum)={rep['W_shift_pertoken_minus_sum']}")
    else:
        print(f"[per-token] {rep['note_logp']}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--logp", default=None)
    ap.add_argument("--json", action="store_true", help="JSON으로 출력")
    a = ap.parse_args(argv)
    rep = run(a.pairs, a.logp)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        _print(rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
