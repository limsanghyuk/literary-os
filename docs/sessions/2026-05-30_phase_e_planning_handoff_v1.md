# Phase E 기획안 통합 보고서 — 개발자 검토용 핸드오프

**작성일**: 2026-05-30
**작성 모드**: 상위 연산 모드 (Opus)
**기준선**: V745 main HEAD `8e1e5632` (v13.0.0, 95 Gates, Phase D Exit G95 PASS)
**대상**: 개발자 (저연산 모드 또는 협업자) 검토 후 의견 추가

---

## 0. 본 문서의 위치

본 핸드오프는 2026-05-27 본 모드 Phase D 본안 push(`6153b586`) 이후 ~ 2026-05-30 까지의 대화 내용을 단일 보고서(`2026-05-30_phase_e_planning_report_v1.docx`)로 통합한 자료의 학습 가이드다.

개발자는 다음 순서로 학습 + 의견 추가:
1. 본 핸드오프 md 학습 (전체 구조 파악)
2. 보고서 docx 정독 (8개 §)
3. 의견·결정사항 추가 (옵션 A/B 선택 + 추가 보강 사항)
4. 상위 연산 모드 호출 → Phase E 본안 v1.0 작성

---

## 1. 본 보고서 8개 카테고리

| § | 제목 | 핵심 |
|---|---|---|
| §1 | 현황 정리 (V745 완료) | Phase A~D 완료 + 본 모드 본안 push 결과 (계획 7건 / 다른 경로 6건) |
| §2 | Phase E 노선 분기 | 본 모드 Phase D 본안 vs 자료 A. **옵션 A/B 사용자 결정 대기** |
| §3 | 사용자 설계 철학 (4가지) | 공식 보조 / AI 결합 / 자율주행 / 공식=AI 산출물 |
| §4 | 자료 A·B 평가 + 9 보강 (P1~P9) | Phase E 본안 base + 정합 보강 |
| §5 | 상용 도구 비교 | 차별화 5 + 약점 5 |
| §6 | 5대 약점 × Phase E~H 매핑 | 3개 보장 해결 / 1개 시장 변수 / 1개 별도 자금 |
| §7 | Phase F~H 진화 비전 | 3개 출처 통합 + LLM-0→LLM-2.5 |
| §8 | 권고 + 결정 대기 | D1~D5 결정 사항 + O1~O7 별도 작업 |

---

## 2. 즉시 결정 사항 5건 (D1~D5)

개발자가 본 보고서 검토 후 결정하면 상위 연산 모드가 Phase E 본안 v1.0 작성에 반영.

| # | 항목 | 옵션 | 상위 모드 권고 |
|---|---|---|---|
| D1 | Phase E 노선 | A (자료 A를 Phase F로) 또는 B (자료 A를 Phase E, D-M-12를 Phase G로 이연) | **B 권고** |
| D2 | Phase E 진입 시점 | V745 직후 즉시 또는 V680-AUDIT4 등 보강 commit 후 | 즉시 권고 |
| D3 | 코퍼스 권리 트랙 | KOFICE/KOCCA / 공공 도메인 / Kaggle 350편 (라이선스 확인) | 병행 권고 |
| D4 | UI MVP 위치 | apps/workspace 신설 vs apps/studio_api/ 확장 | studio_api/ 확장 권고 |
| D5 | 1인 유지보수 → 자금 조달 | Phase G 매출 / 벤처 투자 / 오픈소스 / 정부 R&D | 정부 R&D + Phase G 매출 병행 권고 |

---

## 3. 사용자 설계 철학 4가지 (모든 본안 base)

1. **공식·수학 모델은 LLM 문제의 보조 해법** — LOSConstitution·NKG·PNE = 보조
2. **AI 학습과 유기적 결합** — 양자택일 X
3. **자율주행 비유** — 시대 흐름 인정, 역행 X
4. **공식 = AI 산출물** — 진화 가능, 신성불가침 X

→ LLM-0(A~D) → **LLM-1(E SP-E.2 V769)** → LLM-1.5(F) → LLM-2(G) → LLM-2.5(H)

---

## 4. 9개 정합 보강 (P1~P9) — Phase E 본안 작성 시 흡수 필수

