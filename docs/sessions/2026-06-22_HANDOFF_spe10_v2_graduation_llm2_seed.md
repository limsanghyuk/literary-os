# 2026-06-22 집→회사 인계: SP-E.10 v2 졸업 실측 + LLM-2 기획 씨앗 + Phase 목적 정본

**작성**: 집(RTX 4070) 세션 종료 시점. **다음**: 회사(무GPU)에서 이어감.
**한 줄**: SP-E.10 졸업 프로토콜 v2를 실 4070에서 5라운드 완주 → 메커니즘 대약진하나 **형식 졸업 미달(R4 rollback)**. 원인=신호 포화. 회사에서는 GPU 없이 **LLM-2 설계 + 더 어려운 시험신호 준비**를 진행.

---

## 0. 오늘 한 일 (요약)
1. **SP-E.10 v2 누적 5라운드 실측** (per-round drift + mastery-maintain) — 핵심 산출.
2. 시스템 **작동 원리/순서** 정리 (loop-C 라운드 + LLM 사다리).
3. **LLM-2 기획 씨앗** — 인간 작가팀(메인/서브) → 오케스트레이터 매핑.
4. **허브 "B" 조사** — 작가팀 역할분업이 이미 Phase C.2에 존재함을 확인 + 빈칸 특정.
5. **Phase A~E 목적 정본** 통합 (전수 조사, 단일 정본화).

---

## 1. SP-E.10 v2 누적 라운드 실측 (오늘의 본 작업)

### 1.1 배경 — v1의 결함
직전 v1(누적 5라운드)은 KL을 **base 기준**으로 누적 측정 → 0.06→3.1→5.3→6.4로 폭발 → R2~5 전부 rollback, graduated=False. 메커니즘이 아니라 **누적 졸업 프로토콜의 KL/포화 처리**가 문제였음.

### 1.2 v2 설계 보강 (3가지)
- **per-round drift**: KL을 base가 아니라 **직전 어댑터** 기준으로 측정(τ=0.50). 누적 폭발 차단.
- **mastery-then-maintain**: W≥0.95 도달 시 "마스터" 인정 → 이후 epochs 1.0→0.25로 축소, 결정 상태에 `maintain` 추가.
- **결정 로직**: 마스터 전 `W1>W0 ∧ drift≤τ ∧ c3 → adopt` / 마스터 후 `W1 유지 ∧ drift≤τ ∧ c3 → maintain` / 아니면 `rollback`.
- 킷: `C:\claude\4070_oneclick\train_4070_cumulative_v2.py` (+ `RUN_CUM_V2.bat`). 오늘 c3 생성 가속 패치(생성 시 gradient_checkpointing 끔 + use_cache 켬, N16→10) + 재개 로직(prior=마지막 adopt/maintain 어댑터) 수정.

### 1.3 환경 (재현용)
- 집 RTX 4070 12GB / Python 3.10 / torch 2.6.0+cu124 / transformers 5.12.1 / trl 1.6.0 / peft 0.19.1 / bitsandbytes 0.49.2.
- 모델 meta-llama/Llama-3.1-8B-Instruct 4bit nf4 + QLoRA(q/k/v/o_proj r16, beta0.1).
- 데이터: 생산혼합 P0쌍(P1 15%/P3 55%/P2 20%) train290 / held250(작품단위 분리). 길이매칭+암기게이트 적용.

### 1.4 결과 — 5라운드
| R | 결정 | W0→W1 | CI하한 | drift | c3 | mastered | epochs |
|---|---|---|---|---|---|---|---|
| 1 | adopt | 0.508→0.720 | 0.664 | 0.086 | PASS | False | 1.0 |
| 2 | adopt | 0.728→**0.976** | 0.957 | 0.403 | PASS | **True** | 1.0 |
| 3 | maintain | 0.984→0.992 | 0.981 | 0.374 | PASS | True | 0.25 |
| 4 | **rollback** | 0.996→1.000 | 1.000 | **0.863** | PASS | True | 0.25 |
| 5 | maintain | 1.000→1.000 | 1.000 | 0.341 | PASS | True | 0.25 |

