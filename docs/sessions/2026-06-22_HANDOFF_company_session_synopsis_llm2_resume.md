# 2026-06-22 회사 세션 핸드오프 — 인물·사건 생성 로직 실측 + 시놉시스=LLM-2 빈칸 (집 이어작업용)

> 트랙: **메인(LLM-0→3 자율화)**. 제품전략 B(SaaS UI/UX)와 혼합 금지.
> 선행 문서: `2026-06-22_HANDOFF_spe10_v2_graduation_llm2_seed.md`(집→회사 인계, §4 LLM-2 빈칸 지목) ·
> 본 세션 산출 정본: `2026-06-22_character_event_synopsis_llm2_substrate.md`(100줄, 커밋 5c69666).
> 본 문서는 위 둘의 **회사 세션 활동 로그 + 집 재개 매뉴얼**.

---

## 0. 한 줄 요약
드라마 시놉시스(주제·전체스토리·인물관계도·사건관계도·로그라인·회차설계도) 7요소 중 **5개는 이미 결정론(LLM-0) 엔진이 산출**하고, 빈칸은 정확히 **2개 = (①) Synopsis Assembler(흩어진 산출물→읽을 수 있는 기획안 조립·렌더) + (②) 로그라인·주제 역생성**. 이 Assembler가 **LLM-2 메인 거시→미시 계층 플래너의 첫 실체**이자 2단계(작가 수정-전파)의 첫 진입화면. 본 세션은 이를 V794 정적 실측으로 입증하고 허브에 누적했다.

---

## 1. 오늘 한 일 (요청 3건)
1. **"인물 생성/사건 생성 로직이 있는가"** → V794 코드 정적 실측으로 확인. 둘 다 LLM-0 결정론으로 이미 존재.
2. **"드라마 시놉시스를 우리가 구상 가능한가"** → 시놉시스 7요소를 코드 모듈에 매핑. 5개 엔진 보유, 빈칸 2개 확정.
3. **"대화 내용을 LLM-2 기획 일부로 누적하여 허브에 로드"** → 실측 문서 작성·커밋·push 완료.

## 2. 작업 방식 (method)
- **자료원**: `C:\claude\claude\literary-os-v794.zip`를 샌드박스 `/tmp/hub794`에 추출하여 모듈 단위 grep·정독(런타임 실행 아님 = 정적 실측).
- **검증 원칙**: 모듈 *존재*는 파일·클래스·함수 시그니처로 실측. end-to-end *결선*(아크→인물→사건→회차 일괄 흐름)은 **미실측**으로 명시(절대 미선언 준수).
- **사고 절차**: 7요소 분해 → 각 요소를 산출 가능한 엔진과 1:1 대응 → 대응 실패분만 "빈칸"으로 격리 → 3전략(A 통째 LLM / B 덤프 / C 조립+서술만 LLM) 비교 후 C안 채택.

## 3. 실측 결과 (results)
### 3-1. 인물 생성 로직 = 존재 (LLM-0)
- `analyzer/character_birth_gate.py`(V312): 등장 시점 판정. CORE_GATE_KEYS=(act_necessity, pressure_target_defined, unique_residue_defined, **structure_collapse_if_removed**). 임계 LS_SP_MIN=0.45 / LS_RU_MAX=0.75 / LS_ET_BOOST=0.60.
- `analyzer/ledger_builder.py` + `schemas/character_ledger.py`: 인물 원장 8필드(구조화 빌더).
- `analyzer/grid_builder.py` + `pressure_cast_planner.py`: 씬별 fg3/bg/suppressed 배치(foreground=active[:3]).
- `orchestrators/character_intent_agent.py`(V326): IntentPacket(8 IntentActionType), 인물별 비공개·병렬 의도(asyncio.gather), LLM 1/인물.
- `nkg/character_cluster` · `nie/character_influence_matrix`: 관계 그래프.
- **단**: 인물 속성 *자유생성기*는 없음 — ledger/grid는 빈칸을 채우는 구조이고, 채우기 본체는 생성 LLM 몫.

### 3-2. 사건 생성 로직 = 존재 (LLM-0)
- `arc/series_arc_planner.py`(V380): 16부작 4막 기25·승35·전25·결15, S-tension, 감정목표 8패턴. LLM 0회.
- `arc/causal_plot_graph.py`(V380): 인과·복선 엣지 = 사건 관계도.
- `episode/episode_planner.py`(V392): 미시플롯 개수 K = f(9변수) 결정론.
- `episode/episode_structure_calculator.py`(V482): 60분 분단위 씬 슬롯(cold open 2–4분/3막 ~54분/preview 1–2분).
- `physics/conflict_collision.py`(V383): conflict_intensity·collision_pairs·stagnation_warning. `agents/conflict_resolver.py`(V701).

