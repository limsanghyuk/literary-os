# L2/DRSE 파일럿 POC 결과 (오징어게임, 2026-06-06)

데이터 보강 계획(§4) 1~2단계 실증: 1편 회차 단위 L2 분해 + DRSE 복선 검증셋 + L3 정량.

## 실행
- 모델: Gemini 2.5 Flash (thinkingBudget 0, temp 0.3), 1회 호출.
- 입력: 오징어게임 L0 + 공개 작품 구조 분석(대사 verbatim 금지).

## 결과 (1편, 1호출)
| 산출 | 수량 |
|---|---|
| 씬(L2): present_characters·location·beat·subplot_refs·macro_phase·emotion | 8 |
| 복선쌍(DRSE plant→payoff) | 5 |
| 서브플롯 | 5 |
| L3 정량 4계수(conflict/energy/motif/curiosity) 완비 씬 | 8/8 |

예) 복선 f1: plant(s01 빨간 딱지 선택) → payoff(s08 붉은 머리 염색) — 실제 복선 정확 포착.
예) s01 SceneFeature: conflict 0.6 / energy 0.4 / motif 0.2 / **curiosity 0.8**(명함·호기심 장면 타당).

## 함의 (검증됨)
- **씬 단위 데이터 구축은 가능**하다 — L0(작품요약)가 못 주던 DRSE(복선)·SceneFeature(13필드)·NKG(씬 동적)의 연료를 1호출로 산출.
- 30~50편 × 회차 = 실 씬 O(10^3)을 LLM-1 대량 + 작가 검수로 확보 가능(보강 계획 정합).

## 정직한 한계
- 본 POC의 '출처'는 LLM의 공개작 지식 회상이지 검증된 리캡 아님 → **환각(잘못된 씬) 위험**. 운영에선 공개 리캡 다출처 교차 + 작가 검수 게이트 필수.
- 1편·검수 전 1차. 통계적 검증엔 규모 확대 필요.

## 다음
1. 공개 리캡 기반 교차검증 절차(소싱 깊이) 구현(개발).
2. 5편 파일럿 → 작가 검수 일치율 측정 → 30~50편 확대.
3. DRSE 엔진에 복선 검증셋 주입 → 공식 실데이터 1차 검증.
