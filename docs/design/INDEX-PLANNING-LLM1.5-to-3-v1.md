# INDEX — LLM-1.5→2→3 기획 누적 체계 지도 (v1, 2026-06-24)

> **성격: 결정 문서 아님.** 방향을 *수립·누적*하기 위한 지도다. 그동안 쌓인 기획 문서를 한 체계로 묶어 "무엇이 정착됐고 / 무엇이 아직 의견 수립 중인가"를 분리한다. 새 논의는 이 지도에서 갈래를 찾아 해당 문서에 누적한다.
> **작업 방식(사용자 확정): 대화로 기획 누적 → 더 이상 의견 없을 때 본안→개발.**

## 1. 좌표 (어디까지 왔고 어디로 가나)
| Phase | LLM 레벨 | 버전 | 상태 | 정본 |
|---|---|---|---|---|
| A~D | LLM-0 + 틀·구성요소 | ~V745 | ✅ | — |
| **E** | **LLM-1 쌍대 Critic** | V746~795 | **✅ v14.0.0 졸업(2026-06-24)** | DESIGN-ROADMAP-REANCHOR-v1 |
| F | LLM-1.5 (판정 격상·공식 후퇴·코퍼스200·다언어) | V796~875 | ◻ 기획 누적 중 | DESIGN-PHASE-F-LLM15-v1 |
| G | LLM-2~2.5 (생성 주력) | V876~955 | ◻ 기획 누적 중 | DESIGN-LLM2-* |
| 천장 | LLM-3 (블라인드 인간평가 비열위) | V956~ | 개념 | REANCHOR §5 |

## 2. 정착된 사실 (의견 아님 — 실측·실코드로 확정)
- **v14.0.0 졸업 완료**: loop-C 5/5 ADOPT, graduation_invariant 6/6 (tools/loop_c_4070_kit/round_records_v3.json, ADR-249, tag v14.0.0).
- **생성 "기관"은 이미 실재** (7엔진 전부 LLM 0회 결정론): SeriesArcPlanner·CausalPlotGraph·EpisodePlanner·SequencePlanner·PayoffScheduler·structure_conformance(c3)·NextEpisodeBench.
- **5축 Critic은 이미 LLM**(critic/llm_critics.py, 8B). 진짜 공식종속(이양 대상)=**플로어층**(c3·BANDS·drse) + **판단 모델이 8B**.
- **코퍼스 = 다회차 드라마 129편**(+영화) 데이터화·분석 완료. 원본 ~138편 중 .rar 1편까지 편입(corpus_전수분석_드라마_전체.xlsx).
- **룰 인과 ↔ 진짜 인과 강제력 = 0.56 일치**((b) 파일럿). 패턴기반 CausalPlotGraph.infer_causal_edges는 후보일 뿐 → 프론티어 인과 패스 필요.

## 3. 기획 문서 지도 (갈래별)
### (가) 좌표·사다리
- `docs/design/DESIGN-ROADMAP-REANCHOR-v1.md` — Phase↔LLM↔버전 정합, SP-E.x 복원.
- `docs/design/DESIGN-LLM-LADDER-v1.md` — LLM-0~3 자율성 사다리.
### (나) LLM-2 머리(생성 주력 설계)
- `docs/design/DESIGN-LLM2-ORCHESTRATOR-v1.md` — intent→story_bible→…→scene 오케스트레이터.
- `docs/design/DESIGN-LLM2-SYNOPSIS-ASSEMBLER-v1.md` — ★빈칸 머리 I/O 계약 + ★LLM 인과 분류 패스(1급 산출=causal_spine).
- `docs/design/DESIGN-LLM2-CAPACITY-DIVISION-v1.md` — ★"8B로 16/24부작?" 역할분담(결정론 골격/8B 로컬/프론티어 판단).
### (다) Phase F(LLM-1.5)
- `docs/design/DESIGN-PHASE-F-LLM15-v1.md` — SP F.1~F.6 + 게이트 + 진입/Exit + 결정거리 6 [PROPOSAL].
### (라) 졸업·측정·데이터
- `docs/design/DESIGN-GRADUATION-V2.md` / `DESIGN-P0-PAIRING-BUILDER-v1.md` / `DESIGN-DATA-EVAL-DELIBERATION-v1.md`.
- `docs/adr/ADR-249.md` + `docs/sessions/2026-06-24_SP-E10_GRADUATION_v14.0.0.md`.
### (마) 차기 PLAN·방향
- `docs/sessions/2026-06-23_PLAN_post_llm1_llm2_macro_planner.md` — 작가팀 매핑+3팀 심의+분포 실측+①②③ 로드맵.
- `docs/sessions/2026-06-23_DIRECTION_judgment_layer_llm_migration.md` — 판단층 LLM 이양(공식 floor 잔존+프론티어+loop-C 앵커).
### (바) 제품 트랙(병행, 별개)
- Phase E 본안 v1.0 (메모리 project-phase-e-v1): UI·코퍼스·SDK·RLAIF — 제품 경로. ★계획↔실제 분기: v14.0.0은 제품경로 계획이었으나 실제는 메인트랙 loop-C로 달성.

