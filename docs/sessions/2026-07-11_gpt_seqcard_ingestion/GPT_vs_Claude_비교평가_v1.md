# GPT 분석 산출물 vs 내(Claude) 산출물 — 비교·평가·수정지시·적용안
작성 2026-07-11 · 대상: cityhunter(시티헌터), princess(공주가돌아왔다), p101(101번째프로포즈), kmn(결혼못하는남자)

> 역할: 20년차 드라마 데이터·스키마 감리자 관점. 두 번의 독립 재검증(스키마 불변식 + 원본 참조 존재성)을 거쳐 1차 감사의 오탐 2건을 스스로 정정함.

---

## 0. 먼저 — 1차 감사에서 내가 냈던 오탐 정정 (정직성)
| 1차 감사 주장 | 재검증 결과 | 판정 |
|---|---|---|
| kmn·princess = "다른 드라마 오분석/파일명 불일치" | source_lock·quarter_audits·hwp 파일 전부 work_id와 일치. kmn=결혼못하는남자, princess=공주가돌아왔다. "kmn/princess"는 GPT의 약식 코드일 뿐 | **오탐 — GPT 정상** |
| kmn "댕글링 씬 참조 1건(loc_tgtscene)" | 회차별 씬집합을 정확히 구성해 재검사 → 4작품 전부 댕글링 0. 1차 오탐 원인=브릿지 엣지의 tgt_scene을 잘못된 회차 집합에서 조회 | **오탐 — GPT 정상** |

교훈: 자동 감사 스크립트도 게이트처럼 재검증 대상. 이 정정을 하지 않았으면 GPT에게 틀린 수정지시를 보낼 뻔함.

---

## 1. 비교 평가 (구조·스키마)
GPT의 SceneCard/LocalEdge/CharArc/RelArc/PayoffCandidate **스키마 골격은 내 스키마와 일치**한다. CORE 16 enum 라벨 오류 0, 파싱 오류 0, GPT 자체 검증 `errors: []` PASS.

| 항목 | 내 산출물 | GPT 산출물 | 평가 |
|---|---|---|---|
| SceneCard 필드 | work_id/scene_no/heading/core/core2/intent_gist/skin/by | 동일 | 동등 |
| 로컬엣지 규약 | **회차내 전용(gap=0)**, 회차간은 전부 cross 파일 | 회차내 + **회차말→다음회차 브릿지(gap=1)를 local 파일에 혼재** | **분기(핵심 문제)** |
| work_id (회차파일) | 회차접미사 `공주가돌아왔다_07` | **bare `공주가돌아왔다`** | 분기 |
| cross 채널 | 별도 `_cross_episode_edges.jsonl`(작품당 ~18, Opus fan-in) | 별도 채널 보유(13~55) | 동등(있음) |
| 상위층 스키마 | SequenceBlueprint/EpisodeArc 얇음 | **훨씬 풍부**(§4) | GPT 우위 |
| 근거·검증 부속물 | verify 게이트 1종 | source_lock·quarter_audits·functional_holdout·lineage | GPT 우위 |
| 내용(intent/note) 구체성 | 구체적·원본밀착 | 구체적·원본밀착(예: "도경·찬우 사진이 다음 회차 말 공심에게 발견") | 동등, 환각 징후 없음 |

---

## 2. GPT 방식·내용의 실제 문제점 (근거 포함)
오탐 2건을 걷어낸 뒤 **남는 진짜 문제는 하나의 규약 위반과 그 파생 3건**이다.

### 문제 A (핵심) — "브릿지 엣지를 local_edges에 넣음"
회차 N의 local 파일 끝에 `src_ep=N, tgt_ep=N+1, gap=1, causal` 엣지를 배치.
- 실측 건수: **princess 22, kmn 6, p101 3, cityhunter 0**
- "local(회차내) 엣지가 회차를 넘는다"는 것은 용어상 모순이며, GPT가 이미 별도로 유지하는 cross 채널과 역할이 **중복**된다.
- 내 강한게이트(`verify_new_layers.py`)는 local에 대해 `gap==0 && src_ep==tgt_ep`를 요구 → **이 엣지들 때문에 통째로 REJECT**. 즉 공유 코퍼스/단일 게이트에 병합 불가.

### 문제 B — GPT 내부에서조차 규약이 불일치
- cityhunter(v1): 브릿지 0건 → 안 씀
- v2 리페어 작품들: 브릿지 씀
- p101은 브릿지에 **`lx` 접두 id**(lx012 등)로 구분 표기 / princess·kmn은 일반 `e`-id 재사용 → **한 가지 규칙이 없음**

### 문제 C — 회차파일 work_id가 bare
`공주가돌아왔다`만 기록(회차 접미사 없음). 회차 단위 파일에서 회차 식별을 scene work_id/파일명에 의존하게 되어 병합 시 FK 취약.

### 문제 D — edge_id 포맷 비일관
`e{NN}{iii}`와 `lx{iii}`가 한 작품 내 혼재(p101). id 규칙 단일화 안 됨.

> 내용(사실충실) 측면: 표본 점검상 note·intent_gist는 실제 인물·소품·사건을 지목하며 환각 boilerplate 아님. **내용 문제는 없음**; 문제는 전부 **구조·규약 계층**.

---

