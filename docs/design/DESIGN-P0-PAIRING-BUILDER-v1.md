# DESIGN-P0-PAIRING-BUILDER-v1
## 선호쌍 빌더 (Preference-Pair Builder) — P0 최종 설계 초안서

- **상태**: 확정 (FINAL) — 멀티에이전트 교차검토 완료
- **작성일**: 2026-06-20
- **버전 기준**: literary-os 13.44.0 (HEAD ed769ac6)
- **연계 문서**: DESIGN-DATA-EVAL-DELIBERATION-v1 §3·§9·§10, DESIGN-LLM-LADDER-v1, ADR-LADDER-3
- **심의 방식**: 독립 서브에이전트 3기(수석 아키텍트·수석 컴파일러·수석 데이터) 병렬 설계 → 수석 시스템 프린시펄 엔지니어 감독·교정·확정

---

## 0. 한 줄 요약

DPO 학습용 선호쌍을 **길이매칭 강제 + per-token 전용 채점 + E4 암기게이트 + 작품단위 train/held 분리**로 생성하는 결정론(GPU 불요) 빌더. 페어링 혼합비 **15/55/20/10(P1/P3/P2/P4)**, held >= 250. 목표는 "더 많은 쌍"이 아니라 **"기법(show-don't-tell)을 가르치되 길이 인공물·암기·순환편향을 입구에서 차단한 쌍"**.

---

## 1. 문제 정의 (구조적)

### 1.1 왜 P0인가
전체 로드맵에서 우리는 **LLM-1 진입(코드화·게이팅 완료, 졸업 미달)** 지점에 있다. 졸업 게이트 `G_LOOPC_WINRATE = c1(dW>0) AND c2(KL<=0.50) AND c3(구조 비퇴행)`을 통과하려면 **실 GPU dW 1라운드(P3)**가 필요하나, P3의 입력인 선호쌍 자체가 오염되어 있으면 측정이 무의미하다. Round#2가 이를 실증했다: **sum-logp 기준 dW +0.196이 전적으로 길이 인공물**(per-token dW=0.000)이었고 어댑터는 ROLLBACK되었다.

→ 따라서 **선호쌍 빌더(P0)가 P3의 선결 조건**이며, GPU 없이 즉시 착수 가능한 최우선 작업이다.

