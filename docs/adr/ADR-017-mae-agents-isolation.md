# ADR-017: MAE 에이전트 격리 — 4종 에이전트 아키텍처

**상태:** 채택 (V499~V500)
**결정자:** Chief Architect, Chief Compiler
**날짜:** 2026-05-17

## 컨텍스트

기존 MAEOrchestrator는 Alpha/Beta/Gamma 3에이전트 동등 가중치.
Phase 3는 독자/작가/편집/문화 4종으로 확장하며 가중치를 차별화.

## 결정

### 에이전트 구성 (ADR-006 격리 범위 명시)
```
MAEOrchestratorV2.evaluate()
    ├── ReaderAgentV2   (weight=0.35) — Reader 3 sub-persona 앙상블
    │     ├── F30 (여성30대, 40%)
    │     ├── M60 (남성60대, 35%)
    │     └── T20 (10대, 25%)
    ├── WriterAgentV2   (weight=0.25) — 문체·리듬 평가
    ├── EditorAgentV2   (weight=0.25) — 구조·일관성 평가
    └── CulturalAgentV2 (weight=0.15) — 한국 드라마 관습 준수
```

### 격리 원칙
- LLM 호출: 에이전트 내부에서만 허용 (V509+에서 실 LLM 연결)
- V499 구현: 메트릭 기반 근사 (실 LLM 없음)
- 27% 샘플링: SAMPLE_RATE=0.27 기본값
- σ≥0.15 시 Sonnet 자동 격상 권고 (CostProjection M-N06)

### AMW α 파라미터화 (Gap 1 해결)
- `adaptive_momentum_weights.py`: α_dim ∈ [0.30, 0.80]
- LR_AMW=0.005, 장르별 초기값 (melodrama/thriller/romcom/family)
- advantage 신호를 PhysicsRewardBridge에서 주입

## 결과
- Reader 다양성 확보 (3 sub-persona × 시청층)
- α 하드코딩 0.15 → 학습 파라미터화
- NILStabilityModule (V512+) 연동 준비
