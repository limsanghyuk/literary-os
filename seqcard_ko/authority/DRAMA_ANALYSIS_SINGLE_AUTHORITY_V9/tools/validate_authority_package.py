#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else '.')
req=['README.md','DRAMA_ANALYSIS_SINGLE_AUTHORITY_V9.md','AUTHORITY_MANIFEST.json','schemas/scenecard.schema.json','schemas/sequence_blueprint.schema.json','tools/validate_work_package.py','tools/validate_runtime_checkpoint.py','templates/source_lock.template.json','templates/work_state.template.json']
errors=[f'missing:{p}' for p in req if not (root/p).exists()]
if (root/'AUTHORITY_MANIFEST.json').exists():
 m=json.loads((root/'AUTHORITY_MANIFEST.json').read_text(encoding='utf-8'))
 for rel,exp in m.get('files',{}).items():
  p=root/rel
  if not p.exists(): errors.append(f'manifest missing:{rel}')
  elif hashlib.sha256(p.read_bytes()).hexdigest()!=exp: errors.append(f'hash mismatch:{rel}')
master=(root/'DRAMA_ANALYSIS_SINGLE_AUTHORITY_V9.md').read_text(encoding='utf-8') if (root/'DRAMA_ANALYSIS_SINGLE_AUTHORITY_V9.md').exists() else ''
for phrase in ['한 회차 전체','25분','30분','author_run_id != audit_run_id','SameWorkLegacyLock','SOURCE_GROUNDED_MANUAL_PASS']:
 if phrase not in master: errors.append(f'master missing phrase:{phrase}')
print(json.dumps({'authority_id':'DRAMA_ANALYSIS_SINGLE_AUTHORITY_V9','errors':errors,'verdict':'PASS' if not errors else 'FAIL'},ensure_ascii=False,indent=2))
raise SystemExit(0 if not errors else 1)
