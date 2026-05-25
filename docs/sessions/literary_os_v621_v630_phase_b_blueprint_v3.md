# Literary OS — V621~V630 통합 본안 설계도 v3.0 (Markdown 미러)

**기반 제안서**: `literary_os_v621_v630_phase_b_proposal_v3.docx` (2026-05-25)
**기반 v2.0**: `literary_os_v601_v630_phase_b_blueprint_v2.docx` (commit f16c5c8)
**V620_R supersedes**: `outputs/v620_r_patch/literary_os_v620_r_*.docx` (참조 보존)
**작성**: Chief Architect × Chief Compiler × Chief System Principal Engineer
**작성일**: 2026-05-25

본 문서는 동명 .docx 파일의 markdown 미러 — Sonnet 4.6이 docx 추출 없이 직접 학습 가능.

---

## §0. 본 설계도의 범위

본 설계도는 V621~V630 통합 본안 v3.0 제안서를 코드 수준으로 구체화한다. Sonnet 4.6이 본 문서 + 매핑된 v2.0/V620_R 스켈레톤만으로 구현 가능하도록 자기완결적으로 작성한다.

**전제**: v10.25.2 기준 main HEAD (60/60 Gates, 6,728+ Tests, G61 6축 PASS).

**학습 우선순위**:
1. `docs/sessions/2026-05-25_v621_v630_phase_b_main_handoff_v3.md` — 매 V 진입 시 필수
2. `docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.md` (본 문서) — 코드 스켈레톤 인용
3. `docs/sessions/literary_os_v621_v630_phase_b_proposal_v3.docx` + `blueprint_v3.docx` — 인간 검토
4. `docs/sessions/literary_os_v601_v630_phase_b_blueprint_v2.docx` (commit f16c5c8) — v2.0 원본
5. `outputs/v620_r_patch/` — V620_R 산출물 (supersedes, 참조용)

---

## §1. V621-PRE — 자동 학습 강제 (사전 작업, 0.5일)

목표: V620_R R0 흡수. AGENTS.md / preflight_step15에 자동 학습 강제.

### 1.1 AGENTS.md 상단

```markdown
# AGENTS.md 최상단

## 🔴 필수 학습 (Critical Loading) — 모든 작업 시작 전

작업 시작 전 반드시 읽고 컨텍스트 포함:

1. docs/sessions/2026-05-25_v621_v630_phase_b_main_handoff_v3.md
2. docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.md
3. docs/audit/2026-05-25_phase_b_audit_report.docx

3개 파일이 컨텍스트에 없으면 절대 코드 작성 금지.
docx 추출: python -c "from docx import Document; ..."
```

### 1.2 preflight_step15 추가

```python
# tools/preflight_step15.py
REQUIRED_V3_FILES = [
    'docs/sessions/2026-05-25_v621_v630_phase_b_main_handoff_v3.md',
    'docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.md',
]

def verify_v3_handoff() -> dict:
    missing = [f for f in REQUIRED_V3_FILES if not Path(f).exists()]
    return {'pass': not missing, 'missing': missing}
```

V621-PRE 종료: AGENTS.md 갱신 + preflight 함수 + 5 TC.

---

## §2. V621 — SP-B.2 retrofit (P-IF 3건, 1주)

목표: AgentEnvelope (P-IF-01) + ReaderFeedbackIngest (P-IF-03) + OpenAPI SemVer (P-IF-04) 3건 동시.

### 2.1 AgentEnvelope — canonical_bridge_v2.py 확장

