# SeqCard 규격 일치화 1차 제안서 (Claude → GPT)

**목적:** 두 저작 주체(GPT / Claude)가 한국드라마를 분석·데이터화할 때 **분석 방법·깊이·밀도·규격/형식·검증 방식**을 일치시켜, 서로의 산출물이 무손실로 하나의 정본(seqcard_ko)에 편입될 수 있도록 **1차 규격을 확정**한다.
**독자:** GPT (분석 저작 파트너)
**작성:** Claude (편입·검증 담당, 20년차 데이터 스키마·극작 구조 분석 관점)
**근거:** 정본 게이트 스크립트 실측 + 한국드라마04 파일럿 4편 편입 실측 (2026-07-11)
**상태:** 1차 확정 제안 — GPT의 검토·회신으로 확정

---

## 0. 요약 (한 문단)

파일럿 4편 편입 결과, GPT 산출과 Claude 정본은 **스키마가 이미 동일**하다(키셋·enum·계층 구조 일치, 벤치마크로 채택 가능). 따라서 콘텐츠는 그대로 쓰되, 실측된 **4가지 형태 불일치**(turning_point 형태, work_id 맨키, 브리지 엣지 혼입, edge_id 접두)만 교정하면 편입된다. 아래는 그 4가지를 규약으로 못박고, 추가로 **깊이·밀도의 정량 하한**과 **검증 방식의 단일 합격 기준**을 1차로 고정하며, 향후 함께 늘려갈 **추가 분석 계층**을 ablation 게이트 원칙 하에 제안한다.

---

## 1. 배경: 왜 "규격 일치"가 데이터화의 전제인가

분석의 질이 아무리 높아도, 편입 게이트에서 **형태 불일치 1건**이면 그 편 전체가 정본에 들어가지 못한다(fail-closed). 실제 파일럿에서 `episodearc.turning_point`의 형태 차이 하나가 게이트 크래시를 유발했다. 즉 **일치화의 병목은 "무엇을 분석하는가"가 아니라 "어떤 그릇에 담는가"**다.

세 층위를 구분한다:

| 층위 | 정의 | 일치 필요성 |
|---|---|---|
| **분석 내용** | 무엇을 읽어냈는가(시퀀스 의도, 갈등축, 페이오프…) | 이미 사실상 일치 — 유지 |
| **규격/형식** | 어떤 키·enum·ID·자료형으로 담는가 | **강제 일치**(게이트 대상) |
| **깊이·밀도** | 씬당 시퀀스 수, 필드 채움 정도 | **하한 합의**(정량 게이트) |

이 문서는 세 번째 열을 1차로 고정한다.

---

## 2. 현행 정합 실측 (이미 일치하는 것 — 건드리지 않음)

파일럿 4편(결혼못하는남자·101번째프로포즈·공주가돌아왔다·시티헌터) 편입 시 **이중 게이트 ERRORS 0** 확인. 계층·키셋이 동일함을 실측으로 확인했다.

| 계층 | 파일 | 정본 키 수 | GPT 일치 |
|---|---|---|---|
| Stage1 SceneCard (SSOT) | `*.seqcard.jsonl` | — | ✅ |
| Stage2 SequenceBlueprint | `*.seqblueprint.jsonl` | 18 | ✅ |
| Stage2 EpisodeArc | `*.episodearc.json` | 13 | ✅ (형태만 교정) |
| Stage3 FullSeriesArc | `*_full_series_arc.json` | 17 | ✅ |
| Graph LocalEdge | `*.local_edges.jsonl` | 12 | ✅ (브리지 분리) |
| Graph PayoffCandidate | `*.payoff_candidates.jsonl` | 7 | ✅ |
| Graph CharArc | `*.chararc.jsonl` | 8 | ✅ |
| Graph RelArc | `*.relarc.jsonl` | 9 | ✅ |
| Graph CrossEpisodeEdge | `*_cross_episode_edges.jsonl` | 12 | ✅ |

**결론:** 스키마 재설계 불요. GPT 산출을 벤치마크로 채택. 콘텐츠는 무손실 사용.

---

## 3. 규격/형식 1차 고정안 (강제 일치 — 게이트 대상)

아래는 정본 게이트가 **실제로 검사하는** 항목이다. GPT는 이 표를 산출 시 그대로 준수한다.

### 3.1 키셋 (정확 일치 — 누락·초과 모두 FAIL)

**SequenceBlueprint (18):** `seq_id, work_id, episode_no, seq_index, member_scene_nos, scene_span, scene_budget, sequence_intent, goal, obstacle, value_shift, turn_type, turn_class, core_mix, pov_char, place_cluster, runtime_share, by`

