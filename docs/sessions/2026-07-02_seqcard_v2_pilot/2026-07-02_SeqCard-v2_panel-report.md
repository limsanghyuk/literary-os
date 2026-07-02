# SeqCard v2 확장 심의 보고서 — GPT 12레이어 제안 검토

**작성:** literary-os 기획·심의 모드 (Opus)
**심의:** Sonnet 최고전문가 5인 병렬 패널 + 교차질문
**일자:** 2026-07-02
**대상:** GPT 트랙이 제출한 "12분석레이어(~100필드) 추가 = macro-planner / full-author 프로모션" 제안
**판정 기준:** 클로드 문학창작 모델 관점으로 치환하여, 기존 21작·향후 원본에 적용할 추가 분석항목의 타당성

---

## §0. 심의 개요

개발자 요청은 두 층위다. (1) GPT 제안 내용을 클로드 모델 관점에서 치환 검토, (2) 관련 최고 전문가 에이전트를 총동원하여 비교·교차·논의 후 보고서 작성. 이에 따라 서로 다른 5개 렌즈의 전문가를 병렬 투입하고 상호 교차질문을 부과했다.

| 전문가 | 렌즈 | 핵심 관할 |
|---|---|---|
| Narrative Architect | 거시구조 극작 | 매크로 신호 충분성·인과/복선 계층 |
| Evaluation Scientist | 측정신뢰도 | κ·라벨 타당성·AI-judge-AI 편향 |
| Data & Schema Engineer | 스키마·비용 | 엣지 vs 씬필드·retrofit·throughput |
| Screenwriter + Critic | 현장 크래프트 | 스키마가 살아있는 드라마를 잡는가 |
| Systems Engineer | 아키텍처·범위 | 트랙분리·번들링·시퀀싱 |

심의 대상은 GPT 제안과, 이전에 내가 제시한 하이브리드 C+D 반대안(씬레벨 범주형만 + 별도 관계엣지 레이어 + κ게이트 파일럿 + 생성측 레이어 제외) 양쪽이다.

---

## §1. 만장일치 합의 (5인 전원)

**합의 1 — 연속 0-1 자기점수 전면 기각.**
`core_intensity·causal_strength·agency_level·trust_delta·necessity_score` 및 씬내 tension 파형. 평가과학자는 인간 간 κ를 0.2~0.35로 예측했고, 작가는 "작가는 이것을 수치로 기획하지 않는다", 아키텍트는 "분포가 안정돼 보여도 내적 표류"로 판정했다. 같은 모델 패밀리가 설계·기입·학습하는 폐쇄 루프에서 자기일관성은 지상진실(ground truth)과의 격차를 은폐한다. → **학습 데이터로 사용 금지.**

**합의 2 — 관계 항목은 씬 필드가 아니라 별도 엣지 레이어.**
`causal_edges·plant_payoff_chains·character_arc_turns`는 본질적으로 `(src_scene, tgt_scene, label)` 트리플이다. 씬 레코드에 배열로 인라인하면 (a) sparsity 98%+ null, (b) scene_no 변경 시 양단 쓰기증폭, (c) 16→? taxonomy 진화 시 전 행 스캔, (d) "씬 X에서 파생된 payoff 추적" 쿼리가 full scan. 별도 엣지 테이블이 정규형이다.

**합의 3 — 트랙 경계 강제.**
`L8 tension·L10 craft` = Track A(corpus_ko 산문 임베딩)가 이미 담당. `L11 Retrieval·L12 Gate/Panel/Revision` = 원본 분석이 아니라 **생성 파이프라인 런타임 아티팩트**. 둘 다 SeqCard에 넣으면 의도층이 크래프트 측정값·생성 흔적으로 오염된다. → 별도 저장소로 격리, 스키마 whitelist/deny로 CI 차단.

**합의 4 — κ 게이트는 방향은 옳으나 계수·설계 재작업 필요.**
Cohen's κ 단일·2인·0.6 flat은 부정확. 필드 유형별로 분리해야 한다(§5).

**합의 5 — 두 프로모션 번들 금지, 시퀀스 강제.**
macro-planner(LLM-2)와 full-author(LLM-3)를 단일 스키마 확장으로 묶는 것은 미성숙 결합이다. `10k brief→draft + revision traces`는 분석 과제가 아니라 생성-훈련 코퍼스 → SeqCard 비접촉, `gen_corpus/` 별도 repo.