```python
# literary_system/llm_bridge/canonical_bridge_v2.py (V621 확장, ADR-088)
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict

class AgentRole(Enum):
    SCENE_WRITER = "scene_writer"   # Phase B 기본
    CRITIC = "critic"
    EDITOR = "editor"
    HISTORIAN = "historian"
    READER_VOICE = "reader_voice"

@dataclass
class AgentEnvelope:
    """P-IF-01 (ADR-088). Phase B는 agent_id='default' 단일."""
    agent_id: str = "default"
    role: AgentRole = AgentRole.SCENE_WRITER
    prompt: str = ""
    context: Dict = field(default_factory=dict)
    parent_agent_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class RoutingPolicy:
    cost_weight: float = 0.3
    latency_weight: float = 0.3
    quality_weight: float = 0.4
    agent_routing: Dict[str, 'RoutingDecision'] = field(default_factory=dict)

    def decide_for_agent(self, env: AgentEnvelope) -> 'RoutingDecision':
        if env.agent_id in self.agent_routing:
            return self.agent_routing[env.agent_id]
        if env.role.value in self.agent_routing:
            return self.agent_routing[env.role.value]
        return RoutingDecision.LOCAL_LORA

class CanonicalBridgeV2:
    def generate(self, prompt_or_envelope, **kwargs) -> str:
        """하위 호환 — str(구) 또는 AgentEnvelope(신)."""
        if isinstance(prompt_or_envelope, AgentEnvelope):
            env = prompt_or_envelope
        else:
            env = AgentEnvelope(prompt=str(prompt_or_envelope), **kwargs)
        decision = self.policy.decide_for_agent(env)
        return self._route(env, decision)
```

### 2.2 ReaderFeedbackIngest — 신규

```python
# literary_system/multiwork/reader_feedback_ingest.py (V621 신규, ADR-088)
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol

@dataclass(frozen=True)
class ReaderFeedback:
    reader_id: str
    work_id: str
    scene_id: str
    rating: int                       # 1~5
    comment: Optional[str] = None
    timestamp: datetime = None
    reader_demographic: Optional[dict] = None
    engagement_seconds: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', datetime.utcnow())
        if not (1 <= self.rating <= 5):
            raise ValueError(f"rating must be 1~5, got {self.rating}")

class RewardSignalAdapter(Protocol):
    def from_feedback(self, fb: ReaderFeedback) -> 'RewardSignal': ...

class ReaderFeedbackIngest:
    """P-IF-03 (ADR-088). Phase B는 NotImplementedError."""
    PHASE_C_FEATURE = True

    def __init__(self, reward_adapter: Optional[RewardSignalAdapter] = None):
        self.reward_adapter = reward_adapter
        self._active = reward_adapter is not None

    def ingest(self, feedback: ReaderFeedback):
        raise NotImplementedError(
            "Phase C+ feature (P-IF-03). Phase B defines interface only.")

    def is_phase_c_active(self) -> bool:
        return self._active
```

### 2.3 OpenAPI SemVer — model_serving_endpoint.py 확장

```python
# literary_system/serving/model_serving_endpoint.py (V621 확장, ADR-088)
import yaml
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(title="LiteraryOS-ModelServing", version="1.0.0",
              description="P-IF-04 OpenAPI SemVer 감지 활성")

SEMVER_MAJOR, SEMVER_MINOR, SEMVER_PATCH = 1, 0, 0
SEMVER = f"{SEMVER_MAJOR}.{SEMVER_MINOR}.{SEMVER_PATCH}"

@app.get('/openapi.yaml')
def openapi_yaml():
    schema = get_openapi(title=app.title, version=SEMVER, routes=app.routes)
    return yaml.safe_dump(schema, sort_keys=False)

@app.get('/api_version')
def api_version():
    return {"semver": SEMVER}
```

V621 종료: 3건 + ADR-088 + 60 TC + G56/G57 회귀 0건.

---

## §3. V622 — SP-B.3 retrofit (3건, 1주)

### 3.1 conflict_policy

```python
# literary_system/multiwork/shared_character_db_v2.py (V622 확장, ADR-089)
from enum import Enum
from dataclasses import dataclass
from typing import List

class ConflictPolicy(Enum):
    RENAME = "rename"
    MERGE = "merge"
    FORK = "fork"
    BLOCK = "block"
    ESCALATE = "escalate"

@dataclass
class ConflictPriority:
    has_copyright_holder: int   # 0=있음 우선
    appearance_count_neg: int
    first_appearance_date: str

@dataclass
class ResolutionResult:
    winning_work_id: str
    policy_applied: ConflictPolicy
    audit_trail: List[ConflictPriority]

class SharedCharacterDBV2:
    def __init__(self, graph, provenance_ledger,
                 default_policy: ConflictPolicy = ConflictPolicy.ESCALATE):
        self.policy = default_policy

    def resolve(self, character_id, conflicting_work_ids) -> ResolutionResult:
        priorities = [self._compute_priority(w, character_id)
                      for w in conflicting_work_ids]
        priorities.sort(key=lambda p: (
            p.has_copyright_holder,
            p.appearance_count_neg,
            p.first_appearance_date,
        ))
        return ResolutionResult(
            winning_work_id=conflicting_work_ids[0],
            policy_applied=self.policy,
            audit_trail=priorities,
        )
```