## 3. 해결책 + GPT에게 그대로 전달할 수정 지시문
방침(ToT 3안 비교):
1. 브릿지를 local에 유지하되 게이트 완화 → **기각**(local/cross 분리 원칙 붕괴, 코퍼스 오염)
2. 브릿지 삭제 → **기각**(회차말 HOOK 인과는 보존 가치 큼)
3. **브릿지를 cross_episode_edges로 이전 + 규약 단일화 → 채택**(정보 무손실, 게이트 통과, 개념 보존)

**아래 블록을 GPT에게 그대로 붙여넣으면 됨:**
```
[수정 지시] 4개 산출물(시티헌터·공주가돌아왔다·101번째프로포즈·결혼못하는남자) 공통 규약 정정.

1. local_edges 파일에서 src_episode_no != tgt_episode_no 인 엣지를 전부 제거하고,
   동일 내용을 각 작품의 _cross_episode_edges.jsonl 로 이동하라.
   (gap_episodes = tgt_ep - src_ep 재검산, edge_type=causal 유지, note 유지)
2. local_edges 는 반드시 src_episode_no == tgt_episode_no == 해당 회차, gap_episodes == 0 만 남겨라.
3. 이동 후 각 회차 local_edges 의 edge_id 를 e{회차2자리}{일련3자리} 로 001부터 연속 재부여하라.
   lx 접두 id 는 폐기한다. cross 로 옮긴 엣지는 x{일련3자리} 로 재부여하라.
4. 회차 단위 파일(local_edges/payoff/chararc/relarc)의 work_id 를
   "{작품}_{회차2자리}" 접미사 형식으로 통일하라. cross 파일 work_id 는 접미사 없는 "{작품}".
5. 4개 작품 모두 동일 규칙을 적용하라(시티헌터 v1에도 소급). 규약은 작품·버전 불문 단일해야 한다.
6. 정정 후 재검증: local에 gap!=0 이 0건, 모든 씬 참조가 실존, edge_id·work_id 포맷 100% 일치 임을 리포트하라.
```
→ 이 6항이면 내 강한게이트를 그대로 통과하고, 회차말 HOOK 인과도 cross에 보존된다.

---

## 4. GPT에서 참고·적용할 것 (내 파이프라인에 흡수)
사용자 north-star(전체→회차→시퀀스40~50+인물배분+예산→씬)에 **바로 맞는** 자산들:

| 적용 후보 | GPT가 가진 필드/장치 | 내 north-star 귀속 | 우선도 |
|---|---|---|---|
| **SequenceBlueprint 확장** | goal / obstacle / value_shift{from,to} / turn_type / turn_class / pov_char / place_cluster / runtime_share / scene_budget | 시퀀스층 = 목표-장애-전환 + **pov_char=인물배분** + **runtime_share·scene_budget=시간/대사 예산** | ★최상(빈층 정면 충족) |
| **EpisodeArc 확장** | dramatic_question / act_structure[act,seq_span,function] / entry_state / exit_state | EpisodeArc에 막 구획 + 진입/이탈 상태 추가(내 episode_meta보다 두꺼움) | ★상 |
| **functional_holdout** | seed→expected 씬 검색 recall@5 baseline vs graph, Δ=0.5 | 내 "축C 기능 ablation"과 동형 → 그래프층 효용 자동 측정 템플릿 | ★상 |
| **source_lock** | 회차별 원본 바이트 sha256 + 정규화 씬 해시 + 마커 중복/누락/오탈자 기록 | 내 축B(집계정합) 위에 **원본 무결성 앵커** 추가 | 중 |
| **quarter_audits** | 회차를 Q1~Q4로 나눠 부분 감사 | 대용량 회차 저작시 분할검증 | 중 |
| **episode bridge 개념** | 회차말→다음회차 인과 엣지(HOOK 견인) | 내가 κ에서 유일하게 robust로 확인한 회차말 HOOK을 엣지로 명시 → **단, cross 또는 신규 edge_type `episode_bridge`로 올바로 적재** | ★상(개념만 채택) |

즉시 실행 권고: SequenceBlueprint에 `pov_char·scene_budget·runtime_share·goal·obstacle·turn_class` **6필드 증설**이 가장 효율 높은 흡수 지점(시퀀스 예산·인물배분 층의 빈칸을 정확히 메움). functional_holdout은 그래프층 채택 게이트로 재사용.

---

## 5. 자기 점검(논리 약점)
- 브릿지 건수·work_id·id포맷은 4작품 전수 스캔 실측. 내용 환각 여부는 **표본 점검**(전수 아님) → "환각 없음"은 표본 근거의 잠정 결론.
- functional_holdout Δ=0.5는 GPT 자체·비블라인드(자기 라벨) → 효용 수치 그대로 신뢰 말고 **템플릿(방법)만** 차용.
- 적용 필드 증설은 스키마 변경이므로 실제 반영 전 앵커 1작 ablation 게이트로 필드 가치 검증 후 30작 소급(내 기존 원칙 유지).

## 결론
GPT는 **드라마를 잘못 분석하지 않았고 내용도 건전**하다. 실질 결함은 "브릿지 엣지를 local에 혼재 + 규약 비일관" 하나로 수렴하며, §3 지시문 6항으로 무손실 교정 가능하다. 반대로 GPT의 **풍부한 SequenceBlueprint/EpisodeArc 필드와 functional_holdout·source_lock**은 내 빈 상위층을 메우는 데 즉시 흡수 가치가 있다.
