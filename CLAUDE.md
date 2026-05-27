# Literary OS — 개발자 컨텍스트 (V655 / v11.28.0)

---

## 🚨 세션 시작 즉시 실행 — 이 블록을 건너뛰면 작업 시작 불가

```bash
# ① 최신 상태 pull
git pull origin main

# ② 세션 시작 프로토콜 자동 실행 (Preflight Step 1 + Step 12 포함)
python3 tools/session_start.py

# ③ 위 결과 확인 후 개발 착수
```

> **근거**: DEV_PROTOCOL_v2.0 §1 — Preflight 없이 착수한 커밋은 릴리즈 승인 대상이 아님.  
> **전체 절차**: `docs/workflow/DEV_PROTOCOL_v2.0.md`  
> **Preflight 12단계 상세**: `docs/workflow/PREFLIGHT_GUIDE_v1.1.md`

---

## 🔴 Phase C 절대 원칙 (불변)

| 원칙 | 내용 |
|------|------|
| **LLM-0** | `corpus/`, `constitution/`, `finetune/` 에서 외부 LLM 호출 절대 금지 |
| **LLM-1** | PROMOTED 단계 LoRA 아티팩트만 서빙 (AutoPromotionGate G62 통과 필수) |
| **DEV_MODE** | 항상 `false` 기본값 유지 (ADR-034) |
| **GPU SLO** | 재학습 최소 간격 7일, 월 최대 $200 (ADR-051) |
| **Gate FAIL** | Gate FAIL 상태 절대 커밋 금지 |

---

## 현재 상태 (V655 기준)

| 항목 | 값 |
|------|----|
| 버전 | v11.28.0 |
| 개발 이터레이션 | V655 |
| 릴리즈 게이트 | **66/66 PASS** (G01~G67) |
| 테스트 | **8,053 PASS** |
| 현재 Phase | Phase C SP-C.2 완료 → SP-C.3 진입 예정 |
| Git HEAD (main) | c361bd64 |
| GitHub | https://github.com/limsanghyuk/literary-os |

---

## 세션 시작 프로토콜 (WORKFLOW.md §세션시작)

**집/회사 어느 환경이든 동일 순서로 실행:**

```
1. git pull origin main
2. python3 tools/session_start.py  ← 자동으로 Step 1~12 요약 실행
3. docs/sessions/ 최근 파일 읽어 이전 맥락 파악
4. 현재 브랜치 보고
5. 위 확인 완료 후 개발 착수
```

## 세션 종료 프로토콜 (WORKFLOW.md §세션종료)

```
1. docs/sessions/YYYY-MM-DD_[환경]_[주요내용].md 저장
2. docs/proposals/ 또는 docs/blueprints/ 커밋
3. git commit + push
4. 다음 세션 인수인계 요약 1문단 작성
```

---

## 개발 흐름 (DEV_PROTOCOL_v2.0 요약)

```
[0] git pull → python3 tools/session_start.py
[1] Preflight 12단계 (tools/session_start.py가 Step 1+12 자동 실행)
[2] 구현 (신규파일 + tests/unit/test_vXXX_*.py 33TC)
[3] 검증: pytest → generate_test_inventory.py → run_release_gate.py
[4] GitHub 배포: commit → push → Release 태그
[5] ZIP 패키징 + 7/7 검증 + 이전 버전 비교
[6] 메모리 업데이트 (memory/project_vXXX_state.md)
```

**§3 검증 명령어:**
```bash
python3 -m pytest tests/unit/ -q --tb=short 2>&1 | tail -5
python3 tools/generate_test_inventory.py
python3 -m tools.run_release_gate 2>/dev/null | grep summary
```

---

## 핵심 아키텍처

```
literary_system/
├── agents/               # SP-C.2 멀티에이전트 앙상블 (V646~V653)
│   ├── director_agent.py    # DirectorAgent + MicroPlanner
│   ├── critic_agent.py      # CriticAgent (PASS_THRESHOLD=0.65)
│   ├── editor_agent.py      # EditorAgent + KoreanCadencePlanner
│   ├── agent_coordinator.py # max_rounds=3
│   ├── ensemble_memory_cache.py
│   └── agent_safety_guard.py
├── ensemble/             # SP-C.2 게이트 (V654~V655)
│   ├── mae_multiwork_gate.py      # G66 P95≤8s
│   └── suite_registration_gate.py # G67
├── constitution/         # LOSConstitution v2 + Bayesian Opt (SP-C.1)
├── graph_intelligence/   # NKG + 감정 링커
├── orchestrators/        # 장편 지속 오케스트레이터
├── predictive/           # PNE
├── corpus/               # 외부 코퍼스 브릿지
├── multiwork/            # 다중작품 관리
├── db/                   # LOSDB Facade (SQL/Vector/Graph)
├── gates/                # release_gate.py (66 Gates G01~G67)
└── adapters_live/        # LLM 어댑터 (LLM-0 준수)
```

---

## 레포지토리 목록

| 레포 | 현재 버전 | URL |
|------|-----------|-----|
| literary-os | **V655 (v11.28.0)** | https://github.com/limsanghyuk/literary-os |
| v1700-literary-os | Stage 144 | https://github.com/limsanghyuk/v1700-literary-os |

---

## GitNexus 현황 (V655 기준)

```
literary_system/ 서브패키지: 70개+
Gate 등록: 66개 (G01~G67, G53~G60 없음)
테스트: 8,053 PASS
SP-C.2 신규 모듈: agents/ 7개 + ensemble/ 4개
```

> 재분석: `python3 tools/gitnexus_analyze.py`

---

## 버전 계보

| Phase | 버전 범위 | 완료 게이트 |
|-------|-----------|------------|
| Phase 1~6 | V1~V580 | G01~G39 |
| SP-A (Phase A) | V581~V595 | G40~G52 |
| SP-B.1~B.4 | V596~V630 | G53~G61 |
| SP-C.1 자기학습 | V631~V640 | G62~G63 |
| **SP-C.2 멀티에이전트** | **V646~V655** | **G64~G67** ✅ 완료 |
| SP-C.3 PublicSDK | V656~V665 | G68+ 예정 |
