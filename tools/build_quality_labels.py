"""build_quality_labels.py — meta_gt_drama → 2축 품질 라벨 자동 산출 (V776).
usage: python tools/build_quality_labels.py [--out labels.json]
"""
import argparse, importlib.util, json, sys
from pathlib import Path
from literary_system.quality.quality_aggregator import from_drama_dict, label_summary

def load_drama():
    p = Path("docs/sessions/2026-06-13_corpus_ko_build/experiments/meta_gt_drama.py")
    spec = importlib.util.spec_from_file_location("mgd", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.DRAMA

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=None); a = ap.parse_args()
    labels = from_drama_dict(load_drama())
    print(f"자동 라벨링 {len(labels)}편 | 요약: {label_summary(labels)}")
    for l in sorted(labels, key=lambda x: -(x.craft + x.commercial))[:12]:
        print(f"  {l.work:14} craft={l.craft:.2f} comm={l.commercial:.2f} → {l.tier.value}")
    if a.out:
        Path(a.out).write_text(json.dumps([l.to_dict() for l in labels], ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"저장: {a.out}")
if __name__ == "__main__":
    main()
