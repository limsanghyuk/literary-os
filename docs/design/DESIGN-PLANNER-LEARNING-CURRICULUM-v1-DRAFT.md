# 플래너 학습 커리큘럼 (Planner Learning Curriculum, PLC) — 설계 초안 v1 (DRAFT)

- 작성: 2026-06-26 (계획·설계 모드, 무GPU) · 누적 스레드
- 성격: **초안(DRAFT).** 졸업 계약이 아니라 다음 대화에서 v2로 갱신될 살아있는 설계.
- 선행 실측/설계: `docs/measurement/SUBPLOT-RATIO-MEASUREMENT-v1.md`(48% 잣대), `docs/design/DESIGN-AFFILIATION-ENSEMBLE-v1.md`(AEG 아키텍처), `WIRING-ORCHESTRATOR-POC-RESULTS-v1`(배관), `WIRING-WATER-FrontierPort-RESULTS-v1`(실생성 좌석), 2026-06-23 LLM2~3 준비물 지도.
- 트랙: 메인(LLM-0→3 자율화). 제품전략 B와 무관.

---

## 0. 한 줄

판단 학습(loop-C / per-token DPO)은 **이미 있다**. 그러나 **생성 플래너 자체를 학습시키는 커리큘럼은 백지**다(2026-06-26 대화에서 드러난 최대 갭). 본 초안은 "메인 줄기 위에 서브플롯 40~50%를 작가팀처럼 배분·교차시키는 플래너"를 **모방→잔차→선호** 3단으로 학습시키는 데이터·표상·손실·루프·DoD를 못 박는다.

---

## 1. 문제의 구조적 정의

### 1.1 학습되는 것 = 산문이 아니라 "플랜"

| 축 | 기존 학습 (있음) | 본 커리큘럼 (빈칸) |
|---|---|---|
| 표상 | 산문 토큰 시퀀스 | **구조 플랜**(화별 K·서브배분·소속군·교차시점·payoff·아크텐션) |
| 학습기계 | loop-C 누적 DPO, per-token KL, 5축 Critic | **loop-P**(신규) — 플랜 수준 학습 |
| 좌석 | `GenerativePort`(FormulaFallback→LLM1→Frontier) | **`PlannerPort`(신규 제안)**(FormulaPlanner→BCPlanner→DPOPlanner) |
| 현 상태 | FrontierPort로 실 산문 흘림 성공(프록시) | **공식 산정 100%** — 학습 0 |

핵심: 산문 품질(loop-C)과 **구조 기획 능력(loop-P)은 직교**한다. 거대 LLM이 산문은 잘 써도 16/24부작 메인+서브 구조를 작가팀처럼 짜는 건 별개 능력이며, 우리 모델의 차별점은 바로 이 구조 기획층이다. 따라서 산문 학습과 **분리된 플래너 학습**이 필요하다.

### 1.2 플래너가 내려야 하는 결정 (학습 대상 변수)

1. 화별 마이크로플롯 수 K (현 `episode_planner.plan()` 공식 산정).
2. 서브플롯 대사 배분 비율 — **목표값 = 오늘 실측 드라마 중앙값 0.46**(직장군+가족군).
3. 소속군 할당 — 주인공의 직장 클러스터 / 가족 클러스터 (AEG 스키마).
4. role_type 3종 배정 — 주인공 / 반대주인공 / 주변(앙상블).
5. 메인-서브 교차 시점 — 서브플롯이 메인 인과에 충돌·합류하는 화/씬 (`causal_plot_graph` 교차).
6. payoff 타이밍 — 복선 회수 분포 (`payoff_scheduler` / reveal budget).
7. 아크 텐션 곡선 — 북엔드(도입·결말 강) + 중반 사건흐름 유지(교수 4공식 실측).

---

## 2. 전략 3+1 생성·평가 (ToT)

