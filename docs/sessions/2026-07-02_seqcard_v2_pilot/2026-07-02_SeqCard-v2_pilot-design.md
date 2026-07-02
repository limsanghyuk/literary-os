# SeqCard v2 파일럿 설계 스펙 (silver 모드 · 교차판정)
_2026-07-02 · 대상 2편: 싸인_03(수사·스릴러, 52씬) + 베토벤바이러스_01(음악·군상극, 66씬) = 118씬_

## 0. 이 파일럿의 위상 (명시)
- **목적**: SeqCard v2 신규 필드 스키마와 GPT 교차판정 메커니즘의 **설계 검증(design shakedown)**. 통계적 검정력을 얻는 κ 본연구가 **아님**.
- **라벨 상태**: 전부 **silver**. by=opus_reading. κ 통과 주장 금지. 결론은 "이 필드는 라벨 가능/불가"의 정성 판단까지.
- **표준 저작법**: 신규필드 라벨은 **Sonnet 다중에이전트 병렬**(에피소드당 1에이전트=전체 아크 맥락 보존). Opus 순차 저작 금지.

## 1. 신규 씬 필드 (범주형·불리언 전용 — 연속 0-1 자기점수 없음)
| 필드 | 유형 | 값역 | 판정 기준 |
|---|---|---|---|
| episode_role | 범주(순서형 유사) | opening / setup / development / midpoint / complication / climax / resolution / tag | 회차 아크 내 이 씬의 위치 기능 |
| tension_role | 범주(순서형) | build / peak / release / bridge | 긴장 곡선상 역할. Track A 순수성 훼손 없이 macro 플래너 긴장신호 갈증을 범주로만 충족 |
| hook_flag | bool | true/false | 막·회차 말 관객 견인(클리프행어) 여부 |
| continuity_break | bool | true/false | 앞 씬과의 서사 실 끊김(장소·시점·플롯 점프) |
| broken_thread_id | str\|null | 자유 짧은 id | continuity_break=true일 때 끊긴 실 식별 |
| character_driving_want | str(짧은 범주) | "인물:욕망" 짧은 구 | 이 씬을 미는 인물과 표면 욕망 |
| scene_blocks_need | bool | true/false | 표면 욕망(want)이 진짜 필요(need)와 충돌·차단되는가 |

**연속 점수 전면 배제** (패널 만장일치): core_intensity 등 0-1 자기점수는 예측 κ<0.3~0.4, AI-judge-AI 폐쇄루프 직결.

## 2. 엣지 레이어 (씬 필드 아님 · 별도 레코드)
파일럿 범위=**에피소드 내부 엣지만**(양 끝점이 같은 회차). 교차회차 plant→payoff는 본연구로 이월.
```
{"edge_id","edge_type","src":{work_id,scene_no},"tgt":{...},"label"(16-tax),"gap_episodes":0,"confidence":"high|uncertain","by":"opus_reading"}
```
edge_type ∈ {causal, callback, plant_payoff(내부), subplot_counterpoint}

## 3. 교차판정 프로토콜 (핵심 설계)
1. **블라인드**: GPT-4.1은 클로드 라벨을 **보지 않고** 동일 씬 입력(heading+intent_gist, 필요시 본문)으로 동일 필드를 독립 라벨.
2. **근거 강제**: 필드마다 1줄 근거 요구(사후 감사·쟁점 분석용).
3. **필드유형 층화 신뢰**:
   - 사실/검증형(hook_flag, continuity_break, 엣지 존재) → **강한 신뢰**(팩트체크에 준함).
   - 취향형(tension_role, scene_blocks_need, character_driving_want) → **약한 신뢰**(불일치=신호, confidence:uncertain).
4. **불일치=신호**: 일치율만 보지 않고 불일치 씬을 쟁점(contested)으로 격리→"라벨 불가/재정의 필요" 판별 근거.
5. **지표**: 필드별 raw agreement + 불리언/희귀=PABAK, 순서형(tension_role)=weighted. flat κ≥0.6 단일임계 금지.
6. **한계 명시**: 교차-LLM 일치는 **신뢰도(reliability)**이지 **타당도(validity)** 아님. 공유편향 함정 상존. 소규모 인간 앵커(~50 쟁점씬)는 향후 과제로 열어둠.

## 4. 산출물
- Claude측: /tmp/pilot/{work}.newfields.jsonl
- GPT측: /tmp/pilot/{work}.gptjudge.jsonl
- 분석: 필드별 일치도표 + 쟁점씬 목록 + 라벨가능성 정성판정 → C:\claude 결과 보고서
