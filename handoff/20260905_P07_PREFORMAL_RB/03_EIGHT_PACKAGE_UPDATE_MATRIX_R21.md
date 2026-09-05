# 5파트 8패키지 갱신 매트릭스 R21

## 원칙
이번 세션에서 실제로 내용 변경이 필요한 패키지는 CONTROL(제어권위), PART-A(실험권위), PART-B2(현재연구권위), PART-C2(후보엔진권위)이다. PART-B1(과거연구), PART-C1(ENG:R47 운영코어), PART-D1/D2(DB59 데이터·학습 정본)는 이번 P07 예비시험으로 정본 내용이 바뀌지 않았으므로 **바이트 불변**으로 유지해야 한다.

## 패키지별 적용
### 1) CONTROL(제어권위) — 새 리비전 필요
편입:
- P07 현재 위치 판정 교정: “거의 후반” 철회, “본시험 전 통합 폐쇄 중간~후반 전환점”.
- R-B Narrative Architecture Closure(서사구조 폐쇄)를 CP1보다 우선.
- Formal Count 137, R140 attempt/output/score 0/0/0.
- Development Set 6작품 재사용 금지.
- Backend ClientError(백엔드 클라이언트 오류) 인계 경계.

### 2) PART-A Control & Experiment(제어·실험권위) — 새 리비전 필요
편입:
- R5~R8 비정식 재예비시험 결과와 Claim Boundary(주장 경계).
- P07-PRE-09 E0~E9 기계·공학 결과.
- Bidirectional Refinement(양방향 개선) 진단 21/21, 최소책임 상위계층 13/13, 1회 재기획 6/6.
- Generalized Entity Availability(일반화 인물상태) 음성대조.
- Ordered Beats V2(순서보존 비트 V2) 결함·수리.
- Mechanical Parity(기계적 동등성)와 Craft Parity HOLD(작법 동등성 보류) 분리.
- Full Historical Re-audit(과거 전체 재감사)로 R-B 후보 확정.

### 3) PART-B1 Research History Vol1(과거연구 권위) — 바이트 불변
수정 금지. R1~과거 계보를 재해석하거나 덮어쓰지 않는다. 새 해석은 B2에서 링크한다.

### 4) PART-B2 Research Current Vol2(현재연구 권위) — 새 리비전 필요
편입:
- Literary OS 역할분담: LLM 창작/기획/표면, Python 가교/운영/검사/위험차단.
- Engineering Propagation Gap(공학 전파 공백) 교리.
- R41 Ensemble, R42 Consumer Fidelity, R43 Episode Synopsis, R45/R46 Portfolio, R75~R77 Ecology/Ownership, R82 Safety, R99~R101 Long-horizon, R130/R135~R138 Surface/Voice 계보의 P07 적용표.
- P07 완료조건을 Mechanical Parity만이 아니라 Narrative Architecture + Long-horizon + Surface Craft + Live Craft Parity까지 확장.

### 5) PART-C1 Engine Master Vol1 ENG:R47 Runtime Core(운영 엔진 코어) — 바이트 불변
ENG:R47 Production(운영 엔진)은 R140 대조군이므로 수정 금지.

### 6) PART-C2 Engine Master Vol2 Candidate(후보 엔진 권위) — 새 리비전 필요
편입:
- Development Overlay(개발 오버레이) 계보와 최신 결함·수리 문서.
- Generalized Entity Evidence Guard(일반화 인물증거 관문).
- Semantic Orchestration + Ensemble/Ecology 배선 수리 계보.
- Safe Retrieval 0.60/0.03 + NO_RETRIEVAL.
- Semantic Render Bridge + P9C-D Surface Policy.
- Ordered Beats V2 + Lossless Serialization.
- 새 R-B 구현 요구사항: SocialEcologyGraph, GroupMembership, EventOwnership, DetailedEpisodeSynopsis, THICKSequence/Boundary, Consumer Fidelity.
- Candidate Portfolio/Critic/R82, Carry/Rollback/AuthorizedNovelty, Voice/Texture는 후속 R-C~R-E HOLD로 명시.

### 7) PART-D1 DB59 Vol1(데이터 정본) — 바이트 불변
DB59 SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9` 유지. P06 quarantined malformed successor나 미검증 successor를 R140 입력으로 승격하지 않는다.

### 8) PART-D2 DB59 Drama Learning Vol2(학습 정본) — 바이트 불변
이번 예비시험에서 데이터 의미 정본을 수정한 것이 아니므로 유지. 새 연구 해석은 B2/C2 오버레이에서 연결한다.

## 5파트 해석
- CONTROL: 전체 읽기순서·권위·현재상태
- A: Formal/Preformal Experiment(정식·예비 실험)
- B1+B2: Research History + Current Research(과거·현재 연구)
- C1+C2: Production Engine + Candidate Engine(운영·후보 엔진)
- D1+D2: DB59 Canonical Data + Learning(정본 데이터·학습)

## 물리 재봉인 규칙
로컬 백엔드 복구 후 기존 최신 8 ZIP(압축파일)에 append-only(추가 전용) 방식으로 이 인계 디렉터리를 넣는다. B1/C1/D1/D2의 바이트는 변경하지 않는다. 변경 4개는 새 revision으로 재봉인하고 SHA256/CRC/Fresh Validation(새 검증)을 생성한다. 이전 ZIP은 삭제하지 않는다.