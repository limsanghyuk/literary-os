# Phase E.2 진입 설계 — LLM-1 Critic 정식 도입 (L4 v1.0)

**작성일**: 2026-06-15 · **기준선**: main `01545838` (V752 / v13.6.0) · **문서 ID**: LOS-PHASE-E2-LLM1-ENTRY-L4-V1.0-2026-06-15
**선행**: Pass1~7 배선(V752) · Pass5 실 LLM E2E 실측(4/4 게이트·패널 4/4) · human_gt(V750) · pairwise/validation(V747~749).

---

## 0. 왜 지금 (진입 근거)
생성 척추가 완성됐고(V752), Pass5 실 LLM 생성·Pass6 구조게이트·Pass7 패널이 실동작 입증됐다. 다음 자연 단계는 **외부 LLM을 "Critic 레이어"로 정식화**하는 LLM-0→1 전이다. 핵심: 공식(구조 sanity)·인간 GT(절대 닻)는 유지하고, **외부 LLM을 평가 보조로만** 엄격 경계 안에 들인다.

## 1. LLM-1 정의·경계 (불변 원칙)
| 영역 | 외부 LLM | 근거 |
|---|---|---|
| `critic/` (신규) | **허용** (평가 보조) | LLM-1 핵심 |
| `orchestration/` Pass5 생성 | 허용(이미 사용) | 생성은 원래 LLM 위임 |
| `corpus/`·`constitution/`·`finetune/` | **절대 금지** | LLM-0 보존(G_LLM1_BOUNDARY) |
- 공식 = **sanity baseline(R2→게이트)**, 인간 GT = 절대 닻, Critic(LLM) = 이중 측정자. **공식·인간 GT는 어느 단계서도 제거 안 됨.**

## 2. 번호 정합 (중요 — 원안 충돌 해소)
- **ADR**: 원안 E.2 = ADR-211~220이었으나 **211(Pairwise)·212(Pairwise게이트)·213(human_gt)이 이미 사용됨**. → E.2 ADR = **ADR-214~223** 로 재배정.
- **버전**: 원안 E.2 = V761~775였으나 WP-5 생성본체가 **V750~752를 선소비**(앞당김). → E.2 = **V753부터 순차** 부여(아래 §6 버전맵). 현재 v13.6.0 → E.2 완료 시 v13.9.x 예상.

## 3. 5 Gate (정량 기준)
| 게이트 | 기준 | 비고 |
|---|---|---|
| **G_LLM1_BOUNDARY** | `corpus/constitution/finetune`에 외부 LLM 호출 정적 0건 | llm0_static_gate 확장 |
| **G_LLM1_RAG** | 모든 critic 호출에 RAG 컨텍스트 포함(미포함 0) | Pass4 결선 재사용 |
| **G_LLM1_SAFETY** | 코퍼스 < 50편 시 critic 자동 차단 | 현재 205~395편 → 통과 |
| **G_LLM1_ALIGNMENT** | Critic↔**인간 GT** 일치율 ≥ 0.80 (Gold 30편) | **human_gt.py(V750) 재사용** |
| **G_LLM1_COST** | 월 $50 hard / $30 soft | llm1_metrics |

## 4. critic/ 12모듈 (롤아웃 순서)
`base.py`(CriticInterface 추상) → `structure_critic`·`character_critic` → `dialogue_critic`·`emotion_critic`·`genre_critic`(5축) → `critic_ensemble`(**Pass7 패널 승격**) → `llm1_router` → `rag_context`(Pass4 연결) → `alignment_monitor`(**human_gt 연동**) → `corpus_gate` → `llm1_metrics`.

## 5. 기존 자산 결선 (신설이 아니라 배선)
- **Pass7 패널 → `critic_ensemble`** (3페르소나 = 5축 critic의 원형).
- **human_gt.py → `alignment_monitor`** (G_LLM1_ALIGNMENT의 GT 원천).
- **Pass6 공식게이트 → sanity baseline** (Critic과 이중 측정).
- **pairwise.py → critic 쌍대 비교** (절대점수 금지 유지).
- **Arbitration Protocol v1**: |z(공식)−z(critic)|>1.5σ → 3분기(공식결함 recalibrate / critic결함 프롬프트개선 / 진성모호 인간큐). 인간 판정 = DPO 2배 가중.

## 6. 버전맵 (V753~, 잠정)
| 버전 | 산출 | ADR | Gate |
|---|---|---|---|
| V753 | `critic/base.py` + CriticInterface + G_LLM1_BOUNDARY | 214 | G_LLM1_BOUNDARY |
| V754~756 | structure/character/dialogue/emotion/genre critic 5종 | 215~217 | — |
| V757 | critic_ensemble(Pass7 승격) + G_LLM1_RAG | 218 | G_LLM1_RAG |
| V758 | alignment_monitor + G_LLM1_ALIGNMENT(human_gt) | 219 | G_LLM1_ALIGNMENT |
| V759 | corpus_gate + G_LLM1_SAFETY / llm1_metrics + G_LLM1_COST | 220~221 | G_LLM1_SAFETY·COST |
| V760 | Arbitration Protocol v1 + 5축 측정 통합 | 222 | — |
| V761 | SP-E.2 Exit(5축 충족) → Phase E.3 진입 | 223 | SP-E2-EXIT |

## 7. 5축 측정 (E.2 진행 추적)
적용률(≥0.6)·호출률(≤0.4)·**일치율(≥0.80, 인간 GT 기준)**·비용(≤$50)·안전성(0건).

## 8. Phase F 진입조건 (ADR-223)
일치율 3개월 연속 ≥0.80 · 50편 인덱스 안정 · 비용 6개월 평균 ≤$50 · Critic 5종 모두 ≥0.80.

## 9. 개발자 결정 대기
- D-E2-1 ADR 재배정(214~223) 승인 · D-E2-2 버전 시작점(V753 즉시 vs 원안 V761 유지) · D-E2-3 비용 상한($50 hard) · D-E2-4 critic 5축 정의 확정.

> 본 문서는 LLM-0→1 전이의 진입 명세(L4)다. 첫 구현 V753(critic/base + G_LLM1_BOUNDARY)은 RULE-0 Preflight 후 본 명세대로 착수한다.
