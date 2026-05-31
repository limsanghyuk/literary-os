# Phase E 기획안 통합 보고서 v1.1 핸드오프 — 후속

**작성일**: 2026-05-30 (후속)
**기준선**: V745 main HEAD `8e1e5632` (v13.0.0, 95 Gates)
**선행**: v1.0 (`0679d64f`, 2026-05-30 push)
**대상**: 개발자 검토 후 의견 추가

---

## 0. 본 문서의 위치

본 v1.1은 통합 보고서 v1.0(2026-05-30 `0679d64f` push) **이후 7건의 추가 대화**를 정리한 후속 자료다. v1.0의 8개 §는 유효, 본 v1.1은 그 위에 추가.

**저연산 모드는 v1.0 + v1.1 + 본 핸드오프 3개 파일 학습:**
1. `docs/sessions/2026-05-30_phase_e_planning_report_v1.docx` (v1.0)
2. `docs/sessions/2026-05-30_phase_e_planning_handoff_v1.md` (v1.0)
3. `docs/sessions/2026-05-30_phase_e_planning_report_v1.1.docx` (본 후속)
4. `docs/sessions/2026-05-30_phase_e_planning_handoff_v1.1.md` (본 문서)

---

## 1. v1.0 → v1.1 추가 9개 §

| § | 제목 | 핵심 |
|---|---|---|
| §1 | V745 코퍼스 실측 | 인프라 8 모듈 vs 실 데이터 0편 + 합성 더미 1만 씬 |
| §2 | UI/UX 3-zone 구체화 | Left 25 / Center 50 / Right 25 |
| §3 | Cowork/Codex 보편 패턴 흡수 | 9건 매핑 |
| §4 | UI/UX 12 보강 항목 | UI-1 ~ UI-12 |
| §5 | Claude Design 외부 도구 | 2026-04-17 출시, SP-E.3 15주 → 3~5주 |
| §6 | CSPE 7개 조언 | 옵션 B 즉시 / SP 재정렬 / 단축 / prototype / 자금 |
| **§7** | **LLM-0 → LLM-1 전환 구체화 (핵심)** | **10 ADR + 5 Gate + 12 모듈 + 5축 측정 + Phase F 진입 조건** |
| §8 | Phase E 본안 작성 시 흡수 우선순위 | ★★★★★ LLM-1 30% / 코퍼스 20 / UI 20 / RLAIF 20 / Exit 10 |
| §9 | 결론 + 다음 호출 시 작업 | 본안 v1.0 작성 (15~30분) |

---

## 2. 핵심 §7 — LLM-0 → LLM-1 전환 (사용자 지적 반영)

**사용자 의도**: "LLM-0 → LLM-2.5 점진 완화 로드맵을 Phase E에서 더 구체화"

자료 A는 이 부분을 "RAG 컨텍스트 주입 의무 규칙 ADR 등록" 한 줄만 명시. 본 v1.1에서 10 ADR + 5 Gate + 12 모듈로 확장:

### 10 ADR

