#!/usr/bin/env python3
# E2 데이터셋 빌더 — harvest_pairs(brief2prose) → 학습 파일 (DR Exit 후 소비, §9 규약)
# 결정론. split=작품 단위(씬 누출 금지). EVAL_HOLDOUT 작품 유입 시 즉시 FAIL(G_EVAL_HOLDOUT_ISOLATION).
# usage: python3 build_e2_dataset.py <pairs_dir> <out_dir> [--val-works 시티헌터,오나의귀신님]
import json, glob, os, sys, hashlib, random

EVAL_HOLDOUT = set()  # source_lock EVAL_HOLDOUT 등재 작품 — 현재 0편(입수 시 갱신)
DEF_VAL = ['시티헌터', '오나의귀신님']  # 작품 단위 val (장르 상이 2작)

def main(pairs_dir, out_dir, val_works):
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(pairs_dir, '*.jsonl')))
    stats = dict(train=0, val=0, skipped_verify=0, works=set(), val_set=val_works)
    outs = {s: open(os.path.join(out_dir, f'sft_brief2prose.{s}.jsonl'), 'w', encoding='utf-8') for s in ('train','val')}
    for fp in files:
        work = os.path.basename(fp).rsplit('_', 1)[0]
        if work in EVAL_HOLDOUT:
            print(f'FATAL: EVAL_HOLDOUT work {work} in pairs — G_EVAL_HOLDOUT_ISOLATION FAIL'); sys.exit(2)
        split = 'val' if work in val_works else 'train'
        for line in open(fp, encoding='utf-8'):
            r = json.loads(line)
            if r.get('mode') == 'order' and r.get('verify_win') is False:
                stats['skipped_verify'] += 1
                continue  # AM-6 안전마진: 순서모드 저신뢰 행 제외
            rec = dict(work_id=r['work_id'], scene_no=r['scene_no'],
                       prompt=r['prompt'], completion=r['completion'], split=split)
            outs[split].write(json.dumps(rec, ensure_ascii=False) + '\n')
            stats[split] += 1
        stats['works'].add(work)
    for f in outs.values(): f.close()
    h = hashlib.sha256()
    for s in ('train','val'):
        h.update(open(os.path.join(out_dir, f'sft_brief2prose.{s}.jsonl'),'rb').read())
    man = dict(schema='E2_DATASET_MANIFEST_V1', pairs_train=stats['train'], pairs_val=stats['val'],
               skipped_low_confidence=stats['skipped_verify'], works=len(stats['works']),
               val_works=val_works, sha256=h.hexdigest(),
               policy='verbatim LOCAL ONLY / split=work-level / order-mode verify_win=false 제외')
    json.dump(man, open(os.path.join(out_dir, 'E2_DATASET_MANIFEST.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(json.dumps(man, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    val = DEF_VAL
    if '--val-works' in sys.argv:
        val = sys.argv[sys.argv.index('--val-works')+1].split(',')
    main(sys.argv[1], sys.argv[2], val)