### 3-3. 연결 메커니즘
사건 = 인물 욕망 충돌. IntentPacket 병렬 제출 → ConcurrentActionResolver 충돌 탐지 → ConflictCollisionCalculus 강도 산정 → 미시플롯/씬. (= 사용자가 말한 "주변 인물 먼저 + 거시/미시 플롯" 로직과 대응.)

### 3-4. 시놉시스 7요소 매핑 + 빈칸 2개
| 시놉시스 요소 | 산출 엔진 | 상태 |
|---|---|---|
| 전체 스토리(막 구조) | series_arc_planner | ✅ 엔진 有 |
| 인물 관계도 데이터 | ledger + nkg/character_cluster | ✅ 데이터 有 |
| 사건 관계도 | causal_plot_graph | ✅ 엔진 有 |
| 회차별 미시플롯 | episode_planner | ✅ 엔진 有 |
| 회차 분량 설계도 | episode_structure_calculator | ✅ 엔진 有 |
| **읽을 수 있는 기획안(조립·렌더)** | — | ❌ **빈칸① Synopsis Assembler** |
| **로그라인·주제** | drama_episode_generator의 logline=*입력*(플레이스홀더) | ❌ **빈칸② 역생성** |
- `sdk/sdk_models.py:86 synopsis:str` = pass-through 필드(생성 아님).
- 빈칸① = 데이터가 이미 있어 **GPU 불요·얇은 상층**(아크그래프+원장+인과그래프+회차구조 → 기획안 + 관계도/사건도 렌더). = 선행 핸드오프 §4 StoryBibleAggregator(미구현)의 작가 산출물 형태.
- 빈칸② = 작가가 시드만 줘도 주제·로그라인을 자율 도출하는 부분 부재.

## 4. 권고 (전략 비교 결론)
- **C안 채택**: 구조·인물·사건·회차표 = 결정론 엔진 산출 → Assembler 조립 → 주제문/로그라인/줄거리 산문만 LLM 윤문. ("판단은 로컬, 서술만 LLM" 불변식 준수.)
- A안(LLM 통째)·B안(덤프) 기각/부분. 근거: A안은 공식 floor 무력화(Goodhart), B안은 작가가 못 읽음.

## 5. 산출물·상태
- 정본 문서: `docs/sessions/2026-06-22_character_event_synopsis_llm2_substrate.md` (커밋 5c69666, **원격 main push 완료**).
- 사본: `C:\claude\claude\2026-06-22_character_event_synopsis_llm2_substrate.md` + git 패치 `C:\claude\claude\0001-...Synopsis.patch`.
- 메모리: `project_character_event_synopsis_substrate.md`(push 완료 기록 반영).
- 코드 변경 **없음**(문서·실측만). 게이트/테스트 무변동.

## 6. 집에서 이어서 하는 법 (resume)
1. 허브 최신화: `git clone`(또는 pull) `limsanghyuk/literary-os`, `git log --oneline -3` → HEAD가 **5c69666 이상**인지 확인.
2. 먼저 읽을 것: 본 문서 → `2026-06-22_character_event_synopsis_llm2_substrate.md` → 선행 `2026-06-22_HANDOFF_spe10_v2_graduation_llm2_seed.md` §4.
3. 코드 확인: §3의 모듈 경로를 `literary_system/` 아래에서 직접 열어 시그니처 대조(zip은 `C:\claude\claude\literary-os-v794.zip`).
4. GPU 트랙(SP-E.10 실 누적 5라운드 구동)은 **별개 작업**으로 본 트랙과 혼합 금지.

## 7. 다음 착수점 (next, 집)
1. **Synopsis Assembler 입출력 계약 설계**: 어떤 모듈 출력(series_arc/ledger/causal_plot_graph/episode_*) → 기획안 섹션 어디로 매핑되는지 1:1 표.
2. **관계도/사건도 렌더 스펙**: nkg/causal 그래프 → 작가가 읽는 시각 산출물(노드·엣지 표기 규약).
3. **로그라인·주제 역생성 LLM단 분리**: 시드 → 주제문/로그라인 도출 프롬프트·인터페이스(서술만 LLM, 판단 로컬).
4. **end-to-end 결선 실측**: 아크→인물→사건→회차 1패스 드라이런으로 §3 "엣지 미확인" 해소(선행 핸드오프 §4와 동일 과제).

## 8. 캐비엇 (절대 미선언)
- 모듈 존재 = 실측. **end-to-end 결선은 미실측** — 노드 有, 엣지 미확인(선행 §4와 동일).
- 본 트랙 소속. 제품전략 B와 혼합 금지.
- 코드 미변경이므로 "구현 완료" 아님. 빈칸 2개는 **설계 대상**으로 남아 있음.
