// V621~V630 통합 본안 v3.0 설계도 — 코드 스켈레톤 수준
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat,
  HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, PageBreak,
} = require('docx');

const border = { style: BorderStyle.SINGLE, size: 4, color: "888888" };
const borders = { top: border, bottom: border, left: border, right: border };

function p(text, opts) { opts = opts || {};
  return new Paragraph({
    spacing: { before: opts.before || 60, after: opts.after || 60 },
    alignment: opts.align,
    children: [new TextRun({ text: text, bold: opts.bold, italics: opts.italics, color: opts.color, size: opts.size || 22, font: "Malgun Gothic" })],
  });
}
function h(text, level) {
  const sizes = { 1: 30, 2: 26, 3: 24 };
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text: text, bold: true, size: sizes[level] || 22, font: "Malgun Gothic" })],
  });
}
function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 30, after: 30 },
    children: [new TextRun({ text: text, size: 22, font: "Malgun Gothic" })],
  });
}
function code(text) {
  return new Table({
    width: { size: 10080, type: WidthType.DXA },
    columnWidths: [10080],
    rows: [new TableRow({ children: [new TableCell({
      borders: borders,
      width: { size: 10080, type: WidthType.DXA },
      shading: { fill: "F2F2F2", type: ShadingType.CLEAR },
      margins: { top: 120, bottom: 120, left: 160, right: 160 },
      children: text.split('\n').map(function(line) {
        return new Paragraph({ spacing: { before: 0, after: 0 },
          children: [new TextRun({ text: line || ' ', size: 17, font: "Consolas" })] });
      }),
    })] })],
  });
}
function cell(text, width, opts) { opts = opts || {};
  return new TableCell({
    borders: borders,
    width: { size: width, type: WidthType.DXA },
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text: text, bold: opts.bold, size: opts.size || 19, font: "Malgun Gothic" })] })],
  });
}
function table(rows, widths, headerFill) {
  headerFill = headerFill || "C5E0F0";
  const total = widths.reduce(function(a,b){return a+b;}, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map(function(row, i) {
      return new TableRow({
        tableHeader: i === 0,
        children: row.map(function(c, j) { return cell(c, widths[j], { fill: i === 0 ? headerFill : undefined, bold: i === 0, size: 18 }); }),
      });
    }),
  });
}

const children = [];

