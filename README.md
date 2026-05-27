# Literary OS V655

> **판단은 로컬, 생성만 LLM, 학습은 누적**  
> AI 기반 장편 소설·드라마 시나리오 생성 시스템

[![Version](https://img.shields.io/badge/version-11.28.0-blue)]()
[![Tests](https://img.shields.io/badge/tests-8053%20PASS-brightgreen)]()
[![Gates](https://img.shields.io/badge/release%20gates-66%2F66%20PASS-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 빠른 시작

```bash
# 설치
pip install -e ".[dev]"

# 전체 테스트 실행
pytest tests/ -q
# → 8053 passed

# 릴리즈 게이트 확인
python -m tools.run_release_gate
# → RELEASE GATE PASS: 66/66 gates passed
```

---

## 시스템 개요

Literary OS는 장편 서사 생성을 위한 AI 파이프라인입니다.  
외부 LLM은 산문 생성에만 선택적으로 사용하며, 플롯·캐릭터·구조 판단은 전부 로컬 모델이 처리합니다 (**LLM-0 원칙**, ADR-015/031).

```
literary_system/
├── agents/               # SP-C.2 멀티에이전트 앙상블 (V646~V653)
│   ├── director_agent.py    # DirectorAgent + MicroPlanner
│   ├── script_agent.py      # ScriptAgent + LoRA InferenceGateway
│   ├── critic_agent.py      # CriticAgent + CriticReport (PASS_THRESHOLD=0.65)
│   ├── editor_agent.py      # EditorAgent + KoreanCadencePlanner
│   ├── agent_coordinator.py # AgentCoordinator (max_rounds=3)
│   ├── ensemble_memory_cache.py  # EnsembleMemoryCache + TTL
│   └── agent_safety_guard.py    # AgentSafetyGuard 5축 검증
├── ensemble/             # 앙상블 게이트 (V654~V655)
│   ├── mae_multiwork_gate.py     # MAEMultiWorkGate G66 (P95≤8s)
│   └── suite_registration_gate.py # SuiteRegistrationGate G67
├── constitution/         # LOSConstitution v2 + Bayesian Opt (SP-C.1)
├── graph_intelligence/   # NKG 지식 그래프 + 감정 링커
├── orchestrators/        # 장편 지속 오케스트레이터
├── predictive/           # PNE — 예측적 서사 엔진
├── corpus/               # 외부 코퍼스 브릿지 — BGE-M3 + CIM
├── multiwork/            # 다중작품 관리 오케스트레이터
├── db/                   # LOSDB — SQL/Vector/Graph 스토리지 + Facade
├── gates/                # 릴리즈 게이트 66종 (G01~G67)
├── adapters_live/        # LLM 어댑터 (Claude / OpenAI / Ollama)
└── ...
```

---

## 릴리즈 이력 요약

| 단계 | 버전 | 주요 내용 | 게이트 |
|------|------|-----------|--------|
| Phase 6 | V546~V571 | PNE / CorpusIngestor / MultiWork / AsyncDiscipline | G25~G31 |
| 거버넌스 | V575~V580 | DEV_MODE 보안패치 / Logging / 어댑터 캐노니컬 | G32~G39 |
| LOSDB | V581~V586 | SQL/Vector/Graph REAL + Facade + cross_query | G40~G45 |
| SP-A | V587~V595 | E2EProseGate / GPU SLO / EquivalenceTester / Constitution / CLI | G46~G52 |
| SP-B.1 | V596~V600 | LoRA Fine-tuning Pipeline + HuggingFace | G53~G54 |
| SP-B.2 | V601~V606 | RLHF 루프 / PPO / Reward / ConstitutionAxis | G55~G57 |
| SP-B.3 | V607~V620 | MultiWork 협업 / LoRAStacking / SharedDB | G58~G60 |
| SP-B.4 | V621~V630 | 통합 최적화 / Helm / Monitoring / Phase B Exit | **G61** |
| SP-C.1 | V631~V640 | 자기학습 엔진 / AutoPromotion / SelfLearningMonitor / ContaminationDetector | G62~G63 |
| **SP-C.2** | **V646~V655** | **멀티에이전트 앙상블 / MAE-MultiWork / SuiteRegistration** | **G64~G67** |

---

## 릴리즈 게이트 — 66/66 PASS

```python
from literary_system.gates.release_gate import run_release_gate
result = run_release_gate()
# {"status": "pass", "gates_passed": 66, "total_gates": 66}
```

| 범위 | 게이트 | 내용 |
|------|--------|------|
| G01~G24 | Phase 1~5 | LLM-0 / Arc / RAG / SLM / MultiTenant / RLHF POC |
| G25~G39 | Phase 6 + 거버넌스 | PNE / Corpus / MultiWork / DEV_MODE / AsyncDiscipline |
| G40~G52 | LOSDB + SP-A | SQL/Vector/Graph REAL / E2EProseGate / CLI Exit |
| G53~G61 | SP-B | LoRA Inference / FineTune / PPO / RLHF / LoRAStacking / Phase B Exit |
| G62~G63 | SP-C.1 | AutoPromotionGate (R≥0.78) / SelfLearningGate |
| **G64** | **SP-C.2** | **AgentCoordinatorGate — 오케스트레이션 7CP** |
| **G65** | **SP-C.2** | **EnsembleQualityGate — R≥0.83** |
| **G66** | **SP-C.2** | **MAEMultiWorkGate — P95≤8.0s, 3작품 동시** |
| **G67** | **SP-C.2** | **SuiteRegistrationGate — 4조건 종합 (HF 등록 준비)** |

---

## SP-C.2 멀티에이전트 앙상블 (신규)

```python
from literary_system.ensemble.mae_multiwork_gate import MAEMultiWorkGate, ProjectRunSpec
from literary_system.ensemble.suite_registration_gate import SuiteRegistrationGate

# 3작품 동시 P95 성능 검증
gate = MAEMultiWorkGate()
projects = [ProjectRunSpec(project_id=f"proj_{i}") for i in range(3)]
result = gate.run_gate(projects)
print(result.passed, result.p95_latency_sec)  # True, 0.xxx

# SP-C.2 완료 종합 검증
reg_gate = SuiteRegistrationGate()
reg = reg_gate.run_gate(
    gates_passed=["G64", "G65", "G66"],
    ensemble_score=0.85,
    test_count=8053,
    atia_score=0.80,
)
print(reg.passed)  # True
```

---

## LOSDB 구조 (V586 기준)

| 레이어 | Mock | REAL |
|--------|------|------|
| SQL | V581 ✅ | V582 ✅ |
| Vector | V581 ✅ | V584 ✅ |
| Graph | V581 ✅ | V585 ✅ |
| **Facade** | — | **V586 ✅** |

---

## 개발 환경

```bash
# 전체 테스트
pytest tests/ -q  # → 8053 PASS

# SP-C.2 에이전트 테스트
pytest tests/unit/test_v648_critic_agent.py -v
pytest tests/unit/test_v654_mae_multiwork_gate.py -v
pytest tests/unit/test_v655_suite_registration_gate.py -v

# 릴리즈 게이트
python -m tools.run_release_gate  # → 66/66 PASS
```

---

## ADR 목록

ADR-001 ~ ADR-115 (`docs/adr/` 디렉터리 참조)

| ADR | 내용 |
|-----|------|
| ADR-106 | DirectorAgent + MicroPlanner (V646) |
| ADR-107 | ScriptAgent LoRA InferenceGateway (V647) |
| ADR-108 | CriticAgent + CriticReport (V648) |
| ADR-109 | EditorAgent + KoreanCadencePlanner (V649) |
| ADR-110 | AgentCoordinator (V650) |
| ADR-111 | EnsembleMemoryCache (V651) |
| ADR-112 | AgentEnsembleEvaluator G65 (V652) |
| ADR-113 | AgentSafetyGuard (V653) |
| ADR-114 | MAEMultiWorkGate G66 (V654) |
| ADR-115 | SuiteRegistrationGate G67 (V655) |

---

## 알려진 제약

| ID | 내용 | 영향 |
|----|------|------|
| KL-001 | PERSONAL 라이선스에서 MultiWorkOrchestrator 사용 불가 | 설계 의도. COMMERCIAL 라이선스 필요 |
| KL-002 | OTel tracer 초기화 테스트 1건 SKIP (런타임 비영향) | Release Block 아님 |

---

## 라이선스

MIT License