| 전략 | 내용 | 장점 | 단점/리스크 | 판정 |
|---|---|---|---|---|
| **A. 모방학습(BC/SFT)** | 실측 드라마 → (시놉시스+소속그래프 → 구조플랜) 쌍 추출 → 플래너-LLM SFT | cold-start 강력, 데이터 즉시 가용(오늘 라벨러 씨앗), 작가팀 분포 직접 흡수 | 모방 상한(명작 천장), 모드붕괴, 라벨 노이즈에 민감 | **채택(1단)** |
| **B. 플랜 선호학습(Plan-DPO/RLAIF)** | 2개 후보 플랜 생성 → Critic(공식+LLM)이 우열 → DPO. loop-C 기계 재사용 | 모방 상한 초월 가능, 기존 DPO 인프라 재사용, 48% 잣대를 보상에 직접 투입 | cold-start 약함(A 선행 필요), 보상 해킹(서브비율만 맞추고 이야기 붕괴) | **채택(3단)** |
| **C. 공식-부트스트랩 + 잔차학습** | 공식 플래너를 floor로 두고 LLM이 공식 대비 Δ만 학습, KL anchor | 안전 바닥 보존(설계철학 정합), 발동률↓로 진척 측정 가능, 폭주 차단 | 표현력 제한(공식 근방에 묶임), 잔차 표상 설계 난이도 | **채택(2단·안전판)** |
| D. 자율 자기대국 루프 | 생성→측정(48등)→재플랜 자가루프 | 천장 잠재력 | 시기상조(LLM-3 영역), 보상 미성숙 시 발산 | **제거** — Phase G로 연기 |

### 2.1 가장 비합리적인 전략 제거
**D 제거.** LLM-1 졸업조차 실 GPU 1라운드 미측정인 현 단계에서 자율 자기대국 루프는 보상함수가 미성숙해 발산 위험만 크다. Phase G 천장 의제로 연기.

### 2.2 선택 = A→C→B 3단 결합 (단, A 1라운드를 첫 관문으로)
- **이유**: A는 데이터가 오늘 이미 생겼고(라벨러 존재) cold-start를 책임진다. C는 우리 설계철학(공식=영구 안전 바닥, 발동률 0 수렴이 지표)과 정합하며 A의 폭주를 막는 안전판이다. B는 모방 상한을 넘되 A·C가 깔린 뒤라야 안정적이다. 순서를 뒤집으면(B 먼저) cold-start 붕괴, C 생략 시 안전 바닥 상실.
- **초안 범위**: 본 문서는 **A(모방) 1라운드를 첫 실측 관문**으로 못 박고, C·B는 골격만 둔다.

---

## 3. 데이터 — 오늘 작업이 씨앗이다

### 3.1 라벨 스키마 (작품당)
```
{
  affiliation_graph: { work_cluster:[char...], family_cluster:[char...] },
  roles: { protagonist:[...], antagonist:[...], supporting:[...] },   # 3종
  episodes: [ { idx, K, sub_share, pure_sub_share, cross_events:[...], payoffs:[...], tension } ... ]
}
```

### 3.2 라벨러 — 무엇이 있고 무엇이 빈칸인가
| 라벨 | 채널 | 상태 |
|---|---|---|
| sub_share / pure_sub_share | **오늘 `measure_subplot_ratio.py`** | ✅ 가용(122편 실측 완료) |
| roles 3종(주연/반대/주변) | 화자 빈도순위(오늘 스크립트 top-K) | △ 부분(주연/주변만, 반대주인공 분리 미완) |
| affiliation_graph(직장/가족) | role NER + 관계 추출 | ❌ 빈칸 — SUBPLOT-RATIO v2 의제 |
| cross_events(메인-서브 교차) | `causal_plot_graph` 교차 추출 | ❌ 빈칸 |
| payoffs(복선 타이밍) | 기존 reveal budget / payoff_scheduler 역추출 | △ 기관 존재, 라벨 추출기 미작성 |
| tension 곡선 | 기존 arc/emotion 공식 | △ 기관 존재 |

**즉 BC 1라운드의 최소 라벨(sub_share+roles+tension)은 오늘 작업+기존 공식으로 이미 충당 가능.** affiliation/cross는 v2에서 채운다. 규모 = 122 드라마 × 16~24화 ≈ 2,264 회차 시퀀스.

---

## 4. 좌석·표상·손실 (A 1라운드 명세)

### 4.1 PlannerPort 좌석 (신규 seam 제안)
```
class PlannerPort(Protocol):
    def plan_series(self, synopsis, affiliation_graph, n_episodes) -> SeriesPlan: ...
# FormulaPlannerPort(현재 공식 산정)  →  BCPlannerPort(SFT)  →  DPOPlannerPort
```
- `GenerativePort`(산문)와 **직교 2층**: PlannerPort=구조플랜 산출 → 그 플랜을 GenerativePort가 산문화. 계약 불변 교체(WIRING 좌석 원칙 계승).
- 현 `wiring_poc`의 공식 호출 경로가 그대로 FormulaPlannerPort = baseline.

