# SeqCard v2 파일럿 결과 보고서 (silver · GPT 교차판정)
_2026-07-02 · 대상: 싸인_03(52씬) + 베토벤바이러스_01(66씬) = 118씬 · 판정자: gpt-4.1-mini(블라인드)_

## 요약(TL;DR)
설계 검증 파일럿 성공. 신규 필드는 **팩트형·취향형으로 명확히 갈라졌고**, 그 갈림이 패널이 사전에 세운 "필드유형 층화 신뢰" 가설과 정확히 일치했다. 즉 교차판정은 **어느 필드가 라벨 가능하고 어느 필드가 재정의 필요한지**를 숫자로 가려냈다. 이것이 이 파일럿의 핵심 소득이다(합의율 자체가 목적이 아님).

## 1. 필드별 일치도 (2편 pooled, n=118)
| 필드 | 유형 | raw | 지표 | 판정 |
|---|---|---|---|---|
| hook_flag | bool | 0.93 | PABAK +0.86 | ★강 — 라벨 가능(팩트형) |
| continuity_break | bool | 0.76 | PABAK +0.53 | 중 — 규칙 조이면 상승 |
| scene_blocks_need | bool | 0.69 | PABAK +0.39 | 약 — 구성개념 모호(재정의 필요) |
| episode_role | 범주8 | 0.54 | κ +0.37 | 약 — 입도 과세분(경계 혼동) |
| tension_role | 범주4 | 0.58 | κ +0.37 | 약 — 기준선 상이 |

작품별: 싸인(수사)은 episode_role 0.44로 더 낮고 취향형 bool은 높음(0.79). 베토벤(군상극)은 episode_role 0.62로 높으나 tension 0.53. → **장르가 필드 난이도를 바꾼다**(수사물=구조 단선이라 오히려 역할 배정 이견↑, 군상극=선명한 막구조).

## 2. 불일치는 랜덤이 아니라 체계적 (=신호)
- **episode_role 혼동 top**: complication→development 11, development→resolution 8. 전부 **인접 범주**. 랜덤 오류가 아니라 8분류가 너무 촘촘해 경계가 겹침. → **5~6분류로 병합**하면 κ 급등 예상.
- **tension_role 혼동 top**: bridge→build 15, peak→build 10. "build"가 흡인 범주. 두 판정자가 긴장 **기준선(baseline)**을 다르게 잡음. → 앵커 정의(예: "직전 대비 상승=build") 필요.
- **scene_blocks_need**: GPT true 62 vs Claude true 30. GPT가 want-need 충돌을 2배 넓게 인정. **구성개념 자체가 판정자마다 다르게 조작화됨** = 이 필드는 현 정의로는 라벨 불가에 가까움. 인간 전문가 사이에서도 갈릴 항목(개발자 지적과 정확히 일치).

## 3. 쟁점 씬 16/118 (13.6%) — 구체 사례
- **베토벤 씬65**(강마에 정체 공개): Claude=resolution/hook=T vs GPT=complication/hook=F. 같은 씬을 "회차 종결의 훅"으로 볼지 "새 갈등 점화"로 볼지 갈림 — **정답 없는 해석 분기**.
- **베토벤 씬8**: Claude=setup/need=F vs GPT=complication/need=T("dramatic crisis"). 위기의 조기 배치를 셋업으로 볼지 이미 복합국면으로 볼지.
- **싸인 씬8**(은폐 멘토와 대면): hook·need·continuity 3필드 동시 갈림. 근거는 둘 다 타당.
→ 쟁점씬은 **버그가 아니라 그 자체가 데이터**: "이 씬은 기능이 중의적"이라는 라벨.

## 4. 판정자 신뢰 층화 (검증된 결론)
- **강 신뢰(팩트체크급)**: hook_flag, 엣지 존재 → 교차판정을 검증 게이트로 써도 됨.
- **약 신뢰(불일치=신호)**: scene_blocks_need, episode_role, tension_role → 합의율로 통과/기각 금지. confidence:uncertain 부착 + 쟁점씬 격리.
- **교차-LLM 일치 = 신뢰도(reliability)일 뿐 타당도(validity) 아님** 재확인. gpt-4.1-mini와 클로드가 공유편향을 가질 수 있으므로 hook_flag 0.93도 "둘 다 같은 실수" 가능성은 남음. → 소수 인간 앵커(~쟁점 16씬)는 여전히 미래 과제.

## 5. 이 파일럿이 실제로 준 것 (개발자 논의용)
1. **스키마 즉시 개정 지시 3건**: (a) episode_role 8→5~6 병합, (b) tension_role 앵커 정의 추가, (c) scene_blocks_need는 현 정의 폐기 또는 want/need를 관찰가능 신호로 재조작화.
2. **자동 게이트 배치안**: hook_flag·엣지=자동 교차검증 통과. 취향 3필드=쟁점씬만 인간(또는 3세션 다수결) 회부 → 인간 검수량을 118씬 전체가 아니라 **16씬으로 압축**(개발자의 "3,500 인시간 비현실" 문제를 실제로 축소하는 경로).
3. **방법 자체 검증**: Sonnet 병렬 저작 → GPT 블라인드 판정 → PABAK/κ 층화 파이프라인이 118씬에서 무결 작동(2편, API 왕복 3회, 총 ~$0.01대).

## 6. 한계·정직성
- n=118, 2편, 판정자 1모델·1회 → **검정력 없음**. 전부 silver. κ 통과 주장 안 함.
- gpt-4.1-mini(속도 제약상 mini 사용) — 본연구는 gpt-4.1/gpt-5급 + 3세션 다수결 권장.
- character_driving_want·broken_thread_id는 자유텍스트라 일치도 미산정(설계상 정성 검토 대상).

## 부록: 산출물
- 라벨: /tmp/pilot/{work}.newfields.jsonl · 엣지: {work}.edges.jsonl · GPT판정: {work}.gptjudge.jsonl
- 설계서: 2026-07-02_SeqCard-v2_pilot-design.md · 패널보고서: 2026-07-02_SeqCard-v2_panel-report.md