| ADR | 제목 |
|---|---|
| ADR-α | LLM-1 정의 + 허용·금지 경계 (허용: critic/* / 금지: corpus/, constitution/, finetune/) |
| ADR-β | CriticInterface 추상 레이어 |
| ADR-γ | RAG 컨텍스트 의무 규칙 |
| ADR-δ | AI Critic vs Constitution 일치율 ≥0.80 |
| ADR-ε | 코퍼스 <50편 시 LLM-1 자동 차단 |
| ADR-ζ | LLM-1 비용 추적 (CostLedger 확장) |
| ADR-η | AI Critic Ensemble 5종 (구조·인물·대사·감정·장르) |
| ADR-θ | 공식 sanity check 역할 정의 |
| ADR-ι | 점진 전환 측정 5축 (적용률·호출률·일치율·비용·안전성) |
| ADR-κ | Phase F (LLM-1.5) 진입 조건 5건 |

### 5 Gate

| Gate | 검증 | 기준 |
|---|---|---|
| G_LLM1_BOUNDARY | 경계 정적 검사 | corpus/constitution/finetune에 외부 LLM 호출 0건 |
| G_LLM1_RAG | RAG 의무 런타임 | 모든 critic/* LLM 호출에 ChromaDB 결과 포함 |
| G_LLM1_SAFETY | 안전장치 | 코퍼스 49편 시 PoCRangeExceeded |
| G_LLM1_ALIGNMENT | 일치율 | Gold 30편 ≥0.80 |
| G_LLM1_COST | 비용 SLO | 월 $50 hard / $30 soft |

### 12 신규 모듈

```
literary_system/critic/
├── __init__.py                  
├── base.py                      # CriticInterface (V761, ADR-β)
├── structure_critic.py          # V762
├── character_critic.py          # V763
├── dialogue_critic.py           # V764
├── emotion_critic.py            # V765
├── genre_critic.py              # V766
├── critic_ensemble.py           # V767, ADR-η
├── llm1_router.py               # V768, ADR-α/ε
├── rag_context.py               # V769, ADR-γ
├── alignment_monitor.py         # V770, ADR-δ
├── corpus_gate.py               # V771, ADR-ε
└── llm1_metrics.py              # V772, ADR-ι
```

### 5축 측정 + Phase F 진입 조건

| 축 | 목표 | Phase F 진입 |
|---|---|---|
| 적용률 | ≥0.6 (3/5축) | 5/5축 모두 |
| 호출률 | ≤0.4 | 유연 |
| 일치율 | ≥0.80 (Gold 30편) | 3개월 연속 |
| 비용 | ≤$50 hard | 6개월 평균 ≤$50 |
| 안전성 | 0건 | 0건 유지 |

---

## 3. SP 순서 재정렬 (사용자 의도 반영)

| 우선순위 | CSPE 직전 (UI 우선) | **사용자 의도 반영 (LLM-1 본질)** |
|---|---|---|
| 1순위 | SP-E.3 UI MVP | **SP-E.2 LLM-1 도입** |
| 2순위 | SP-E.1 코퍼스 | SP-E.1 코퍼스 (LLM-1 선행) |
| 3순위 | SP-E.2 AI Critic | SP-E.3 UI (Claude Design 병렬) |
| 4순위 | SP-E.4 RLAIF | SP-E.4 RLAIF |

→ **최종**: SP-E.1 → SP-E.2 (핵심) → SP-E.3·SP-E.4 (병렬)

---

## 4. 결정 사항 8건 (D1~D8) — 개발자 결정 대기

| # | 항목 | CSPE 권고 | 결정 |
|---|---|---|---|
| D1 | Phase E 노선 (옵션 A/B) | **B 즉시** (Phase E = 자료 A) | ⏳ |
| D2 | Phase E 진입 시점 | 즉시 | ⏳ |
| D3 | 코퍼스 권리 트랙 | 병행 (KOFICE + Kaggle + 정부 R&D) | ⏳ |
| D4 | UI MVP 위치 | apps/studio_api/ 확장 | ⏳ |
| D5 | 자금 조달 | 정부 R&D + Phase G 매출 병행 | ⏳ |
| **D6 (신규)** | **SP 순서** | **SP-E.1 → SP-E.2 (핵심) → SP-E.3·SP-E.4 병렬** | ⏳ |
| **D7 (신규)** | **Phase E 범위** | **V746~V795 (50v 단축)** | ⏳ |
| **D8 (신규)** | **Claude Design 사용** | **즉시 가입 + prototype 생성** | ⏳ |

---

## 5. Phase E 본안 v1.0 작성 시 흡수 우선순위 (분량 비중)

| 우선 | 항목 | SP | 분량 |
|---|---|---|---|
| ★★★★★ | **LLM-0 → LLM-1 전환 (10 ADR + 5 Gate + 12 모듈 + 5축 + Phase F 조건)** | E.2 | **30%** |
| ★★★★ | 코퍼스 50편 + ChromaDB + Provenance | E.1 | 20% |
| ★★★★ | UI 3-zone + Claude Design 활용 | E.3 | 20% |
| ★★★ | DPO RLAIF + best-of-n | E.4 | 20% |
| ★★★ | Exit Gate + ADR-κ | E.5 | 10% |

---

## 6. 다음 호출 시 상위 모드 작업

개발자 의견·결정 추가 후 호출:

```
"Phase E 본안 작성하라 (옵션 B, SP-E.1 → SP-E.2 핵심 → SP-E.3·SP-E.4 병렬, V795 단축)"
또는
"위에 추가 검토 의견 있다: [구체 의견]"
```

상위 연산 모드 작업:
- Phase E 본안 v1.0 단일 통합 docx + 단일 핸드오프 md
- **§7 LLM-1 전환을 메인 섹션 (분량 30%)**으로 다룸
- 자료 A base + P1~P9 정합 보강 + 본 v1.1 12 UI 보강 + Claude Design 워크플로우 흡수
- 사용자 철학 (공식 sanity check + AI 학습 점진 도입) 반영
- V745 실측 commit 위치 정확 반영
- GitNexus 사전 인덱스 + 3인 합의 (CSA·CSC·CSPE) + 보강 12건 분산 부착

---

## 7. 위험 신호 — 본안 작성 전 보고

| 신호 | 의미 |
|---|---|
| Claude Design Research Preview 가입 차단 | 구독 등급 또는 지역 제한 — 대체 도구 검토 |
| AI Critic 일치율 ≥0.80 미달성 (Gold 30편) | LLM-1 도입 보류 / Critic 재설계 |
| 코퍼스 50편 권리 확보 실패 | KOFICE/Kaggle/공공 도메인 폴백 결정 |
| LLM-1 월 비용 $50 hard 초과 | 호출률 ≤0.4 강제 / 비용 알람 |
| 작가 베타 모집 실패 (Phase E SP-E.3) | UI MVP 검증 불가 → 본안 재평가 |

---

## 8. 메타데이터

- **문서 ID**: LOS-PHASE-E-PLANNING-V1.1-2026-05-30
- **선행**: v1.0 (`0679d64f`, 2026-05-30)
- **보고서 docx**: `docs/sessions/2026-05-30_phase_e_planning_report_v1.1.docx`
- **로컬 작업 경로**: `C:\literary_claude\claude`
- **유효 기간**: 개발자 의견 추가 후 Phase E 본안 v1.0 작성 시점까지
