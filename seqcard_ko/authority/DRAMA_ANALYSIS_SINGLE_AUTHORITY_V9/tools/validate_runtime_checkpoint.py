#!/usr/bin/env python3
import argparse, datetime as dt, json
from pathlib import Path

def parse(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('work_state'); ap.add_argument('--journal'); ap.add_argument('--now'); args=ap.parse_args()
    st=json.loads(Path(args.work_state).read_text(encoding='utf-8')); errors=[]; warnings=[]
    now=parse(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    last=st.get('last_checkpoint_at')
    if last:
        mins=(now-parse(last)).total_seconds()/60
        if mins>=30: errors.append(f'NO_CHECKPOINT_HARD_STOP:{mins:.1f}min')
        elif mins>=25: warnings.append(f'CHECKPOINT_REQUIRED:{mins:.1f}min')
        elif mins>=20: warnings.append(f'CHECKPOINT_PREPARE:{mins:.1f}min')
    if args.journal:
        rows=[json.loads(x) for x in Path(args.journal).read_text(encoding='utf-8').splitlines() if x.strip()]
        if rows and rows[-1].get('event') not in {'CHECKPOINT_LOCKED','RUN_STOP','RECOVERY_LOCKED'}: warnings.append('JOURNAL_NOT_CLEANLY_CLOSED')
    print(json.dumps({'errors':errors,'warnings':warnings,'verdict':'PASS' if not errors else 'FAIL'},ensure_ascii=False,indent=2))
    return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
