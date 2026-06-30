# SeqCard 코퍼스 검증 세션 — 적재 상태 (2026-06-29)

> 위상: 분석/PoC (κ게이트 미통과, corpus_ko 학습 타깃 미승급)
> 산출: Opus 전씬 독해(by=opus_reading) — 소제목(title)+의도(intent_gist)+core/core2+skin

## 적재 내역
- **원본 추출본** `original_extracted/` — 싸인 01~20 .txt (db\Scripts\한국드라마02 원본에서 추출)
- **빌드 스크립트** build_sign_01/02_seqcard.py
- **갭분석** 싸인_원본대조_갭분석.md — 원본 vs corpus 씬수 대조
- **1:1 보존검증** CORPUS-1to1-VERIFICATION-fallback_block-v1.md
- **데이터화 아키텍처** SEQCARD-DATAFICATION-ARCH-v1.md
- **SeqCard 실물** seqcards/*.seqcard.jsonl + *.episode_meta.json, 루트 *.seqcard.md

## SeqCard 완성도 (Opus 저작, null-free title/intent)
| work | scenes(jsonl) | episode_meta | 상태 |
|------|---------------|--------------|------|
| 대장금_01 | 28350B | - | 완성 |
| 싸인_01 | 49 | - | 완성 |
| 싸인_02 | 74 | - | 완성 |
| 싸인_03 | **19 / 52** | scene_count=52 | ⚠ **truncated** (씬20 mid-line 절단) — 재생성 필요 |
| 싸인_04 | 61 | 61 | 완성 |
| 싸인_05 | 63 | 63 | 완성 |
| 싸인_06 | 59 | 59 | 완성 (신규) |
| 싸인_07 | 65 | 65 | 완성 (신규, 06.hwp[1–15]+07.hwp[16–65] 완본) |

## 잔여 (집 이어작업)
- ⚠ **싸인_03 jsonl 재생성**: 양 마운트 공통으로 씬20에서 절단됨. episode_meta(52)와 불일치. 원본(original_extracted/싸인_03.txt) 재독해로 20~52 보강 필요.
- 싸인 08–19 SeqCard (현 C:\claude 08~19는 stale null skeleton — 미적재)
- 싸인 20부 최종회 SeqCard (씬#1–68)
- 싸인 01·02·04 원본 재검증 (원본 대비 -2씬 이슈)
- 전 싸인 완료 후 series_arc.json 구축
- κ게이트: 블라인드 인간 스폿체크 κ≥0.6 통과 전 corpus_ko 학습 타깃 승급 금지

## episode_function 진화 thesis (1화→7화)
1화 ESTABLISH12 / 2화 CONFLICT17·PERIL14·REVELATION12 / 3화 ESTABLISH14(1년후 리셋) / 4화 REVELATION13+ESTABLISH12 / 5화 REVELATION16=ESTABLISH16+PERIL8 / 6화 REVELATION19(단독최다)+RESCUE5(신규)+PERIL10 / **7화 REVELATION12+ESTABLISH10=RESCUE10(5→10 증폭)+PERIL8 앙상블(이봉 구조)**. '보조 함수가 회차마다 교체'된다는 thesis 재강화.

## 진행 갱신 (2026-06-29, Cowork Opus 오케 + Sonnet 4.6 저작)
- ★싸인_03 재생성 완료 — 전 52씬(절단 해소, by=sonnet-4.6).
- ★싸인 08·09·10·11·12 SeqCard 신규 완성 (by=sonnet-4.6): 08=49 / 09=57 / 10=56 / 11=71 / 12=62씬. null-free, episode_meta 포함.
- **싸인 현황: 01~12화 완성** (01·02·04~07=opus_reading, 03·08~12=sonnet-4.6). 잔여 = 13~20화 + series_arc.json.
- 방식: Cowork(Opus) 오케스트레이터가 원본(original_extracted/싸인_NN.txt) 배정 → Sonnet 4.6 서브에이전트 정독 저작(세션별 누적). 사용자 지시 "Sonnet 4.6 높은 모드".
- 다음 배치: 싸인 13~16 → 17~20(20부 마커 '씬/N' 0개라 형식 별도 확인 필요) → 완주 후 series_arc.json → κ게이트.

## ★싸인 완주 (2026-06-29, Sonnet 4.6 3인 멀티에이전트 2차 배치)
- 신규: 13(80)·14(69)·15(74)·16(69)·17(75)·18(66)·19(67)·20(68, 최종회 '씬#N.' 형식). 전부 by=sonnet-4.6, null 0, episode_meta 포함.
- **★싸인 01~20 완주 완료** (01·02·04~07·대장금1·도깨비1=opus_reading / 03·08~20=sonnet-4.6).
- ⚠ 정합 처리: `original_extracted/싸인_15.txt`가 **15회(74씬)+16회(69씬) 2-in-1 추출 오류**. 싸인_15.seqcard는 앞 74장(15회분)으로 정리, 16회는 별도 싸인_16.txt(69) 정본 유지. → 개발자: 싸인_15.txt 원본추출 분리 권고.
- ⚠ 싸인_18: 원본 마커 71 중 5개(씬43·44 묶음·49·64·68)를 비-씬으로 판단해 66장. 필요시 재검토.
- 다음: **series_arc.json**(싸인 20화 episode_function 전이문법 집계) → κ게이트(블라인드 인간 κ≥0.6) → 이후 ~50편(완주 우선).