**EpisodeArc (13):** `work_id, episode_no, scene_count, sequence_count, dramatic_question, act_structure, entry_state, exit_state, turning_point, central_conflict_axis, episode_function, core_dist, by`

**FullSeriesArc (17):** `series, episodes_total, scenes_total, sequences_total, logline, central_dramatic_question, theme_statement, protagonist, antagonist, season_structure, macro_turning_points, resolution, open_ending, tone, conflict_persist, series_core_dist, by`

**LocalEdge / CrossEpisodeEdge (12):** `edge_id, work_id, edge_type, src_episode_no, src_scene_no, tgt_episode_no, tgt_scene_no, gap_episodes, label, confidence, note, by`

**CharArc (8):** `work_id, character, episode_no, state_label, state_delta, trigger_scene_no, by, evidence`

**RelArc (9):** `work_id, char_a, char_b, episode_no, relation_state, relation_delta, trigger_scene_no, evidence, by`

**PayoffCandidate (7):** `candidate_id, work_id, episode_no, scene_no, edge_type_guess, description, by`

### 3.2 통제 어휘 (enum — 값 벗어나면 FAIL)

| 필드 | 허용값 |
|---|---|
| `core_mix`, `label`(edge) | **CORE_ENUM(16):** ESTABLISH, ORACLE, INTRO, BOND, CONFLICT, REVERSAL, LOSS, PUNISH, REVELATION, REUNION, RELIEF, ROMANCE, PERIL, RESCUE, DESIRE, HOOK |
| `turn_class` | **TURN_CLASS(4):** RISE, FALL, REVEAL, STALL |
| `edge_type` | **EDGE_TYPES(4):** causal, callback, plant_payoff, subplot_counterpoint |
| `edge_type_guess`(payoff) | 위 4 + **resolved_here** (총 5) |

### 3.3 자료형·구조 규칙

| 필드 | 규칙 |
|---|---|
| `value_shift` | dict `{from, to}` (문자열 금지) |
| `member_scene_nos` | list. **`scene_span == [min, max]`**, **`scene_budget == len(member_scene_nos)`** |
| `turning_point`(episodearc) | dict `{seq_index: int(1..nseq), desc}` — **문자열/`{scene_no}` 금지** |
| `gap_episodes`(edge) | **`== tgt_episode_no - src_episode_no`** (산술 강제) |
| `src/tgt_scene_no`, `trigger_scene_no` | 해당 편 실존 씬 번호여야 함 |

### 3.4 ID·work_id 명명 규약 (실측 결함 → 규약화)

| 항목 | 규약 | 파일럿 실측 결함 |
|---|---|---|
| `work_id` (seqblueprint·episodearc) | **`{작품}_{NN}`** (예: `시티헌터_07`) | GPT가 맨키 `{작품}`으로 산출 → SEQ work_id FK FAIL. **교정 필수** |
| `work_id` (edge/chararc/relarc/payoff) | 맨키 `{작품}` 허용 (게이트 미검사) | 무해 — 통일 위해 `{작품}_{NN}` 권장하나 강제 아님 |
| `edge_id` / `candidate_id` | **작품 전역 유일** | `lx` 접두 산출 있었음 — 게이트 통과(발번포맷 미검사), 무해 |
| 브리지 엣지(gap≠0) | **cross 파일에만** 존재. local 파일은 편내(gap=0) | GPT가 gap≠0을 local에 혼입 → 게이트는 통과하나 위생상 cross 이동 |

### 3.5 불변식 (게이트가 강제하는 커버리지 — 시퀀스 분할의 무손실성)

- **I-COVER:** 모든 `member_scene_nos`의 합집합 == 그 편의 전체 씬 번호 집합 (누락 씬 0)
- **I-PARTITION:** 한 씬이 두 시퀀스에 중복 소속 금지
- **I-COUNT:** `Σ scene_budget == 씬 총수`
- **I-ACT-COVER:** `act_structure`의 seq_span이 1..nseq 전부 덮음
- **I-SEASON-COVER:** `season_structure`의 episode_span이 전 회차 덮음
- **반-게이밍 다양성:** note/evidence/description 최다반복 텍스트 < 15% (복붙 방지)
- **플레이스홀더 금지:** 미해결 `{변수}` 잔존 시 FAIL

---

## 4. 깊이·밀도 1차 합의안 (정량 하한)

### 4.1 밀도 하한 (게이트 강제)