### 1.5 졸업 판정 — graduated=False
문서화된 graduation_invariant(V794, 6불변식)를 기록에 적용:
- PASS: Σpairs≥250 · 모든 CI하한>0.5 · 길이규칙 0.5≤0.60 · c3 전부 PASS · n_pairs.
- **FAIL: "5연속 성공"** — 엄격(5연속 adopt)·관대(rollback 0) 두 해석 모두 **R4 rollback이 깸**.
- 결과: **형식 졸업 미달**. (단 v1=0/5 성공 → v2=4/5 성공으로 대약진)

### 1.6 진단 — 핵심: 신호 포화
R2에 이미 W=1.0 도달. 이후 R3~5는 **배울 게 없는데도** 학습 압력이 chosen/rejected 분리만 키움(rewards/rejected −9.6→−19.2→−19.5, margins 4.7→9.0→10.3). 그 부작용으로 drift가 가끔 튐(R4 0.863). **게이트는 그 과열 라운드를 정직하게 적발 = 제 일을 함.** 즉 미달 원인은 메커니즘 결함이 아니라 **시험 신호가 2라운드 만에 마스터될 만큼 쉬움**.

### 1.7 두 갈래 길 + 권고
- **(A) 기계적 도장**: 마스터 후 학습압력 더 죽임(epochs 0.1 또는 freeze-후-재측정) → drift 완전억제 → 5연속 maintain. 빠르나 포화 신호 위 도장(invariant가 adopt만 인정 시 의미 약).
- **(B) 실질 진전**(권고): 2라운드에 안 끝나는 **더 어려운 신호** — P3 craft 스케일업 / NextEpisodeBench 은닉 GT / 인간 GT. adopt 연속이 *진짜 계속 배움*의 증거가 됨.
- 권고=B. Phase E 목적(LLM-0→1 졸업을 *실증*)을 형식이 아니라 실질로 만족시키는 길.

### 1.8 산출물(로컬, 집)
- `C:\claude\4070_oneclick\round_records_v2.json` (5라운드 기록)
- `C:\claude\4070_oneclick\lora_v2_1 ~ lora_v2_5` (어댑터)
- ※ 어댑터/verbatim은 허브에 올리지 않음 — 수치 기록만.

---

## 2. 시스템 작동 원리/순서 (정리)
**원리**: 판단은 로컬(공식·Critic), 생성만 LLM, 학습은 loop-C로 누적, **공식 R=바닥(floor)이지 보상 아님**(Goodhart 안전).
**loop-C 한 라운드 순서**: ① 페어링(P0: P1 열화/P3 AI간/P2 온폴리시, 길이매칭+암기게이트+작품분리) → ② 학습(4070 QLoRA DPO) → ③ 측정(held: c1 per-token 승률 / c2 drift≤τ / c3 구조 비퇴행) → ④ 게이트(c1∧c2∧c3 → adopt/maintain/rollback) → ⑤ 누적 체이닝(5라운드) → 졸업.
**사다리**: LLM-0(결정론) → **LLM-1(쌍대 Critic·현재)** → LLM-1.5 → LLM-2(생성 주력) → LLM-3(천장=모작).

---

## 3. LLM-2 기획 씨앗 (작가팀 메인/서브)
사용자 제기: 인간 작가팀 = 메인(전체 구성·회차 플롯·씬 분할 결정) + 서브(개별 씬 생성).
**정정 3**: ① 내려보내는 단위는 씬 하나씩이 아니라 **회차 통째**(비트로 묶임). ② 단방향 하청 아니라 **되먹임 루프**(메인 검토·노트·재수정). ③ 한국 드라마는 전통적으로 **스타작가 단독집필** 多(팀 모델은 지향 구조).
**매핑**: 메인=플래너/오케스트레이터(intent→story_bible→season_arc→beat→scene breakdown) / 서브=생성 LLM / 쇼러너 노트=Critic+공식 게이트 / 복선 회수=macro c3.

---

