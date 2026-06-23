# 2026-06-22 보정(ADDENDUM) — SP-E.10 졸업 v3 (graduation_invariant 실코드 정합)

직전 인계(HANDOFF) 이후 라이브 main(6cb2441)의 `loopc_closure.py` 실독으로 **결정적 교정**.

## 1. 결정적 발견
- `graduation_invariant`은 **말미 '연속 adopt'만** 센다(`decision.lower().startswith("adopt")`). **maintain은 rollback처럼 스트릭을 끊는다.** → v2의 'mastery→maintain'은 졸업을 *구조적으로 불가능*하게 만든 결함.
- 개발자 `CumulativeLoop`는 `decision = "adopt" if gate.passed else "rollback"` — **maintain 자체가 없음.** 의도(line 202) = "adopt → 선호쌍 확대 후 다음 라운드".
- 결론: 졸업 = **maintain 없이, 라운드마다 더 어려운/늘린 쌍으로 5연속 진짜 adopt(W1>W0)**. 경로 B가 **필수**(쉬운 혼합신호는 W=1.0 포화로 5연속 adopt 원천 불가).

## 2. v3 교정 키트 (무GPU 준비 완료, C:\claude\4070_oneclick)
- `train_4070_cumulative_v3.py` — maintain 제거, adopt/rollback만. adopt = `w1>w0 ∧ drift≤0.50 ∧ CI>0.5 ∧ length_rule_rate≤0.60 ∧ c3`. 채택만 어댑터 승격. 끝에 graduation_invariant 인라인 판정. `RUN_CUM_V3.bat`.
- `gen_pathB_curriculum.py` — 하드 신호 생성기(무GPU·OpenAI). chosen=show / rejected='능숙하나 평면적' tell(난도↑, base W~0.55 목표). hardB_held(250)+hardB_r1~5_train(각70). 길이매칭 charΔ≤8%·premise-disjoint·verbatim 미사용.

## 3. 실행 순서
1. **(회사, 무GPU)** `set OPENAI_API_KEY=...` && `python gen_pathB_curriculum.py --held 250 --per_round 70`
2. **(집, 4070)** `RUN_CUM_V3.bat`
3. 5연속 adopt → `graduated=True`. 미달 시 per_round/epochs 난도 재조정, 또는 신호를 **M2 NextEpisodeBench 은닉GT**(개발자 V783 기구축, 가장 강함)로 교체.

## 4. 정직한 캐비엇
난도 캘리브레이션(5R에 걸쳐 W가 천천히 오르게)은 실측 의존. 첫 v3 결과를 보고 조정 필요. 형식 졸업보다 **실질(진짜 계속 배움)** 증명이 목적.
