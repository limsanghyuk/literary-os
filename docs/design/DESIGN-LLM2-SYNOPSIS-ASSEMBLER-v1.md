# DESIGN-LLM2-SYNOPSIS-ASSEMBLER-v1 — LLM-2 거시 플래너 기획 + Synopsis Assembler 설계

- 상태: 제안(PROPOSAL) · 2026-06-24 · 기준 v14.0.0 (Phase E Exit / SP-E.10 졸업 완료)
- 감독: SPE · 연계: DESIGN-ROADMAP-REANCHOR-v1, project-llm2-direction-seed(메모리), 회사세션 「LLM2 기획안」, ②인과트랙 파일럿, (b)LLM분류 파일럿
- 원칙: 미선언 금지 — 아래 기관 주장은 전부 실코드 경로로 grounding됨.

## 0. Phase 좌표 (확정)
| Phase | LLM 레벨 | 버전 | 상태 |
|---|---|---|---|
| A | LLM-0 결정론 코어 | ~V595 | ✅ |
| B/C/D | 멀티작품·자기학습·운영 (틀+구성요소) | ~V745 | ✅ |
| **E** | **LLM-1 쌍대 Critic** | V746~795 | **✅ SP-E.10 = v14.0.0 졸업 완료(2026-06-24)** |
| F | LLM-1.5 (5축 전체 AI + 생성초안 공식완화 + 코퍼스200·다언어) | V796~875 | ◻ 다음 |
| G | **LLM-2~2.5 (생성 주력)** | V876~955 | ◻ ★본 문서가 기획하는 단계 |
| 천장 | LLM-3 (블라인드 인간평가 비열위) | V956~ | ◻ 개념 |

→ 사용자 질문 답: **현재 = SP-E.10/Phase E Exit(LLM-1 졸업) 완료.** 다음 = **Phase F(LLM-1.5)**, 그 다음 = **Phase G(LLM-2, 생성주력)**. LLM-2 기획 = Phase G 기획이며, 본 문서가 그 척추.

## 1. LLM-2의 본질 — "0→1"이 아니라 "부품→조립 + 통제권 이양" (회사세션 정합)
Phase A~D = 문학 생성의 **틀·가이드라인 + 구성요소(레일)**. Phase E = 원본 입수·DB화·학습 + **판단의 LLM화 시작**(5축 Critic LLM 이양 + loop-C DPO). LLM-2는 *없는 걸 새로 만드는* 게 아니라 *이미 만든 생성 기관의 통제권을 공식에서 LLM으로 넘기고, 흩어진 부품을 자율 조립*하는 단계.

## 2. 준비물 지도 (실코드 grounding)
### (a) 이미 있음 — 생성 "기관"
| 기관 | 실코드 | 역할 |
|---|---|---|
| 거시 아크 | `arc/series_arc_planner.py::SeriesArcPlanner.plan()` | 16부 4막(기25/승35/전25/결15)·S텐션·복선예산 자동 |
| 인과 플롯 그래프 | `arc/causal_plot_graph.py::CausalPlotGraph` | 에피소드 인과·복선 엣지 (★`infer_causal_edges`=**패턴기반 LLM 0회**) |
| 회차 분해 | `episode/episode_planner.py::EpisodePlanner.plan()` | K(미시플롯 수)=9변수 결정론 |
| 미시플롯 | `episode/microplot_matrix.py::MicroPlotMatrix` | 회차 내 미시플롯 배치 |
| 복선 회수 | `causal_plan/payoff_scheduler.py::PayoffScheduler` | residue를 16부에 스케줄(get_episode_brief·rebalance) |
| 시퀀스 | `orchestrators/sequence_planner.py::SequencePlanner` | 씬 묶음 |
| 인물·사건 | `analyzer/orchestrator.py` (character_birth/ledger/grid/pressure_cast) | 인물 등장판정·원장·배치 |
| 5축 비평 | `critic/llm_critics.py` (Structure/Character/Dialogue/Emotion/Genre) | **이미 LLM 쌍대 비교** |
| 다음회차 예측 | `critic/next_episode_bench.py` (M2 은닉GT) | 헤드룸 넓은 평가신호 |

### (b) 공식 종속 = 이양 대상 (플로어층)
`critic/structure_conformance.py`(c3), 트레이너 BANDS, drse, emotion 밴드 + **판단 모델이 8B**(프론티어 아님). → Phase F/G에서 점진 이양(공식은 floor로 잔존, 발동률 0 수렴이 LLM-2~3 지표).

### (c) 빈칸 = LLM-2가 새로 만들 것
1. **Synopsis Assembler** (머리 — 설계만 있고 구현 0, 클래스 부재 확인) ← 본 문서 §3
2. **로그라인/주제 역생성** (전제→로그라인·aboutness)
3. **수정 전파 엔진** (작가가 한 부분 고치면 인과로 엮인 뒤 이야기를 다시 짜는 엔진 — 회사세션 지목)

## 3. ★ Synopsis Assembler 설계 (LLM 인과 분류 패스 기반)
### 3.1 위치
씨앗 하나(장르·전제·제약)에서 시놉시스 한 장으로 top-down 조립하는 **머리**. 흩어진 §2(a) 기관들을 호출 그래프로 묶는다.