### 3.2 workload_profile

```python
# literary_system/multiwork/multi_work_orchestrator_v2.py (V622 확장, ADR-089)
from enum import Enum
from dataclasses import dataclass

class WorkloadProfile(Enum):
    SINGLE = "single"
    DUAL = "dual"
    TRIPLE = "triple"

@dataclass
class SLOByProfile:
    single_ms: int = 3000
    dual_ms: int = 5000
    triple_ms: int = 8000

class MultiWorkOrchestratorV2:
    def __init__(self, ..., slo: SLOByProfile = None):
        self.slo = slo or SLOByProfile()

    def detect_profile(self) -> WorkloadProfile:
        n = len([w for w in self.active_works.values() if w.state == 'active'])
        if n <= 1: return WorkloadProfile.SINGLE
        if n == 2: return WorkloadProfile.DUAL
        return WorkloadProfile.TRIPLE

    def slo_for_current(self) -> int:
        return {WorkloadProfile.SINGLE: self.slo.single_ms,
                WorkloadProfile.DUAL: self.slo.dual_ms,
                WorkloadProfile.TRIPLE: self.slo.triple_ms}[self.detect_profile()]
```

### 3.3 adv_seeds

```python
# literary_system/rlhf/reward_model.py (V622 retrofit, ADR-089)
from dataclasses import dataclass

@dataclass
class AdvSeed:
    id: str
    text: str
    expected_penalty: float = 0.10

ADV_SEEDS_REQUIRED = [
    AdvSeed("marker_stuff",     "[BEAT][TENSION][BEAT] 5회 반복", 0.15),
    AdvSeed("length_inflate",   "씬 1500자 → 5000자 부풀림",      0.10),
    AdvSeed("repeat_pattern",   "동일 문장 5회 반복",             0.12),
    AdvSeed("extreme_emotion",  "극단 감정 9점 강제",             0.08),
    AdvSeed("genre_deviation",  "드라마 → 판타지 이탈",           0.10),
]

class RewardModel:
    def score_with_adv_seeds(self, scenes, seeds=None) -> dict:
        seeds = seeds or ADV_SEEDS_REQUIRED
        results = {'blocked': 0, 'total': len(seeds), 'details': []}
        for seed in seeds:
            sig = self.score(seed.text, {'scene_id': seed.id})
            blocked = sig.marker_penalty >= seed.expected_penalty
            if blocked: results['blocked'] += 1
            results['details'].append({'seed': seed.id, 'blocked': blocked,
                                       'penalty': sig.marker_penalty})
        return results
```

V622 종료: 3건 retrofit + ADR-089 + 60 TC + G58/G59 회귀 0건.

---

## §4. V623 — SystemIntegrationTest + Helm 사전 검증 (3일)

```python
# tests/integration/test_system_integration.py (V623 확장, ADR-090)
def test_lora_rlhf_multiwork_e2e_v623():
    """V613 base + V621/V622 retrofit 통합."""
    # 1) LoRA
    out = lora_gateway.call("test")
    # 2) RewardModel + adv_seeds 5종 (V622)
    adv_result = reward_model.score_with_adv_seeds(scenes=[out])
    assert adv_result['blocked'] >= 4
    # 3) AgentEnvelope (V621)
    from literary_system.llm_bridge.canonical_bridge_v2 import (
        AgentEnvelope, AgentRole)
    env = AgentEnvelope(role=AgentRole.SCENE_WRITER, prompt='x')
    out2 = bridge.generate(env)
    # 4) MultiWork 3작품 + workload_profile
    for w in ['drama_a', 'drama_b', 'drama_c']:
        orchestrator.submit(w, scene_request={'prompt': 'next'})
    profile = orchestrator.detect_profile()
    assert profile == WorkloadProfile.TRIPLE
    assert orchestrator.slo_for_current() == 8000

# Helm 사전 검증 (P-Arch-01)
import subprocess
def test_helm_train_plane_lint():
    r = subprocess.run(['helm', 'lint', 'deploy/helm/train_plane'])
    assert r.returncode == 0

def test_helm_train_plane_dry_run():
    r = subprocess.run(['helm', 'install', '--dry-run', '--debug',
                        'train-plane', 'deploy/helm/train_plane'])
    assert r.returncode == 0
```

