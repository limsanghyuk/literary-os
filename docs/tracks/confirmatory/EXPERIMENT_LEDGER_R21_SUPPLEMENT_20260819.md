# Confirmatory Track — R21 Experiment Ledger Supplement (2026-08-19)

**Purpose:** 기존 `EXPERIMENT_LEDGER.md`의 CT-12A 이후 공백을 보완하고, 2026-08-18~19 GPT 세션에서 최종 폐쇄된 CT-13 R3와 현재 retrieval/hierarchical planning 연구 방향을 기록한다.

이 supplement는 기존 ledger를 삭제하거나 재작성하지 않는다. 개별 prereg/report가 가장 세부 권위이며, drama corpus/method/release 수치는 `limsanghyuk/v1700-literary-os`의 live R21 pointer가 권위다.

## CT-13 R3 — EpisodeSynopsisPlan renderer utility

### 원 실험 계보
- R3 preregistration/execution kit: 기존 CT-13 R3 문서군.
- external renderer stage: `CT13_R3_RENDERER_STAGE_REPORT_20260818.md`.
- 48/48 renderer outputs.
- 6 isolated Claude sessions × 8 inputs.
- schema errors 0.
- sealed renderer manifest SHA256: `b9a7c420dde4c58d2c7469272aa230fb220f0cc4784e1859a83b272b804774e0`.

### 2026-08-18~19 GPT closing diagnostic
단일 GPT session 내부에서 strict / semantic-lenient / conservative 세 rubric pass로 robustness를 재확인했다. **이 세 pass는 independent blind scorers가 아니다.**

C vs B:
- P1 p=.0078125
- P2 p=.0009765625
- P3 p=.00048828125
- direction agreement=.9722222

C vs N:
- P1/P2 p=.001953125
- P3 p=.00048828125
- direction agreement=1.0

P4 explicit high-specificity post-N leakage diagnostic = 0.

### 판정
- numeric PASS-like pattern: strong.
- formal preregistered verdict: **UNDECLARED**.
- reason: preregistration §7의 genuinely separated 3 blind scorer requirement가 충족되지 않음.
- same-session replicated scoring을 3인 scorer로 재명명하지 않는다.
- reverse-engineered 38-work EpisodeSynopsisPlan corpus는 CANONICAL 유지.
- autonomous forward EpisodePlan control은 EXPERIMENTAL_HOLD.

### 다음 연구 질문
CT-13은 좋은 Plan이 주어졌을 때 utility를 본다. 다음 핵심은:

`N-1 state + retrieval -> autonomously generated EpisodeSynopsisPlan -> SequencePlans -> ScenePlans -> Beats`

을 미래 SOURCE 없이 blind forward로 시험하는 것이다.

## 기존 증거와 현재 연결

### Blind Forward 2026-08-11
- 공주가돌아왔다: A65 / B84 / C88.
- 결혼못하는남자: SequencePlan 86, leakage 0, scene draft 77→86, holdout compatibility 73.
- PASS_WITH_LIMITATIONS.

### CT-07 / CT-08 family
- representation depth가 generation steering에 기여하는 반복 양의 신호.
- CT-07 r_L2G=.807.
- CT-08 계열은 measurement/scorer gates 때문에 formal strength 제한.

### CT-11
- overall boundary reproduction NOT ESTABLISHED.
- 그러나 cross-work retrieval `C-B = +.070`은 prereg auxiliary threshold +.05를 넘음.
- C의 sequence-count error가 A/B/N보다 크게 감소.
- 해석: retrieval이 설계에 도움이 될 수 있다는 신호이지, retrieval scaling이 이미 증명됐다는 뜻은 아님.

### CT-11B / CT-11C / CT-12A
- boundary prediction 자체는 baseline을 안정적으로 넘지 못함.
- CT-12A가 canonical boundary endpoint contamination 가능성을 확인.
- 따라서 current Boundary R1 repair 이후 retrieval/planning 실험을 재설계해야 함.

## Current research program

1. Retrieval scaling: no retrieval / 5 / 10 / 20 / 38 works.
2. Representation depth scaling: thin / THICK / THICK+Boundary / THICK+Boundary+EpisodePlan.
3. Blind forward autonomous EpisodeSynopsisPlan from N-1.
4. Hierarchical EpisodeSynopsisPlan -> SequencePlans.
5. SequencePlans -> ScenePlans -> Beats.
6. Multi-episode rollout.
7. Originality / retrieval-source leakage.
8. Learned narrative priors, retrieval weights, dynamic narrative attention.

## Cross-repo authority

- drama corpus/method/release: `limsanghyuk/v1700-literary-os` R21 live pointer.
- CT preregistration/engine experiment interpretation: `limsanghyuk/literary-os`.
- full session experiment registry: `v1700-literary-os/DRAMA_ANALYSIS_SESSION_EXPERIMENT_REGISTRY_R21_20260819.md`.