---

## §2. 핵심 이견과 조정안

패널이 완전히 일치하지 않은 지점은 셋이며, 이것이 이번 심의의 실질 산출이다.

### 이견 A — 매크로 플래너의 "긴장 신호 갈증" (Systems Eng. ↔ Narrative/Screenwriter)

Systems Engineer와 Narrative Architect가 동일 지점을 제기: tension을 전부 Track A(연속·산문 임베딩)에 두면, **SeqCard만 읽는 LLM-2 매크로 플래너는 "어디서 긴장이 터져야 하는가"를 카드에서 읽지 못한다.** 트랙 순수성과 플래너 실효성이 충돌한다.

**조정안(채택):** 연속 수치가 아니라 **범주형 1필드** `tension_role ∈ {build, peak, release, bridge}`를 SeqCard에 편입. 이것은 Track A의 연속 곡선과 다르며(범주형·κ 검증 가능), 플래너에게 회차 호흡 신호를 제공한다. 트랙 분리 원칙은 "연속 측정값 금지"로 재정의하면 위반이 아니다 — Track A는 *측정*(임베딩 기반 연속), SeqCard는 *의도 라벨*(범주)로 역할이 갈린다.

### 이견 B — 스키마가 "살아있는 드라마"를 잡는가 (Screenwriter의 근본 회의)

작가/비평가는 양 스키마 모두 "계기판 수치를 드라마로 착각"하거나 "정밀한 뼈대에 살 붙일 자리가 없다"고 판정하며, 양 제안 모두 놓친 실제 기획 대상 5종을 제시했다. 그중 **욕구-필요 분리(want vs need)**를 "플래너가 죽은 대본을 생산하는 단일 최대 원인"으로 지목했다: 함수를 고르게 배치하면 구조적으로 완전해 보이지만, want/need 충돌이 없으면 인물은 사건의 수신자로 전락하고 관객은 무관심해진다.

**조정안(부분 채택):** 씬당 범주+불리언 2필드 `character_driving_want`(이 씬에서 인물이 얻으려는 것, 범주) + `scene_blocks_need`(bool, 그 행동이 진짜 성장을 막는가)를 **파일럿 대상에 포함**. 단 §5의 라벨러 정보범위 문제(맥락 의존도가 높아 κ 정의가 흔들림)를 파일럿에서 먼저 검증한 뒤 확정.

### 이견 C — κ 게이트의 순환성 (Evaluation Scientist의 최핵심 지적)

가장 날카로운 미해결 지점. 현재 SeqCard 라벨은 `by=opus_reading` **단일 모델 = Silver 라벨**이다. 그 위에 κ 게이트를 돌리면 게이트가 오염 기준으로 자기검증하는 순환이 된다. κ 게이트를 깨려면 **독립 인간 어노테이터**가 필요하고, 이것이 throughput 병목이다(Data Eng. 산정: 70k 레코드 × 2인 × 90초 ≈ **3,500 인시간**).

**조정안:** 두 갈래 중 개발자 결정 필요 — (1) 인간 주석자 조달 경로 확보 후 파일럿 2작(~800씬)에 3인 투입, 또는 (2) 조달 불가 시 라벨을 **명시적 Silver 상태**로 표기하고 "κ 검증됨" 주장을 금지, LLM-1 Critic을 준독립 심판으로 병행하되 그 한계를 문서화. §8 자기점검 참조.

---

## §3. 패널이 새로 발굴한 항목 (양 제안 모두 누락)

교차심의의 가장 값진 산출. GPT안에도 내 C+D안에도 없던 실제 극작 기획 대상.