V623 종료: ADR-090 + 30 TC.

---

## §5. V624 — 24h 장기 시나리오 + 메모리 회귀 (3일)

```python
# tests/integration/test_v624_24h_scenario.py (V624 신규, ADR-091)
import pytest, time
from literary_system.optimization.long_run_monitor import LongRunMonitor
from literary_system.optimization.memory_leak_detector import MemoryLeakDetector

@pytest.mark.slow
@pytest.mark.timeout(86400 + 600)
def test_24h_continuous_generation():
    monitor = LongRunMonitor(duration_seconds=86400)
    leak = MemoryLeakDetector()
    leak.start()
    monitor.start()
    while monitor.is_running():
        out = bridge.generate(AgentEnvelope(prompt="continuous"))
        monitor.record_request()
        if monitor.elapsed_seconds() % 3600 == 0:
            snap = leak.snapshot()
            assert snap.growth_rate_mb_per_hour < 10
    leak.stop()
    report = monitor.summary()
    assert report.error_rate < 0.005
    assert report.p95_latency_ms < 1500
```

```yaml
# .github/workflows/long_run_24h.yml
name: 24h Long-Run Test
on:
  schedule:
    - cron: '0 0 * * 0'   # 매주 일요일 자정
  workflow_dispatch:
jobs:
  long_run:
    runs-on: self-hosted-gpu
    timeout-minutes: 1500   # 25h
    steps:
      - uses: actions/checkout@v4
      - run: pytest -m slow tests/integration/test_v624_24h_scenario.py
```

V624 종료: ADR-091 + 30 TC.

---

## §6. V625 — biweekly_train + Lambda 폴백 + 자동 복구 (1주)

```yaml
# .github/workflows/biweekly_train.yml (V625 신규, ADR-092)
name: Biweekly LoRA + RLHF Training
on:
  schedule:
    - cron: '0 17 1,15 * *'   # 매월 1·15일 02:00 KST
  workflow_dispatch:
jobs:
  train:
    runs-on: ubuntu-latest
    timeout-minutes: 360
    steps:
      - uses: actions/checkout@v4
      - name: Check RunPod
        id: rp
        run: python tools/check_runpod_availability.py
      - name: Fallback Lambda
        if: failure()
        run: |
          python tools/notify_slack.py --msg "RunPod 부족 — Lambda H100"
          python literary_system/finetune/lora_job_runner.py \
            --backend lambda_h100 --dry-run
      - name: Run training (dry)
        run: |
          python literary_system/finetune/lora_job_runner.py \
            --base llama-3.1-8b --dry-run
      - name: Notify done
        if: always()
        run: python tools/notify_slack.py --msg "Training cycle done"
```

```python
# tools/check_runpod_availability.py (V625 신규)
import os, requests, sys
def main() -> int:
    key = os.environ.get('RUNPOD_API_KEY')
    if not key: return 1
    r = requests.get('https://api.runpod.io/v1/gpu/availability',
                     headers={'Authorization': f'Bearer {key}'})
    if r.status_code != 200: return 1
    avail = r.json().get('rtx_4090_available', 0)
    return 0 if avail > 0 else 1
if __name__ == '__main__': sys.exit(main())

# tools/notify_slack.py (V625 신규)
import os, requests, argparse
def notify(channel, msg):
    webhook = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook: return
    requests.post(webhook, json={'channel': channel, 'text': msg})
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--channel', default='#losdb-ops')
    parser.add_argument('--msg', required=True)
    notify(**vars(parser.parse_args()))
```

V625 종료: ADR-092 + 50 TC.

---

## §7. V626 — TrainPlane Helm 검증 (3일)

