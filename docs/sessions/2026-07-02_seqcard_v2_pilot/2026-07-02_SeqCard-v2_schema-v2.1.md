# SeqCard v2.1 스키마 개정 (파일럿 결과 반영)
_2026-07-02 · 결정 반영: (1) 스키마 개정 적용, (2) 본연구 착수 / (3) 개발자 직접 인간앵커 = 제외_
_근거: 2026-07-02_SeqCard-v2_pilot-results.md (118씬 교차판정)_

## 개정 1 — episode_role: 8분류 → 6분류 병합
불일치가 전부 인접범주(complication↔development 11, development↔resolution 8)에 몰려 8분류 과세분 확인.
- **폐지·병합**: `midpoint` → `development`에 흡수, `tag` → `resolution`에 흡수.
- **v2.1 값역(6)**: `opening / setup / development / complication / climax / resolution`
- 기대효과: 경계 혼동 제거로 κ 상승. 재라벨 시 midpoint/tag 부착분은 위 규칙대로 매핑.

## 개정 2 — tension_role: 값역 유지(4), 앵커 정의 추가
"build" 흡인(bridge→build 15, peak→build 10)=판정자 기준선 상이. 조작적 정의로 고정.
- `build` = **직전 씬 대비 긴장이 상승**하는 씬(누적 압력↑).
- `peak` = 국소 정점. 대치·폭로·충돌이 그 씬에서 터짐.
- `release` = 정점 후 **하강·이완**(해소/여파/숨고르기).
- `bridge` = 긴장 궤적과 **무관한 연결·정보전달·장면전환**(상승도 하강도 아님).
- 판정 규칙: 앞 씬을 반드시 참조해 상대적으로 판정(절대 강도 금지).

## 개정 3 — scene_blocks_need: 재조작화 + review-only 강등
GPT true 62 vs Claude 30 = 구성개념이 판정자마다 다르게 조작화됨. 자동 라벨 부적합.
- **관찰가능 재정의(v2.1)**: true = 씬 안에서 인물이 **표면 욕망(want)을 좇는 행위가, 명시적으로 드러난 더 깊은 필요(need)에 비용·장애를 발생**시키는 경우. need가 텍스트에 드러나지 않으면 false(추정 금지).
- **필수 부속필드**: `need_ref`(어떤 need인지 짧은 근거구). need_ref 없이 true 금지.
- **상태**: `confidence:"uncertain"` 기본 + **review-only**(자동 게이트 통과·기각에 사용 금지, 쟁점씬 회부 대상).

## 자동 게이트 배치(파일럿 실증)
| 필드 | 신뢰 | 처리 |
|---|---|---|
| hook_flag, 엣지 존재 | 강 | 교차판정 자동 검증 게이트 |
| continuity_break, episode_role(6), tension_role | 중 | 다수결 + 불일치 격리 |
| scene_blocks_need | 약(review-only) | 쟁점씬만 인간/다수결 회부 |

## 재라벨 불필요 원칙
파일럿 118씬 라벨은 silver 원본 보존. 개정은 **본연구 재라벨 시점부터** 적용(소급 재작업 아님).