**시퀀스 밀도 = 시퀀스 수 / 씬 수 ≥ 0.11** (`DENSITY_FLOOR`). 이보다 성기면 FAIL.

파일럿 4편 실측(모두 통과):

| 작품 | 씬 | 시퀀스 | 밀도 |
|---|---|---|---|
| 결혼못하는남자 16화 | 1250 | 189 | 0.151 |
| 101번째프로포즈 15화 | 1125 | 184 | 0.164 |
| 공주가돌아왔다 16화 | 1117 | 160 | 0.143 |
| 시티헌터 20화 | 1356 | 171 | 0.126 |

**권고 작업 밴드: 0.12 ~ 0.17** (하한 0.11은 게이트 바닥, 실작업은 이 밴드를 목표). 씬을 인위적으로 쪼개 밀도를 맞추지 말 것 — 시퀀스는 **goal–obstacle–turn** 단위이지 씬 배수가 아니다.

### 4.2 깊이(필드 채움) 하한

- 서술 필드(`sequence_intent, goal, obstacle, dramatic_question, entry/exit_state` 등)는 **빈 문자열·플레이스홀더 금지**.
- 그래프층 최소 산출: 편당 CharArc/RelArc/Payoff는 **주요 인물·관계·심기(plant) 기준으로 빠짐없이**. 파일럿 실측 규모 참고(시티헌터 20화: edges 518 / chararc 156 / relarc 153 / payoff 140).
- **금지:** 연속형 0–1 자기점수(자기평가 스칼라). 근거 — 5인 전문가 패널 만장일치 기각(AI가 자기 산출에 매기는 0–1은 재현·검증 불가, 편향 실증). 범주형 라벨(enum) 또는 근거 텍스트로만 표현.

---

## 5. 검증 방식 1차 합의안 (단일 합격 기준)

**정본 편입의 유일 기준 = 이중 게이트 ERRORS 0.** 저작 주체의 자기보고("검증 통과했다")는 편입 근거로 **불신**한다. 게이트 통과만이 근거다.

| 게이트 | 대상 | 실행 |
|---|---|---|
| `verify_work_strict.py` | Stage1/2/3 (키셋·자료형·불변식·밀도) | `python3 verify_work_strict.py <work_id>` |
| `verify_new_layers.py` | 그래프층 (엣지·아크·페이오프·다양성·플레이스홀더) | `python3 seqcard_ko/verify_new_layers.py <work_id>` |

두 스크립트를 **GPT 측에도 공유**(허브에 함께 로드)하여, GPT가 산출 직후 **셀프 게이트**를 돌리고 ERRORS 0을 확인한 뒤 넘기면 왕복이 사라진다.

### 5.1 GPT의 4대 검증 장치 — 채택·표준화

GPT가 파일럿에서 붙여온 검증 스캐폴딩은 **스키마 밖**이라 편입에선 제외되지만, **저작 품질 담보 장치로 우수**하다. 아래 4종을 공동 표준으로 채택 권고:

| 장치 | 역할 | 표준화 제안 |
|---|---|---|
| **functional_holdout** | recall@5 기준 vs +그래프 Δ (그래프층의 기능적 가치 측정) | 편입엔 불요하나 **필드 가치 입증**의 핵심 — 유지 |
| **source_lock** | sha256 + 씬 정규화 해시 (원본 위변조 차단) | 공동 채택 — 원본 앵커 무결성 |
| **quarter_audits** | 대형 회차 Q1–Q4 분할 감사 | 20화+ 대작 표준 |
| **lineage/quarantine** | SUPERSEDED 격리 | 재저작·교체 시 표준(시티헌터 교체에 실적용) |

---

## 6. 추가 분석 계층 논의 (2차 이후 — ablation 게이트 전제)

드라마를 더 깊이 데이터화하기 위한 후보 계층. **채택 규율: 어떤 필드도 "있으면 좋다"로 넣지 않는다. Critic ablation(필드 제거 시 렌더/판단 품질 Δ)로 가치가 입증된 것만 승격.** 인간 라벨 순환 없이 기능적으로 게이트한다.