```yaml
# .github/workflows/helm_train_plane.yml (V626 신규, ADR-093)
name: TrainPlane Helm Validation
on:
  pull_request:
    paths: ['deploy/helm/train_plane/**']
  workflow_dispatch:
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-helm@v4
        with: { version: 'v3.14.0' }
      - name: Helm lint
        run: helm lint deploy/helm/train_plane
      - name: Helm template
        run: helm template train-plane deploy/helm/train_plane > /tmp/rendered.yaml
      - name: Kubeval
        run: |
          curl -L https://github.com/instrumenta/kubeval/releases/latest/download/kubeval-linux-amd64.tar.gz | tar xz
          ./kubeval /tmp/rendered.yaml
```

V626 종료: ADR-093 + 30 TC.

---

## §8. V627 — ServePlane Helm 신설 + 검증 (1주)

```yaml
# deploy/helm/serve_plane/Chart.yaml (V627 신규, ADR-094)
apiVersion: v2
name: serve-plane
description: Literary OS ServePlane — FastAPI ModelServing + Canary
type: application
version: 1.0.0
appVersion: "10.25.2"
```

```yaml
# deploy/helm/serve_plane/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-serving
spec:
  replicas: {{ .Values.replicas | default 2 }}
  selector:
    matchLabels: { app: model-serving }
  template:
    spec:
      containers:
      - name: model-serving
        image: {{ .Values.image }}
        ports: [{ containerPort: 8000 }]
        env:
        - name: LORA_ARTIFACT_PATH
          value: {{ .Values.loraArtifactPath }}
        readinessProbe:
          httpGet: { path: /health, port: 8000 }
        livenessProbe:
          httpGet: { path: /health, port: 8000 }
```

```yaml
# deploy/helm/serve_plane/templates/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: model-serving-ingress
spec:
  rules:
  - host: {{ .Values.host }}
    http:
      paths:
      - path: /generate
        pathType: Prefix
        backend: { service: { name: model-serving, port: { number: 8000 } } }
      - path: /openapi.yaml          # V621 retrofit
        pathType: Exact
        backend: { service: { name: model-serving, port: { number: 8000 } } }
      - path: /model_card
        pathType: Exact
        backend: { service: { name: model-serving, port: { number: 8000 } } }
      - path: /api_version
        pathType: Exact
        backend: { service: { name: model-serving, port: { number: 8000 } } }
```

V627 종료: ServePlane chart + Ingress + helm_serve_plane.yml workflow + ADR-094 + 50 TC.

---

## §9. V628 — Grafana + Prometheus dashboard (3일)

```yaml
# monitoring/prometheus/scrape_config.yml (V628 신규, ADR-095)
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'literary-os-model-serving'
    static_configs:
      - targets: ['model-serving:8000']
    metrics_path: /metrics
  - job_name: 'literary-os-rlhf-monitor'
    static_configs:
      - targets: ['rlhf-monitor:9090']
```

```json
# monitoring/grafana/dashboards/cost_slo.json (V628 신규)
{
  "title": "LOS Cost SLO Dashboard",
  "panels": [
    {"title": "Daily GPU Cost (USD)",
     "targets": [{"expr": "sum(rate(gpu_cost_total[1d])) by (backend)"}]},
    {"title": "Monthly Cost vs SLO ($120)",
     "targets": [{"expr": "sum(gpu_cost_total) / 120"}]},
    {"title": "Cost per Scene",
     "targets": [{"expr": "rate(gpu_cost_total[1h]) / rate(scenes_generated[1h])"}]}
  ]
}

# monitoring/grafana/dashboards/krippendorff_alpha.json (V628 신규)
{
  "title": "RLHF Krippendorff α Drift",
  "panels": [
    {"title": "α by Cycle",
     "targets": [{"expr": "rlhf_krippendorff_alpha"}]},
    {"title": "α Drift Alert (>0.1)",
     "alert": {"condition": "abs(delta(rlhf_krippendorff_alpha[1h])) > 0.1"}}
  ]
}
```

V628 종료: ADR-095 + 30 TC.

---

## §10. V629 — 운영 문서 + ATIA mini-audit + Branch Protection (1주)

### 10.1 Diataxis 4 운영 문서

