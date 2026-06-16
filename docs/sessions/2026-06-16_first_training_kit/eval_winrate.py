"""eval_winrate.py — 학습 전후 승률 비교 (V771).
before: 원본 선호쌍의 baseline 승률. after: 학습된 모델로 재생성→재판정(개발자가 채움).
usage: python eval_winrate.py --pairs dpo_pairs.jsonl [--after 0.65]
"""
import argparse
from literary_system.learning.loop_c import load_preference_pairs
from literary_system.learning.first_training_kit import baseline_winrate, winrate_delta

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--after", type=float, default=None, help="학습후 재측정 승률(있으면 델타 출력)")
    a = ap.parse_args()
    before = baseline_winrate(load_preference_pairs(a.pairs))
    print(f"baseline 승률(학습전): {before}")
    if a.after is not None:
        d = winrate_delta(before, a.after)
        print(f"학습후: {a.after} | 델타 {d['delta']} → {d['verdict']} (moved={d['moved']})")
        print("판정: 1회 목적은 '움직임 확인'. 향상이면 반복·데이터 확대로 진행.")
    else:
        print("학습 후 모델로 동일 프롬프트 재생성→패널 재판정한 승률을 --after 로 전달하세요.")

if __name__ == "__main__":
    main()
