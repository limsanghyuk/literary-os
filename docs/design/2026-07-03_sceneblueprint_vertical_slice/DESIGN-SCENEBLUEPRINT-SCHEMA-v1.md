# DESIGN — SceneBlueprint 스키마 정식화 v1
## GPT V1700 필드 ↔ literary-os SeqCard 매핑 + 갭 분석

**작성**: 2026-07-03 · **근거**: 비밀의숲_01 오프닝 수직 슬라이스(S1–S7) 실측(SLICE_RESULTS.md)
**목적**: Full-Series Creative OS의 leaf 노드(SceneBlueprint)를 "렌더러가 산문을 생성하기에 충분한 계약"으로 정식화한다. GPT가 제안한 23필드를 우리 실 데이터(SeqCard 30작/593회)와 대조하여 (a) 이미 있는 것, (b) 다른 층에 흩어진 것, (c) 진짜 빈칸을 확정한다.

---

## 0. 요약 (TL;DR)

수직 슬라이스가 입증한 사실: **SeqCard는 씬의 "기능·의도"는 강하게 전달하나(Critic 4.1/5), "사실·동선·폭로·제약"은 거의 전달하지 못한다(2.0/5).** 렌더러는 그 공백을 창작으로 메우며, 최악의 경우 원본에 없는 서브플롯을 환각한다(S7). 따라서 SceneBlueprint 정식 스키마는 **기존 의도층을 유지하되, GPT의 "사실·인과·연출·제약" 필드군을 흡수**해야 한다.

결론: GPT 23필드 중 **9개는 이미 존재**(SeqCard base+v2+edges+meta), **6개는 파생·승격으로 확보 가능**, **8개가 진짜 신규 빈칸**이며 이 8개가 슬라이스 결함(사실 2.0·밀도 2.0)의 직접 원인이다.

---

## 1. 문제의 구조적 정의

Full-Series Creative OS = top-down 생성(FullSeriesArc→EpisodeArc→Sequence→**Scene**→Prose) + bottom-up 검증. 이 중 **Scene 노드**는 유일하게 산문 렌더러의 직접 입력이 되는 leaf다. 따라서 스키마 완결성의 판정 기준은 학문적 합의가 아니라 **기능적 충족**이다:

> "이 필드를 담은 blueprint를 렌더러에 넘겼을 때, Critic이 '의도한 기능을 더 잘 수행한다'고 판정하는 산문이 나오는가(ablation)."

이 기준은 인간 작가 합의(κ)를 요구하지 않으므로, "3.8만 씬을 평가할 실력 작가 부재" 병목을 우회한다. 필요한 것은 렌더러(LLM-1, 입증됨)+Critic 앙상블+loop-C뿐이다.

---

## 2. 3가지 스키마 전략 (ToT 평가)

| 전략 | 내용 | 장점 | 단점/리스크 | 비용 |
|------|------|------|------------|------|
| **A. GPT 23필드 전면 채택** | GPT 스키마를 그대로 SeqCard에 이식 | 완결성 높음 | 30작 재저작 필요·중복필드·연속 0–1 자기점수 유입(패널 기각 항목) | 매우 큼 |
| **B. 기존 유지 + 갭만 신규** | base/v2 유지, 빈칸 8필드만 추가 | 재저작 최소·검증된 필드 보존·층 분리 유지 | 필드 출처가 3층에 분산(조립 필요) | 중 |
| **C. 최소주의(의도만)** | 현행 SeqCard 그대로, 렌더러 프롬프트로 보강 | 데이터 불변 | 슬라이스가 실패 입증(사실·밀도 2.0)·환각 지속 | 작으나 무효 |

**기각**: C(슬라이스가 이미 반증). A(패널이 만장일치 기각한 "연속 0–1 자기점수"를 재유입, 30작 재저작 비용 과다).
**채택**: **B** — 검증된 의도층을 보존하고, 슬라이스가 지목한 사실·제약 빈칸만 신규. layer 분리 원칙(관계=edges, 회차=meta, 시리즈=arc)과도 정합.

---

## 3. 매핑표 — GPT 23필드 ↔ SeqCard

범례: ✅ 존재 · 🔶 파생/승격 가능 · ❌ 신규 빈칸