```
docs/operations/ (V629 신규, ADR-096)
├── tutorial/
│   ├── 01_first_lora_training.md
│   ├── 02_rlhf_cycle.md
│   └── 03_multiwork_3works.md
├── how_to/
│   ├── add_new_lora_adapter.md
│   ├── debug_rlhf_kl_divergence.md
│   └── recover_from_canary_rollback.md
├── reference/
│   ├── api_v1.0.0_reference.md   # OpenAPI 기반
│   ├── lora_artifact_3tag.md
│   └── adv_seeds_5kinds.md
└── explanation/
    ├── phase_b_architecture.md
    ├── g61_6plus1_axes.md
    └── p_if_traces.md
```

### 10.2 ATIA mini-audit

```python
# tools/atia_mini_audit.py (V629 신규, ADR-096)
"""ATIA 메타데이터 + 100건 무작위 + sha256 chain 일괄 감리."""
import random, hashlib, json
from pathlib import Path

REQUIRED_ATIA_FIELDS = ('scene_id', 'work_id', 'created_at', 'sha256',
                        'source_corpus', 'license', 'pii_scrub_version')

def audit_100_random_scenes(corpus_dir: Path) -> dict:
    all_scenes = list(corpus_dir.glob('**/*.json'))
    sample = random.sample(all_scenes, min(100, len(all_scenes)))
    results = {'passed': 0, 'meta_missing': [],
               'sha_mismatches': [], 'sample_size': len(sample)}
    for path in sample:
        data = json.loads(path.read_text())
        if not all(k in data for k in REQUIRED_ATIA_FIELDS):
            missing = [k for k in REQUIRED_ATIA_FIELDS if k not in data]
            results['meta_missing'].append({'path': str(path), 'missing': missing})
            continue
        recomputed = hashlib.sha256(
            json.dumps({k: v for k, v in data.items() if k != 'sha256'},
                       sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        if recomputed != data['sha256']:
            results['sha_mismatches'].append(str(path))
            continue
        results['passed'] += 1
    return results

if __name__ == '__main__':
    import sys
    corpus = Path(sys.argv[1] if len(sys.argv) > 1 else 'corpus/')
    res = audit_100_random_scenes(corpus)
    print(f"PASS {res['passed']}/{res['sample_size']}")
    if res['meta_missing']: print(f"meta missing: {len(res['meta_missing'])}")
    if res['sha_mismatches']: print(f"sha mismatch: {len(res['sha_mismatches'])}")
    sys.exit(0 if res['passed'] == res['sample_size'] else 1)
```

### 10.3 Branch Protection (GitHub Settings, UI 작업)

```
Branch name pattern: main

[x] Require pull request reviews
    Required approving reviews: 1
    Dismiss stale on new commits: ON

[x] Require status checks to pass
    Required status checks:
      - ci / ruff
      - ci / pytest
      - ci / release_gate (60 Gates ALL PASS)
      - openapi_diff (V621)
      - helm_train_plane (V626)
      - helm_serve_plane (V627)
      - atia_mini_audit (V629)
    Require up to date: ON

[x] Require linear history (force push 차단)
[x] Do not allow bypassing
Restrict push: limsanghyuk only
```

V629 종료: Diataxis 4 + atia_mini_audit + Branch Protection + ADR-096 + 60 TC.

---

## §11. V630 — G61 6+1축 + v11.0.0 (3일)

### 11.1 G61 6+1축 (ADR-097 supersedes ADR-080)

