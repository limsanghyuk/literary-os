# Stage3~6 쌍대 임계 개정안 v1.0 — 검증 후반부 쌍대 전환 + B_NTC2 실측 정정 + soft formula 갱신 (2026-06-12)

**기준선**: HEAD `1dcbe0c` (V749 v13.3.0, WP-0·1·4b 완료) · **작성**: 본 모드(기획) · **집행 대상**: 저연산(Sonnet) 개발 모드
**선행 정본**: unified_priority_map(06-11) · pairwise_redesign_proposal(06-11, D-PW1~3) · P1-P5 보강 §4(06-10, Stage3~6 사전등록표) · EFG 보강 §2·§5-2(06-10) · realdrama_sg_ep9(06-12, SG-2 FAIL)
**문서 성격**: 제안서+집행 명세. 본 문서가 unified_priority_map §3 [본 모드 트랙] ⅰ번("Stage3~6 쌍대 임계 개정")의 산출물이다.

═══════════════════════════════════════════
## §0. 요약 + 결정 요청 3건
═══════════════════════════════════════════
검증주간 실측(쌍대 45/49=91.8% vs 절대 채점 전면 FAIL)과 G_NO_ABSOLUTE_REWARD(V748) 제정에 따라, 아직 실행되지 않은 Stage3~6의 사전등록 임계를 쌍대 기준으로 개정한다. 아울러 공식 정본 문서가 '미수정'으로 기재한 B_NTC2가 실코드에서 이미 수정되어 있음을 실측 확인했고(잔여 결함 3건은 별도), soft formula(§5-2) 과제는 쌍대 전환으로 필요성이 축소되어 조건부로 강등한다.

| ID | 결정 요청 | 근거 |
|---|---|---|
| **D-SR1** | stage_registry STAGE_THRESHOLDS v2 채택(§2·§3) — 품질성 지표는 쌍대 승률 1차, 절대 상관은 BT 호환 2차로 강등. 매체(prose/screenplay) 분기 필드 신설 | 실측 45/49 + SG-2 포맷 전이 |
| **D-SR2** | B_NTC2 잔여 결함 3건을 초소형 WP-NTC로 편입(§4) | HEAD 실코드 실측 |
| **D-SR3** | soft formula(미분가능 근사)를 'F 착수 의무'에서 'PPO 채택 시 조건부 연구'로 강등(§5) | DPO는 선호쌍만 요구 — 근사기 불요 |

═══════════════════════════════════════════
## §1. 개정의 적법성 (사전등록 규약 위반 아님)
═══════════════════════════════════════════
P1-P5 보강 §4 공통 규약은 "사후 임계 조정 금지 + 변경은 별도 커밋·사유 의무"다. Stage3~6은 **아직 1회도 실행되지 않았다**(가동 조건: Gold 전사·패널·Mode 1 — 모두 미충족 또는 부분 충족). 따라서 본 개정은 결과를 본 뒤의 사후 조정이 아니라 **실행 전 사전등록의 개정**이며, 사유(절대 채점 무효 실측 6건 + ADR-211 G_NO_ABSOLUTE_REWARD)와 함께 본 문서·본 커밋으로 기록함으로써 규약을 준수한다. Stage1~2는 이미 실행·통과(쌍대 27/29 포함)했으므로 **소급 개정하지 않는다**.

**전환 원칙 (어디까지 쌍대화하나)**: 절대 채점 금지의 정확한 범위는 "품질 스칼라를 LLM/패널에게 직접 묻는 것"이다.
- **쌍대 전환 대상**: 품질·선호·우열 판정 (necessity 비교, simulator 정합, 블라인드 선호).
- **유지 대상**: 이진 사실 GT(복선이 실제 회수되었나 → F1), 결정론 형상 비교(곡선 vs 라벨 DTW), 셔플 대비 백분위(SG-4 방식). 이들은 절대 '채점'이 아니라 사실 대조다.

