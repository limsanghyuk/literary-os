# 생성 본체 통합 설계 — 16부작 자율 생성 연결 (SeriesComposer) + 회사→집 핸드오프 (2026-06-18)

**문서 ID**: LOS-GEN-INTEGRATION-L4-V1-2026-06-18 · **제안 ADR**: ADR-244 (연결 오케스트레이터)
**성격**: 기획안 보강 — "작가처럼 16화를 설계·구성하는" 로직의 **현 상태 진단 + 미연결 빈칸의 통합 설계**.
**기준 허브**: HEAD `8960b1b` (V786 계열). **원칙**: 설계만(코드 구현은 개발자 트랙), verbatim 금지.

---

## 1. 현 상태 진단 (코드 실측, 추정 아님)

"우리 모델이 인간 작가처럼 16화를 설계·구성하는 로직이 있는가"에 대한 실측 답: **설계 두뇌는 코드로 존재하나, 16화를 끝까지 써내는 통합 작가는 아직 미연결.**

### 1-1. 이미 존재하는 성숙 부품 (LLM-0 결정론)
| 부품 | 위치/버전 | 역할 = 작가의 무엇 | 입출력 |
|---|---|---|---|
| **SeriesArcPlanner** | `arc/series_arc_planner.py` V380 | 쇼러너의 **작품 바이블**: 16부작 전체 아크 | premise → `CausalPlotGraph`(ArcPlotNode/Edge). 4막(기25·승35·전25·결15)·S텐션곡선·회차감정(1화 기대감…8화 충격·10화 절망…)·복선예산·ep_n→ep_n+1 인과 |
| **EpisodePlanner** | `episode/episode_planner.py` V392 | **회차 구성**: 각 화를 미시플롯 몇 개로 | arc_node+state → `EpisodePlan`(K=9변수 결정함수·씬예산·감정/갈등목표·slot_functions) → `EpisodeState`(MicroPlotSlot[]) |
| **episode_state** | `episode/episode_state.py` | 회차 상태·이월 | `NarrativeStateTensor`·`ActPosition`·`SeriesConfig`·`MicroPlotSlot` |
| **PassPipeline** | `generation/pass_pipeline.py` V781 | **씬 집필 본체** | premise→Pass1 WorkSpec→Pass2 Beat[]→Pass3 SceneBrief[]→Pass4 RAG→Pass5 생성→Pass6 게이트→Pass7 패널. 훅: retrieve/generate/judge |

### 1-2. 빈칸 3가지 (정직)
1. **층간 미연결**: `SeriesArcPlanner`↔`EpisodePlanner`를 함께 쓰는 파일 0, "16화 전체 생성 진입점" 0. 아크 설계기와 씬 생성기가 **따로** 성숙. PassPipeline은 기본 n_episodes=1 단일 덩어리로만 동작(Pass2가 자체 flat ARC 생성, arc/episode plan 미사용).
2. **Pass5 생성기 = 기본 stub**: 주석 그대로 "loop-C로 학습되는 생성기가 꽂히는 자리". 실 생성기 미학습(명작 대비 46%).
3. **수정 전파 엔진 부재**: 작가가 노드 수정 시 뒷이야기 일관 재창작(human-in-the-loop) = 제품 비전 핵심 빈칸.

→ **비유**: 기획 노트·구조 설계 두뇌=완성 / 명문장 쓰는 손=견습(46%) / 전체를 끝까지 잇는 작업흐름·수정반영=미완.

---

## 2. 통합 설계 — `SeriesComposer` (연결 오케스트레이터)

### 2-1. 전략 비교 (3안)
| 안 | 방식 | 장점 | 단점·리스크 |
|---|---|---|---|
| **A. 얇은 어댑터(SeriesComposer)** ★권고 | 신규 오케스트레이터가 기존 부품을 호출·연결. 기존 클래스 미변경 | 저위험·성숙코드 재사용·빠름·LLM-0 결정성 보존 | 브리지(MicroPlotSlot→Beat) 신규 표면 정확도 |
| B. PassPipeline을 episode-aware로 개조 | Pass2가 EpisodeState 소비 | 단일 파이프라인 깔끔 | V781 성숙코드 침습·회귀위험·단일작 모드 파손 |
| ~~C. 통합 전면 재작성~~ | 둘 대체 신모듈 | 개념상 최정합 | 성숙·테스트된 arc/episode 폐기·과대비용 → 제거 |