| # | GPT SceneBlueprint 필드 | 상태 | literary-os 대응 위치 | 비고 |
|---|------------------------|:---:|----------------------|------|
| 1 | scene_id | ✅ | base.work_id + scene_no | |
| 2 | sequence_id | 🔶 | 시퀀스 분할(4계층) 미결합 | SequencePlan 승격 필요 |
| 3 | scene_order | ✅ | base.scene_no | |
| 4 | scene_function_core | ✅ | base.core | INTRO/LOSS/ORACLE… |
| 5 | scene_function_core2 | ✅ | base.core2 | |
| 6 | scene_purpose | ✅ | base.intent_gist | 슬라이스: 강하게 전달됨 |
| 7 | scene_objective | 🔶 | v2.character_driving_want | want→objective 승격 |
| 8 | dramatic_conflict | ❌ | **없음** | 슬라이스 결함 직접원인 |
| 9 | character_entry_state | ❌ | **없음** | 인물 진입 감정/지식 상태 |
| 10 | character_exit_state | ❌ | **없음** | 인물 이탈 상태(=다음 씬 입력) |
| 11 | relationship_delta | ✅ | edges.jsonl(관계 트리플) | v2 관계층 |
| 12 | causal_input | 🔶 | v2.need_ref / causal_plot_graph | 그래프에서 파생 |
| 13 | causal_output | 🔶 | causal_plot_graph 엣지 | |
| 14 | plant_operations | ❌ | **없음** | 복선 심기(payoff와 짝) |
| 15 | payoff_operations | ❌ | **없음** | 복선 회수 |
| 16 | information_reveal | ❌ | **없음** | 관객/인물 정보 공개 관리 |
| 17 | emotional_turn | 🔶 | v2.tension_role(범주형) | 정서 전환 근사 |
| 18 | visual_or_directorial_notes | ❌ | base.skin(톤만) | skin=분위기, 연출·소품·동선 아님 |
| 19 | dialogue_intention | ❌ | **없음** | 대사가 수행할 기능 |
| 20 | subtext_target | ❌ | **없음** | 표면 아래 진짜 의미 |
| 21 | ending_hook_or_transition | ✅ | v2.hook_flag(+episode_role) | advisory 등급 |
| 22 | renderer_prompt_constraints | ❌ | **없음** | 길이·금칙·시점·밀도 |
| 23 | hard_rule_self_check | 🔶 | Critic/구조게이트에 별도 존재 | 필드화 미결 |

**집계**: ✅9 · 🔶6 · ❌8.

---

## 4. 진짜 빈칸 8필드 — 슬라이스 결함과의 인과

| 신규 필드 | 미보유가 유발한 슬라이스 결함 |
|-----------|------------------------------|
| dramatic_conflict | S2·S5 갈등의 구체가 없어 렌더러가 임의 갈등 창작 |
| character_entry/exit_state | 씬 간 인물 상태 승계 부재 → 연속성은 title 요약에만 의존 |
| plant_operations / payoff_operations | S7 복선 없이 렌더러가 협박 녹음 서브플롯 **환각** |
| information_reveal | 원본의 폭로 순서(칼 발견→자상 판독) 미전달 → 임의 재구성 |
| dialogue_intention / subtext_target | 대사가 전혀 다른 내용으로 대체(S2 번지수개그 소실) |
| **renderer_prompt_constraints** | **길이 무통제 → 2.7–10.1× 팽창(전 씬)** |

→ 8필드는 "있으면 좋은" 장식이 아니라, **슬라이스가 실측으로 지목한 결함의 1:1 처방**이다.

---

## 5. 정식 스키마 v1 (전략 B) — 계층 배치

```
SeriesArc      (series_arc.json)      : 이미 30작 존재
 └ EpisodeArc  (episode_meta.json)    : episode_role 등
   └ SequencePlan  [승격 필요: #2 sequence_id + length + kind]
     └ SceneBlueprint (seqcard.jsonl) :
         [base]  work_id, scene_no, heading, title, intent_gist, core, core2, skin
         [v2]    episode_role, tension_role, hook_flag, character_driving_want,
                 scene_blocks_need, need_ref, continuity_break
         [edges] relationship_delta            (관계층 분리 유지)
         [신규8] dramatic_conflict, character_entry_state, character_exit_state,
                 plant_operations[], payoff_operations[], information_reveal,
                 dialogue_intention, subtext_target,
                 renderer_prompt_constraints{max_len, pov, forbid[], density}
         [파생]  causal_input/output ← causal_plot_graph, hard_rule_self_check ← Critic
```

**설계 원칙(패널 정합)**: ①연속 0–1 자기점수 금지(범주형·구조적 값만). ②관계는 edges 트리플 유지(씬 필드로 병합 금지). ③hard_rule_self_check는 생성 서브시스템(Critic)에 격리, blueprint에는 참조만.

---

## 6. 검증 방법 — 필드별 ablation 게이트

각 신규 필드의 채택 기준(κ 아님, 기능):
1. 동일 씬을 **필드 포함 vs 제거**로 각각 렌더.
2. Critic 앙상블(3+)이 "의도 기능 충족"을 blind 비교.
3. 포함본이 유의하게 우세하면 **필드 load-bearing 입증→채택**.

슬라이스에서 intent_gist는 이 게이트를 통과(S5 ablation: 제거 시 인물 각인 소실). renderer_prompt_constraints는 다음 라운드 최우선 검증 대상(길이 결함이 가장 크고 측정 명료).

---

## 7. 논리적 약점 자가점검 → 개선

- **약점1**: 슬라이스 N=7·1작. → 일반화 주장 아님. 다장르 3–5작 확대 후 필드 확정(방법은 확립).
- **약점2**: Critic=Opus 단일. → 채점은 AI-judge-AI 편향 가능. 정식 게이트는 3+ 앙상블·교차모델 필수(문서 §6 반영).
- **약점3**: 신규 8필드 저작 비용. → 30작 전량 아님. ablation으로 **필드당 가치 먼저 입증→통과분만** 확대 저작(fail-fast).
- **약점4**: GPT 필드명 그대로 채택 시 우리 core 택소노미와 의미 충돌 가능. → 매핑표(§3)로 명시 정합, 신규는 우리 명명 규칙 준수.

**개선된 최종 권고**: 전략 B 채택. 다음 실행 단위 = renderer_prompt_constraints 1필드 ablation(길이 결함, 최대·최명료) → 통과 시 dramatic_conflict·plant/payoff 순차. 30작 재저작은 필드 가치 입증 전까지 보류.
