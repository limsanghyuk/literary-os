# Literary OS V792

> **판단은 로컬, 생성만 LLM, 학습은 누적**  
> AI 기반 장편 소설·드라마 시나리오 생성 시스템

[![Version](https://img.shields.io/badge/version-13.45.1-blue)]()
[![Tests](https://img.shields.io/badge/tests%20(V792)-11462-brightgreen)]()
[![Phase](https://img.shields.io/badge/RLAIF-loop--C%20GPU%203--mode-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

> ⚠️ 태그 `v13.45.2`는 v13.45.1 오태그(내용 동일) — 정식 권위=**v13.45.1**.
>
> **현재 상태**: V792 / v13.45.1 · 테스트 11,462 · 97 Gates(90 PASS, 잔여 7 = Phase D 미완 WIP). **P0 선호쌍 빌더 + E4 암기게이트 + per-token 승률 + 구조 적합 게이트** 완료. 진행 누적(V781~V792): 생성본체 7-pass L4 승격(V781) · M1 Critic 자격검정(V782) · M2 NextEpisodeBench 은닉GT(V783) · M3 분포 가드레일·재보정(V784·V787) · 자체평가→loop-C 통합(V785) · 클라우드 비공개 저장·실측 학습노드(V786) · KL 표준 0.50+구조게이트+per-token 재측정(V788) · LLM 자율성 사다리 설계(V789) · 데이터·평가 3인 교차논의(V790) · E4 암기·표절 하드게이트(V791) · **P0 선호쌍 빌더 패키지 learning/pairing/(I1~I5 불변식 코드화) + 검증 라운드 하드닝 G-A/G-B(V792)**. 핵심 학습 불변식: I1 per-token 전용 · I2 길이중립 · I3 무단복제 0 · I4 작품단위 분리 · I5 토크나이저 잠금 · E4 암기 하드게이트. **다음**: P3 GPU ΔW 1라운드(pairwise_winner sum 경로 차단 + winner_pertoken 배선) · P2.5 구조계층 추출패스 · Phase D 미완 7게이트(별도 트랙). 재검증: `python3 tools/run_release_gate.py` · `python3 tools/generate_test_inventory.py`.

## 빠른 시작

```bash
# 설치
pip install -e ".[dev]"

# 전체 테스트 실행
pytest tests/ -q
# → 9766 passed

# Preflight (RULE-0 의무 — DEV_PROTOCOL_v3.0)
python3 tools/run_preflight.py
# → 13단계 ALL PASS

# 릴리즈 게이트 확인
python3 tools/run_release_gate.py
# → RELEASE GATE PASS: 97 gates passed
```

---

## 시스템 개요

Literary OS는 장편 서사 생성을 위한 AI 파이프라인입니다.  
외부 LLM은 산문 생성에만 선택적으로 사용하며, 플롯·캐릭터·구조 판단은 전부 로컬 모델이 처리합니다 (**LLM-0 원칙**, ADR-015/031).

```
literary_system/
├── sdk/          # PublicSDK v1.0 (SP-C.3) — analyze/repair/predict/generate
├── ensemble/     # AgentCoordinator (Director→Script→Critic→Editor, SP-C.2)
├── agents/       # 멀티에이전트 앙상블 + MultiAgent Coordination (SP-D.2)
├── gates/        # 릴리즈 게이트 97종 (G01~G95 + SP-D Exit)
├── plugins/      # Plugin Registry + Sandbox + Lifecycle (SP-D.3)
├── security/     # ZeroTrust Token + TenantAuthority + Middleware + AuditLog (SP-D.3)
├── chaos/        # Chaos Engineering: Engine/Injector/Scenario/CircuitBreaker/Runner (SP-D.3)
├── ops/          # Observability: OtelSdkAdapter + TraceSampler + Dashboard (SP-D.1)
├── constitution/ # LOSConstitution v2 + Bayesian Opt
├── world/        # PluginRegistry + 5 genre plugins
├── governance/   # ATIAMetadataAuditor
├── graph_intelligence/   # NKG 지식 그래프 + 감정 링커
├── orchestrators/        # 장편 지속 오케스트레이터
├── predictive/           # PNE — 예측적 서사 엔진
├── corpus/               # 외부 코퍼스 브릿지 — BGE-M3 + CIM
├── multiwork/            # 다중작품 관리 오케스트레이터
├── adapters_live/        # LLM 어댑터 (Claude / OpenAI / Ollama)
└── ...           # 86개 패키지 전체 연결 (고립 0, ADR-128 G_CONNECTIVITY)
```

---

## Phase별 완성 현황

| 단계 | 버전 | 주요 내용 | 게이트 |
| --- | --- | --- | --- |
| Phase 6 | V546~V571 | PNE / CorpusIngestor / MultiWork / AsyncDiscipline | G25~G31 |
| SP-A | V587~V595 | E2EProseGate / GPU SLO / EquivalenceTester / Constitution / CLI | G46~G52 |
| SP-B.1 | V596~V600 | LoRA Fine-tuning Pipeline + HuggingFace | G53~G54 |
| SP-B.2 | V601~V606 | RLHF 루프 / PPO / Reward / ConstitutionAxis | G55~G57 |
| SP-B.3 | V607~V620 | MultiWork 협업 / LoRAStacking / SharedDB | G58~G60 |
| SP-B.4 | V621~V630 | 통합 최적화 / Helm / Monitoring / Phase B Exit | **G61** |
| SP-C.1 | V631~V640 | 자기학습 엔진 / AutoPromotion / SelfLearningMonitor | G62~G63 |
| SP-C.2 | V641~V655 | 멀티에이전트 앙상블 / MAE-MultiWork / SuiteRegistration | G64~G67 |
| SP-C.3 | V656~V665 | PublicSDK v1.0 / OpenAPI / B2B Partner API / Feedback Loop | G68~G71 |
| SP-C.4 | V666~V680 | 경쟁흡수 / DistillationExport / Enterprise SLO / Phase C Exit | G72~G80 |
| SP-D.1 | V681~V695 | Observability Stack (Trace/Sampler/Dashboard/OtelSdk) | G81~G83 |
| SP-D.2 | V696~V710 | MultiAgent Coordination Layer (Bus/Workflow/CircuitBreaker/Supervisor) | G84~G85 |
| **SP-D.3** | **V711~V730** | **Plugin Registry + ZeroTrust + Chaos Engineering** | **G87~G89** |
| SP-D.4 | V731~V745 | 보조 게이트 + Phase D Exit | G92~G95 |
| 검증주간 | V746~V749 | 무결성·Pairwise·Transitivity·인간GT 인프라 | G_INTEGRITY/PAIRWISE/HUMAN_GT |
| **Phase E.2** | **V753~V761** | **LLM-1 Critic (5축·ensemble·alignment·arbitration)** | **G_LLM1_BOUNDARY/RAG/ALIGNMENT/SAFETY/COST** |
| **Phase E.4** | **V762~V766** | **RLAIF loop-C (보상·오케·트리거) + LLM-1 전이 Exit** | **PHASE-E-LLM1-EXIT** |
| GPU 3-모드 | V767~V773 | LocalGPU(4070)·ProviderRouter·SplitPipeline·RealRunPod·클라우드 배선 | G_GPU_ROUTING |
| **E.4 확장** | **V774~V780** | **loop-C 폐회로·2축 품질라벨+Critic 판별·자동집계·RunPod 운영·E.4 Exit** | **G_LOOPC_WINRATE** |
| 생성·자체평가 | V781~V787 | 7-pass L4 승격·M1/M2/M3 자체평가·loop-C 통합·클라우드 학습노드·분포 재보정 | ADR-241~248 |
| SGATE·암기 | V788~V791 | KL 표준 0.50+구조게이트+per-token 재측정 · LLM 사다리·3인 교차논의 설계 · E4 암기 하드게이트 | G_STRUCTURE_CONFORMANCE |
| **P0 페어링** | **V792** | **선호쌍 빌더 learning/pairing/(I1~I5)+E4 게이트+per-token 승률 + 검증 하드닝(G-A/G-B)** | **I1~I5 / E4** |
| **V792** | **v13.45.1** | **현재 — 11,462 Tests / 97 Gates(90 PASS) / 무결성 SHA256 2,061 일치** | **✅** |

---

## 릴리즈 게이트 — 97 PASS

```python
from literary_system.gates.release_gate import GATES
print(len(GATES))  # → 97
```

| 범위 | 게이트 | 내용 |
|------|--------|------|
| G01~G24 | Phase 1~5 | LLM-0 / Arc / RAG / SLM / MultiTenant / RLHF POC |
| G25~G39 | Phase 6 + 거버넌스 | PNE / Corpus / MultiWork / DEV_MODE / AsyncDiscipline |
| G40~G52 | LOSDB + SP-A | SQL/Vector/Graph REAL / E2EProseGate / CLI Exit |
| G53~G61 | SP-B | LoRA Inference / FineTune / PPO / RLHF / Phase B Exit |
| G62~G63 | SP-C.1 | AutoPromotionGate (R≥0.78) / SelfLearningGate (α≥0.70) |
| G64~G67 | SP-C.2 | AgentCoordinator / EnsembleQuality / MAEMultiWork / SuiteRegistration |
| G68~G71 | SP-C.3 | ReaderFeedback / FeedbackLoop / SDKStability / B2BPartner |
| G72~G80 | SP-C.4 | CompetitorAbsorption×5 / DistillationExport / EnterpriseSLO / Revenue / Phase C Exit |
| G81~G83 | SP-D.1 | PreFlightFix / StaticTypeSafety / ObservabilityFoundation |
| G84~G85 | SP-D.2 | AgentCoordinationGate / AgentWorkflowGate |
| **G87** | **SP-D.3** | **Plugin Registry (PR-1~PR-7)** |
| **G88** | **SP-D.3** | **ZeroTrust Security (ZT-1~ZT-7)** |
| **G89** | **SP-D.3** | **Chaos Resilience (CR-1~CR-6)** |
| **G92~G95** | **SP-D.4** | **보조 게이트 3종 + Phase D Exit Gate** |
| **named** | **검증주간** | **G_INTEGRITY_MANIFEST / G_PAIRWISE_REGRESSION / G_TRANSITIVITY / G_HUMAN_GT_ALIGNMENT** |
| **named** | **Phase E.2** | **G_LLM1_BOUNDARY / RAG / ALIGNMENT / SAFETY / COST (LLM-1 Critic 8모듈)** |
| **named** | **Phase E.4** | **G_LOOPC_WINRATE / PHASE-E-LLM1-EXIT / G_GPU_ROUTING** |

---

## 개발 환경

```bash
# 전체 테스트
pytest tests/ -q  # → 11,292 PASS

# Preflight — 각 버전 개발 전 필수 (DEV_PROTOCOL_v3.0 RULE-0)
python3 tools/run_preflight.py  # → 13단계 ALL PASS

# 릴리즈 게이트
python3 tools/run_release_gate.py  # → 97 gates PASS
```

---

## ADR 목록

ADR-001 ~ ADR-240 (`docs/adr/` 디렉터리 참조)

| ADR 범위 | 내용 |
|----------|------|
| ADR-001~097 | Phase 6 → SP-B 전체 |
| ADR-098~128 | SP-C.1~SP-C.4 + G_CONNECTIVITY |
| ADR-129~142 | SP-C.4 안정화 + Phase C Exit |
| ADR-143~157 | SP-D.1 Observability Stack (V681~V695) |
| ADR-158~171 | SP-D.2 MultiAgent Coordination (V696~V710) |
| ADR-172~181 | SP-D.3 Plugin Registry + ZeroTrust (V711~V720) |
| ADR-182~189 | SP-D.3 Auth Bridge + Chaos Engineering (V721~V728) |
| **ADR-190** | **G89 ChaosResilienceGate (V729)** |
| **ADR-191** | **SP-D.3 Exit Gate (V730)** |
| ADR-192~208 | SP-D.4 보조 게이트 + Phase D Exit (V731~V745) |
| ADR-209~213 | 검증주간 — 무결성/Pairwise/Transitivity/인간GT (V746~V750) |
| **ADR-214~221** | **Phase E.2 LLM-1 Critic 8종 (V753~V761)** |
| **ADR-222~226** | **Phase E.4 RLAIF 코어 + LLM-1 전이 Exit (V762~V766)** |
| **ADR-227~233** | **GPU 학습 3-모드 + 클라우드 배선 (V767~V773)** |
| **ADR-234~240** | **loop-C 폐회로·2축 품질라벨·RunPod 운영·E.4 Exit·무결성·gates 정리 (V774~V780)** |

---

## 알려진 제약

| ID | 내용 | 영향 |
|----|------|------|
| KL-001 | PERSONAL 라이선스에서 MultiWorkOrchestrator 사용 불가 | 설계 의도. COMMERCIAL 라이선스 필요 |
| KL-002 | OTel tracer 초기화 테스트 1건 SKIP (런타임 비영향) | Release Block 아님 |
| KL-003 | PluginSandbox: RestrictedPython 의존성 필요 (`pip install RestrictedPython`) | G88 ZT-5 PASS 필수 |

---

## 라이선스

MIT License
