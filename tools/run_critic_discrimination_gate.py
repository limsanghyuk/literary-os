"""run_critic_discrimination_gate.py — G_CRITIC_DISCRIMINATION (V775).
외부 라벨(명작계열/졸작)로 평가기 판별력(AUC) 측정. 기본 scorer=작품성축(데모).
"""
import sys
from literary_system.quality.critic_discrimination_gate import g_critic_discrimination, craft_axis_scorer
from literary_system.quality.quality_labels import DEMO_LABELS, summary

if __name__ == "__main__":
    print("라벨 요약:", summary())
    r = g_critic_discrimination(craft_axis_scorer, DEMO_LABELS)
    print(f"[{'PASS' if r.passed else 'FAIL'}] G_CRITIC_DISCRIMINATION")
    print(" ", r.detail)
    sys.exit(0 if r.passed else 1)