```python
# literary_system/gates/phase_b_exit_gate.py (V630 확장, ADR-097)
import importlib

P_IF_TRACE_REQUIRED = [
    ('literary_system.llm_bridge.canonical_bridge_v2', 'AgentEnvelope', 'V621'),
    ('literary_system.llm_bridge.canonical_bridge_v2', 'RoutingPolicy', 'V621'),
    ('literary_system.multiwork.reader_feedback_ingest', 'ReaderFeedbackIngest', 'V621'),
    ('literary_system.multiwork.reader_feedback_ingest', 'ReaderFeedback', 'V621'),
    ('literary_system.serving.model_serving_endpoint', 'SEMVER', 'V621'),
]

def verify_interfaces_trace() -> dict:
    """C7: P-IF-01~05 표면 존재 (ADR-097, V621 retrofit 결과 검증)."""
    missing, found = [], []
    for mod_path, sym, v_src in P_IF_TRACE_REQUIRED:
        try:
            mod = importlib.import_module(mod_path)
            (found if hasattr(mod, sym) else missing).append(
                f"{mod_path}.{sym} ({v_src})")
        except ImportError as e:
            missing.append(f"{mod_path} ({v_src}) — ImportError: {e}")
    return {'pass': len(missing) == 0, 'found': found, 'missing': missing,
            'total': len(P_IF_TRACE_REQUIRED)}

class PhaseBExitGate:
    """ADR-097 (supersedes ADR-080). G61 6+1축."""
    AXES = ('C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7')   # 6 → 7

    def evaluate(self, report) -> dict:
        c7 = verify_interfaces_trace()
        checks = {
            'C1_LoRA_G54': report.g54_pass,
            'C2_RLHF_G56_G57': report.g56_pass and report.g57_pass,
            'C3_MultiWork_G59': report.g59_pass,
            'C4_Performance_G60': report.g60_pass,
            'C5_Gates_60': report.gates_total >= 60,
            'C6_Tests_7000': report.tests_total >= 7000,   # 6700 → 7000 강화
            'C7_Interfaces_Trace': c7['pass'],
        }
        report.c7_detail = c7
        return checks
```

### 11.2 v11.0.0 GitHub Release

```toml
# pyproject.toml
version = "11.0.0"
description = "Literary OS V630 — Phase B Complete (G61 6+1축, ADR-097)"
```

```markdown
# README.md
# Literary OS V630 (Phase B Complete)
[![Version](https://img.shields.io/badge/version-11.0.0-brightgreen)]()
[![Tests](https://img.shields.io/badge/tests-7228%2B%20PASS-brightgreen)]()
[![Gates](https://img.shields.io/badge/release%20gates-60%2F60%20PASS-brightgreen)]()
[![G61](https://img.shields.io/badge/G61-6%2B1축%20PASS-brightgreen)]()
```

```bash
git tag -a v11.0.0 -m "Phase B Complete — V630"
git push origin v11.0.0
gh release create v11.0.0 \
  --title "v11.0.0 — Phase B Complete (V630)" \
  --notes-file docs/changelog/CHANGELOG_V630.md
```

V630 종료: G61 6+1축 + ADR-097 + ATIA 100/100 + v11.0.0 release + 50 TC + 회귀 +45.

---

## §12. Gate + ADR 매트릭스

### 12.1 Gate 갱신
| Gate | V620 정의 | V630 갱신 | 비고 |
|---|---|---|---|
| G61 | 6축 (C1~C6, 6700+ Tests) | 6+1축 (C1~C7, 7000+ Tests) | ADR-080 → ADR-097 supersedes |

### 12.2 ADR 11건
| ADR | V | 제목 |
|---|---|---|
| ADR-088 | V621 | SP-B.2 retrofit (P-IF 3건) |
| ADR-089 | V622 | SP-B.3 retrofit (conflict+workload+adv) |
| ADR-090 | V623 | System Integration + Helm 사전 |
| ADR-091 | V624 | 24h 시나리오 + 메모리 회귀 |
| ADR-092 | V625 | biweekly_train + Lambda 폴백 |
| ADR-093 | V626 | TrainPlane Helm 검증 |
| ADR-094 | V627 | ServePlane Helm 신설 |
| ADR-095 | V628 | Grafana + Prometheus dashboard |
| ADR-096 | V629 | 운영 문서 + ATIA + Branch Protection |
| ADR-097 | V630 | G61 6+1축 + v11.0.0 (supersedes ADR-080) |
| ADR-PC-IF | V621/V630 | Phase C/D 인터페이스 트레이스 통합 |

---

## §13. 모듈 매트릭스 (총 30건)

