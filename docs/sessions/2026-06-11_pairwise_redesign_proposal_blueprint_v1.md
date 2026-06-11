# 쌍대(Pairwise) 측정·보상 재설계 — 정식 제안서 + 설계도 v1.0 (2026-06-11)

**기준선**: HEAD `d826ab4` · 선행 심의: 3인 교차 심의(0a22018) · 실증: 실험 F(11/11)·H(11/11)·LW-5(6/6)
**문서 성격**: 심의록을 **집행 가능한 제안서(§1~3)+설계도(§4~6)**로 정식화. 대상 = 개발자 결정 + 저연산(Sonnet) 개발 모드 집행.

═══════════════════════════════════════════
## 제1부 — 제안서
═══════════════════════════════════════════
### §1. 배경과 문제 (왜 지금인가)
실측 6건(Mode2 파일럿, LF 장기실측, 후속 A~G, 실험 H, LW-1~5)이 수렴한 결론:
1. **절대 스칼라 채점은 측정 형식 자체가 신호를 죽인다** — 모든 절대 경로 FAIL(5~7/11, ΔR 0.016) vs 쌍대 11/11(p=0.0005).
2. 절대 채점은 **proxy 순환을 증폭**한다 — LLM이 자기 문체 모작에 명작보다 높은 점수(8.17>7.50). 이 신호로 학습하면 모델은 명작에서 멀어진다.
3. 선호 질문은 문체 축에서 무효 — 목표 문체 달성 6/6인 출력이 선호 심사 2/6 (LLM 화려체 편향).
→ 측정·검증·보상의 기본 연산을 절대 점수에서 **쌍대 비교**로 전환해야 하며, 문체 축은 선호가 아닌 **특성·근접도 판단**으로 분리해야 한다.

### §2. 제안 (결정 요청 3건)
- **D-PW1**: 공식 검증·생성 평가의 1차 지표를 쌍대 승률(forced choice)로 채택. 절대 점수는 Bradley-Terry 집계 산물로 강등. [실증 완료 — 승인만 필요]
- **D-PW2**: RLAIF/DPO 보상은 선호쌍만 사용, 절대 채점 보상 **금지** 게이트(G_NO_ABSOLUTE_REWARD) 신설. [D 역전이 근거]
- **D-PW3**: 문체·안티LLM 축 평가는 선호 질문 금지, 특성 판단+정전(canon) 근접도 2종으로 제한. 인간 GT는 박빙·문체 축에만 투입. [LW-5가 근거]

### §3. 효과와 비용
- 효과: 변별력 7/11→11/11(+4, 실증), 판정 콜 수 절반(두 씬 1콜), 인간 GT 부담 급감(점수표→양자택일), DPO와 무변환 정합.
- 비용: 프롬프트 형식 변경 + 신규 모듈 1(pairwise.py) + BT 변환 계층 1 — WP-4b 규모 중소. 기존 절대 임계 게이트는 BT 변환 계층으로 무수정 호환.
- 리스크: 심의 P-1~P-6(비이행성·위치편향·판정자단일·anchor드리프트·비용·게이트호환) — §5에 대책 내장.

═══════════════════════════════════════════
## 제2부 — 설계도 (WP-4b 집행 명세)
═══════════════════════════════════════════
### §4. 모듈 설계 `literary_system/validation/pairwise.py`
```python
class PairwiseJudgment(TypedDict):
    pair_id: str; left_id: str; right_id: str
    winner: Literal['left','right']
    mode: Literal['preference','trait','canon_proximity']   # D-PW3: 문체축은 trait/canon만
    trait: str | None        # mode=trait일 때 판단 기준 명세 (예: '절제 저온 문체')
    rationale: str           # R5 근거 (의무)
    judge_id: str            # 모델+페르소나+temp (P-3)
    position_seed: int       # 위치 무작위 재현 (P-2)

def compare(a_id, b_id, db, mode, trait=None, judge=DEFAULT_JUDGE, cost_cap=...) -> PairwiseJudgment
    # 비교 주석(양씬 1콜) → 6컴포넌트 동시 → Δfitness 판정 + LLM 판정 병기 (실험 H 프로토콜)
def tournament(ids, db, anchors: list[str], k=5) -> list[PairwiseJudgment]
    # 전수 금지(C 합의) — anchor set k=5와만 비교 O(kn), 순위 필요 시 스위스 페어링
def bt_scores(judgments) -> dict[str, float]
    # Bradley-Terry 잠재 점수 — 기존 절대 임계 게이트 호환 계층 (P-6)
def transitivity_check(judgments) -> float
    # 판정 그래프 순환률 — G_TRANSITIVITY: <5% (P-1)
```
- **anchor set v1**: PD 명작 5씬(운수 좋은 날 s2·s10·s11 + 추가 PD 2씬), sha256 고정·버전화, 교체는 ADR 의무 (P-4).
- **위치 편향 대책**: 무작위 시드 기록, |Δ|<0.3 박빙 쌍은 양방향 2판정·불일치 시 무효 (P-2).
- **판정자**: 기본 gpt-4o temp0 + 페르소나·온도 교차 패널 옵션, judge_id 의무 기록 (P-3). cost_cap 필수 (P-5).

### §5. 게이트 신설 3종
| 게이트 | 내용 | 임계 |
|---|---|---|
| G_PAIRWISE_REGRESSION | 실험 F·H 프로토콜을 회귀 테스트로 고정(명작 vs 강열화 11쌍) | 승률 ≥9/11 유지 |
| G_TRANSITIVITY | 판정 그래프 순환률 | <5% |
| G_NO_ABSOLUTE_REWARD | 학습 보상 경로에 절대 점수 유입 차단(타입 수준) | 위반 0 |

### §6. 테스트 목록 (선기재 — Sonnet 집행용)
`tests/validation/test_pairwise.py`:
`test_compare_blind_position_randomized` · `test_trait_mode_rejects_preference_prompt` · `test_bt_scores_monotonic_with_winrate` · `test_transitivity_detector_finds_cycle`(합성 순환 픽스처) · `test_anchor_set_sha_pinned` · `test_cost_cap_aborts` · `test_no_absolute_reward_type_guard` · `test_regression_f_protocol_fixture`(LLM mock)
**DoD**: 8 테스트 green + 실키 스모크 1회(11쌍, cost_cap $0.15) ≥9/11 + WP 보고서. **권장 V761~V763 (WP-4b)**.

### §7. 난이도 사다리 (가중치 값어치 검증 — 차기 실험 예약)
실험 H 절제에서 무가중도 11/11 → 가중치 부가가치 미입증. 사다리: L1 명작 vs 강열화(완료, 11/11) → L2 명작 vs 약열화(디테일만 제거) → L3 명작 vs 생성 → L4 생성 vs 생성(박빙). **L3~L4에서 가중 fitness가 무가중 대비 우위를 보이는지**가 fitness 가중 재보정(생애주기 recalibrate)의 정식 판정 기준. 사전등록: L3·L4에서 가중>무가중 일치율 +10%p 이상.

**문서 ID**: LOS-PAIRWISE-PROPOSAL-V1.0-2026-06-11
