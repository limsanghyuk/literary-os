#!/usr/bin/env python3
# G_PLANNING_LAYER — WorkPlanningCard 결정론 게이트 (DR-1, AM-1/AM-5/AM-8)
# FAIL = 오프라인 결정론 항목만. LLM/임베딩 검사 없음(CI 키 불요).
# usage: python3 verify_planning_layer.py <planning_dir> <authored_dir>
import json, re, sys, glob, os

REQ = ['schema','status','work_id','logline','premise','core_conflict','target_audience',
       'synopsis_300','synopsis_full','planning_intent','genre','format','evidence','no_outcome_check','by']
# AM-1 결말 누출 휴리스틱 사전(결정론) — 입력측 필드(logline/premise/core_conflict)에서 강한 결말 서술 탐지
OUTCOME_PAT = re.compile(r'(끝내|마침내|결국)\s|죽는다|사망한다|성공한다|승리한다|결혼한다|통합을 완성|이루어낸다|칭호를 얻|해피엔딩|비극으로 끝')

def check_card(path, authored):
    errs, warns = [], []
    try:
        c = json.load(open(path, encoding='utf-8'))
    except Exception as e:
        return [f'JSON_PARSE: {e}'], []
    for k in REQ:
        if k not in c or c[k] in ('', None, []): errs.append(f'MISSING:{k}')
    lg = c.get('logline','')
    if not (8 <= len(lg) <= 90): errs.append(f'LOGLINE_LEN:{len(lg)}')
    if len(c.get('planning_intent','')) < 40: errs.append('INTENT_FLOOR<40')
    if len(re.sub(r'\s','',c.get('synopsis_300',''))) < 150: warns.append('SYNOPSIS300_SHORT')
    # AM-1: 입력측 결말 누출
    for f in ['logline','premise','core_conflict']:
        if OUTCOME_PAT.search(c.get(f,'')): errs.append(f'OUTCOME_LEAK:{f}')
    # evidence: key_scene_refs >=3 + 실재 검증
    refs = c.get('evidence',{}).get('key_scene_refs',[])
    if len(refs) < 3: errs.append(f'SCENE_REFS<3:{len(refs)}')
    for r in refs:
        m = re.match(r'(.+)#(\d+)$', r)
        if not m: errs.append(f'REF_FORMAT:{r}'); continue
        ep_id, sno = m.group(1), int(m.group(2))
        fp = os.path.join(authored, f'{ep_id}.seqcard.jsonl')
        if not os.path.exists(fp): errs.append(f'REF_EP_MISSING:{r}'); continue
        nums = {json.loads(l)['scene_no'] for l in open(fp, encoding='utf-8')}
        if sno not in nums: errs.append(f'REF_SCENE_MISSING:{r}')
    fmt = c.get('format',{})
    if not isinstance(fmt.get('episodes'), int): errs.append('FORMAT_EPISODES')
    if 'by' in c and not c['by'].strip(): errs.append('BY_EMPTY')
    return errs, warns

def main(pdir, adir):
    total_e = 0
    for p in sorted(glob.glob(os.path.join(pdir, '*.planning.json'))):
        errs, warns = check_card(p, adir)
        total_e += len(errs)
        print(f'{os.path.basename(p)}: ERRORS {len(errs)} WARNINGS {len(warns)}')
        for e in errs: print('  E:', e)
        for w in warns: print('  W:', w)
    print('GATE', 'PASS' if total_e == 0 else 'FAIL', f'(total errors {total_e})')
    sys.exit(0 if total_e == 0 else 1)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