| # | 경로 | V버전 | 신규/확장 | Tests + |
|---|---|---|---|---|
| 1 | AGENTS.md / tools/preflight_step15.py | V621-PRE | 확장 | +5 |
| 2 | canonical_bridge_v2.py | V621 | 확장 (AgentEnvelope) | +30 |
| 3 | reader_feedback_ingest.py | V621 | 신규 | +15 |
| 4 | model_serving_endpoint.py | V621 | 확장 (/openapi.yaml + SEMVER) | +15 |
| 5 | detect_openapi_breaking.py + export_openapi.py | V621 | 신규 | (CI) |
| 6 | openapi_diff.yml | V621 | 신규 | (CI) |
| 7 | shared_character_db_v2.py | V622 | 확장 (ConflictPolicy) | +25 |
| 8 | multi_work_orchestrator_v2.py | V622 | 확장 (WorkloadProfile) | +20 |
| 9 | reward_model.py | V622 | 확장 (adv_seeds 5종) | +15 |
| 10 | test_system_integration.py | V623 | 확장 | +30 |
| 11 | helm_*_test | V623 | 신규 | (CI) |
| 12 | test_v624_24h_scenario.py | V624 | 신규 | +15 |
| 13 | long_run_24h.yml | V624 | 신규 | (CI) |
| 14 | test_v624_memory_regression.py | V624 | 신규 | +15 |
| 15 | biweekly_train.yml | V625 | 신규 | (CI) |
| 16 | check_runpod_availability.py + notify_slack.py | V625 | 신규 | +20 |
| 17 | test_v625_auto_recovery.py | V625 | 신규 | +30 |
| 18 | helm_train_plane.yml | V626 | 신규 | (CI) |
| 19 | test_v626_helm_train.py | V626 | 신규 | +30 |
| 20 | deploy/helm/serve_plane/* | V627 | 신규 | (infra) |
| 21 | helm_serve_plane.yml | V627 | 신규 | (CI) |
| 22 | test_v627_helm_serve.py | V627 | 신규 | +50 |
| 23 | monitoring/prometheus/ + grafana/ | V628 | 신규 | +30 |
| 24 | docs/operations/ Diataxis 4 (9 문서) | V629 | 신규 | +15 |
| 25 | atia_mini_audit.py | V629 | 신규 | +25 |
| 26 | GitHub Branch Protection + test_branch_protect_status.py | V629 | 신규 | +20 |
| 27 | phase_b_exit_gate.py | V630 | 확장 (C7 + 7,000 강화) | +30 |
| 28 | pyproject.toml / README.md / CHANGELOG_V630.md | V630 | 확장 (v11.0.0) | - |
| 29 | docs/adr/ADR-088 ~ 097.md + ADR-PC-IF.md | 전 V | 신규 (11건) | - |
| 30 | 기존 60 Gates 회귀 + 통합 회귀 | V630 | 확장 | +65 |

총 30건. Tests +500.

---

## §14. V버전별 체크리스트

핸드오프 `2026-05-25_v621_v630_phase_b_main_handoff_v3.md` §4 참조.

---

## §15. 위험 신호

- PASS 6,728 → 6,720 미만 후퇴
- V621 retrofit이 V606 G56/G57 회귀 ≥1건
- V622 conflict_policy retrofit이 기존 코드 깸
- V625 biweekly_train dry_run 5회 연속 실패
- V627 ServePlane Ingress가 V605 ModelServing 충돌
- V629 ATIA 100건 sha256 mismatch ≥1건
- V630 verify_interfaces_trace() 실패
- V630 Tests 7,000 미달 (-50 이상)

---

## §16. 설계도 승인

본 V621~V630 Blueprint v3.0은 통합 본안 v3.0 제안서를 코드 수준으로 구체화한다.

- 10 V버전 + V621-PRE 사전 = 약 5주
- 30개 신규/확장 모듈
- 1개 Gate 갱신 (G61 6→7축) + 11개 ADR
- Tests +500 (V620 6,728 → V630 7,228+)
- V630 = v11.0.0 + Phase B 완전 종료 + Phase C 본안 트리거

V630 종료 시점 Literary OS는 한국 드라마 LoRA v1.0 (8B+3B) + RLHF v1.0 + MultiWork v2.0 + Phase B Exit G61 6+1축 + P-IF-01~05 + conflict_policy 5종 + workload_profile 1/2/3 SLO + adv_seeds 5종 + biweekly_train + Branch Protection + TrainPlane/ServePlane Helm + Grafana dashboard + Diataxis 4 운영 문서 + ATIA mini-audit + v11.0.0 / 60 Gates / 7,228+ Tests를 보유. **Phase C 진입의 모든 안정·인터페이스·운영·감사·문서 기반 완성.**

---

— V621~V630 Blueprint v3.0 (Markdown 미러) | 2026-05-25 —
