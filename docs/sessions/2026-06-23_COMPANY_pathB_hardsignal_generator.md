# 2026-06-23 (회사·무GPU) — SP-E.10 v3 하드신호 생성기 구현 + v2 포화 포렌식

집 4070이 SP-E.10 졸업 실측을 도는 동안, **회사(GPU 없음)에서 병렬로 가능한 최고 레버리지 작업**을 실행한 기록.
결론: v3 졸업의 *문서상 필수 선결물*인 하드신호 생성기 `gen_pathB_curriculum.py`가 허브·로컬 어디에도 **존재하지 않음을 실측** → 본 세션에서 작성·오프라인 검증 완료.

## 0. 한 줄 요약
SP-E.10 v2 졸업 실패는 **신호가 너무 쉬워서**다(실측: 2R만에 per-token W1=0.976 포화 → 3·5R maintain, 4R rollback → "5연속 adopt" 구조적 불가). v3은 "경로 B 필수"라고만 적혀 있고 **생성기 코드가 없었다**. 회사에서 그 생성기를 만들었다(무GPU, OpenAI). 집에서 데이터 생성→학습만 돌리면 됨.

## 1. v2 포화 실패 포렌식 (round_records_v2.json 실측)
| R | decision | w0 | w1 | w1_ci_lower | KL | 비고 |
|---|----------|------|------|-------------|--------|------|
| 1 | adopt    | 0.508| 0.720| 0.664 | 0.086 | 정상 학습 |
| 2 | adopt    | 0.728| 0.976| 0.957 | 0.403 | **여기서 포화(mastered)** |
| 3 | maintain | 0.984| 0.992| 0.981 | 0.374 | 배울 게 없음 → 스트릭 끊김 |
| 4 | rollback | 0.996| 1.000| 1.000 | **0.863** | KL 폭발(τ=0.50 초과) |
| 5 | maintain | 1.000| 1.000| 1.000 | 0.341 | 천장 |

`graduation_invariant`은 **말미 연속 adopt ≥5 + 윈도 내 rollback=0**을 요구. v2는 adopt가 2개뿐이고 maintain/rollback이 끼어 **졸업 불가**가 구조적으로 확정. 원인은 게이트가 아니라 **신호 난도**: chosen=명작 vs rejected=조잡한 초안의 대비가 너무 커서 8B가 1~2R에 천장 도달.

## 2. Path B 난도 캘리브레이션 (산정 근거)
- 목표: base(미학습) per-token W ≈ **0.55** (천장 0.95에서 멀리), 라운드마다 **조금씩만** 이기게 하여 5연속 진짜 adopt(W1>W0) 유도.
- 수단: rejected를 "조잡한 초안"이 아니라 **"능숙하나 평면적인 tell"**로 — chosen=show와 *같은 솜씨·같은 길이*, 오직 show↔tell 축만 차이 → 마진 축소.
- 커리큘럼: 라운드가 오를수록 rejected 완성도를 올려(gap 축소) 천장 포화를 늦춤. level 매핑 R1=2, R2=3, R3=3, R4=4, R5=5 (held=3 고정).

## 3. 산출물: `gen_pathB_curriculum.py` (무GPU)
위치: `C:\claude\db\4070_oneclick\gen_pathB_curriculum.py` (+ 허브 `tools/loop_c_4070_kit/`).
- 입력: 상황 시드만(코퍼스 원문 미투입=I3 verbatim 0). train↔held **상황 풀 분리**(premise-disjoint=I4).
- 출력 스키마 = 트레이너가 읽는 것과 동일: `{pair_id, work_id, strategy:"pathB", chosen:<show>, rejected:<tell>, level}`.
- 파일: `hardB_held.jsonl`(250) + `hardB_r1..r5_train.jsonl`(각 70).
- 게이트: 길이매칭 |Δlen|/max ≤ 8%(I2·per-token 길이 인공물 차단=I1), show 감정어 누설 시 폐기, 시간예산·재개 지원.
- 검증(무과금 self_test): 스키마·파싱·길이매칭(PASS)·premise-disjoint(OK)·라운드별 level·재개 무중복 **전수 통과**.

## 4. 실행 순서 (집·4070)
1. (이미 됨, 회사) 생성기 작성·검증.
2. (회사 또는 집, 무GPU) `set OPENAI_API_KEY=sk-...` && `python gen_pathB_curriculum.py --held 250 --per_round 70 --out .`
   - 회사에서 실데이터 250+350쌍 생성을 *아직 안 돌림*: OpenAI 키를 env에 주입해야 함(과금). 사용자 승인 후 회사서 생성 가능 → 집은 학습만.
3. (집, 4070) v3 트레이너로 5라운드: 각 라운드 hardB_r{n}_train로 DPO, hardB_held로 per-token W 측정, adopt=`w1>w0 ∧ drift≤0.50 ∧ CI>0.5 ∧ length_rule_rate≤0.60 ∧ c3`. **maintain 없음**(adopt/rollback만).
4. 5연속 adopt → `graduation_invariant graduated=True`. 미달 시 per_round/level/epochs 재조정(캘리브레이션은 실측 의존).

## 5. 캐비엇 (절대 미선언)
- 난도 캘리브레이션이 5R에 걸쳐 W를 완만히 올릴지는 **첫 v3 실측 전까지 미검증**. base W~0.55는 *설계 목표*이지 측정값 아님.
- 본 생성기는 텍스트만 산출. 졸업 성패는 집 GPU 학습 결과로만 판정.
- 형식 졸업이 목적이 아니라 **실질(라운드마다 진짜 계속 배움)** 증명이 목적.
- `train_4070_cumulative_v3.py`(트레이너)는 ADDENDUM에 스펙만 있고 로컬 4070_oneclick에는 v2까지만 존재 → 집에 v3 트레이너 유무 확인 필요. 없으면 v2에서 maintain 분기 제거가 최소 변경.

## 6. 트랙 표시
메인 트랙(LLM-0→3 자율화) 소속. 제품전략 B와 무관.
