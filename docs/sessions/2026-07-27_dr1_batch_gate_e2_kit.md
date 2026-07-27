# DR-1 승인·확산 + G_PLANNING_LAYER 게이트 + E2 런치 킷 보고 (2026-07-27)

**기준선**: HEAD `e538cdc` · 사용자 결정: ①대장금 기획카드 승인 ②E2 착수 — 본 커밋이 두 결정의 집행이다.

## 1. DR-1 — 승인 반영 + 4작 확산 (기획층 5작 확보)
- **대장금**: status `PILOT_PENDING_USER_APPROVAL` → **`USER_APPROVED_2026-07-27`**.
- 신규 4작 저작(`USER_APPROVED_BATCH`): **모래시계**(시대극/숙명극·ORACLE 243 근거) · **시그널**(수사/REVELATION 동력·persist 0.439) · **파스타**(전문직 로맨스·episodearc 근거, series_arc 미등재 명기) · **킬미힐미**(심리 미스터리·persist 0.62, 인격=단서 보관함 설계).
- 전 카드 AM-1(결말 누출 금지)·AM-8(core_conflict/target_audience) 준수, key_scene_refs 전부 실재 씬.

## 2. G_PLANNING_LAYER 게이트 구현·실행
`tools/planning/verify_planning_layer.py` — 오프라인 결정론(AM-5): 필수키 15종 / logline 8~90자 / intent ≥40자 / **결말 키워드 휴리스틱(OUTCOME_LEAK)** / scene_refs ≥3 + SceneCard 실재 대조 / format 검증.
**실행 결과: 5카드 ERRORS 0 — GATE PASS.**

## 3. E2 런치 킷 — 데이터셋 빌드 완료
`tools/e2/build_e2_dataset.py` (결정론) 실행 산출(로컬 `db/harvest_pairs/e2_dataset/`):

| 항목 | 값 |
|---|---|
| train | **20,835쌍** (26작) |
| val | **2,195쌍** (작품 단위 분리: 시티헌터·오나의귀신님) |
| 제외 | 627쌍 (순서모드 verify_win=false — AM-6 안전마진) |
| sha256 | `517588c4…` (manifest 동봉) |
| 격리 | EVAL_HOLDOUT 유입 시 빌더가 즉시 FAIL(G_EVAL_HOLDOUT_ISOLATION 선구현) |

### E2 실행 런북 (개발자, 4070/RunPod — 기존 실증 경로 재사용)
1. 데이터: `db/harvest_pairs/e2_dataset/sft_brief2prose.train.jsonl` (verbatim — **비커밋 유지**).
2. 1라운드 = 250쌍 커리큘럼(4070 졸업과 동일 규모). SFT 1에폭 → 생성 스모크(val 브리프 20건, cost_cap $0.50) → 쌍대 판정(생성 vs val 원문, G_NO_ABSOLUTE_REWARD 준수).
3. 채택 게이트: 기존 `G_LOOPC_WINRATE` 그대로 — W1 하한 CI>0.5 + KL 상한 + length-rule 0.
4. 라운드 예산: 전체 20,835쌍 ≈ 83라운드 분량. 우선 3라운드로 ΔW 방향 확인 후 확대.
5. 홀드아웃(DR-5) 입수 시: EVAL_HOLDOUT 등록 → 빌더 재실행(자동 격리 검증).

## 4. 다음
- DR-1 확산 계속(정독 잔여 작품, 회당 배치) · DR-4(acclaim) 병렬 착수 가능.
- E2 실 학습 = **개발자 GPU 액션**(런북 §3). 잔여 14작 파서 진단 트랙은 후순위 유지.

## 5. 자기 점검
- 4작 카드의 시놉시스는 seqcard 아크·카드 근거의 역생성이며 실제 방영 기획서와 다를 수 있음(설계 의도). 파스타는 series_arc 미등재로 episodearc 근거만 사용 — evidence에 명기.
- OUTCOME_LEAK 휴리스틱은 사전 기반이라 우회 가능 — 확산 단계에서 스팟체크 병행(제안서 §4 파일럿 FAIL 기준 유지).
- E2 데이터셋의 순서모드 행은 구조적 1:1 근거이나 판별 패배 행 제외로 보수 운용 — 제외분 627은 소비하지 않는다.

**문서 ID**: LOS-DR1-BATCH-E2KIT-V1.0-2026-07-27