═══════════════════════════════════════════
## §2. Stage3~6 개정 표 (사전등록 v2)
═══════════════════════════════════════════
| Stage | 기존 임계(v1, V747 등록) | 개정 임계(v2) | 변경 성격 |
|---|---|---|---|
| **3** Longform | payoff_debt F1≥0.6 / necessity AUC≥0.7 | payoff_debt **F1≥0.6 유지**(사실 GT) / necessity는 쌍대 전환: 다중에이전트가 "씬 제거 시 더 붕괴되는 쪽" 강제선택, 공식 necessity 순위와 일치 **승률≥0.65** (N≥30쌍, 양방향 판정) | 부분 전환 |
| **4** Trajectory·ReaderSim | simulator vs 패널 중앙값 ρ≥0.4 | 패널에 점수 대신 **양자택일**("두 씬 중 다음이 더 궁금한 쪽") — simulator 순위와 일치 **승률≥0.65** (N≥30쌍, judge_id·position_seed 의무, cost_cap 사전 계산) | 전면 전환 |
| **5** NIE·tension·CIM | DTW 백분위≤30% / CIM 방향 일치≥70% | **유지**(결정론 형상·방향 대조 — 절대 채점 아님) + 보조 추가: 원순서 vs 셔플 인접 일관성 백분위≥95 (SG-4 실증 방식의 정식화) | 유지+보강 |
| **6** Prose·종합 | 종합점수가 블라인드 선호 ρ≥0.5 예측 | Mode 1 블라인드 **쌍대**: 공식 Δ점수 방향이 다중에이전트 선호 방향과 일치 **승률≥0.70** (N≥30쌍). **문체 축은 선호 질문 금지** — trait/canon_proximity 모드만(D-PW3 준수), 인간 GT는 박빙 쌍에만 | 전면 전환 |

**공통 신설 2건**:
1. **medium 필드**: 각 Stage 등록에 `medium: prose | screenplay` 분기. SG-2(각본 14/20 FAIL)가 실증한 포맷 전이 — 임계는 매체별 독립 등록, screenplay 측 fitness는 생애주기 `recalibrate` 상태로 시작(formula_ledger 기록).
2. **임계 수치의 근거**: 승률 0.65/0.70은 실측 91.8%(명작 vs 강열화 = 난이도 L1)에서 보수 하향한 값 — Stage3·4·6은 L2~L4 난이도(박빙·생성물 포함)이므로 L1 수치를 그대로 요구하면 과잉. 난이도 사다리(쌍대 제안서 §7)와 정합.

═══════════════════════════════════════════
## §3. stage_registry v2 집행 명세 (WP-1b, 소규모)
═══════════════════════════════════════════
`literary_system/validation/stage_registry.py`:
```python
PREREG_VERSION = 2   # v1→v2 사유: 본 문서 + ADR-211. v1 dict는 _STAGE_THRESHOLDS_V1로 보존(이력)
STAGE_THRESHOLDS = {
    3: dict(gt="payoff_actual",  metric="f1",               tau=0.60, min_works=1, medium="prose"),
    3.5: dict(gt="necessity_pair", metric="pairwise_winrate", tau=0.65, min_n=30, medium="prose"),
    4: dict(gt="panel_pair",     metric="pairwise_winrate", tau=0.65, min_n=30, medium="prose"),
    5: dict(gt="labeled_curves", metric="dtw_pct",          tau=0.30, min_works=2, medium="prose"),
    5.5: dict(gt="shuffle_seq",  metric="percentile",       tau=0.95, min_works=1, medium="any"),
    6: dict(gt="blind_pair",     metric="pairwise_winrate", tau=0.70, min_n=30, medium="prose"),
}
# screenplay 분기는 SG 데이터 누적 후 별도 행 등록(현재 fitness=recalibrate 상태만 ledger 기록)
```
- `pairwise_winrate` 측정은 기존 `pairwise.py`(V748)의 `compare/tournament/bt_scores` 재사용 — **신규 판정 코드 금지**.
- 불변성 테스트 갱신: `test_preregistered_tau_immutable_in_code`는 PREREG_VERSION 단위로 동결 — v2 등록 후 수치 변경은 v3 선언+사유 커밋 없이는 FAIL.
- DoD: 갱신 TC 6 green (`test_prereg_v2_loaded` · `test_v1_preserved_readonly` · `test_pairwise_metric_routes_to_pairwise_module` · `test_medium_field_required` · `test_winrate_threshold_check` · `test_version_bump_required_for_change`) + ledger에 prereg v2 이벤트 1건.

═══════════════════════════════════════════
## §4. B_NTC2 실측 정정 — "미수정"은 더 이상 사실이 아님 (WP-NTC, 초소형)
═══════════════════════════════════════════
**실측(HEAD 1dcbe0c, `literary_system/nie/narrative_tension_curve.py`)**: L161~162에 `[B2-FIX] ADR-020 준수: l_final = λ·l_tension + (1-λ)·l_coverage` — 공식 정본 문서(V571 Master Reference·V620 진화판)가 '주요 미수정 버그'로 기재한 λ계수 반전은 **이미 수정되어 있다**. 단 잔여 결함 3건:

