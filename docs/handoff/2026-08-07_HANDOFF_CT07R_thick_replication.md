# HANDOFF — CT-07R 후판 재현 관문 집행 완료 (회사 → 집)

Document ID: `LOS-HANDOFF-20260807-CT07R`
Date: 2026-08-07
작성: 회사 세션 (Opus)
기준 커밋: 본 커밋 · 직전 baseline `a287bac`

## 0. 한 문단 요약

CT-07R을 사전등록대로 집행하고 판정을 냈다. **PASS(강한 재현 아님).** `r_T = 0.817`,
`D_N = +2.533`, 임계는 하나도 건드리지 않았다. 98작 후판 사이드카 전량 저작이 승인됐다.
그러나 승인의 정체가 예상과 다르다 — 사전지정 범주 분해에서 전체 0.817이
**씬내부 0.567 / 배치관계 1.386** 의 혼합값임이 드러났다. 후판은 사람 씬카드를 대체하지 않고,
씬카드가 구조적으로 다룰 수 없는 **배치관계 층**을 채운다. 98작 발주 지시문의 무게중심을
씬 묘사가 아니라 앞뒤 씬과의 관계에 두어야 한다.

## 1. 집에서 5분 안에 재현하는 법

허브 clone 만으로 보고서의 **모든 수치가 다시 계산된다.** 원문·정답표 정본이 필요 없다.

```
python docs/tracks/confirmatory/artifacts/ct07r/CT07R_analyze.py --run docs/tracks/confirmatory/artifacts/ct07r
```

기대 출력: 판정 `PASS`, `r_T 0.817`, `D_N +2.533`, S2 leave-one-out 최소 0.727 / 최대 0.905,
S3 범주 분해 씬내부 0.567 / 배치관계 1.386, 채점자 일치도 572/600 = 95.3%,
채점자별 총점 61.0 / 61.0 / 67.0 (만점 200).

수치가 다르면 스크립트가 아니라 데이터를 의심할 것. `CT07R_SHA256_MANIFEST.json` 에
129파일의 개별 sha256과 디렉터리별 concat sha256이 들어 있다.

## 2. 읽는 순서

1. `docs/tracks/confirmatory/CT-07R_2026-08-07_result.md` — 판정 본문 (`LOS-CT07R-RESULT-V1.0`)
2. `docs/tracks/confirmatory/CT-07R_2026-08-07_execution_method.md` — 무엇을 어떻게 했는가 (`LOS-CT07R-METHOD-V1.0`)
3. `docs/tracks/confirmatory/CT-07R_2026-08-07_amendment_02_as_executed_normalization.md` **§0.5 먼저** — 규칙 분기 대조
4. `docs/tracks/confirmatory/CT-07R_2026-08-07_amendment_01_short_anchor_sensitivity.md` — 민감도 사전지정
5. `docs/tracks/confirmatory/EXPERIMENT_LEDGER.md` 말미 CT-07R 절 — 원장 반영분

## 3. 이번에 올린 것

| 대상 | 경로 | 비고 |
|---|---|---|
| 판정 보고서 | `docs/tracks/confirmatory/CT-07R_2026-08-07_result.md` | 10절 |
| 집행 방법 | `docs/tracks/confirmatory/CT-07R_2026-08-07_execution_method.md` | 8절, 재현 절차 포함 |
| 개정 01 | `..._amendment_01_short_anchor_sensitivity.md` | 렌더 0건 시점 사전지정 |
| 개정 02 (집행분) | `..._amendment_02_as_executed_normalization.md` | §0.5 규칙 분기 대조 신설 |
| 원자료 | `docs/tracks/confirmatory/artifacts/ct07r/` | 132파일 676K |
| 재계산 스크립트 | `artifacts/ct07r/CT07R_analyze.py` | `LOS-CT07R-ANALYZE-V1.0` |
| 안전판 생성기 | `artifacts/ct07r/CT07R_make_hubsafe.py` | `LOS-CT07R-HUBSAFE-V1.0` |
| SHA 매니페스트 | `artifacts/ct07r/CT07R_SHA256_MANIFEST.json` | 129파일 |
| 상태 파일 갱신 | `docs/tracks/confirmatory/CT07R_CURRENT_STATUS.json` | `renders=0/scores=0` → 실측치로 정정 |
| 원장·README 갱신 | `EXPERIMENT_LEDGER.md` (V1.3) · `README.md` | CT-06H·CT-07·CT-07R 행 추가 |

`artifacts/ct07r/` 내역: `render_inputs/` 40, `renders/` 40, `scoring_packets/` 40,
`scores/` 3, `hubsafe/` 2, `BLIND_MAP.json`, `element_labels.json`, `RESULT.json`,
`build_render_inputs.py`.

## 4. 올리지 않은 것과 그 이유

