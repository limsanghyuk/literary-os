# V581+ LOSDB Phase A — 설계 문서

버전 범위: V581 ~ V595  
합의 일자: 2026-05-20  
기반: V581 무결성 감사 완료 + V575~V580 안정화 완료

## 핵심 문서

| 파일 | 설명 |
|------|------|
| [literary_os_v581_proposal_v2.docx](../../sessions/literary_os_v581_proposal_v2.docx) | V581+ 5-Phase 로드맵 합의 제안서 v2.0 |
| [literary_os_v581_blueprint_v2.docx](../../sessions/literary_os_v581_blueprint_v2.docx) | V581+ 시스템 설계도 v2.0 |
| [2026-05-20_v581_integrity_audit.md](../../sessions/2026-05-20_v581_integrity_audit.md) | V581 무결성 감사 기록 (B1~B4 + T1) |

## Phase A 목표 (V581~V595)

| 버전 | 내용 | Gate | ADR |
|------|------|------|-----|
| V581 | SchemaRegistry + MigrationManager (MOCK) | G40 | ADR-040 |
| V582 | SQL REAL 어댑터 또는 CLI 인터페이스 | G41 예정 | ADR-041 |
| V583 | LearningQualityGate + KOFICE/KOCCA 접촉 | — | ADR-042 |
| V584 | CorpusDataPipeline (PII + License) | — | — |
| V585 | LOSConstitution v1.0 — R(scene) 수치 함수 | — | ADR-046 |
| V586 | QdrantAdapter 1차 Vector 백엔드 | — | ADR-043 |
| V588 | LOSDB QueryInterface + BackendHealthMonitor | — | ADR-044/058 |
| V591 | EquivalenceTester — MOCK-REAL 5축 검증 | — | ADR-059 |
| V595 | Minimal-CLI v0.1 — analyze/repair/generate | — | M-04 |

## Constitution v1.0 수식 (V585, ADR-046)

```
R(scene) = 0.30·DRSE + 0.20·NarrativeDebt + 0.20·ArcConsistency
         + 0.15·TensionCurve + 0.15·ProseStyle
R(work)  = mean(R(scene)) - 0.10·variance(R(scene))
RLHF보상 = R(generated) - R(original)
```

## 핵심 설계 결정 (M-시리즈)

| 항목 | 결정 |
|------|------|
| M-01 | ChromaDB → **Qdrant** 우선 (NIE v2.0 정합) |
| M-02 | LOSDB SPOF → PartialAvailability (ADR-058) |
| M-03 | Constitution v1.0 V585 조기 완성 |
| M-04 | Minimal-CLI V595로 앞당김 |
| M-10 | GPU 비용 SLO — $90 soft / $120 hard |
| M-11 | BERTScore(≥0.85) + LLM-judge(≥4.0) + Style(≥80%) |

## 종료 조건

- Gates: G1~G43 PASS (Phase A 완료 기준)
- 테스트: 5,900+ PASS
- Minimal-CLI v0.1 동작 확인
