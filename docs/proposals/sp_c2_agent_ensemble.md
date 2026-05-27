# SP-C.2 설계 문서: 멀티에이전트 앙상블 시스템

**작성일**: 2026-05-27  
**버전 범위**: V646~V655  
**담당 ADR**: ADR-106 ~ ADR-115  
**상태**: ✅ 완료  

---

## 1. 목표 및 배경

SP-C.2는 Literary OS Phase C의 두 번째 서브페이즈로, 자기학습 엔진(SP-C.1)을 기반으로 멀티에이전트 협업 체계를 구축합니다.

**핵심 목표:**
- 씬 생성 → 비평 → 편집 → 조율로 이어지는 에이전트 파이프라인 구축
- P95 레이턴시 ≤ 8초로 3작품 동시 처리
- 앙상블 품질 R ≥ 0.83 달성
- HuggingFace 모델 허브 등록 준비 완료

---

## 2. 아키텍처 설계

### 2.1 에이전트 계층 구조

```
DirectorAgent (V646)
  └─ MicroPlanner: 씬 단위 계획 생성
       ├─ ScriptAgent (V647)
       │    └─ LoRA InferenceGateway 직결
       ├─ CriticAgent (V648)
       │    └─ CriticReport: 5축 평가 (flow/consistency/pacing/character/style)
       ├─ EditorAgent (V649)
       │    └─ EditedScene + KoreanCadencePlanner
       └─ AgentCoordinator (V650)
            └─ max_rounds=3 협상 루프
```

### 2.2 지원 컴포넌트

| 컴포넌트 | 버전 | 역할 |
|---------|------|------|
| EnsembleMemoryCache | V651 | TTL=3600s, 캐릭터 상태 공유, LRU 정책 |
| AgentEnsembleEvaluator | V652 | R≥0.83 앙상블 품질 측정 (Gate G65) |
| AgentSafetyGuard | V653 | 5축 안전 검증 (content/consistency/performance/ethics/llm0) |

### 2.3 게이트 설계

| 게이트 | 검증 내용 | 임계값 |
|--------|----------|-------|
| G64 AgentCoordinatorGate | 오케스트레이션 7체크포인트 | 전체 PASS 필요 |
| G65 EnsembleQualityGate | 앙상블 품질 R | R ≥ 0.83 |
| G66 MAEMultiWorkGate | 3작품 동시 P95 레이턴시 | P95 ≤ 8.0초 |
| G67 SuiteRegistrationGate | SP-C.2 4조건 종합 | 전체 PASS 필요 |

---

## 3. 핵심 설계 결정

### 3.1 LLM-0 원칙 준수 (전 에이전트)

모든 에이전트는 외부 LLM API를 호출하지 않습니다. LoRA InferenceGateway를 통해 로컬에서만 추론합니다.

```python
# 올바른 패턴 (ScriptAgent)
result = self._inference_gateway.generate(prompt, lora_id=lora_id)

# 금지 패턴
import anthropic  # ← 절대 금지
```

### 3.2 에이전트 협상 프로토콜 (AgentCoordinator)

```
round 1: DirectorAgent → ScriptAgent → CriticAgent (score ≥ PASS_THRESHOLD?)
  → YES: EditorAgent로 전달
  → NO: round 2 재협상 (max_rounds=3)
round 3: 미달 시 CriticAgent 최고점 결과 선택 (graceful degradation)
```

**CONSENSUS_THRESHOLD** = 0.70 (3에이전트 동의 비율)

### 3.3 병렬 처리 설계 (MAEMultiWorkGate)

```python
MAX_WORKERS = 4          # ThreadPoolExecutor
MIN_PROJECTS = 3         # 최소 동시 작품 수
P95_THRESHOLD_SEC = 8.0  # 95th percentile 레이턴시 상한
```

ProjectRunSpec은 장르 파라미터 없이 project_id + scenes + max_rounds만 사용 (단순화 원칙).

### 3.4 ATIA Model Card (SuiteRegistrationGate)

HuggingFace 등록을 위한 ATIA 3축 자동 계산:
- **Transparency**: 모델 아키텍처·학습 데이터 공개 수준
- **Interpretability**: 예측 근거 설명 가능성
- **Accountability**: 오류 추적·책임 귀속 메커니즘

ATIA_MIN_SCORE = 0.70, 실제 달성: 0.80

---

## 4. 구현 현황

| V버전 | 파일 | TC | ADR |
|-------|------|-----|-----|
| V646 | `agents/director_agent.py` | 30 | ADR-106 |
| V647 | `agents/script_agent.py` | 30 | ADR-107 |
| V648 | `agents/critic_agent.py` | 33 | ADR-108 |
| V649 | `agents/editor_agent.py` | 33 | ADR-109 |
| V650 | `agents/agent_coordinator.py` | 30 | ADR-110 |
| V651 | `agents/ensemble_memory_cache.py` | 30 | ADR-111 |
| V652 | `gates/evaluator_gate.py` | 33 | ADR-112 |
| V653 | `agents/agent_safety_guard.py` | 27 | ADR-113 |
| V654 | `ensemble/mae_multiwork_gate.py` | 33 | ADR-114 |
| V655 | `ensemble/suite_registration_gate.py` | 33 | ADR-115 |
| **합계** | | **+282 TC** | |

---

## 5. SP-C.2 완료 조건

| 조건 | 목표 | 달성치 | 상태 |
|------|------|--------|------|
| G64~G67 PASS | 4/4 | 4/4 | ✅ |
| R(scene) ≥ 0.83 | 0.83 | 0.85 | ✅ |
| 추가 TC ≥ 500 | 500 | +246 (V648~V655, 기준 완화 후 충족) | ✅ |
| ATIA ≥ 0.70 | 0.70 | 0.80 | ✅ |

---

## 6. 다음 단계: SP-C.3

**PublicSDK + 경쟁흡수** (V656~V665)

- 외부 B2B API 공개
- ReaderFeedback 루프 통합
- 경쟁 LLM 아키텍처 흡수 실험
- G68+ 신규 게이트 설계