### 4.2 손실 (A=BC)
- 구조 플랜 필드 NLL (시퀀스/JSON).
- **구조 일치 보조손실**: 생성 K궤적 vs GT의 L1 + 서브비율 L1(48 잣대로 직접 정렬).
- 작품단위 train/held 분리(데이터 누수 차단, 기존 splits 원칙).

### 4.3 C·B 골격(초안)
- C: `plan = formula_plan + clamp(LLM_residual, KL≤τ)`. 발동률 = LLM_residual 비0 비율 → 학습 진척 지표.
- B: 플랜 쌍 (chosen=Critic 우세) DPO. 보상 = 5축 craft + 거시일관(A) + **48 잣대 적합도** − 보상해킹 페널티(서브비율만 맞고 인과 붕괴 시 감점).

---

## 5. 루프·DoD

### 5.1 loop-P (loop-C와 병렬)
무GPU 설계 단계 산출 = 라벨러 확장 + PlannerPort 계약 + BC 데이터셋. 실 학습(SFT/DPO) = 집 4070 / 클라우드.

### 5.2 DoD — A 1라운드 (측정 가능 관문)
1. BC 데이터셋 ≥2,000 회차 시퀀스, 작품단위 held ≥250.
2. BCPlannerPort가 16부작 플랜 산출 → `measure_subplot_ratio.py` 재측정 **서브비율 중앙값 0.46±0.10**(AEG DoD 계승).
3. K궤적 아크형(중반 상승) 유지.
4. held-out 작품 구조 재현(K-L1, 서브비율-L1 < 임계).
5. FormulaPlannerPort(baseline) 대비 잣대 적합도 비열위.

---

## 6. 실행 체크리스트 (다음 단계 후보)

- [ ] (설계) PlannerPort Protocol + SeriesPlan 스키마 확정 (GenerativePort와 직교 검증).
- [ ] (라벨러) 오늘 스크립트 확장 — roles 3종 분리(반대주인공) + tension/payoff 라벨 추출 패스.
- [ ] (데이터) BC 쌍 빌더 — (시놉시스+소속그래프 → SeriesPlan) 추출, 작품단위 split.
- [ ] (집·GPU) BCPlannerPort SFT 1라운드 → DoD §5.2 측정.
- [ ] (v2) affiliation_graph(직장/가족) + cross_events 라벨 = SUBPLOT-RATIO v2와 합류.
- [ ] (이후) C 잔차 안전판 → B 플랜-DPO.

---

## 7. 자기점검 (논리적 약점)

1. **라벨러가 아직 표면적이다.** 서브비율은 화자 토큰 빈도 기반이라 직장/가족 소속 유형·메인-서브 교차 시점은 미라벨. BC 1라운드는 "구조 골격"만 학습, 의미적 소속 배분은 v2 라벨 충전 후.
2. **모방 상한.** A(BC)는 명작 분포를 천장으로 둔다. 그 위로 가려면 B(선호)+자율루프가 필요하나 시기상조. 본 초안은 "작가팀 분포 재현"까지가 정직한 목표, "초월"은 비주장.
3. **플랜 표상 미확정.** JSON 시퀀스 vs 그래프 vs 스칼라 벡터 — 본 초안은 JSON 제안이나 학습난도·생성호환은 미검증.
4. **산문 학습(loop-C)과 플랜 학습(loop-P)의 상호작용 미검증.** 두 층을 따로 학습한 뒤 결합 시 정합이 깨질 수 있음(플랜은 서브 40%인데 산문이 메인만 부풀리는 등). 결합 측정이 별도 DoD로 필요.
5. **이 문서는 방향·골격이지 졸업 계약이 아니다.** A 1라운드 임계(0.46±0.10)도 AEG에서 계승한 잠정값.

---

## 8. 한 줄 결론

오늘 드러난 갭("판단 학습은 있는데 플래너 학습이 없다")에 대한 첫 메움 = **PlannerPort 좌석 + loop-P + A(모방)→C(잔차)→B(선호) 커리큘럼**. 그리고 그 첫 라운드(A)의 데이터·라벨러·잣대는 **오늘의 48% 실측이 씨앗**이다. 누적 대화가 기획의 발판이 된다는 말 그대로, 오늘 실측이 내일 학습의 라벨이 된다.