// 표지
children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Literary OS", bold: true, size: 40, font: "Malgun Gothic" })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "V621~V630 통합 본안 설계도 v3.0", bold: true, size: 32, font: "Malgun Gothic" })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Sonnet 4.6 구현 지시서 — 10 V버전 코드 스켈레톤 + ADR-088~097", size: 24, font: "Malgun Gothic" })] }));
children.push(p(""));
children.push(p("기반 제안서: literary_os_v621_v630_phase_b_proposal_v3.docx (2026-05-25)", { align: AlignmentType.CENTER }));
children.push(p("기반 v2.0: literary_os_v601_v630_phase_b_blueprint_v2.docx (commit f16c5c8)", { align: AlignmentType.CENTER }));
children.push(p("V620_R supersedes: literary_os_v620_r_*.docx (참조 보존)", { align: AlignmentType.CENTER }));
children.push(p("Chief Architect × Chief Compiler × Chief System Principal Engineer", { align: AlignmentType.CENTER, bold: true }));
children.push(p("2026-05-25", { align: AlignmentType.CENTER }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// §0
children.push(h("§0. 본 설계도의 범위", 1));
children.push(p("본 설계도는 V621~V630 통합 본안 v3.0 제안서를 코드 수준으로 구체화한다. Sonnet 4.6 연산 모드가 본 문서 + 매핑된 본안 v2.0 + V620_R 코드 스켈레톤만으로 구현 가능하도록 자기완결적으로 작성한다."));
children.push(p("전제: v10.25.2 기준 main HEAD (60/60 Gates, 6,728+ Tests, G61 6축 PASS)."));
children.push(p("Sonnet 4.6 학습 우선순위:", { bold: true }));
children.push(bullet("1순위: docs/sessions/2026-05-25_v621_v630_phase_b_main_handoff_v3.md — 매 V 진입 시 필수"));
children.push(bullet("2순위: docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.md — 코드 스켈레톤 인용 시"));
children.push(bullet("3순위: docs/sessions/literary_os_v621_v630_phase_b_proposal_v3.docx + blueprint_v3.docx — 인간 검토"));
children.push(bullet("4순위 (보조): docs/sessions/literary_os_v601_v630_phase_b_blueprint_v2.docx (commit f16c5c8) — 본안 v2.0 원본"));
children.push(bullet("5순위 (보조): outputs/v620_r_patch/ — V620_R 산출물 (v3.0이 supersedes, 참조용)"));
children.push(p(""));

// §1 V621-PRE
children.push(h("§1. V621-PRE — 자동 학습 강제 (사전 작업, 0.5일)", 1));
children.push(p("목표: V620_R R0 흡수. AGENTS.md / preflight_step15에 자동 학습 강제."));

children.push(h("1.1 AGENTS.md 상단 추가", 2));
children.push(code(
`# AGENTS.md 최상단

## 🔴 필수 학습 (Critical Loading) — 모든 작업 시작 전

작업 시작 전 반드시 읽고 컨텍스트 포함:

1. docs/sessions/2026-05-25_v621_v630_phase_b_main_handoff_v3.md
2. docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.md
3. docs/audit/2026-05-25_phase_b_audit_report.docx

3개 파일이 컨텍스트에 없으면 절대 코드 작성 금지.
docx 추출: python -c "from docx import Document; ..."`
));

children.push(h("1.2 preflight_step15 추가", 2));
children.push(code(
`# tools/preflight_step15.py
REQUIRED_V3_FILES = [
    'docs/sessions/2026-05-25_v621_v630_phase_b_main_handoff_v3.md',
    'docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.md',
]

def verify_v3_handoff() -> dict:
    missing = [f for f in REQUIRED_V3_FILES if not Path(f).exists()]
    return {'pass': not missing, 'missing': missing}
`
));
children.push(p("V621-PRE 종료: AGENTS.md 갱신 + preflight 함수 추가 + 5 TC.", { italics: true }));
children.push(p(""));

// §2 V621 SP-B.2 retrofit
children.push(h("§2. V621 — SP-B.2 retrofit (P-IF 3건, 1주)", 1));
children.push(p("목표: AgentEnvelope (P-IF-01) + ReaderFeedbackIngest (P-IF-03) + OpenAPI SemVer (P-IF-04) 3건 동시 부착."));

children.push(h("2.1 AgentEnvelope — canonical_bridge_v2.py 확장", 2));
children.push(code(
`# literary_system/llm_bridge/canonical_bridge_v2.py (V621 확장, ADR-088)
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
        return self._route(env, decision)`
));

children.push(h("2.2 ReaderFeedbackIngest — 신규", 2));
children.push(code(
`# literary_system/multiwork/reader_feedback_ingest.py (V621 신규, ADR-088)
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
        return self._active`
));

children.push(h("2.3 OpenAPI SemVer — model_serving_endpoint.py 확장", 2));
children.push(code(
`# literary_system/serving/model_serving_endpoint.py (V621 확장, ADR-088)
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

# tools/detect_openapi_breaking.py + .github/workflows/openapi_diff.yml
# (V620_R R3 설계도 그대로 — 본 설계도 §3 참조)`
));
children.push(p("V621 종료: AgentEnvelope + ReaderFeedbackIngest + OpenAPI SemVer 3건 + ADR-088 + 60 TC + G56/G57 회귀 0건.", { italics: true }));
children.push(p(""));

// §3 V622 SP-B.3 retrofit
children.push(h("§3. V622 — SP-B.3 retrofit (3건, 1주)", 1));
children.push(p("목표: conflict_policy 5종 + workload_profile 1/2/3 SLO + adv_seeds 5종."));

children.push(h("3.1 conflict_policy — shared_character_db_v2.py 확장", 2));
children.push(code(
`# literary_system/multiwork/shared_character_db_v2.py (V622 확장, ADR-089)
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class ConflictPolicy(Enum):
    RENAME = "rename"
    MERGE = "merge"
    FORK = "fork"
    BLOCK = "block"
    ESCALATE = "escalate"

@dataclass
class ConflictPriority:
    has_copyright_holder: int   # 0=있음 우선
    appearance_count_neg: int   # 많을수록 우선 (음수)
    first_appearance_date: str

@dataclass
class ResolutionResult:
    winning_work_id: str
    policy_applied: ConflictPolicy
    audit_trail: List[ConflictPriority]

class SharedCharacterDBV2:
    def __init__(self, graph, provenance_ledger,
                 default_policy: ConflictPolicy = ConflictPolicy.ESCALATE):
        # 기존 + default_policy
        self.policy = default_policy

    def resolve(self, character_id: str,
                conflicting_work_ids: List[str]) -> ResolutionResult:
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
        )`
));

children.push(h("3.2 workload_profile — multi_work_orchestrator_v2.py 확장", 2));
children.push(code(
`# literary_system/multiwork/multi_work_orchestrator_v2.py (V622 확장, ADR-089)
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
                WorkloadProfile.TRIPLE: self.slo.triple_ms}[self.detect_profile()]`
));

children.push(h("3.3 adv_seeds — reward_model.py 확장", 2));
children.push(code(
`# literary_system/rlhf/reward_model.py (V622 retrofit, ADR-089)
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
    def score_with_adv_seeds(self, scenes: list, seeds: list = None) -> dict:
        seeds = seeds or ADV_SEEDS_REQUIRED
        results = {'blocked': 0, 'total': len(seeds), 'details': []}
        for seed in seeds:
            sig = self.score(seed.text, {'scene_id': seed.id})
            blocked = sig.marker_penalty >= seed.expected_penalty
            if blocked: results['blocked'] += 1
            results['details'].append({'seed': seed.id,
                                       'blocked': blocked,
                                       'penalty': sig.marker_penalty})
        return results`
));
children.push(p("V622 종료: 3건 retrofit + ADR-089 + 60 TC + G58/G59 회귀 0건.", { italics: true }));
children.push(p(""));

// §4 V623~V624
children.push(h("§4. V623 — SystemIntegrationTest + Helm 사전 검증 (3일)", 1));
children.push(code(
`# tests/integration/test_system_integration.py (V623 확장)
def test_lora_rlhf_multiwork_e2e_v623():
    """V613 base + V621/V622 retrofit 결과 통합 검증."""
    # 1) LoRA 추론
    out = lora_gateway.call("test")
    # 2) RewardModel + adv_seeds 5종 (V622 retrofit)
    adv_result = reward_model.score_with_adv_seeds(scenes=[out])
    assert adv_result['blocked'] >= 4  # 5건 중 4 이상 차단
    # 3) AgentEnvelope (V621 retrofit)
    from literary_system.llm_bridge.canonical_bridge_v2 import AgentEnvelope, AgentRole
    env = AgentEnvelope(agent_id='default', role=AgentRole.SCENE_WRITER, prompt='x')
    out2 = bridge.generate(env)
    # 4) MultiWork 3작품 + conflict_policy
    for w in ['drama_a', 'drama_b', 'drama_c']:
        orchestrator.submit(w, scene_request={'prompt': 'next'})
    profile = orchestrator.detect_profile()
    assert profile == WorkloadProfile.TRIPLE
    assert orchestrator.slo_for_current() == 8000  # ≤8초

# Helm 사전 검증 (P-Arch-01)
def test_helm_train_plane_lint():
    result = subprocess.run(['helm', 'lint', 'deploy/helm/train_plane'])
    assert result.returncode == 0

def test_helm_train_plane_dry_run():
    result = subprocess.run(['helm', 'install', '--dry-run', '--debug',
                             'train-plane', 'deploy/helm/train_plane'])
    assert result.returncode == 0`
));
children.push(p("V623 종료: E2E 확장 + Helm 사전 lint + dry-run + ADR-090 + 30 TC.", { italics: true }));
children.push(p(""));

children.push(h("§5. V624 — 24h 장기 시나리오 + 메모리 회귀 (3일)", 1));
children.push(code(
`# tests/integration/test_v624_24h_scenario.py (신규)
import time
from literary_system.optimization.long_run_monitor import LongRunMonitor
from literary_system.optimization.memory_leak_detector import MemoryLeakDetector

@pytest.mark.slow                    # 일반 CI에서 skip
@pytest.mark.timeout(86400 + 600)    # 24h + 10min 여유
def test_24h_continuous_generation():
    """V617 LongRunMonitor + V616 MemoryLeak 통합 24h."""
    monitor = LongRunMonitor(duration_seconds=86400)
    leak = MemoryLeakDetector()
    leak.start()
    monitor.start()
    while monitor.is_running():
        out = bridge.generate(AgentEnvelope(prompt="continuous test"))
        monitor.record_request()
        if monitor.elapsed_seconds() % 3600 == 0:
            snapshot = leak.snapshot()
            assert snapshot.growth_rate_mb_per_hour < 10  # 시간당 10MB 미만
    leak.stop()
    report = monitor.summary()
    assert report.error_rate < 0.005
    assert report.p95_latency_ms < 1500

# .github/workflows/long_run_24h.yml
# schedule: cron '0 0 * * 0'  # 매주 일요일 자정
# runs-on: self-hosted-gpu
# manual trigger only`
));
children.push(p("V624 종료: 24h 시나리오 + 메모리 회귀 + ADR-091 + 30 TC.", { italics: true }));
children.push(p(""));

// §6 V625 biweekly
children.push(h("§6. V625 — biweekly_train + Lambda 폴백 + 자동 복구 (1주)", 1));
children.push(code(
`# .github/workflows/biweekly_train.yml (V625 신규, ADR-092)
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
      - name: Fallback Lambda H100
        if: failure()
        run: |
          python tools/notify_slack.py --channel '#losdb-ops' \\
            --msg "RunPod 부족 — Lambda H100 전환"
          python literary_system/finetune/lora_job_runner.py \\
            --backend lambda_h100 --dry-run
      - name: Run training (dry)
        run: |
          python literary_system/finetune/lora_job_runner.py \\
            --base llama-3.1-8b --dry-run
      - name: Notify done
        if: always()
        run: python tools/notify_slack.py --msg "Training cycle done"
`
));
children.push(code(
`# tools/check_runpod_availability.py (V625 신규)
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
    notify(**vars(parser.parse_args()))`
));
children.push(p("V625 종료: biweekly_train.yml + check_runpod + notify_slack + auto_recovery + ADR-092 + 50 TC.", { italics: true }));
children.push(p(""));

// §7 V626 TrainPlane Helm 검증
children.push(h("§7. V626 — TrainPlane Helm 검증 (3일)", 1));
children.push(code(
`# .github/workflows/helm_train_plane.yml (V626 신규, ADR-093)
name: TrainPlane Helm Validation
on:
  pull_request:
    paths:
      - 'deploy/helm/train_plane/**'
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
      - name: Helm template (dry render)
        run: helm template train-plane deploy/helm/train_plane > /tmp/rendered.yaml
      - name: Kubeval (schema)
        run: |
          curl -L https://github.com/instrumenta/kubeval/releases/latest/download/kubeval-linux-amd64.tar.gz | tar xz
          ./kubeval /tmp/rendered.yaml
      - name: Helm test (if kind cluster available)
        if: env.KIND_AVAILABLE == 'true'
        run: |
          helm install --dry-run train-plane deploy/helm/train_plane
`
));
children.push(p("V626 종료: Helm 검증 workflow + ADR-093 + 30 TC.", { italics: true }));
children.push(p(""));

// §8 V627 ServePlane Helm 신설
children.push(h("§8. V627 — ServePlane Helm 신설 + 검증 (1주)", 1));
children.push(code(
`# deploy/helm/serve_plane/Chart.yaml (V627 신규, ADR-094)
apiVersion: v2
name: serve-plane
description: Literary OS ServePlane — FastAPI ModelServing + Canary
type: application
version: 1.0.0
appVersion: "10.25.2"

# deploy/helm/serve_plane/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-serving
spec:
  replicas: {{ .Values.replicas | default 2 }}
  selector:
    matchLabels:
      app: model-serving
  template:
    spec:
      containers:
      - name: model-serving
        image: {{ .Values.image }}
        ports:
        - containerPort: 8000
        env:
        - name: LORA_ARTIFACT_PATH
          value: {{ .Values.loraArtifactPath }}
        readinessProbe:
          httpGet: { path: /health, port: 8000 }
        livenessProbe:
          httpGet: { path: /health, port: 8000 }

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
        backend:
          service: { name: model-serving, port: { number: 8000 } }
      - path: /openapi.yaml      # V621 retrofit
        pathType: Exact
        backend:
          service: { name: model-serving, port: { number: 8000 } }

# .github/workflows/helm_serve_plane.yml (V626와 동일 패턴)`
));
children.push(p("V627 종료: ServePlane Helm chart + Ingress (openapi.yaml 포함) + 검증 workflow + ADR-094 + 50 TC.", { italics: true }));
children.push(p(""));

// §9 V628 Grafana + Prometheus
children.push(h("§9. V628 — Grafana + Prometheus dashboard (3일)", 1));
children.push(code(
`# monitoring/prometheus/scrape_config.yml (V628 신규, ADR-095)
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

# monitoring/grafana/dashboards/cost_slo.json (V628 신규)
{
  "title": "LOS Cost SLO Dashboard",
  "panels": [
    {"title": "Daily GPU Cost (USD)",
     "targets": [{"expr": "sum(rate(gpu_cost_total[1d])) by (backend)"}]},
    {"title": "Monthly Cost vs SLO",
     "targets": [{"expr": "sum(gpu_cost_total) / 120"}]},   # SLO $120
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
}`
));
children.push(p("V628 종료: prometheus scrape + grafana dashboards 2종 + ADR-095 + 30 TC.", { italics: true }));
children.push(p(""));

// §10 V629
children.push(h("§10. V629 — 운영 문서 + ATIA mini-audit + Branch Protection (1주)", 1));

children.push(h("10.1 Phase B 운영 문서 (Diataxis 4)", 2));
children.push(code(
`# docs/operations/ (V629 신규, ADR-096)
docs/operations/
├── tutorial/          # 학습용 (How to first run LoRA training)
│   ├── 01_first_lora_training.md
│   ├── 02_rlhf_cycle.md
│   └── 03_multiwork_3works.md
├── how_to/            # 작업 가이드 (How to ...)
│   ├── add_new_lora_adapter.md
│   ├── debug_rlhf_kl_divergence.md
│   └── recover_from_canary_rollback.md
├── reference/         # API 참조
│   ├── api_v1.0.0_reference.md   # OpenAPI yaml 기반
│   ├── lora_artifact_3tag.md
│   └── adv_seeds_5kinds.md
└── explanation/       # 개념 설명
    ├── phase_b_architecture.md
    ├── g61_6plus1_axes.md
    └── p_if_traces.md`
));

children.push(h("10.2 ATIA mini-audit", 2));
children.push(code(
`# tools/atia_mini_audit.py (V629 신규, ADR-096)
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
            results['meta_missing'].append({'path': str(path),
                                            'missing': missing})
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
    sys.exit(0 if res['passed'] == res['sample_size'] else 1)`
));

children.push(h("10.3 Branch Protection (GitHub Settings)", 2));
children.push(code(
`# V629 수행 시 GitHub Settings → Branches → Add rule (ADR-096)
Branch name pattern: main

[x] Require pull request reviews
    Required approving reviews: 1
    Dismiss stale approvals on new commits: ON

[x] Require status checks to pass
    Required status checks:
      - ci / ruff
      - ci / pytest
      - ci / release_gate (60 Gates ALL PASS)
      - openapi_diff (V621 retrofit)
      - helm_train_plane (V626)
      - helm_serve_plane (V627)
      - atia_mini_audit (V629)
    Require up to date: ON

[x] Require linear history (force push 차단)
[x] Do not allow bypassing
Restrict push: limsanghyuk only`
));
children.push(p("V629 종료: Diataxis 4 문서 + atia_mini_audit.py + Branch Protection 적용 + ADR-096 + 60 TC.", { italics: true }));
children.push(p(""));

// §11 V630
children.push(h("§11. V630 — G61 6+1축 + v11.0.0 GitHub Release (3일)", 1));

children.push(h("11.1 G61 6+1축 (ADR-097 supersedes ADR-080)", 2));
children.push(code(
`# literary_system/gates/phase_b_exit_gate.py (V630 확장, ADR-097)
import importlib

P_IF_TRACE_REQUIRED = [
    # (모듈, 심볼, V버전 출처)
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
            missing.append(f"{mod_path} — ImportError ({v_src}): {e}")
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
        return checks`
));

children.push(h("11.2 v11.0.0 GitHub Release", 2));
children.push(code(
`# pyproject.toml
version = "11.0.0"
description = "Literary OS V630 — Phase B Complete (G61 6+1축, ADR-097)"

# README.md
# Literary OS V630 (Phase B Complete)
[![Version](https://img.shields.io/badge/version-11.0.0-brightgreen)]()
[![Tests](https://img.shields.io/badge/tests-7228%2B%20PASS-brightgreen)]()
[![Gates](https://img.shields.io/badge/release%20gates-60%2F60%20PASS-brightgreen)]()
[![G61](https://img.shields.io/badge/G61-6%2B1축%20PASS-brightgreen)]()

# GitHub Release
git tag -a v11.0.0 -m "Phase B Complete — V630"
git push origin v11.0.0
gh release create v11.0.0 \\
  --title "v11.0.0 — Phase B Complete (V630)" \\
  --notes-file docs/changelog/CHANGELOG_V630.md`
));
children.push(p("V630 종료: G61 6+1축 + ADR-097 + ATIA 100건 0 mismatch + v11.0.0 release + 50 TC + 회귀 +45 TC.", { italics: true }));
children.push(p(""));

// §12 Gate + ADR 매트릭스
children.push(h("§12. Gate + ADR 매트릭스 (V621~V630)", 1));
children.push(table([
  ["Gate", "현 정의 (V620)", "V630 갱신", "비고"],
  ["G61", "Phase B Exit 6축 (C1~C6, 6700+ Tests)", "Phase B Exit 6+1축 (C1~C7, 7000+ Tests)", "ADR-080 → ADR-097 supersedes. C7 verify_interfaces_trace 추가"],
], [600, 3500, 3500, 1480]));
children.push(p(""));
children.push(table([
  ["ADR", "V버전", "제목", "주요 결정"],
  ["ADR-088", "V621", "SP-B.2 retrofit (P-IF 3건)", "AgentEnvelope + ReaderFeedbackIngest + OpenAPI SemVer 통합"],
  ["ADR-089", "V622", "SP-B.3 retrofit (3건)", "conflict_policy 5종 + workload_profile + adv_seeds 5종"],
  ["ADR-090", "V623", "System Integration + Helm 사전 검증", "E2E + helm lint + dry-run"],
  ["ADR-091", "V624", "24h 시나리오 + 메모리 회귀", "scheduled long-run + tracemalloc"],
  ["ADR-092", "V625", "biweekly_train + Lambda 폴백", "매월 1·15일 02:00 KST + 자동 전환"],
  ["ADR-093", "V626", "TrainPlane Helm 검증", "helm lint + kubeval + dry-run"],
  ["ADR-094", "V627", "ServePlane Helm 신설", "deploy/helm/serve_plane/ + Ingress"],
  ["ADR-095", "V628", "Grafana + Prometheus 표준", "Cost SLO + α drift dashboard"],
  ["ADR-096", "V629", "운영 문서(Diataxis) + ATIA + Branch Protection", "Diataxis 4 + 100건 감리 + main sign-off"],
  ["ADR-097", "V630", "G61 6+1축 + v11.0.0 (supersedes ADR-080)", "C7 verify_interfaces_trace + semver major"],
  ["ADR-PC-IF", "V621/V630", "Phase C/D 인터페이스 트레이스 통합", "P-IF-01~05 명세 + V621 retrofit 결과"],
], [800, 700, 4000, 3580]));
children.push(p(""));

// §13 모듈 매트릭스
children.push(h("§13. 신규/확장 모듈 매트릭스 (총 24건)", 1));
children.push(table([
  ["#", "경로", "V버전", "신규/확장", "Tests +"],
  ["1", "AGENTS.md / tools/preflight_step15.py", "V621-PRE", "확장", "+5"],
  ["2", "literary_system/llm_bridge/canonical_bridge_v2.py", "V621", "확장 (AgentEnvelope+RoutingPolicy 4축)", "+30"],
  ["3", "literary_system/multiwork/reader_feedback_ingest.py", "V621", "신규", "+15"],
  ["4", "literary_system/serving/model_serving_endpoint.py", "V621", "확장 (/openapi.yaml + SEMVER)", "+15"],
  ["5", "tools/detect_openapi_breaking.py + export_openapi.py", "V621", "신규", "(CI)"],
  ["6", ".github/workflows/openapi_diff.yml", "V621", "신규", "(CI)"],
  ["7", "literary_system/multiwork/shared_character_db_v2.py", "V622", "확장 (ConflictPolicy 5종)", "+25"],
  ["8", "literary_system/multiwork/multi_work_orchestrator_v2.py", "V622", "확장 (WorkloadProfile)", "+20"],
  ["9", "literary_system/rlhf/reward_model.py", "V622", "확장 (adv_seeds 5종)", "+15"],
  ["10", "tests/integration/test_system_integration.py", "V623", "확장 (V621/V622 통합)", "+30"],
  ["11", "tests/integration/helm_*_test", "V623", "신규", "(CI)"],
  ["12", "tests/integration/test_v624_24h_scenario.py", "V624", "신규", "+15"],
  ["13", ".github/workflows/long_run_24h.yml", "V624", "신규", "(CI)"],
  ["14", "tests/integration/test_v624_memory_regression.py", "V624", "신규", "+15"],
  ["15", ".github/workflows/biweekly_train.yml", "V625", "신규", "(CI)"],
  ["16", "tools/check_runpod_availability.py + notify_slack.py", "V625", "신규", "+20"],
  ["17", "tests/test_v625_auto_recovery.py", "V625", "신규", "+30"],
  ["18", ".github/workflows/helm_train_plane.yml", "V626", "신규", "(CI)"],
  ["19", "tests/test_v626_helm_train.py", "V626", "신규", "+30"],
  ["20", "deploy/helm/serve_plane/* (Chart + templates)", "V627", "신규", "(infra)"],
  ["21", ".github/workflows/helm_serve_plane.yml", "V627", "신규", "(CI)"],
  ["22", "tests/test_v627_helm_serve.py", "V627", "신규", "+50"],
  ["23", "monitoring/prometheus/ + monitoring/grafana/dashboards/", "V628", "신규", "+30"],
  ["24", "docs/operations/{tutorial,how_to,reference,explanation}/", "V629", "신규", "+15"],
  ["25", "tools/atia_mini_audit.py", "V629", "신규", "+25"],
  ["26", "GitHub Branch Protection 설정 + tests/test_branch_protect_status.py", "V629", "신규", "+20"],
  ["27", "literary_system/gates/phase_b_exit_gate.py", "V630", "확장 (C7 verify_interfaces_trace + 7,000 강화)", "+30"],
  ["28", "pyproject.toml / README.md / docs/changelog/CHANGELOG_V630.md", "V630", "확장 (v11.0.0)", "-"],
  ["29", "docs/adr/ADR-088 ~ ADR-097.md + ADR-PC-IF.md", "전 V", "신규 (11건)", "-"],
  ["30", "기존 60 Gates 회귀 + 통합 회귀 보강", "V630", "확장", "+65"],
], [400, 4200, 800, 2800, 1080]));
children.push(p("총 신규/확장: 30건 (+CI 워크플로우 8건 + Helm chart 1식 + Branch Protection 1식). Tests +500 (V620 6,728 → V630 7,228+).", { italics: true }));
children.push(p(""));

// §14 V버전별 체크리스트
children.push(h("§14. V버전별 핵심 체크리스트 (Sonnet 4.6 작업 순서)", 1));

children.push(h("14.1 V621-PRE (0.5일)", 2));
[
  "[ ] AGENTS.md 상단 '필수 학습' 블록 추가 (handoff_v3 + blueprint_v3 강제)",
  "[ ] tools/preflight_step15.py: verify_v3_handoff() 함수 추가",
  "[ ] +5 TC",
  "[ ] commit: 'V621-PRE: 자동 학습 강제 (R0 흡수)'",
].forEach(function(t){ children.push(bullet(t)); });

children.push(h("14.2 V621 (1주)", 2));
[
  "[ ] canonical_bridge_v2.py: AgentRole + AgentEnvelope + RoutingPolicy 4축 + generate() 하위 호환",
  "[ ] reader_feedback_ingest.py 신규: ReaderFeedback + Ingest + RewardSignalAdapter Protocol",
  "[ ] model_serving_endpoint.py: SEMVER + /openapi.yaml + /api_version",
  "[ ] tools/detect_openapi_breaking.py + tools/export_openapi.py 신규",
  "[ ] .github/workflows/openapi_diff.yml 신규 (warn-only 1주 → fail mode)",
  "[ ] ADR-088 작성 + ADR-PC-IF 초안",
  "[ ] +60 TC + G56/G57 회귀 0건",
  "[ ] commit: 'V621: SP-B.2 retrofit P-IF 3건 (ADR-088, P-IF-01/03/04)'",
].forEach(function(t){ children.push(bullet(t)); });

children.push(h("14.3 V622 (1주)", 2));
[
  "[ ] shared_character_db_v2.py: ConflictPolicy 5종 + ConflictPriority + resolve()",
  "[ ] multi_work_orchestrator_v2.py: WorkloadProfile + SLOByProfile + detect_profile()",
  "[ ] reward_model.py: AdvSeed + ADV_SEEDS_REQUIRED 5종 + score_with_adv_seeds()",
  "[ ] ADR-089 작성",
  "[ ] +60 TC + G58/G59 회귀 0건",
  "[ ] commit: 'V622: SP-B.3 retrofit conflict+workload+adv_seeds (ADR-089)'",
].forEach(function(t){ children.push(bullet(t)); });

children.push(h("14.4 V623 (3일)", 2));
[
  "[ ] test_system_integration.py: V621/V622 통합 검증 추가",
  "[ ] Helm 사전 lint + dry-run 검증 함수",
  "[ ] ADR-090 작성",
  "[ ] +30 TC",
  "[ ] commit: 'V623: SystemIntegration + Helm 사전 검증 (ADR-090)'",
].forEach(function(t){ children.push(bullet(t)); });

children.push(h("14.5 V624 (3일)", 2));
[
  "[ ] test_v624_24h_scenario.py: LongRunMonitor + MemoryLeakDetector 통합",
  "[ ] long_run_24h.yml workflow (수동 트리거 + 매주 일요일)",
  "[ ] 메모리 회귀 baseline + assertion",
  "[ ] ADR-091 작성",
  "[ ] +30 TC",
  "[ ] commit: 'V624: 24h 시나리오 + 메모리 회귀 (ADR-091)'",
].forEach(function(t){ children.push(bullet(t)); });

children.push(h("14.6 V625 (1주)", 2));
[
  "[ ] biweekly_train.yml + check_runpod_availability.py + notify_slack.py",
  "[ ] auto_recovery.py (Lambda 폴백 + 알림)",
  "[ ] dry_run 모드 기본 + 실 학습은 운영자 수동",
  "[ ] ADR-092 작성",
  "[ ] +50 TC",
  "[ ] commit: 'V625: biweekly_train + Lambda 폴백 (ADR-092)'",
].forEach(function(t){ children.push(bullet(t)); });

children.push(h("14.7 V626 (3일)", 2));
[
  "[ ] helm_train_plane.yml: helm lint + kubeval + dry-run",
  "[ ] tests/test_v626_helm_train.py",
  "[ ] ADR-093 작성",
  "[ ] +30 TC",
  "[ ] commit: 'V626: TrainPlane Helm 검증 (ADR-093)'",
].forEach(function(t){ children.push(bullet(t)); });

children.push(h("14.8 V627 (1주)", 2));
[
  "[ ] deploy/helm/serve_plane/Chart.yaml + templates/{deployment,ingress,service,configmap}",
  "[ ] Ingress에 /generate + /openapi.yaml + /model_card 모두 라우팅",
  "[ ] helm_serve_plane.yml workflow",
  "[ ] tests/test_v627_helm_serve.py",
  "[ ] ADR-094 작성",
  "[ ] +50 TC",
  "[ ] commit: 'V627: ServePlane Helm 신설 + 검증 (ADR-094)'",
].forEach(function(t){ children.push(bullet(t)); });

children.push(h("14.9 V628 (3일)", 2));
[
  "[ ] monitoring/prometheus/scrape_config.yml",
  "[ ] monitoring/grafana/dashboards/{cost_slo,krippendorff_alpha,gpu_util,p95_latency}.json",
  "[ ] dashboard JSON schema 검증 테스트",
  "[ ] ADR-095 작성",
  "[ ] +30 TC",
  "[ ] commit: 'V628: Grafana + Prometheus dashboard (ADR-095)'",
].forEach(function(t){ children.push(bullet(t)); });

children.push(h("14.10 V629 (1주)", 2));
[
  "[ ] docs/operations/ Diataxis 4 카테고리 신설 + 9 문서",
  "[ ] tools/atia_mini_audit.py + 실 감리 1회 실행 (100건 무작위)",
  "[ ] GitHub Settings → Branch Protection 적용 (UI)",
  "[ ] tests/test_branch_protect_status.py (status check 검증)",
  "[ ] ADR-096 작성",
  "[ ] +60 TC",
  "[ ] commit: 'V629: 운영 문서 + ATIA + Branch Protection (ADR-096)'",
].forEach(function(t){ children.push(bullet(t)); });

children.push(h("14.11 V630 (3일)", 2));
[
  "[ ] phase_b_exit_gate.py: P_IF_TRACE_REQUIRED + verify_interfaces_trace() + AXES C7 + Tests 7,000 강화",
  "[ ] pyproject.toml version 10.25.2 → 11.0.0 + description 갱신",
  "[ ] README.md badge 4종 갱신 (version/tests/gates/G61)",
  "[ ] docs/changelog/CHANGELOG_V630.md (v11.0.0)",
  "[ ] live_core_manifest.json + MANIFEST.md 갱신",
  "[ ] ATIA mini-audit 100건 0 mismatch 최종 확인",
  "[ ] 최종 검증: pytest tests/ -q (7,228+ PASS), release_gate.py (60/60 PASS), G61 6+1축 PASS",
  "[ ] git tag -a v11.0.0 + gh release create v11.0.0",
  "[ ] ADR-097 작성 (supersedes ADR-080)",
  "[ ] commit: 'V630: G61 6+1축 + v11.0.0 — Phase B Complete (ADR-097)'",
  "[ ] 상위 연산 모드 호출 (Opus): 'Phase C (V631~) 본안 v3.0 작성 요청'",
].forEach(function(t){ children.push(bullet(t)); });
children.push(p(""));

// §15 위험 신호
children.push(h("§15. 위험 신호 — 상위 모드 호출 조건", 1));
children.push(bullet("PASS 6,728 → 6,720 미만 후퇴 (any V)"));
children.push(bullet("V621 retrofit 시 G56/G57 회귀 ≥1건"));
children.push(bullet("V622 conflict_policy retrofit이 기존 SharedCharacterDBV2 사용 코드 깸"));
children.push(bullet("V625 biweekly_train dry_run 5회 연속 실패"));
children.push(bullet("V627 ServePlane Helm Ingress가 V605 ModelServing 라우팅 충돌"));
children.push(bullet("V629 ATIA mini-audit 100건 중 sha256 mismatch ≥1건"));
children.push(bullet("V629 Branch Protection 적용 후 PR 흐름 차단 (false positive)"));
children.push(bullet("V630 verify_interfaces_trace() 실패 (V621 retrofit 누락)"));
children.push(bullet("V630 Tests 7,000 미달 (-50 이상)"));
children.push(p(""));

// §16 결론
children.push(h("§16. 설계도 승인", 1));
children.push(p("본 V621~V630 Blueprint v3.0은 통합 본안 v3.0 제안서를 코드 수준으로 구체화한다."));
children.push(bullet("10 V버전 + V621-PRE 사전 = 약 5주"));
children.push(bullet("30개 신규/확장 모듈 (코드 + CI 8 + Helm 1식 + Branch Protection)"));
children.push(bullet("1개 Gate 갱신 (G61 6→7축, ADR-080 → ADR-097 supersedes) + 11개 ADR (088~097 + PC-IF)"));
children.push(bullet("Tests +500 (V620 6,728 → V630 7,228+)"));
children.push(bullet("V630 종료 = v11.0.0 + Phase B 완전 종료 + Phase C 본안 작성 트리거"));
children.push(p(""));
children.push(p("V630 종료 시점 Literary OS는 한국 드라마 LoRA v1.0 (8B+3B) + RLHF v1.0 + MultiWork v2.0 + Phase B Exit G61 6+1축 + P-IF-01~05 + conflict_policy 5종 + workload_profile 1/2/3 SLO + adv_seeds 5종 + biweekly_train + Branch Protection + TrainPlane/ServePlane Helm + Grafana dashboard + Diataxis 4 운영 문서 + ATIA mini-audit + v11.0.0 / 60 Gates / 7,228+ Tests를 보유한다. Phase C 진입의 모든 안정·인터페이스·운영·감사·문서 기반이 완성된다.", { bold: true }));
children.push(p(""));
children.push(p("Chief Architect       Chief Compiler       Chief System Principal Engineer", { bold: true, align: AlignmentType.CENTER }));
children.push(p("___________          ___________          ___________________________", { align: AlignmentType.CENTER }));
children.push(p(""));
children.push(p("V621~V630 Blueprint v3.0 (Final) | Based on v2.0 commit f16c5c8 | 2026-05-25", { align: AlignmentType.CENTER, italics: true }));

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Malgun Gothic", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Malgun Gothic" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Malgun Gothic" },
        paragraph: { spacing: { before: 180, after: 90 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [
      { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
    ] },
  ] },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1080, bottom: 1440, left: 1080 } },
    },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Literary OS — V621~V630 Blueprint v3.0", size: 18, font: "Malgun Gothic", italics: true })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " / ", PageNumber.TOTAL_PAGES], size: 18, font: "Malgun Gothic" })] })] }) },
    children: children,
  }],
});

Packer.toBuffer(doc).then(function(buf) {
  fs.writeFileSync('literary_os_v621_v630_phase_b_blueprint_v3.docx', buf);
  console.log('OK blueprint v3', buf.length);
});