**채택 = A**. 이유: arc/episode 플래너(결정론·성숙)와 V781 pass body를 그대로 살리고, 신규 로직(브리지·상태이월·복선원장·수정전파)만 단일 신모듈로 격리 → 최저 회귀위험·최단 경로.

### 2-2. SeriesComposer 파이프라인 (의사코드)
```
def compose_series(premise) -> SeriesResult:
    # ① 작품 바이블: 16부작 아크
    arc = SeriesArcPlanner().plan(premise)          # CausalPlotGraph (16 ArcPlotNode)
    state = NarrativeStateTensor.initial(premise)    # 지식상태·열린실타래·텐션모멘텀
    ledger = ForeshadowLedger(arc)                   # 복선 예산·심기/회수 원장(작품 전역)
    episodes = []
    for e in arc.episodes:                            # 1..16 순방향
        # ② 회차 구성: 미시플롯 K·씬예산
        ep_plan  = EpisodePlanner().plan(e, state)    # EpisodePlan → EpisodeState
        ep_state = ep_plan.to_episode_state()
        scenes = []
        for slot in ep_state.microplot_slots:
            # ③ ★브리지(신규): MicroPlotSlot → Beat[] → SceneBrief[]
            beats  = slot_to_beats(slot, e, ledger)   # 감정/갈등목표·복선예산→인과비트
            briefs = PassPipeline().pass3_scene_brief(work_spec(e), beats)
            # ④ 씬 집필 본체(V781 그대로)
            pp = PassPipeline()
            pp.pass4_rag(briefs, retrieve=corpus_ko_rag)
            pp.pass5_draft(briefs, generate=loopC_model)   # 미학습시 stub
            issues = pp.pass6_gate(briefs)
            pp.pass7_panel(briefs, judge=critic_panel, references=ledger.refs(slot))
            scenes += briefs
        # ⑤ 상태 이월(회차간 일관): 심은/회수 모티프·지식상태·텐션 끝점
        state = state.advance(scenes, ledger)
        episodes.append(EpisodeOutput(e, scenes, issues))
    # ⑥ 작품 전역 일관 검사
    consistency = CrossEpisodeCheck(episodes, nkg=NKG, ledger=ledger)  # 복선 전수회수·캐릭터 연속·텐션곡선 적합
    return SeriesResult(arc, episodes, consistency)
```

### 2-3. ★핵심 신규 계약 3가지 (개발자 구현 대상)
1. **`slot_to_beats(slot, ep_idx, ledger)`** — 브리지. `MicroPlotSlot`(act_function·emotional_target·conflict_weight·reveal_budget) + 복선원장 → `Beat[]`(intent·plant/payoff_motifs·target_tension). = 현 PassPipeline.pass2_causality의 flat 버전을 **아크/회차 구동**으로 교체.
2. **`ForeshadowLedger`** — 작품 전역 복선 예산·심기/회수 추적. SeriesArcPlanner의 회차별 복선예산 + Beat의 plant/payoff_motifs 연동. **불변식: 심은 모든 모티프는 예산된 회차 내 회수**(Pass6/CrossEpisodeCheck 게이트).
3. **`NarrativeStateTensor.advance()`** — 회차 출력 후 지식상태·열린 실타래·텐션 모멘텀 갱신 → 다음 회차 입력(회차간 인과·일관의 운반체). 부품은 episode_state에 이미 존재 → advance 로직만 신규.

### 2-4. 수정 전파 훅 (빈칸 #3, 동일 골격에 얹음)
```
def propagate_edit(series, edited_node):
    affected = arc.downstream_from(edited_node)       # ep_n→ep_n+1 인과로 영향 회차 산출
    state = series.state_before(affected[0])          # 수정 지점 직전 상태로 롤백
    recompose(series, from_episode=affected[0], state) # ②~⑤만 재실행(앞부분 보존)
```
= compose_series의 **부분 재실행**. 작가가 노드 수정 → 영향 하류만 일관 재창작(human-in-the-loop). 전량 재생성 아님(비용·보존).

