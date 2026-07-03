# 세션 핸드오프 — SceneBlueprint 필드 검증 + 계층 생성 프레이밍 정식화
**날짜:** 2026-07-04 · **허브 HEAD:** e9a8d4e · **모드:** 기획·설계·오케스트레이션(Opus) · **저작:** 별도 Sonnet 멀티에이전트

---

## 0. TL;DR (집/회사 어디서든 여기부터)
1. 오늘 = "SceneBlueprint 필드 하나(renderer_prompt_constraints)를 **기능적 ablation으로 검증**"한 라운드. 결과 = **VALIDATED**(길이 팽창 7.1×→1.13× 붕괴).
2. 개발자 지적으로 **교란변수 분리 완료**: 밀도/길이 WEAK 2.0은 SeqCard 한계가 아니라 *렌더러 프롬프트에 예산·긴장·목적을 안 준 내 누락*이었다. 사실충실 2.0 + S7 환각만 **진짜 스키마 갭**으로 남는다.
3. 오늘 사용자가 확정한 **north-star 계층 프레이밍**을 literary-os 5계층에 정식 매핑(§2). renderer_prompt_constraints의 예산값은 **SequenceBlueprint 층**에 귀속.
4. 다음 라운드 후보 = **사실충실 갭필드 ablation**(dramatic_conflict → plant/payoff → information_reveal), 타깃 = S7형 환각.

---

## 1. 오늘 작업 — 무엇을·어떻게·결과

### 1.1 방법론 피벗 — 기능적 평가 (핵심 통찰)
SceneBlueprint 필드의 가치를 **인간 라벨 일치**로 재지 않는다(작가 희소성 병목). 대신:
> "그 필드를 담은 설계도를 렌더러에 주면, Critic이 *의도 기능을 더 잘 충족한다*고 판정하는 산문이 나오는가?" (필드 ablation)

파이프라인: **SeqCard/SceneBlueprint → 렌더러(GPT-5, 설계도만·원본 미열람) → Critic(Opus, 교차모델=자기평가편향 회피)**.

### 1.2 수직 슬라이스 (허브 9e8584a) — 비밀의숲_01 7씬
| Critic 축 | 점수 | 판정 |
|---|---|---|
| 기능충실(의도 전달) | 4.1/5 | **STRONG** |
| 사실충실(플롯 팩트) | 2.0/5 | WEAK — S7 협박녹음 서브플롯 통째 환각 |
| 밀도·길이 | 2.0/5 | WEAK — 2.7~10.1× 팽창 |

- **intent_gist ablation**: 제거 시 S5 인물이 냉정→인간적으로 표류 → intent_gist는 **load-bearing** 실증.
- **결론(1차)**: SeqCard 의도층은 극적기능·인물심리는 신뢰 전달, 구체 플롯팩트·스테이징·리빌·길이는 미전달(렌더러가 진공을 발명으로 채움).
- **GPT V1700 23필드 ↔ SeqCard 매핑**: 9 존재 / 6 파생 / **8 진짜 갭**(dramatic_conflict·character_entry_state·character_exit_state·plant_operations·payoff_operations·information_reveal·dialogue_intention·subtext_target) + renderer_prompt_constraints.

### 1.3 ablation-2 — renderer_prompt_constraints 검증 (허브 e9a8d4e)
개발자 교란변수 지적("길이 제한·밀도·긴장·씬 목적을 프롬프트에 제대로 줬나?") → 자기감사 **맞음**. baseline 프롬프트는 "원본 1씬 수준(과하게 길지 않게)"뿐 = 수치목표 없음.

**주입한 renderer_prompt_constraints 블록:**
- ① 목표 분량: 원본 char 역산 tgt, 허용 0.8~1.3×, 방영 60분 초과 금지
- ② 긴장 역할(tension): core→긴장 매핑, 과잉 연출 금지
- ③ 지문/대사 배분: 방송대본 지문은 간결·함축, 행동·대사로 드러내기
- ④ 이 한 씬의 목적만 달성(앞뒤 발명 금지)

| 씬 | 팽창(제약 전) | 팽창(제약 후) |
|---|---|---|
| S6 | 10.1× | **0.98×** |
| S4 | 8.4× | **1.08×** |
| S2 | 2.7× | **1.33×** |
| 평균 | **7.1×** | **1.13×** |

방송포맷 완결성 유지(잘림 0). **밀도/길이 WEAK = SeqCard 천장 아니라 필드 부재** → 스키마 보강 필요(필드 추가). 예산값은 **SequenceBlueprint 층 귀속**(아래 §2).

---

## 2. 계층 생성 프레이밍 정식화 (사용자 north-star, 2026-07-04 확정)

### 2.1 사용자 모델
드라마 분석·학습의 목적 = "**왜 이런 구성인가 · 무엇을 말하려는가**"를 이해하고 생성으로 되짚는 것.
- 전체 시놉시스(작품 주제·구성 의도) → 각 회 시놉시스 → 그 시놉시스로 각 회의 **시퀀스/마이크로플롯** → 개별 **씬**을 왜·무엇을·어떻게 구성·생성할지.
- 60분 드라마 = 씬 **60~90개**, 시퀀스 **40~50개**. 시나리오 작성 = **등장인물별 사건·이야기의 배분(비중)을 고려해 어떤 내용을 생성할지 정하는 것.**