**정답표 정본 `keys/*.key.json` 은 허브에 없다.** 원문 직접인용(`evidence`)을 담기 때문이다.
허브에는 인용을 앞 8자로 절단한 `hubsafe/CT07R_KEYS.hubsafe.json` 만 있다(38건 중 21건 절단).
집행 정본은 로컬 `C:\claude\CT07R_run_20260807\keys\` 이며 sha256만 봉인돼 있다
(`f456a957…` / `16719be5…`). **채점 재집행에는 안전판을 쓰지 말 것.**

**렌더 40본은 절단하지 않고 원본 그대로 올렸다.** 모델 생성물이지 대본 원문이 아니기 때문이다.
대신 정량 축자 게이트를 통과시켰다 — 원문 행 사전 30,579행(2작)과 대조하여
프롬프트가 공급한 씬 표제를 제외한 최장 일치 **15자**, 차단 기준(16자 이상) **0건**.
일치 목록 전량을 `hubsafe/CT07R_VERBATIM_GATE.json` 에 공개했다. 판정을 믿지 말고 직접 대조하라.

## 5. 반드시 알고 시작해야 할 세 가지

**(1) 효과 크기는 재현되지 않았다.** CT-07의 후판 직접 렌더 `r`=1.63 대 CT-07R `r_T`=0.817.
부호와 존재는 재현됐고 크기는 절반이다. 절대 수준도 T 2.700/5 = 54%로 낮다.
발주 규모나 기대 품질을 1.63으로 산정하면 안 된다.

**(2) 허브에 개정 02가 두 개 있고 규칙이 반대다.**
GPT `LOS-CT07R-PREREG-AMENDMENT-02` 는 정보량 균등화를 **TN 채워 올림**으로,
본 세션 `LOS-CT07R-AMD-02` 는 **양팔 절단**으로 규정했다. **집행은 후자를 썼다** —
`r_T` 에 대해 더 가혹한 쪽이다. 문서를 삭제하지 않고 §0.5에 대조표로 남겼다.
전자 규칙 아래의 판정은 새 렌더 세트가 있어야 답한다. 강건성 재현 항목.

**(3) 승인 범위가 좁다.** 승인된 것은 후판 사이드카 98작 저작뿐이다.
승인되지 **않은** 것: ①최소 필드 사양(다섯 필드 중 무엇이 기여하는지 모른다)
②회차→시퀀스 단(한 번도 측정된 적 없다) ③씬 내부 설계의 대체(r_T 0.567).

## 6. 98작 발주 시 반드시 지킬 것

1. **필드를 융합하지 말 것.** `cast[]` / `event` / `info_shift[]` / `plant_payoff[]` / `scene_notes[]`
   다섯을 분리 가능한 형태로 저작해야 이후 해체 실험(ablation)이 성립한다. 융합하면 최소 사양을
   영원히 못 구한다.
2. **지시문 무게중심을 배치관계에 둘 것.** 실측상 후판이 이기는 지점은 앞뒤 씬과의 관계
   (r_T 1.386)이고 씬 내부는 지는 지점(0.567)이다. 씬 묘사를 두껍게 쓰라는 지시는 측정된 이득이 없다.
3. **배선을 저작과 묶을 것.** R5 `PlannerInputRecord`, R8 `RuntimeSceneProjection`.
   저작만 하고 배선을 미루면 "저작했으나 아무도 읽지 않는 층"이 또 하나 늘어난다(D-28 계열 재발).
4. **승인 근거 요약에 이 문장을 그대로 넣을 것** (AMD-01 §4 해석 규약):
   *"상향 편향된 조건에서도 음성대조와 분리된 성립."*

## 7. 다음 우선순위 (제안, 확정 아님)

| 순위 | 항목 | 선행 | 비고 |
|---|---|---|---|
| 1 | 98작 후판 저작 발주 | 개발자 수용 | §6 네 조건 준수 |
| 2 | 후판 필드 해체 실험 | 98작 저작이 분리형일 것 | 최소 사양 도출 |
| 3 | 회차→시퀀스 단 진단 (CT-06H 등가) | 없음 | 미측정 구간, 발명 층 |
| 4 | GPT 규칙 하 CT-07R 강건성 재현 | 렌더 예산 | 새 렌더 세트 필요 |
| 5 | CT-03 문체 재입힘 재판별 | D-34 척도 신설 | 불규칙성 재현 트랙 |

## 8. 개발자 결정 대기 (이월)

1. **허브 원문 대본 130파일 노출** — `docs/sessions/**/original_extracted/` 8.6MB·197,776행,
   커밋 `362c6f7`, public. 이력 재작성이 필요하다. **제안: 저장소를 private 로 전환.**
2. D-45 `validate_encoding.py` 완화 여부
3. 업로드된 키 회전 여부
4. CT-05용 OpenAI 크레딧 충전
5. 박판 `authored_seq` DROP 여부

## 9. 미결 티켓 (트랙 무관, 이월)

`#69` n=48 판정 불일치 · `#74` D-27 재산출 · `#134` skin 위생 R1(18작 312회차) ·
`#135` 베이스라인 대조(로컬 EXT6 33/PHASE02 27 vs 권위 35/35) · 허브 원장 D-38~D-46 등재