| # | 항목 | 발굴자 | 형식 | 왜 필요한가 |
|---|---|---|---|---|
| 1 | want vs need | Screenwriter | 범주 + bool | 캐릭터 아크 엔진. 없으면 인물=사건 수신자 |
| 2 | tension_role | Systems Eng. | 범주{build/peak/release/bridge} | 플래너 회차 호흡 신호, Track A 연속곡선 대체 |
| 3 | continuity_break | Narrative Arch. | bool + broken_thread_id | 회수 없이 소멸한 서브플롯·드롭된 로맨스선 표지. 없으면 플래너가 망각한 복선을 무증상 생성 |
| 4 | episode_role | Narrative Arch. | 범주{cold_open/climax/cliffhanger/bridge/standalone} | 회차 레벨 매크로 역할. 한국 2화 분량 구조 정량화 |
| 5 | 정보비대칭(셋업상태) | Screenwriter | 범주/상태 | 극적 아이러니의 발생원. ORACLE/REVELATION은 이벤트일 뿐 격차 상태 없음 |
| 6 | 관계온도(밥상 방향) | Screenwriter | 범주{reset/rise/fall} | 밥상씬 94.2% 출현 이유 = 관계 재보정. 단순 BOND로 뭉개짐 |
| 7 | 서브플롯 카운터포인트 | Screenwriter | 엣지/관계 | A/B/C 플롯 긴장 교차 리듬. 현재 씬을 독립 단위로 봄 |
| 8 | 전회 감정계승 | Screenwriter | 에피소드 경계 필드 | 주간 방영 재착지. 없으면 매 회를 리셋으로 처리 |

1~4는 즉시 파일럿 후보(범주형·κ 검증 가능). 5~8은 정의 난이도가 높아 파일럿 2단계 또는 엣지 레이어로 흡수.

---

## §4. 최종 SeqCard v2 확장안

### 4-1. 씬 레벨 (기존 9필드 + 파일럿 후보만 추가)

기존: `work_id, scene_no, heading, title, intent_gist, core, core2, skin, by`
**추가 파일럿 후보(범주/불리언만, 연속수치 없음):**
`episode_role`, `tension_role`, `hook_flag(bool)`, `continuity_break(bool)+broken_thread_id`, `character_driving_want`, `scene_blocks_need(bool)`

### 4-2. 별도 엣지 레이어 (신규 파일 `edge/*.jsonl`)

```json
{
  "edge_id": "E-도깨비01-0042-0091",
  "edge_type": "plant_payoff",        // causal | plant_payoff | arc_turn | callback | subplot_counterpoint
  "src": {"work_id": "도깨비", "scene_no": 42},
  "tgt": {"work_id": "도깨비", "scene_no": 91},
  "label": "REVERSAL",                 // 16-tax에서만 (FK 제약)
  "gap_episodes": 3,
  "confidence": "high",                // high | uncertain (범주, 연속 아님)
  "by": "opus_reading",
  "tax_version": "16-v1",              // §8 진화 대비
  "created_at": "2026-07-02"
}
```

### 4-3. 스키마 거버넌스 (Track A/B 블리드 차단, CI 강제)

```
seqcard/*.jsonl  허용필드 whitelist:
  [work_id, scene_no, heading, title, intent_gist, core, core2, skin, by,
   episode_role, tension_role, hook_flag, continuity_break, broken_thread_id,
   character_driving_want, scene_blocks_need]
edge/*.jsonl     허용필드 whitelist:
  [edge_id, edge_type, src, tgt, label, gap_episodes, confidence, by, tax_version, created_at]
DENY (validator 즉시 reject):
  tension_*(단 tension_role 제외), craft_*, embed_*, retrieval_*, revision_*,
  *_score(연속 float), *_intensity, *_strength(연속)
```
`validate_seqcard_schema.py`를 CI에 삽입, 허용 외 필드는 커밋 차단.

---

## §5. 신뢰도 재설계 (κ 게이트 v2)

| 필드 유형 | 계수 | 임계값 | 근거 |
|---|---|---|---|
| 명목 다범주(core, skin, want) | Krippendorff α (nominal) | α≥0.65 | k인·결측 처리, 2인 편중 제거 |
| 이진(hook_flag, scene_blocks_need, episode_role 경계) | Cohen κ + PABAK | κ≥0.60 & PABAK≥0.65 | 희귀라벨(HOOK 5~8%) base-rate 과소추정 보정 |
| 순서형(tension_role 도입 시) | Weighted κ (linear) | κ_w≥0.65 | 인접 등급 오류 차등 처벌 |
| 관계 엣지 존재(Y/N) | κ (binary) | κ≥0.60 | 엣지 라벨링(방향·유형)은 별도 α |

