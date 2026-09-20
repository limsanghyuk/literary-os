#!/usr/bin/env python3
import argparse, hashlib, importlib.util, json, os, pathlib, sys, tempfile, zipfile
from copy import deepcopy

def sha_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def load_runtime(zip_path,tmp):
    with zipfile.ZipFile(zip_path) as z: z.extractall(tmp)
    root=pathlib.Path(tmp)/'literary_os_runtime'
    spec=importlib.util.spec_from_file_location('r70_live_rt',root/'__init__.py',submodule_search_locations=[str(root)])
    pkg=importlib.util.module_from_spec(spec); sys.modules['r70_live_rt']=pkg; spec.loader.exec_module(pkg)
    import importlib
    return importlib.import_module('r70_live_rt.provider_backed_renderer')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--runtime',required=True)
    ap.add_argument('--payloads',required=True)
    ap.add_argument('--seal',required=True)
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    seal=json.loads(pathlib.Path(args.seal).read_text())
    if seal.get('status')!='SEALED_BEFORE_OUTPUTS': raise SystemExit('execution seal not finalized')
    for k in ('model','reasoning_effort','max_output_tokens','timeout_seconds','max_attempts_per_arm'):
        if seal.get(k) in (None,''): raise SystemExit(f'missing sealed setting: {k}')
    if sha_file(args.runtime)!=seal['frozen_runtime_sha256']: raise SystemExit('runtime hash mismatch')
    if sha_file(args.payloads)!=seal['paired_payload_file_sha256']: raise SystemExit('payload file hash mismatch')
    if not os.environ.get('OPENAI_API_KEY'): raise SystemExit('OPENAI_API_KEY not available; no provider calls made')
    payloads=json.loads(pathlib.Path(args.payloads).read_text())
    with tempfile.TemporaryDirectory(prefix='r70live_') as td:
        rt=load_runtime(args.runtime,td)
        provider=rt.OpenAIResponsesProvider(
            model=seal['model'],reasoning_effort=seal['reasoning_effort'],
            max_output_tokens=int(seal['max_output_tokens']),timeout_seconds=int(seal['timeout_seconds']))
        all_rows=[]
        for pair in payloads['pairs']:
            row={'case_id':pair['case_id'],'arms':{}}
            for arm,key in (('CONTROL','control_payload'),('TREATMENT','treatment_payload')):
                pp=pair[key]
                attempts=[]; valid=None
                for attempt in range(1,int(seal['max_attempts_per_arm'])+1):
                    res=provider.generate(pp)
                    guard=rt.evaluate_render_contract_locally(pp,res)
                    prov=deepcopy(res.get('provenance') or {})
                    record={'attempt':attempt,'provider_result':res,'local_guard':guard}
                    attempts.append(record)
                    ok=(res.get('status')=='OK' and guard.get('decision')=='PASS' and
                        prov.get('live_call') is True and prov.get('response_id') and
                        prov.get('model_requested')==seal['model'] and
                        (not prov.get('model_returned') or prov.get('model_returned')==seal['model']))
                    if ok:
                        valid=record; break
                row['arms'][arm]={'valid':valid is not None,'attempts':attempts,'accepted_attempt':valid}
            row['pair_valid']=all(row['arms'][a]['valid'] for a in ('CONTROL','TREATMENT'))
            all_rows.append(row)
        out={
          'schema':'R70StageBLiveProviderRawResultR1','execution_seal':seal,
          'pair_count':len(all_rows),'valid_pairs':sum(x['pair_valid'] for x in all_rows),
          'invalid_pairs':sum(not x['pair_valid'] for x in all_rows),'pairs':all_rows
        }
        pathlib.Path(args.output).write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))
        print(json.dumps({'valid_pairs':out['valid_pairs'],'invalid_pairs':out['invalid_pairs'],'output_sha256':sha_file(args.output)},ensure_ascii=False))
if __name__=='__main__': main()