### 3.2 I/O 계약
```
SynopsisRequest:
  genre: str            # 주장르(+혼합 비중, ②파일럿: K드라마는 코믹/멜로 상시혼합)
  premise: str|None     # 전제(있으면) — 없으면 logline 역생성으로 보강
  logline: str|None
  constraints: {episodes:int, runtime_min:int, tone:[...], target:str}
SynopsisDraft (PD 10요소 + 작가 인과척추 1급):
  logline, theme(aboutness),
  characters[](주인공/반대/주변 + birth_gate 근거),
  central_conflict,
  causal_spine: [CausalLink]   # ★1급 산출 (아래)
  macro_arc(4막·텐션곡선),
  episode_beats[](회말 훅 5종),
  subplot_tracks[](메인/서브 3기준 분리),
  tone_genre_profile,
  track_axis: '시간선형'|'진영형'   # ②파일럿 발견 = 작품군 1급 축
```
### 3.3 호출 그래프
```
premise → [로그라인 역생성(빈칸)] → theme
       → SeriesArcPlanner.plan() → CausalPlotGraph(거시 아크·4막·텐션)
       → ★LLM 인과 분류 패스 → causal_spine 확정 (아래 3.4)
       → EpisodePlanner.plan() → 회차별 K·비트
       → PayoffScheduler.generate_schedule() → 복선 setup→payoff 배치
       → 인물엔진(birth_gate/ledger/pressure_cast) → 인물 세트
       → SynopsisDraft 조립 (+분포는 부산물 검증)
```
### 3.4 ★LLM 인과 분류 패스 = 1급 산출 (본 설계의 핵심)
- **문제(실측 근거)**: `CausalPlotGraph.infer_causal_edges()`는 **패턴 기반·LLM 0회**. (b) LLM분류 파일럿에서 룰(인물공유 등 패턴)↔진짜 인과 강제력 **일치 0.56**, 특히 **위음성 8/32**(인물 안 겹쳐도 인과 — 사물·정보·사건으로 잇는 인과를 룰이 놓침). 3-전문가팀 결론("인과척추=LLM 본질, 룰 그림자 아님")이 수치로 입증.
- **설계**: CausalPlotGraph가 깐 후보 엣지(패턴) 위에 **LLM 강제력 판정 패스**를 얹는다. 각 (씬/비트 A → B) 후보에 LLM이 `{causal: bool, force: 0~1, type: enable|cause|foreshadow|payoff, why}` 판정. 룰 엣지는 *후보 생성(recall)*, LLM은 *강제력 확정(precision)* + 룰이 놓친 비인접·비인물 인과 *추가 발굴*.
- **앵커(Goodhart 방지)**: LLM 판정은 명작 코퍼스의 실측 인과척추(②확장 데이터)에 대해 일치도(κ)로 캘리브레이트. floor(c3 structure_conformance)는 잔존, LLM 발동률·일치도를 상시 계측.
- **산출**: `causal_spine` = 강제력≥τ 엣지의 DAG(주제 질문 포함). 이것이 SynopsisDraft의 1급, 인물 분포는 부산물 검증으로 강등.

### 3.5 비용·리스크
순수 설계+소액 API(인과 패스 PoC). GPU 불요. 리스크: 호출할 생성모델은 LLM-1 졸업 직후라 출력품질 미검증 → 생성모델을 **인터페이스로 추상화**(졸업 후 일부 필드 재설계 가능, 계약은 유효).

## 4. 구체화 필요 의제 (이전 세션·파일럿 누적 — 미해결)
1. **로그라인 역생성**(빈칸2) 알고리즘 — 전제→로그라인·theme. LLM 생성 + 명작 로그라인 코퍼스 대조.
2. **수정 전파 엔진**(회사세션 지목) — 작가 개입 시 causal_spine 따라 후속 비트 재계획(PayoffScheduler.rebalance 재사용 가능성).
3. **판단 이양 PoC** (회사세션 ②): (a)8B→프론티어 판정자 격상 일치도/정확도, (b)플로어(c3/BAND) LLM 재현 일치도 → 발동률 0 수렴 경로.
4. **1급 트랙축 분류 강화**(②파일럿): 과거/현재 명시태그 의존 한계 → 더 긴 문맥·씬연쇄 LLM 입력.
5. **양성 평가축**(3팀): 변화회계·설정-회수율·선택의 비용·서브텍스트 밀도 + 축간 균형 메타게이트(측정 쉬운 축 쏠림 방지).
6. **제작가능성·시장 게이트 스코프**(PD팀): 1차=집필(인과척추), 제작게이트는 입력조건 인터페이스만 빈칸(Phase G 후반/제품트랙).
7. **인간 GT**: rejected=AI 평이체 → 인간 명작 직접대조(최종시험).

## 5. 정직한 경계
- 본 문서는 **방향·설계**이지 Phase G 졸업 계약 아님. LLM-2 임계(자가평가 κ≥0.6 등)는 F 통과 후 못 박는다.
- "기관이 다 있다"는 *존재*이지 LLM 주력 하 정합 작동의 *보장*이 아님.
- 인과 LLM 패스의 (b) 근거는 소표본 지시값 — Synopsis Assembler 착수 시 라벨셋 확장 재측정 필요.

## 6. 다음 산출
`SynopsisRequest`/`SynopsisDraft` 스키마 코드 + LLM 인과 패스 PoC(명작 코퍼스 라벨 대비 κ) → DESIGN을 코드 스캐폴딩으로.
