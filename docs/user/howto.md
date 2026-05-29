# Literary OS — How-to 가이드

실제 작업별 절차를 설명합니다.

---

## 한국 드라마 에피소드 일괄 생성

```python
from literary_system.scene_generation.drama_episode_generator import DramaEpisodeGenerator
from literary_system.llm_bridge.mock_bridge import MockLLMBridge

# MOCK 모드로 5화 생성
gen = DramaEpisodeGenerator(bridge=MockLLMBridge(
    scripted_responses=["씬 텍스트 예시"] * 50
))
episodes = gen.generate_series(
    title="비와 편지",
    num_episodes=5,
    scenes_per_episode=8,
)
for ep in episodes:
    print(f"EP{ep.episode_num:02d}: {len(ep.scenes)}개 씬, {ep.word_count}자")
```

---

## 서사 부채 감지 및 자동 수리

```python
from literary_system.gig.narrative_graph_store import NarrativeGraphStore
from literary_system.asd.narrative_debt_detector import NarrativeDebtDetector
from literary_system.asd.auto_repair_executor import AutoRepairExecutor
from literary_system.gig.code_dependency_graph import CodeDependencyGraph

store = NarrativeGraphStore()
detector = NarrativeDebtDetector(store)
executor = AutoRepairExecutor(store, CodeDependencyGraph())

# 부채 탐지
report = detector.detect(project_id="drama_001")
print(f"미해결 부채: {len(report.debts)}건")

# 자동 수리 실행 (안전 모드)
result = executor.repair(report, dry_run=False)
print(f"수리 완료: {result.repaired_count}건")
```

---

## E2E 게이트 수동 실행

```bash
# MOCK 모드 (CI 기본)
python -c "
from literary_system.gates.e2e_prose_gate import gate_e2e_prose
result = gate_e2e_prose(mock=True)
print(f'체크포인트: {result.checkpoints_passed}/6')
print(f'소요 시간: {result.elapsed_ms:.1f}ms')
"

# 실 LLM 모드 (수동)
python -m pytest tests/e2e/ -v -m real_llm
```

---

## L0+L1 fast-path 게이트만 실행

```python
from literary_system.gates.release_gate import run_release_gate_tiered

# PR 체크용 — 10게이트, 약 1초
r = run_release_gate_tiered(tiers=['L0', 'L1'])
print(f"fast-path: {r['gates_passed']}/{r['total_gates']} PASS")
```

---

## 게이트 실행 시간 측정

```bash
# L0+L1 fast-path 측정
python tools/measure_gate_time.py --quick --output docs/perf/gate_timings.json

# 전체 측정
python tools/measure_gate_time.py --output docs/perf/gate_timings_full.json
```

---

## LOSDB 연결 확인

```python
from literary_system.db.losdb_client import LOSDBClient

client = LOSDBClient()
status = client.check_all_connections()
print(status)
# {'sql': True, 'vector': True, 'graph': True}

# 교차 쿼리
results = client.cross_query(
    query="주인공의 감정 변화",
    sql_filter={"episode_id": "EP01"},
    top_k=5
)
```