**설계:** 파일럿 = 장르 대조 2작(~800씬), **3인 독립 어노테이터**(2인 대비 α 추정 분산 ~30% 감소). 분석 단위 = 씬 1개. 빈도<5% 라벨은 positive 100씬 확보 후 재측정. 판정: 3인 중 2인 = 골드, 전원 불합의 = "contested" 학습 제외.

**AI-judge-AI 드리프트 검출(4단계):** ①인간 앵커 800씬 고정, 매 500씬 α 이탈 ±0.05 초과 알람 ②분기 blind rotation — 제3 인간이 모델/인간 라벨 출처 모르고 판정, "구별불가 60%+"면 경보(과거 안티-LLM 실험 편향 재현 방지) ③구조 불변식 검사(causal_strength↑ ⟹ 인접 core REVERSAL/CONFLICT↑, 위반율 >8% = 자기일관성 붕괴) ④모델 버전 교체 시 앵커 재채점 Δα>0.07이면 롤백.

---

## §6. 페이즈 시퀀스 (전략 선택)

3개 전략을 비교하고 가장 비합리적인 것을 제거한 결과다.

| 전략 | 내용 | 장점 | 단점/리스크 | 판정 |
|---|---|---|---|---|
| S1. GPT 전면 채택 | 12레이어 100필드 즉시 | 최대 표현력 | 연속점수 κ<0.3·트랙오염·순환·비용폭발 | **제거** (측정불가+폐쇄루프) |
| S2. 현행 동결 | 9필드 유지, 확장 안 함 | 무비용·무오염 | 매크로 플래너 신호 부족, 인과/복선 부재 | 제거 (플래너 substrate 미달) |
| S3. 게이트형 점진 확장 | 범주형만+엣지레이어+κ파일럿 후 편입 | 측정가능·트랙보존·시퀀스 | 인간주석 조달 필요·속도 느림 | **채택** |

**S3 채택 이유:** 자율주행 사다리 철학(공식 floor → 외부 측정 검증 → 점진 완화)과 정합. 측정 불가능한 필드를 학습 기반에서 배제해 폐쇄루프 counterfeit를 차단하면서, 매크로 플래너에 필요한 범주 신호와 관계 구조는 확보한다.

**Phase 1 (지금):** 9필드+episode_meta+series_arc 동결. 엣지 레이어(`edge/*.jsonl`) 분리 추가. L8/L10/L11/L12 진입 차단 CI화. 파일럿 2작에 §4-1 추가필드 + §4-2 엣지 시범 라벨링.
**Phase 2 (LLM-2 착수 직전, κ≥임계 인증 후):** 통과 필드만 전 코퍼스 편입. plant_payoff·causal·arc_turn 엣지 확장. macro-planner substrate 완성 선언.
**Phase 3 (LLM-3 준비, LLM-2 실증 후):** 10k brief→draft + revision traces를 `gen_corpus/` 독립 repo 신설(SeqCard 비접촉). full-author 기준은 gen_corpus 품질·Critic 점수로 측정.

---

## §7. GPT 레이어 라우팅 종합표

| GPT Layer | 라우팅 | 근거 |
|---|---|---|
| L1 Scene Identity | SeqCard-Now | 기존 9필드 |
| L2 Intent/Function | SeqCard-Now | intent_gist·core |
| L3 Relational edges | SeqCard-Now (별도 엣지파일) | ID+label 트리플 |
| L4 Plant→Payoff | SeqCard-Later (κ 후) | 파일럿 2작 검증 |
| L5 Character-arc turns | SeqCard-Later | 엣지 레이어 |
| L6 Series/episode arc | SeqCard-Now | 기존 series_arc |
| L7 Causal edges | SeqCard-Later | L4와 동시 파일럿 |
| L8 Tension (연속) | **Track A** | 측정값. 단 범주 tension_role만 SeqCard |
| L9 Promotion metadata | Generation-subsystem | 분석스키마 오염 금지 |
| L10 Craft scores | **Track A** | 공식/Critic 소관 |
| L11 Retrieval index | Generation-subsystem | SeqCard 파생물 |
| L12 Gate/Panel/Revision | Generation-subsystem | 생성-훈련 코퍼스, 별도 repo |
| 연속 자기점수 전반 | **Reject** | κ<0.4·AI-judge-AI |