---

## 3. 게이트·검증 결합 (기존 자산 재사용)
- **Pass6 구조게이트**(LLM-0): 씬별 초안·등장인물·콜백 회수.
- **CrossEpisodeCheck**(신규, 공식): ① 복선 전수회수(ledger) ② 캐릭터 연속성(NKG) ③ 회차별 텐션 = SeriesArcPlanner T_ideal 곡선 적합 ④ 감정목표 일치.
- **Pass7 패널 → loop-C 선호쌍**: 생성↔학습 연결(이미 `to_preference_pairs`). 통합 후 **회차·작품 단위 승률**(NextEpisodeBench)로 확장.

---

## 4. 회사 → 집 이어가기 핸드오프

### 4-1. 지금까지 (회사, 완료)
- corpus_ko **2,030작품**·209,144청크·무결성 입증(고아청크 0·3중 씬 일치)·실측 3종(생성 46%·검색 99.5%·장르변별 ✓). durable: scenes/·emb_cache/(1,075 shard)·features/·nkg.json (FUSE).
- 본 통합 설계(SeriesComposer) 작성·허브 push.

### 4-2. 집에서 (다음, 순서)
| # | 작업 | 위치 | 비고 |
|---|---|---|---|
| 1 | corpus_ko 재동기화 | Drive zip → 로컬 | **교정본 확인**(인코딩 stale 주의). ChromaDB·features.db 로컬 재빌드(`store_chroma.py`+`features.py`, 무API) |
| 2 | SeriesComposer 스켈레톤 | `literary_system/orchestrators/series_composer.py`(신규) | §2-2 의사코드. 브리지·ledger·advance 스텁부터 |
| 3 | 브리지 `slot_to_beats` 구현 | 同 | §2-3 #1. 최소 동작(감정/갈등목표→intent·tension) |
| 4 | 1회차 E2E 드라이런 | 로컬 | premise→arc→ep1→씬브리프→Pass4 RAG(corpus_ko)→Pass5 stub→Pass6. 연결 확인(생성품질 무관) |
| 5 | Pass5에 생성기 연결 | 同 | OpenAI(즉시) 또는 loop-C 학습모델(GPU 후). 키 재주입 |
| 6 | CrossEpisodeCheck + ForeshadowLedger | 同 | 복선 전수회수·텐션곡선 적합 게이트 |

### 4-3. 집 환경 주의 (메모리 기준)
- **FUSE는 sqlite/ChromaDB 쓰기 불가** → 로컬 디스크에 재빌드. emb_cache·scenes·nkg.json은 durable.
- 키(OpenAI/GH/RunPod)는 env·시크릿만, 코드·허브 커밋 금지.
- 허브엔 집계·수치만(verbatim·dpo_pairs 로컬 전용).

---

## 5. 자기 점검 (논리 약점)
- 본 설계는 **연결**에 집중 — 생성 *품질*(46%→상향)은 별개 트랙(loop-C 학습). 연결돼도 Pass5 미학습이면 16화는 "구조는 작가급·문장은 견습" 상태(정상 중간 단계).
- 브리지 `slot_to_beats`가 신규 정확도 표면 — 명작 회차 구조로 역검증(NextEpisodeBench) 필요.
- 수정 전파의 "영향 하류 산출"은 인과그래프 정확도에 의존 — NKG·arc edge 품질이 전제.

## 6. 한 줄
부품(16부작 아크 설계기·회차 플래너·7-pass 씬 본체)은 다 있으나 **미연결**. `SeriesComposer`(얇은 어댑터)로 아크→회차→씬을 잇고, 브리지·복선원장·상태이월·수정전파만 신규 구현하면 "작가처럼 16화를 설계·구성·집필"이 폐회로가 된다. 집에서 스켈레톤 → 1회차 드라이런부터 이어간다.
