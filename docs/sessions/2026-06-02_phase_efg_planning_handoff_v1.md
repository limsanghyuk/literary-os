# Phase E~G 통합 기획 보고서 v1.0 — 핸드오프

**작성일**: 2026-06-02
**기준선**: V745 (v13.0.0, 95 Gates, ADR 14~208, 384 테스트파일)
**선행 흡수**: Phase E 보고서 v1.1 (commit 2b3c3bc5)
**문서 ID**: LOS-PHASE-EFG-PLANNING-V1.0-2026-06-02
**대상**: 개발자 검토 + 저연산 개발 모드 학습

---

## 0. 본 문서의 위치

본 v1.0(E~G 통합)은 기존 Phase E 보고서 v1.0/v1.1을 **흡수**하고, 그 위에 (1) V745 무결성 실측 결과를 Phase E 선결과제로 편입, (2) Phase F·G를 SP·ADR·Gate 수준으로 신규 확장한 단일 통합 기획서다.

저연산 모드 학습 파일:
1. `docs/sessions/2026-05-30_phase_e_planning_report_v1.1.docx` (선행)
2. `docs/sessions/2026-06-02_phase_efg_planning_report_v1.docx` (본 보고서)
3. `docs/sessions/2026-06-02_phase_efg_planning_handoff_v1.md` (본 문서)

---

## 1. 신규 핵심 — V745 무결성 결함 (SP-E.0 선결과제)

V745 패키지 실측 결과: **코드 무결성은 보존, 그러나 릴리즈 자기검증 메타데이터 stale**.

| 검사 | 결과 |
|---|---|
| 내부 SHA256SUMS.txt (971항목) | 정상 883 / 미패키징 35 / **해시불일치 53** |
| 53건의 정체 | 전부 phase-d-exit 막판 패치셋(release_gate.py·pyproject.toml·test_inventory.json·finetune/*·constitution/*) |
| test_inventory.json | test_count 6801, 05-25 생성 < 패키지 V745(05-29) → stale |
| ADR 결번 | 37·38(INDEX 등재인데 파일 누락=실누락), 83~87·126·127(의도적 결번 추정) |

근본 원인: 막판 패치 후 SHA256SUMS·test_inventory 미재생성. release_gate에 '매니페스트 재생성 강제' 단계 부재.

선결과제(SP-E.0, V746):
- TD-E0-1: release_gate에 매니페스트 재생성+자기검증 게이트(G_INTEGRITY_MANIFEST)
- TD-E0-2: test_inventory 자동 재생성 hook
- TD-E0-3: ADR-37·38 복구 + 결번 INDEX 명시(G_ADR_CONTINUITY)

---

## 2. LLM-0 → LLM-2.5 점진 완화 (대전제)

| 단계 | 구간 | 외부 LLM 허용 | 공식 역할 |
|---|---|---|---|
| LLM-0 | ~V745 | 없음 | 주 평가·생성 |
| LLM-1 | Phase E | critic/* 보조만 | sanity baseline(일치율≥0.80) |
| LLM-1.5 | Phase F | Critic 5축 전체 + 생성 초안 | 가드+baseline 이중 |
| LLM-2.0 | Phase G 전반 | 생성 주력 | 최소 sanity·가드레일 |
| LLM-2.5 | Phase G 후반/H 경계 | 자율 생성-평가 루프 | 윤리·안전 가드레일만 |

원칙: 전이=직전 핵심 Gate 연속 PASS / 비가역 아님(자동 롤백 degradation path) / 공식은 어느 단계서도 제거 안 됨.

---

## 3. Phase E (V746~V795, LLM-1)

SP 순서: **E.0(무결성) → E.1(코퍼스 50편) → E.2(LLM-1 핵심) → E.3·E.4(병렬) → E.5(Exit)**

- E.2 핵심: 10 ADR(211~220) + 5 Gate(G_LLM1_BOUNDARY/RAG/SAFETY/ALIGNMENT/COST) + 12 모듈(literary_system/critic/) + 5축 측정(적용률·호출률·일치율·비용·안전성)
- E.3 UI: 3-zone + Claude Design(15주→3~5주)
- E.4 RLAIF: DPO + best-of-n(멀티 프로바이더)
- Phase F 진입조건(ADR-220): 일치율 3개월 연속 ≥0.80 등

---

## 4. Phase F (V796~V875, LLM-1.5)

SP: F.1 코퍼스 200편 / F.2 Critic 5축 전체 AI / F.3 생성 초안 부분완화 / F.4 다언어(한→영·일) / F.5 Exit
- ADR-224~233, Gate: G_LLM15_CRITIC_FULL·G_GEN_DRAFT_BOUNDARY·G_CORPUS_200·G_PLAGIARISM·G_MULTILANG
- 생성 완화 전략 3안 비교 → **안1(초안만) 권고** (최종본은 공식+인간 승인 필수)

---

## 5. Phase G (V876~V955, LLM-2.0~2.5 + 사업화)

SP: G.1 생성 주력(LLM-2.0) / G.2 자율 평가루프+RLAIF / G.3 B2B SaaS(멀티테넌시·billing) / G.4 Marketplace+매출 / G.5 Exit+LLM-2.5 경계
- ADR-236~248, Gate: G_LLM2_GEN_PRIMARY·G_AUTONOMOUS_LOOP_SAFETY·G_TENANT_ISOLATION·G_BILLING_INTEGRITY
- 자금 3안 비교 → **정부 R&D + 스튜디오 제휴 병행, VC 보류** / 사업 트랙은 Phase E부터 병행 착수

---

## 6. 결정 사항 D1~D15 (개발자 결정 대기)

D1~D8(v1.1 승계) + 신규: D9 무결성 선결, D10 생성완화=초안만, D11 다언어 한→영 우선, D12 자금=R&D+스튜디오, D13 사업트랙 Phase E 병행, D14 ADR 211 연속·결번 명시, D15 자동 롤백 의무.

---

## 7. 다음 호출

1. D1~D15 확정 → 본안(blueprint) 작성: 각 SP를 버전 단위 작업·검증 기준으로 분해
2. SP-E.0(무결성)은 결정 대기 없이 즉시 착수 가능(release_gate 보강)
3. 사업 트랙(D5·D12·D13)은 코드와 독립 — Phase E 동시 착수

자기 점검(본 보고서 §9): F·G 일정은 추정 → 절대 일정 대신 Gate 기반 진행 채택으로 위험 흡수.
