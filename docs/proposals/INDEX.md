# Proposals & Designs — Index

> **Single Source of Truth**: 모든 제안서·설계도는 본 디렉터리 아래에 보관한다.
> 구글 드라이브 복사본은 폐기하고, 본 디렉터리만 인용한다.

## 구조

```
docs/proposals/
├── INDEX.md                          ← (이 파일)
├── phase3_v451_v480/                 ← Phase 3 멀티테넌트·프로덕션 (V451~V480)
│   ├── PROPOSAL_v2.docx              ← 합의안 제안서 v2.0
│   ├── DESIGN_v2.docx                ← 시스템 설계도 v2.0
│   └── README.md                     ← 단계 요약·게이트·ADR
└── v575_v580_stabilization/          ← V575~V580 안정화 7주 로드맵
    ├── PROPOSAL_v2.docx              ← 합의안 제안서 v2.0
    ├── DESIGN_v2.docx                ← 시스템 설계도 v2.0
    ├── V574_Principal_Engineer_Report.docx  ← 기반 보고서
    └── README.md                     ← 단계 요약·신규 게이트·ADR
```

## 1. Phase 3 (V451~V480) — Production Multi-tenant Blueprint

| 항목 | 값 |
|---|---|
| 버전 범위 | V451 ~ V480 (30 버전 / 5 SubPhase) |
| 합의 일자 | 2026-05-15 |
| 작성 주관 | Chief Architect × Chief Compiler × CSPE |
| 핵심 산출물 | ADR-011 ~ ADR-019 (9건) · Gate 19/19 누적 · RPO 1h · 결제 PG 다중화 · 데이터 주권 |
| 종료 조건 | Release Gate 19/19 PASS + NPS ≥ +30 + p95 < 3s + RPO 1h 검증 |
| 일정 | 32주 (2026-11-07 ~ 2027-06-19) |
| 자원 추정 | ₩ 4.8억 |

**5개 SubPhase**:

1. **SP1 (V451~V456)** — Real-LLM Live Integration & Live Cost
2. **SP2 (V457~V462)** — Multi-tenant Production Infrastructure
3. **SP3 (V463~V468)** — Compliance · Governance · Data Sovereignty
4. **SP4 (V469~V474)** — Fine-tune LoRA POC (축소)
5. **SP5 (V475~V480)** — Production Launch · Scale · DR

## 2. V575~V580 — 안정화 7주 로드맵

| 항목 | 값 |
|---|---|
| 버전 범위 | V574.1 핫픽스 + V575 ~ V580 (7주) |
| 합의 일자 | 2026-05-19 |
| 기반 | V574 Principal Engineer Report (Critical 4 + High 6 식별) |
| 작성 주관 | Chief Architect × Chief Compiler × CSPE |
| 핵심 산출물 | ADR-032 + ADR-034 ~ ADR-039 (7건) · Gate G32 ~ G39 (8 신설) · GATE_REGISTRY.py 단일 소스 · Survival Matrix v1.2 |
| 종료 조건 | Critical 0건 + High 0건 + Gate 39/39 등록 + 커버리지 ≥ 95% + 성능 -5% 이내 |
| 일정 | 7주 (2026-05-19 V574.1 → 2026-07-07 V580) |
| 자원 추정 | ₩ 7,500만 |

**단계**:

| 버전 | 제목 | 기간 | Preflight 위험도 |
|---|---|---|---|
| V574.1 | 즉시 핫픽스 | 0.5일 | 🟢 G |
| V575 | Security & Hygiene | 1주 | 🟡 Y |
| V576 | Test Fortification | 1주 | 🟡 Y |
| V577 | LLM Adapter Consolidation | 1.5주 | 🔴 R |
| V578 | Gate Registry & ADR | 1주 | 🔴 R |
| V579 | Duplicate + mypy gradual | 1주 | 🔴 R |
| V580 | Async + Performance | 1.5주 | 🔴 R |

## 3. 두 로드맵의 관계

```
[과거] V450 (Phase 2 완료) ─→ V571 (Phase 6 Stage C 완료)
                                 │
[현재] V574 (7.9.0) ─────────────┤
                                 │
[차순위] V575~V580 안정화 7주 ───→ V580 (프로덕션 A 등급)
                                 │
[병행 검토] Phase 3 V451~V480 ───→ 멀티테넌트 SaaS (Phase 3 시점은 V580 이후 키오프 권장)
```

**우선순위 권고**: V575~V580 7주 안정화를 먼저 완료한 후 Phase 3(V451~V480 — 실제로는 V581+ 의미)를 키오프한다. v2 합의안 모두 이 순서를 전제로 한다.

## 4. 변경 이력

- **2026-05-15**: Phase 3 (V451~V480) v1 초안 → v2 합의안 (CA·CC 작성 + CSPE 감수 + 3인 합의)
- **2026-05-19**: V575~V580 안정화 v2 합의안 (V574 보고서 비판 → CSPE 감수 → 3인 합의)
- **2026-05-19**: 본 docs/proposals/ 구조로 GitHub 정리 (집·회사 PC 단일 진실 원천 확립)