| # | 결함 | 수정 |
|---|---|---|
| 1 | **λ 의미론 3중 불일치**: 모듈 docstring(L8)·메서드 주석(L153)은 `L_final = L_tension + λ·L_coverage`(제3형태), 상수 주석(L25)은 "λ=L_coverage 가중치", 실코드는 λ가 **tension** 가중치 | ADR 1건으로 정본 확정(권고: 코드 현행 = λ·L_tension+(1-λ)·L_coverage, λ=0.30) + docstring·주석 3곳 정합 + 공식 문서 erratum을 formula_ledger에 기록 |
| 2 | `update_lambda` 클램프 `[0, 2.0]` — λ>1이면 가중합 의미 파탄(음수 가중 발생) | `[0, 1]`로 축소 + 경계 TC |
| 3 | Gate25 임계 0.15는 반전 수정 **이전** 분포에서 보정된 값일 가능성 | 회귀 픽스처로 현행 가중에서 L_final 분포 재확인 — 임계 변경이 필요하면 별도 사유 커밋(사전등록 규약 동일 적용) |

DoD: TC 3 + ADR 1 + ledger erratum 1. MetaLearner(V515+)가 λ를 학습 대상으로 삼으므로 결함 2는 학습 발산 방지 차원에서 실익이 있다.

═══════════════════════════════════════════
## §5. soft formula(§5-2) 갱신 — 쌍대 전환의 파급
═══════════════════════════════════════════
EFG 보강 §5-2는 "R2 보상이 비미분 → fitness 신경망 근사기(soft formula)를 Phase F에서 착수"로 등록되어 있다. 쌍대 전환이 이 전제를 바꾼다:
- **DPO 경로(현 정본, EFG §4 패치 채택)**: 선호쌍 (chosen, rejected)만 요구 — 보상모델·미분가능 근사 **모두 불요**. 공식의 역할은 선호쌍 생성기(Δfitness 방향 + 쌍대 판정)로 충분하다.
- **PPO 경로(예비)**: 보상 스칼라가 필요하나 BT 잠재 점수(`bt_scores`)가 이미 스칼라 — 근사기 없이 주입 가능. dense gradient가 정말 필요한 경우에만 soft formula가 유효하다.
- **개정**: §5-2를 "Phase F 착수"에서 **"PPO 채택이 결정된 경우에 한해 착수하는 조건부 연구"로 강등**. '그림자 원칙'(원 공식 상시 감사)은 유지. EFG 보강 §2 LLM-1.5 행의 "미분가능 근사 착수" 문구는 본 조항으로 대체된다.
- 부수 효과: F 단계 연구 부담 1건 제거 — 절감분은 F.4b(언어 불변성 검증)로 재배정 권고.

═══════════════════════════════════════════
## §6. 실행 계획 (WP 큐 반영)
═══════════════════════════════════════════
| WP | 내용 | 규모 | 선행 | 버전 후보 |
|---|---|---|---|---|
| WP-1b | stage_registry v2 (§3) | 소 | 없음(데이터 불요) | V750 |
| WP-NTC | B_NTC2 잔여 3건 (§4) | 초소 | 없음 | V750 동반 가능 |
- 기존 큐(WP-2 트라이스토어 → WP-3 EmbeddingProvider → WP-4 refcheck)는 변동 없음 — WP-1b·NTC는 독립이라 선행 삽입해도 충돌 없음.
- RULE-0 준수: 각 WP 착수 전 `tools/run_preflight.py` PASS 의무.
- 개발자 트랙 불변: 전자책 전사(문체 축) + Pachinko FYC 추가 입수(구조 축)가 Stage3·5·6 가동 조건의 관문.

═══════════════════════════════════════════
## §7. 자기 점검 (논리 약점 사전 공개)
═══════════════════════════════════════════
1. 승률 임계 0.65/0.70은 보수 하향이지만 **여전히 추정** — 난이도 L2~L4 실측이 누적되면 v3 개정 사유가 될 수 있다(사전등록 규약대로 별도 커밋).
2. Stage4 패널 쌍대는 LLM 다회 호출 — cost_cap 사전 계산 의무(P1-P5 §7-7)를 v2 등록에 그대로 승계한다.
3. §4의 B_NTC2 실측은 소스 1파일 직접 확인이며 ADR-020 원문 대조는 미수행 — WP-NTC 착수 시 개발 모드가 ADR-020을 재확인하고, 코드·ADR이 충돌하면 ADR 우선으로 에스컬레이션.
4. 공식 정본 코퍼스(비커밋)의 erratum은 허브에 수식 본문을 전재하지 않고 ledger 이벤트(ID·사유만)로 기록 — 비노출 원칙 유지.
5. Stage5 DTW 유지 판단은 "결정론 대조는 절대 채점이 아니다"라는 §1 원칙에 의존 — 만약 라벨 자체가 패널 채점산이면 라벨 수집 시점에 쌍대화 재검토.

**문서 ID**: LOS-STAGE36-PAIRWISE-REV-V1.0-2026-06-12 · 차기 진입: INDEX → unified_priority_map → 본 문서