---

## §8. 자기 점검 (논리적 약점) 및 개선 최종안

**약점 1 — Silver 라벨 순환(미해결).** §2-C의 지적이 이 보고서 전체 결론의 최대 취약점이다. 인간 주석자 조달 없이 κ 게이트를 돌리면 자기검증이다. **개선:** κ 게이트를 "인증"이 아니라 "조달 성공 시에만 유효한 조건부 관문"으로 격하. 조달 실패 시 라벨은 Silver로 명시하고 어떤 프로모션 게이트도 κ근거로 통과 주장 금지. 이 결정은 개발자 몫으로 남긴다(§9).

**약점 2 — tension_role의 트랙 경계 침식 우려.** 범주형이라도 크래프트 신호를 SeqCard에 들이면 경계가 흐려질 수 있다. **개선:** tension_role은 "연출 강도"가 아니라 "플래너용 회차 호흡 역할 라벨"로 정의를 못박고, 연속 tension 곡선은 여전히 Track A 독점. 정의 문서에 이 구분을 성문화.

**약점 3 — 신규 8항목이 파일럿 부하를 키움.** want/need·정보비대칭 등은 맥락 의존적이라 라벨러 정보범위에 따라 κ 정의가 흔들린다(작가·평가과학자 공동 지적). **개선:** 파일럿을 2단계로 — 1단계는 저-맥락 필드(episode_role·tension_role·hook_flag·continuity_break)만, 2단계에서 고-맥락 필드(want/need·정보비대칭)를 라벨러에게 전 회차 맥락 제공 조건으로 별도 측정.

**약점 4 — GPT 제안을 과도하게 기각했을 위험(반대 관점).** GPT의 방향(풍부한 관계·인과 표현) 자체는 매크로 플래너에 정당하다. 내가 기각한 것은 *형식*(연속 자기점수·트랙 혼입)이지 *의도*가 아니다. 실제로 plant_payoff·arc_turn은 전원이 "고전적 실제 크래프트"로 유지 판정했다. → 이 보고서는 GPT 제안의 60~70%를 형식 변환하여 수용하며, 전면 거부가 아님을 명확히 한다.

---

## §9. 개발자 결정 요청 항목

1. **인간 어노테이터 조달** — 파일럿 2작 3인 독립 주석(≈800씬) 경로가 있는가? 없으면 라벨을 Silver로 명시하고 κ 검증 주장을 포기하는 데 동의하는가?
2. **파일럿 착수 승인** — 장르 대조 2작 선정. §4-1 신규 필드 + §4-2 엣지 레이어 시범 라벨링. (표준 방식 = Sonnet ~8 멀티에이전트 병렬)
3. **신규 필드 편입 범위** — tension_role·want/need를 파일럿에 포함할지, 저-맥락 4필드만 1단계로 할지.
4. **엣지 레이어 물리 설계** — 별도 `edge/*.jsonl` + tax_version 관리 방식 승인.
5. **생성측 격리** — L11/L12 및 10k pair를 `gen_corpus/` 별도 repo로 분리하는 데 동의하는가?

---

## 부록 — 패널 원문 교차질문 요지

- Narrative→Eval: 장거리(gap≥5화) plant를 인간 2인이 독립 특정 가능한가? 단편/장편 케이스 혼합평균 금지.
- Eval→Narrative: 28,836씬 core 분포가 실제로 장르·성공도 구별 클러스터를 형성하는가? 아니면 SeqCard 전체가 장식 레이어인가?
- Eval→Data: silver 라벨 위 κ의 순환을 깰 독립 인간판단 조달 경로가 있는가?
- Data→Systems: 16-tax 진화 시 committed 엣지 label 버전관리(tax_version vs immutable versioned table)?
- Screenwriter→Eval: want/need·서브텍스트 라벨러에게 씬만 주는가 전 회차 맥락을 주는가? 맥락의존도가 κ 정의를 흔든다.
- Systems→Screenwriter: 의도층에 크래프트 신호 0이어도 매크로 플랜 장르리듬 명세 가능한가? → 조정안 tension_role로 수렴.