## 4. 열린 의견 의제 (★의견 수립 중 — 결정 아님)
| # | 의제 | 갈래 | 어디서 누적 |
|---|---|---|---|
| O1 | 판정 모델: 프론티어 상시 vs 8B+프론티어 중재만 | F.2 | PHASE-F §5 |
| O2 | 공식 완화 범위: 초안만 vs 초안+중간본 | F.3 | PHASE-F §5 |
| O3 | 다언어 우선: 한→영 vs 한→일 | F.4 | PHASE-F §5 |
| O4 | 코퍼스 200 구성: 드라마만 vs 드라마+영화 | F.1 | PHASE-F §5 |
| O5 | 인과 강제력 축: 6번째 축 vs Structure 흡수 | F.2/③ | PHASE-F §5 |
| O6 | 사업 트랙 병행 시점 | F | PHASE-F §5 |
| O7 | 로그라인/주제 역생성 알고리즘(빈칸2) | G | SYNOPSIS-ASSEMBLER §4 |
| O8 | 수정 전파 엔진(작가 개입→인과 재계산) | G | SYNOPSIS-ASSEMBLER §4 / CAPACITY §5 |
| O9 | 판단 이양 PoC(8B→프론티어 / 플로어 LLM 재현) | F 선행 | PHASE-F §3 |
| O10 | 1급 트랙축 분류 강화(태그없는 회상 미탐) | ②/G | SYNOPSIS-ASSEMBLER §4 |
| O11 | 양성 평가축 + 축간 균형 메타게이트 | G | PLAN/심의 |
| O12 | 제작가능성·시장 게이트 스코프 | G 후반/제품 | PLAN/심의 |
| O13 | 인간 GT(최종시험) 도입 시점 | F~G | PLAN |

## 5. 오늘(2026-06-24) 누적된 방향 (결정 아님, 방향 정리)
1. **졸업 마감**: v14.0.0 공식 종료(검증·버전권위 V795·매니페스트·Release).
2. **코퍼스 전수화**: ①분포 129편 + ②인과/트랙 129편 + 미변환 원본(HWP/zip) 편입.
3. **(b) 파일럿**: 룰 인과 0.56·타임라인 0.50 → "인과 척추=LLM 본질"을 수치로 확인.
4. **세션 전수 조사**: 차기 기획=두 트랙(메인 LLM-2 + 제품 Phase E 본안), 계획↔실제 분기 확정.
5. **③ Synopsis Assembler 설계** + **8B 역할분담** + **Phase F 기획안** 3종 누적.

## 6. 다음 누적 지점
- 의견 의제 O1~O13 중 사용자 선택분을 해당 문서에 누적.
- 의견이 수렴(더 없음)하면 → 해당 SP 본안(ADR/Gate/TC) → 개발.
- 본 INDEX는 누적 시마다 갱신(living).