## 4. 허브 "B" 조사 결과 (오늘)
v730 스냅샷 검증. 작가팀 역할분업 직결 자산:
- **①직접 매치(이미 코드 존재)**: Phase C SP-C.2(V650) `ensemble/agent_coordinator.py` + `agents/` = **DirectorAgent.generate_blueprint(씬 청사진 5요소: 긴장/갈등/전환점/감정/여운) → ScriptAgent(최대3 regen) → CriticAgent(5축 헌법) → request_regeneration 되먹임 → EditorAgent.finalize()**. 사용자 메인/서브+되먹임과 거의 1:1.
- **②Phase B 본인**: SP-B.3 `MultiWorkOrchestratorV2`(V608) = 작품 *간* 오케스트레이션(다른 축, 인프라 재사용만).
- **③Phase C.4 경쟁흡수**: NovelCrafter(Beat Sheet·Scene Outline·Codex)·Sudowrite(스토리바이블) 흡수 명세 → distillation 로드맵. `world.story_bible.StoryBibleAggregator`는 노트만·**미구현**.
- **빈칸 확정**: 서브+비평+편집은 코드 존재. **메인의 거시→미시 계층 플래너(회차 단위 생성본체 조립)가 LLM-2의 진짜 빈칸.** LLM-2는 맨땅 아님 — DirectorAgent 파이프라인+흡수 명세 재사용 가능.

---

## 5. Phase A~E 목적 정본
- **북극성**: 인간 드라마/영화 작가팀 대체(16/24부작 통째 생성). 불변식=판단 로컬·생성만 LLM·학습 누적.
- **A**(v10.0.2): 잴 수 있는 작동 골격 고정(LOSDB+벡터검색+Constitution+공식+게이트). LLM-0.
- **B**(v11.0.0): 단순생성→자가개선 전환(LoRA+RLHF+멀티작품).
- **C**(v12.0.0): 자기학습+작가팀 역할분업(Director→Script→Critic→Editor)+경쟁흡수.
- **D**(→v13.0.0): 운영 견고화(관측성·타입·분산·플러그인·Zero-Trust·카오스).
- **E**(→v14.0.0): **계획↔실제 분기** — 계획=UI/SDK 제품화, **실제=LLM-0→1 졸업 실증으로 피벗**(지금 loop-C). 피벗 이유: 핵심 학습이 실제로 생성을 개선하는지 미증명이면 제품화는 시기상조.

---

## 6. ★회사(무GPU)에서 할 수 있는 것 / 없는 것
**불가(집 4070/클라우드 필요)**: QLoRA DPO 학습, 졸업 라운드, 실 GPU per-token 측정.
**가능(무GPU, 회사에서 진행)**:
1. **LLM-2 오케스트레이터 설계서 작성** — DirectorAgent 파이프라인 재사용 + 메인 거시 플래너(intent→story_bible→season_arc→beat→scene_breakdown) 조립 설계. 빈칸이 명확하므로 바로 착수 가능.
2. **더 어려운 시험신호 준비(경로 B)** — NextEpisodeBench 은닉 GT 쌍 구성, P3 craft 스케일업 쌍 생성. ※ 쌍 생성은 OpenAI API(gpt-4o-mini)로 무GPU 가능. 학습만 집에서.
3. **graduation_invariant 정합 검토** — "maintain"을 성공으로 인정할지 코드 의미론 확정(개발자 결정 필요).
4. 문서/설계/코드 스켈레톤 작업 전반.
**집에 돌아와서**: 준비된 어려운 신호로 4070 재라운드 → 실질 졸업 시도(B).

---

## 7. 다음 단계 권고 (우선순위)
1. (회사) graduation_invariant의 maintain 처리 확정 — A/B 경로 분기점.
2. (회사) 경로 B 신호 준비: NextEpisodeBench 은닉 GT 쌍 (가장 강력) 또는 P3 craft 스케일업.
3. (회사) LLM-2 오케스트레이터 설계서 — DirectorAgent + 메인 거시 플래너 빈칸 조립.
4. (집) 준비된 신호로 4070 재라운드 → 실질 졸업 판정.

---

## 부록 — 메모리 정본(이 세션에서 갱신)
- `project-phase-purpose-canon` (★Phase A~E 목적 단일 정본)
- `project-llm2-direction-seed` (작가팀→LLM-2 매핑 + 허브 B 조사)
- `project-real4070-dpo-state` (SP-E.10 v2 5라운드 실측 추가)
