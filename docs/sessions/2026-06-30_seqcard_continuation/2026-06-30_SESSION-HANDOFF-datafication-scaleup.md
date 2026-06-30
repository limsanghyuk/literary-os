# 2026-06-30 세션 핸드오프 — SeqCard 데이터화 대규모 확장 (회사 이어가기)

> 작성: Cowork(Opus 오케스트레이터 + Sonnet 4.6 멀티에이전트). 트랙 B(SeqCard 의도층). 
> 이 문서 하나로 회사 컴퓨터에서 끊김 없이 이어간다. 방법론 정본=SEQCARD-METHODOLOGY-AND-HANDOFF-v1.md.

## 0. TL;DR
오늘 SeqCard 저작을 **3시리즈(싸인·도깨비·대장금) 완주 + 마왕 19/20**로 확장하고, **싸인·도깨비·대장금 series_arc.json**(전이문법)을 만들었다. 다음 작품 선정안도 push. 전부 by="sonnet-4.6"(원본 정독), Opus가 오케스트레이션.

## 1. 오늘 한 것 (내용·결과)
| 작품 | 회차 | 상태 | 위치 |
|---|---|---|---|
| 싸인 | 1~20 | ✅완주 + series_arc.json | 2026-06-29.../seqcards/ (08~20 sonnet, 01~07 opus) |
| 도깨비 | 1~16 | ✅완주 + series_arc.json | 2026-06-30.../seqcards_authored/ (02~16 sonnet) |
| 대장금 | 1~54 | ✅완주 + series_arc.json | 동 (02~54 sonnet, 통합마커 처리) |
| 마왕 | 1~19 | 🔶 ep20만 미저작(원본 변환완료) | 동 (sonnet) |

- series_arc.json 3종 = 회차 전이문법 첫 추출. 장르 지문 확인: **싸인**(수사 ESTABLISH/REVELATION/PERIL)·**도깨비**(판타지멜로 ROMANCE115)·**대장금**(사극 CONFLICT679/PERIL483, CONFLICT→CONFLICT 0.323). **마왕**(복수스릴러 PERIL/ORACLE/REVELATION) = 4번째 장르 진행 중.
- 다음작품 선정안 push: NEXT-WORKS-SELECTION-v1 (1차 스카이캐슬 권고 등).

## 2. 방식 (회사에서 재현)
- **Sonnet 4.6 멀티에이전트 웨이브**(model=sonnet): 회차 2개/에이전트, **웨이브당 6~8개**가 안전(★11개 동시는 세션 한도 일괄 소진—실패 경험).
- **SeqCard 스키마**(불변): {work_id,scene_no,heading,title(소제목),intent_gist(이 씬이 *하는 일*),core/core2(16기능),skin,by}. +episode_meta(core_dist·episode_function).
- **씬 분할 마커는 작품마다 다름** — 통합 정규식 사용: 싸인 `씬/N`(20부는 `씬#N`), 도깨비 `S#N`, 대장금 `(?:S#|#|씬/?)\d+`(혼용), 마왕 `씬N`. ★단일 마커 가정 금지(대장금 1화 #7~19가 S#형식이라 초기 오판한 교훈).
- **원본 primacy**: corpus_ko 아닌 Scripts 원본 정독. HWP는 hwp5txt 변환.

## 3. ★주의·이슈 (회사에서 반드시 처리)
1. **gitignore**: docs/sessions가 gitignore라 seqcard는 `git add -f` 필수(마왕이 이걸로 한 번 누락됐다 복구).
2. **듀얼 경로**: 일부 서브에이전트가 /tmp/hub4 대신 /sessions/.../mnt/tmp/hub4에 씀 → 웨이브 후 병합 필요.
3. **원본 추출 실패작**: 스카이캐슬(hwp5txt 마커 24/80 누락)·내조의여왕(빈 출력) = 현 도구로 불완전 → **개발자 Windows의 한글(HWP) 네이티브 환경에서 재추출** 권고.
4. 싸인_15.txt = 15+16회 2-in-1 추출오류(분리 처리함, 원본 재추출 권고). 싸인_18 일부 omit 마커.

## 4. ★다음 착수 순서 (회사)
1. **마왕_20(마지막회) SeqCard** 1건 → 마왕 완주 + 마왕_series_arc.json. (원본 준비됨: original_extracted/마왕_20.txt, 87씬)
2. 선정안대로 다음 작품: 스카이캐슬/내조의여왕(HWP 재추출 후) 또는 변환 검증된 작품 우선. 장르 다양성(코미디·가족극 미확보).
3. 5~6시리즈 완주 시 **κ게이트**(블라인드 인간 κ≥0.6) 첫 검증 → 통과 시 corpus_ko 학습 타깃 승급.
4. series_arc 누적 → loop-P(PlannerPort BC) 학습 데이터로 연결.

## 5. 정직한 경계
- 저작 누계 = 싸인20+도깨비16+대장금54+마왕19 = 109회차 / 4시리즈(완주 3). "분해(읽기)≠생성", PoC 위상, κ 미통과. 목표 ~50시리즈의 초반.