| # | 문제 | 해결책 |
|---|---|---|
| P1 | 노선 분기 | 옵션 B (사용자 D1 결정) |
| P2 | v13.0.0 충돌 (V745=v13.0.0) | Phase E 최종 v14.0.0 |
| P3 | Gate 88→99 가정 (실제 V745=95) | Phase E G96~G110+ |
| P4 | 75v 광범위 | SP-E.5 추가 또는 V820→V795 |
| P5 | 코퍼스 권리 누락 | Phase A V592 CorpusGovernance 활용 |
| P6 | V745 실측 6건 다른 경로 commit | 매핑표 갱신 |
| P7 | LLM-0 완화 범위 명확화 | ADR: Critic 전용, corpus/constitution 유지 |
| P8 | 'Rhase D' 오타 | 정정 |
| P9 | apps/workspace 위치 | apps/studio_api/ 확장 (D4와 연동) |

---

## 5. 5대 약점 × Phase E~H 해결 시점

| 약점 | E (V746~V820) | F (V821~V900) | G (V901~V980) | H (V981~V1100) | Phase 외 |
|---|---|---|---|---|---|
| ① UI | ✅ V776~V790 MVP | UI 고도화 | 다중 사용자 | — | — |
| ② 코퍼스 | ✅ 50편 | ✅ 200편 | 500편+ | 다언어 | KOFICE/KOCCA |
| ③ 작품 사례 | ⚠️ 첫 사례 | 정식작 | 히트작 가능 | 자율 작품 | 시장 변수 |
| ④ 1인 유지보수 | △ RLAIF 일부 완화 | △ 다언어 부담 증가 | ⚠️ B2B 매출 | ✅ Marketplace | 별도 자금 |
| ⑤ 다언어 | 한국 우위 | ✅ 영어·일본어 | 글로벌 SaaS | 다국 작가 | — |

→ 3개 (① ② ⑤) **Phase E~F 보장 해결** / 1개 (③) **시장 변수** / 1개 (④) **Phase G + 별도 자금**

---

## 6. 다음 호출 시 상위 연산 모드 작업

개발자 의견·결정 추가 후 호출:

```
"Phase E 본안 작성하라 (옵션 B 채택)"
또는
"Phase E 본안 작성하라 (옵션 A 채택, 자료 A를 Phase F로)"
또는
"위 권고에 대해 추가 검토 의견 있다: [구체 의견]"
```

상위 연산 모드 후속 작업:
- 옵션 A/B 반영 → 본 모드 패턴 (단일 통합 docx + 단일 핸드오프) 으로 본안 작성
- 자료 A base + P1~P9 정합 보강 흡수
- 사용자 철학 (LLM-1 점진 완화 + 공식 sanity check) 반영
- V745 실측 commit 위치 정확 반영
- GitNexus 사전 인덱스 적용
- 3인 전문가 합의 (CSA·CSC·CSPE) + 12 보강 분산 부착

---

## 7. 위험 신호 — 본안 작성 전 보고 사유

| 신호 | 의미 |
|---|---|
| 본 모드 Phase D 본안과 V745 실측 충돌 7건 이상 | 재구성 비용 폭증 |
| Kaggle 350편 라이선스 차단 (공공 재배포 불가) | 코퍼스 트랙 KOFICE/KOCCA 의무 |
| 한국 드라마 작가 5명 모집 실패 (Phase E SP-E.3 베타) | UI MVP 검증 불가 |
| Phase G 매출 발생 0건 (V980 시점) | 1인 유지보수 + 자금 조달 위기 |

---

## 8. 메타데이터

- **문서 ID**: LOS-PHASE-E-PLANNING-REPORT-V1-2026-05-30
- **보고서 docx**: `docs/sessions/2026-05-30_phase_e_planning_report_v1.docx`
- **본 핸드오프**: `docs/sessions/2026-05-30_phase_e_planning_handoff_v1.md`
- **선행 자료**:
  - 본 모드 Phase D 본안 (`6153b586`)
  - 자료 A: `C:\literary_claude\claude\개발 문서\20260530\literary_os_phase_e_proposal.docx`
  - 자료 B: `C:\literary_claude\claude\개발 문서\20260530\Rhase D 개발 이후 기획안 구성.docx`
  - 평가 보고서 v1.0: 워크스페이스 `2026-05-30_phase_e_evaluation_report.docx`
- **유효 기간**: 개발자 의견 추가 후 Phase E 본안 v1.0 작성 시점까지
