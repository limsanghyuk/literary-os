from pathlib import Path
import hashlib, json, re

BASE = Path('handoff/20260911/i4k5r3_attempt1')
FORBIDDEN = [
    'Event Ecology', 'thread', 'engine', 'planner', 'Treatment', 'Control',
    'threshold', 'goal', 'obstacle', 'exit_state', 'downstream_decision_owner',
    'future_thread_owner', 'PSSB', 'Performance-Specific', 'shared upstream',
    'scene plan', 'sequence plan'
]


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def body_from_segment(text):
    m = re.search(r'(?m)^S#\d+\.', text)
    if not m:
        raise RuntimeError('missing scene header')
    end = text.rfind('[END ATTEMPT1')
    if end < 0:
        raise RuntimeError('missing attempt1 end marker')
    return text[m.start():end].rstrip('\n')


def measure_arm(arm):
    root = BASE / arm.lower()
    files = sorted(root.glob(f'P07_I4K5R3_A1_{arm}_SQ*_SC*.txt'))
    rows = []
    bodies = []
    scene_ids = []
    for p in files:
        rb = p.read_bytes()
        text = rb.decode('utf-8')
        body = body_from_segment(text)
        ids = [int(x) for x in re.findall(r'(?m)^S#(\d+)\.', body)]
        rows.append({
            'name': p.name,
            'file_sha256': sha256_bytes(rb),
            'file_bytes': len(rb),
            'body_chars': len(body),
            'scene_ids': ids,
        })
        bodies.append(body)
        scene_ids.extend(ids)
    logical = '\n\n'.join(bodies)
    lines = [x.strip() for x in logical.splitlines() if x.strip()]
    long_lines = [x for x in lines if len(x) >= 40]
    counts = {}
    for x in long_lines:
        counts[x] = counts.get(x, 0) + 1
    duplicates = {x:n for x,n in counts.items() if n > 1}
    body_chars = sum(len(x) for x in bodies)
    return {
        'segment_count': len(files),
        'segments': rows,
        'body_chars': body_chars,
        'logical_join_sha256': sha256_bytes(logical.encode('utf-8')),
        'scene_count': len(scene_ids),
        'scene_ids': scene_ids,
        'scene_ids_exact_1_50': scene_ids == list(range(1, 51)),
        'forbidden_internal_meta_literals': {x: sum(b.count(x) for b in bodies) for x in FORBIDDEN},
        'CH_id_count': sum(len(re.findall(r'\bCH\d+\b', b)) for b in bodies),
        'SQ_id_count': sum(len(re.findall(r'\bSQ\d+\b', b)) for b in bodies),
        'exact_long_duplicate_line_count': len(duplicates),
        'exact_long_duplicate_ratio': (len(duplicates) / len(long_lines)) if long_lines else 0.0,
        'duplicate_examples': list(duplicates.items())[:20],
    }

R = {arm: measure_arm(arm) for arm in ['CONTROL', 'TREATMENT']}
gap = abs(R['CONTROL']['body_chars'] - R['TREATMENT']['body_chars']) / max(R['CONTROL']['body_chars'], R['TREATMENT']['body_chars'])
out = {
    'schema': 'P07I4K5R3Attempt1MeasurementR1',
    'source_main_commit': '7395faed683132d56352fdada1e1b18dabfb394f',
    'measurement_class': 'READ_ONLY_DETERMINISTIC_PRESCORE_NO_QUALITY',
    'body_char_method': 'sum(len(segment_body)) from first S# header to before END marker; transport metadata and synthetic inter-segment separators excluded',
    'rows': R,
    'relative_gap': gap,
    'relative_gap_percent': gap * 100,
    'gates': {
        'control_body_ge_35000': R['CONTROL']['body_chars'] >= 35000,
        'treatment_body_ge_35000': R['TREATMENT']['body_chars'] >= 35000,
        'gap_le_0_10': gap <= 0.10,
        'control_10_segments': R['CONTROL']['segment_count'] == 10,
        'treatment_10_segments': R['TREATMENT']['segment_count'] == 10,
        'control_scene_ids_exact': R['CONTROL']['scene_ids_exact_1_50'],
        'treatment_scene_ids_exact': R['TREATMENT']['scene_ids_exact_1_50'],
        'treatment_forbidden_zero': sum(R['TREATMENT']['forbidden_internal_meta_literals'].values()) == 0,
        'treatment_CH_SQ_zero': R['TREATMENT']['CH_id_count'] == 0 and R['TREATMENT']['SQ_id_count'] == 0,
        'treatment_exact_long_duplicate_zero': R['TREATMENT']['exact_long_duplicate_line_count'] == 0,
    }
}
Path('_i4k5r3_measure').mkdir(exist_ok=True)
Path('_i4k5r3_measure/metrics.json').write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print('I4K5R3_ATTEMPT1_METRICS=' + json.dumps(out, ensure_ascii=False, sort_keys=True))