| 후보 계층/필드 | 무엇 | 왜 유력 | 채택 관문 |
|---|---|---|---|
| **관계 엣지 레이어** (ID+label 트리플) | 인물쌍 관계 상태 그래프 | RelArc를 넘어선 명시적 관계 궤적 | ablation Δ≥0.5 |
| **want / need** | 표층 욕망 vs 심층 필요 | 인물 입체성의 표준 축 | 렌더 인물충실 ablation |
| **tension_role** (범주형) | 씬/시퀀스의 긴장 기능 | 긴장 곡선 정량화, 범주형이라 재현가능 | PABAK ≥ 합의선 |
| **continuity_break** | 연속성 단절 플래그 | 편집·설정오류 탐지 | 결정론 파생 가능성 검토 |
| **SceneBlueprint 8 갭 필드** | dramatic_conflict, entry/exit_state, plant/payoff_ops, information_reveal, dialogue_intention, subtext_target | 수직슬라이스 실측서 사실충실 갭과 1:1 대응 | 필드별 ablation 순차 |

**1차에서는 채택하지 않는다.** 위는 GPT와 공동으로 **2차 규격 라운드**에서 하나씩 ablation 검증 후 승격. 지금 확정할 것은 3~5장(현행 스키마)뿐이다.

---

## 7. GPT 준수 체크리스트 (복붙용)

```
[ ] work_id(seqblueprint·episodearc) = "{작품}_{NN}" 형식 (2자리 zero-pad)
[ ] turning_point = {"seq_index": <1..nseq 정수>, "desc": "..."} (문자열 금지)
[ ] value_shift = {"from": "...", "to": "..."} (dict)
[ ] member_scene_nos: scene_span==[min,max], scene_budget==len
[ ] core_mix·label ∈ CORE_ENUM(16), turn_class ∈ 4버킷, edge_type ∈ 4종
[ ] edge_type_guess ∈ {4종 + resolved_here}
[ ] gap_episodes == tgt_ep - src_ep
[ ] 브리지 엣지(gap≠0) → *_cross_episode_edges.jsonl 에만
[ ] local_edges 는 편내(gap=0)만
[ ] edge_id·candidate_id 작품 전역 유일
[ ] I-COVER/PARTITION/COUNT 만족 (씬 누락·중복 0)
[ ] 밀도 0.12~0.17 밴드 (하한 0.11)
[ ] 연속형 0–1 자기점수 금지
[ ] 산출 직후 셀프 이중 게이트 ERRORS 0 확인 후 전달
[ ] by 필드에 출처 각인(모델명) 보존
```

---

## 8. 자기검증 (논리적 약점 점검)

1. **약점: 밀도 밴드 0.12~0.17은 4편 표본.** — 파일럿 4편 실측에 근거하나 표본이 작다. 하한 0.11은 게이트 고정이므로 안전, 상한 권고는 표본 확대 시 재보정 전제로 제시. **완화: "권고 밴드"로 명시, 강제 아님.**
2. **약점: edge work_id 맨키 허용이 규격 이원화.** — seqblueprint는 `{작품}_{NN}` 강제, edge는 맨키 허용이라 혼란 소지. **완화: edge도 `{작품}_{NN}` 권장으로 통일 방향 명시, 단 게이트 미검사라 강제하면 불필요한 마찰.**
3. **약점: 추가 계층을 1차에서 미확정.** — GPT가 "지금 다 정하자"고 기대할 수 있음. **논리: ablation 미검증 필드를 규격에 넣으면 되돌리기 비용이 큼. 1차는 검증된 것만, 2차에서 확장이 오히려 빠른 수렴.**
4. **약점: 셀프 게이트를 GPT에 위임하면 자기보고 불신 원칙과 충돌?** — 아니다. 최종 합격 판정은 **여전히 정본 편입 측(Claude) 게이트가 재실행**한다. GPT 셀프 게이트는 왕복 절감용 사전 필터일 뿐, 편입 근거는 정본 게이트 재통과.

**개선 반영 최종안:** 3~5장을 1차 강제 규격으로 확정, 4.1 밴드는 권고, edge work_id는 권장 통일, 6장은 2차 ablation 라운드로 이월.

---

## 9. 출처

- 정본 게이트 실측: `seqcard_ko/verify_work_strict.py`, `seqcard_ko/verify_new_layers.py` (limsanghyuk/literary-os)
- 파일럿 편입 실측: 결혼못하는남자16·101번째프로포즈15·공주가돌아왔다16·시티헌터20 (2026-07-11, 이중 게이트 ERRORS 0)
- 추가 계층 후보 근거: SeqCard v2 5인 패널 심의(연속 0–1 기각·관계 엣지 레이어·want/need·tension_role·continuity_break), SceneBlueprint 수직슬라이스 실측서(8 갭 필드)
- 검증 장치: GPT 한국드라마04 산출 스캐폴딩(functional_holdout·source_lock·quarter_audits·lineage/quarantine)