### 1.2 입력이 오염되는 3대 경로 (반드시 차단)
1. **길이 confound** — 인간/명작 텍스트가 짧음 → sum-logp가 기계적으로 짧은 쪽을 선호. (Round#2 실증)
2. **암기/표절** — 명작 원문 단편이 그대로 후보에 유입되면 모델이 베끼기를 학습. (E4 게이트 대상)
3. **순환편향(AI-judge-AI)** — 생성자=심사자일 때 자기 미화. 블라인드 3모드 평가에서 심사위원이 안티-LLM을 인간과 구별 못함(§10-A)으로 실연됨.

### 1.3 설계가 보존해야 할 통찰
"인간 글이 짧은 것은 길이 인공물이 아니라 **기법(show-don't-tell)의 그림자**"(§9). 따라서 길이매칭은 **기계적 절단이 아니라**, 안티-LLM+작가문체로 기법을 가르쳐 *자연히* 짧아지게 하되, 측정 단계에서 잔존 길이차를 중립화하는 이중 장치여야 한다.

---

## 2. 멀티에이전트 교차검토 — 충돌과 해소

| # | 쟁점 | 수석 아키텍트(ARCH) | 수석 컴파일러(COMP) | 수석 데이터(DATA) | 프린시펄 확정 |
|---|------|------|------|------|------|
| C1 | 쿼터 미달 시 | 소프트쿼터 자동충원 | (중립) | 부족분 폐기 | **Fail-fast + 1.3x 과생성 풀.** 자동충원은 편향쌍 재유입 → 기각 |
| C2 | 길이 임계값 | token Δ/max <= 0.20(느슨) | <= 0.20 | token <= 5% hard·char <= 8% soft | **DATA 채택(타이트).** 0.20은 길이 confound 재진입 → DROP |
| C3 | E4 실행 시점 | (미정) | (미정) | 길이매칭 *후* 재실행 | **DATA 채택.** 매칭이 텍스트를 바꾸므로 게이트는 사후 |
| C4 | 채점 스킴 | per-token | per-token | per-token | **per-token 하드코딩 + sum 3중 차단 가드** |
| G1 | (프린시펄 발견) 토크나이저 불일치 | — | — | — | **단일 모델 토크나이저 + tokenizer_sha 잠금** |
| G2 | (프린시펄 발견) ablation 입력셋 | — | — | — | **P0은 input-set 해시만 동결, ablation은 P3로 이연** |

가장 비합리적 전략 제거: ARCH의 **소프트쿼터 자동충원(C1)**과 **느슨한 0.20 임계(C2)**는 둘 다 "쌍 수 채우기"를 위해 오염을 허용 → 본 프로젝트의 1.2절 차단 목표와 정면충돌하므로 제거.

---

## 3. 최종 설계

### 3.1 페어링 전략 혼합비
```
P1  graded-degradation  15%   (열화쌍; 길이매칭+break_causality 길이중립 가중)
P3  AI-vs-AI 주력        55%   (안티-LLM 페어 = 1순위 강화후보, per-token +0.434 미세신호)
P2  on-policy            20%
P4  ties/기타            10%
```
- P1을 30→15%로 낮춘 근거: 열화 4축 중 3축이 텍스트 단축 → V788 길이교란 재유입(DATA 지적).
- 모든 전략 공통: **길이매칭 강제 → E4 게이트 → 작품단위 분리**.

### 3.2 처리 파이프라인 (결정론)
```
load_pairs -> length_match(token<=5%h, char<=8%s) -> E4 memorization_gate
-> per-token score(sum 차단) -> work-level train/held split(held>=250)
-> ledger emit(logp 방출) -> report(분포·임계 위반 카운트) -> freeze input-set hash
```

### 3.3 핵심 불변식 (Invariants)
- **I1 per-token only**: 채점은 `pertoken_winrate.per_token()`만. sum 경로는 (a)함수 가드 (b)CLI 거부 플래그 (c)pre-commit 정적검사 3중 차단.
- **I2 length neutrality**: 모든 채택쌍 token Δ/max <= 5%. 위반 쌍은 리포트에 카운트 후 폐기.
- **I3 no verbatim**: 명작 원문 텍스트 필드는 빌더 산출물에서 삭제(통계만 보존). pre-commit `[가-힣]{20,}` 훅으로 커밋 차단.
- **I4 work-level split**: 같은 작품의 씬이 train/held에 동시 출현 금지(누설 방지). held >= 250.
- **I5 tokenizer lock**: 단일 모델 토크나이저, `tokenizer_sha`를 ledger·report에 기록·동결.

### 3.4 파일별 작업 지시서 (구현 순서)
1. `splits.py` — 작품단위 train/held 분리, held>=250 보장, 누설 검사.
2. `length_match.py` — token/char Δ 계산, 5%/8% 임계, 위반 카운트.
3. `strategies/base.py` — 전략 인터페이스(생성→길이매칭→E4 순서 강제).
4. `strategies/{p1,p3,p2,p4}.py` — 4전략, 혼합비 15/55/20/10, 1.3x 과생성.
5. `credit.py` — P4 `UniformCreditAssigner` 스텁(크레딧 할당 계약 빈칸).
6. `report.py` — 임계 위반·길이분포·E4 reject율·혼합비 실측 리포트.
7. `emit.py` — ledger 방출(logp, n_tokens, tokenizer_sha, input_set_hash).
8. `builder.py` — 오케스트레이터, fail-fast.
9. ledger 스키마 + smoke pytest(전 불변식 I1~I5 검증).

### 3.5 c3(구조 비퇴행) 게이트 조건부
P2.5 구조 라벨 커버리지가 **< 90%**이면 c3 게이트는 HOLD(2,030 전체 미검증). 커버리지 충족 시 ON.

---

## 4. 자기검증 (논리적 약점 점검)

1. **임계값·혼합비는 미실측 휴리스틱.** 5%/8%, 15/55/20/10은 이론적 근거는 있으나 실 GPU dW 1라운드+인간 블라인드로 캘리브레이션 전까지 잠정값. → ADR로 재캘리브레이션 의무 명시.
2. **per-token 마진 +0.434는 승자역전 미달의 미세신호.** P0이 좋은 쌍을 만들어도 P3에서 dW가 유의미하게 양수일 보장 없음. P0은 "오염 제거"까지만 책임지고, 학습신호 강도는 P3 측정 후 판단.
3. **n=1·심사1 일화적.** AI-judge-AI 편향은 *존재* 실연이지 *크기* 정량화 아님 → 확정 판정은 per-token held + 인간 블라인드 이중 못박음 유지.
4. **P4 크레딧 할당은 스텁.** 거시아크 크레딧 분배 계약은 P4(HIER-PLANNER) 설계 미존재 → 빈칸 등록, P0은 인터페이스만.

---

## 5. DoD (Definition of Done)

- [ ] smoke pytest: I1~I5 전 불변식 green
- [ ] held >= 250, train/held 작품 누설 0
- [ ] 채택쌍 token Δ/max <= 5% 100%
- [ ] 산출물에 명작 verbatim 0 (pre-commit 훅 통과)
- [ ] ledger에 logp·n_tokens·tokenizer_sha·input_set_hash 전부 기록
- [ ] report에 혼합비 실측·E4 reject율·임계위반 0 확인
- [ ] 회귀: 기존 75 passed 유지

---

## 6. 다음 (P0 이후)

P0 산출 쌍 -> **P3 실 GPU dW 1라운드**(RunPod 키 미제공이 유일 차단) -> per-token held로만 졸업 판정 -> 인간 블라인드 확정. P2.5(구조 추출, GPU 불요)는 병렬 진행하여 c3 게이트와 P4 입력 준비.