### 2.2 literary-os 5계층 매핑
| 계층 | 사용자 표현 | 산출물(현행) | 상태 | 빈칸 |
|---|---|---|---|---|
| **FullSeriesArc** | 전체 시놉시스(왜·무엇) | series_arc.json (30작) | 부분존재(집계값만) | **Synopsis Assembler + 로그라인 역생성**(LLM-2 첫 실체) |
| **EpisodeArc** | 회차 시놉시스 | episode_meta.json(episode_function) | 부분존재(기능라벨) | 회차 시놉시스 서술 필드 |
| **SequenceBlueprint** | 시퀀스/마이크로플롯 40~50 + **인물 사건 배분** + 대사/시간 예산 | — | **미존재(신규 층)** | 전체 신규. **renderer_prompt_constraints 예산 귀속처** |
| **SceneBlueprint** | 씬 60~90 | SeqCard 의도층 + 8 갭필드 | 존재(의도)+검증됨 | 사실충실 갭필드 |
| **RendererPromptPacket** | (씬→산문) | 렌더러 프롬프트 | 검증(intent load-bearing) | — |

### 2.3 카디널리티 실측 대조 + SequenceBlueprint 그레인 결정(ToT)
| 단위 | 사용자 제시 | 코퍼스 실측 | 정합 |
|---|---|---|---|
| 씬/회 | 60~90 | 평균 ~57 (30작/593회/38,046씬) | 일치(실측은 단편 포함 하한) |
| 시퀀스/회 | 40~50 | 장소시퀀스 36.5 / 의미비트 12~15 / 서브플롯 7 | 40~50 ≈ 장소시퀀스 상위 그레인 |

**SequenceBlueprint 그레인 3안:**
- **안A 장소시퀀스(~36.5)**: 장점=결정론 검출 가능(분할기 이미 존재). 단점=사용자 40~50보다 성김, 서사 의미 미포착.
- **안B 의미비트(12~15)**: 사용자 수치와 3배 괴리 → **기각**.
- **안C 사용자 40~50 하이브리드**(장소시퀀스 + 서사 전환 세분): 장점=사용자 워크플로·대사예산 배분 단위와 일치. **채택**.

### 2.4 인물별 사건 배분 = SequenceBlueprint 핵심 연산
사용자의 "인물별 사건·이야기 배분"은 이미 측정한 신호가 입력이 된다:
- **화별 인물 비중**(주연/상대역/주변) — 측정 완료
- **장르 혼합 · 미시플롯 개수** — 측정 완료
- **서브플롯 ~7 · 전환점** — 측정 완료
→ SequenceBlueprint = 이 배분표를 40~50 시퀀스에 할당하고, 각 시퀀스에 **길이/대사 예산**(60분 역산)을 부여하는 층. 이것이 renderer_prompt_constraints가 상속받는 상위값.

---

## 3. 갭 지도 (검증 상태)
| 필드/층 | 검증 상태 | 근거 |
|---|---|---|
| intent_gist | ✅ load-bearing | ablation 제거 시 인물 표류 |
| renderer_prompt_constraints | ✅ VALIDATED | 팽창 7.1×→1.13× |
| dramatic_conflict | ❌ 미검증 | S7 환각 원인 후보 1 |
| plant/payoff_operations | ❌ 미검증 | 후보 2 |
| information_reveal | ❌ 미검증 | 후보 3 |
| Synopsis Assembler(FullSeriesArc) | ❌ 미구현 | LLM-2 거시플래너 빈칸 |
| SequenceBlueprint 층 | ❌ 미구현 | 신규 층, 예산·인물배분 담지 |

---

## 4. 이어작업 체크리스트 (집 또는 회사)
1. `git clone https://github.com/limsanghyuk/literary-os.git` → HEAD e9a8d4e 확인.
2. 오늘 산출: `docs/design/2026-07-03_sceneblueprint_vertical_slice/`(SLICE_RESULTS.md·DESIGN-SCENEBLUEPRINT-SCHEMA-v1.md·render_scene.py·render_constrained.py·render_ablate.py·샘플 txt).
3. 이 핸드오프: `docs/sessions/2026-07-04_session_handoff/`.
4. SeqCard 정본: `db/seqcard_ko/authored/`(30작/593회/38,046씬, validate ERRORS:0).
5. **다음 착수(택1):**
   - (A) 사실충실 갭필드 ablation — dramatic_conflict 단일필드부터, 타깃 S7 환각, 지표=환각률·원본 팩트매치. render_constrained.py를 필드 추가 버전으로 확장.
   - (B) SequenceBlueprint 층 예산 배분 설계 정식화 — 60분→시퀀스 40~50→씬 60~90→대사예산, §2.4 인물배분표 입력.
6. **주의:** 렌더러=GPT-5(설계도만, 원본 미열람), Critic=Opus 교차모델 유지. OpenAI 키·GH 토큰은 사용 후 즉시 삭제. SeqCard 저작은 Sonnet 멀티에이전트(Opus 순차 저작 금지).

---

## 5. 방법론 불변식 (반복 리마인더)
- 필드 가치 = **Critic ablation**으로 측정(인간 라벨 아님).
- fail-fast 필드별 검증. **30작 재저작은 필드가치 입증 전 보류.**
- κ게이트 미착수 유지 = 분석/PoC 위상, prior 주입 보류.
- 트랙 분리: 트랙 A(corpus_ko 본문=LLM-1) ↔ 트랙 B(SeqCard 의도층=LLM-2~3) 혼동 금지.
