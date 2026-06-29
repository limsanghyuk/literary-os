# SeqCard 의도층 — 집 이어작업 CONTINUATION HANDOFF v1
date: 2026-06-30 · author: opus (Cowork) · track: B (SeqCard 의도층 / LLM-2~3 자율기획 substrate)

> 이 문서 하나로 집 컴퓨터에서 끊김 없이 이어간다. 방법론 전체는 같은 폴더의
> `SEQCARD-METHODOLOGY-AND-HANDOFF-v1.md`(8섹션)를 정본으로 본다. 본 문서는 **현재 진척·
> 정본 파일 위치·다음 착수 절차·로컬에서 복사해야 할 파일** 4가지만 체계적으로 정리한다.

---

## 0. TL;DR (집에서 제일 먼저 읽을 것)

- **트랙 분리 재확인.** 트랙 A = corpus_ko(씬 본문 분할·임베딩·features·NKG = LLM-1). 트랙 B = **SeqCard 의도층**(소제목+의도+기능 = LLM-2~3). 본 핸드오프는 **전부 트랙 B**.
- **저작 원칙(불변).** SeqCard는 Opus가 **원본 대본을 직접 정독**하여 손으로 채운다(by="opus_reading"). GPT API로 분할/라벨하지 않는다. null-skeleton 도구 만들지 않는다. text-embedding-3-small·결정론 regex는 허용.
- **κ 게이트(불변).** 자동 생성 라벨은 분석/PoC 위상 유지. 인간 블라인드 κ≥0.6 통과 전 corpus_ko **학습 타깃 승급 금지**, prior 주입 금지.
- **이번 세션 핵심 성과:** 대장금·도깨비 **원본을 텍스트로 추출 완료**(이전엔 original_extracted가 싸인만 존재). 이제 **집에서 별도로 복사해 보여줄 파일은 없다** — 원본·저작본·방법론 전부 허브에 있다(§4 참조).
- **다음 1순위:** 싸인_03 **재생성**(현재 19/52만 존재, truncated). 그다음 싸인 08–20 → series_arc.json → Sonnet 4.6로 유명드라마 ~50편.

---

## 1. 저작 완료(AUTHORED) 현황 — null-free, by="opus_reading"

| work_id | 씬수 | 정본 위치(허브) | 비고 |
|---|---|---|---|
| 싸인_01 | 49 | seqcards_authored/싸인_01.seqcard.jsonl | 완성 |
| 싸인_02 | 74 | 싸인_02.seqcard.jsonl | 완성 |
| 싸인_04 | 61 | 싸인_04.seqcard.jsonl | 완성(literary 정본) |
| 싸인_05 | 63 | 싸인_05.seqcard.jsonl | 완성 |
| 싸인_06 | 59 | 싸인_06.seqcard.jsonl | 완성 |
| 싸인_07 | 65 | 싸인_07.seqcard.jsonl | 완성 |
| 대장금_01 | 69 | 대장금_01.seqcard.jsonl | 완성 |
| 도깨비_01 | 55 | 도깨비_01.seqcard.jsonl | PoC 스키마(extra: scope/kind/why_link). 핵심 6필드 동일 |

**episode_meta.json** 동반 완료: 싸인 03/04/05/06/07 (seqcards_meta/).

**= 저작 완료 8편(싸인6 + 대장금1 + 도깨비1).** 사용자 목표 "의미 있으려면 최소 ~50편"의 첫 16% 구간.

---

## 2. 미완·재작업 대상 (PENDING)

| 항목 | 상태 | 원본 위치(허브) | 비고 |
|---|---|---|---|
| **싸인_03** | **재생성 필요** — 현재 19/52 truncated | original_extracted/싸인_03.txt | seqcards_authored/싸인_03.PARTIAL19of52… 에 19행만. 처음부터 52씬 재정독 |
| 싸인 08–19 | 미착수 | original_extracted/싸인_08~19.txt | 원본대조 신규 저작 |
| 싸인 20부(최종회) | 미착수 | original_extracted/싸인_20.txt | 씬 ~#1–68 |
| 싸인 01·02·04 | 원본 재검증 권장 | original_extracted/ | 초기본—원본 1:1 재확인 |
| 대장금 02–54 | 미착수 | original_extracted/대장금_02~54.txt | 본 세션에서 원본 추출 완료(54편 전부) |
| 도깨비 02–16 | 미착수 | original_extracted/도깨비_02~16.txt | 본 세션에서 hwp→txt 추출 완료(16편 전부) |
| series_arc.json | 싸인 완주 후 | — | episode_function 전이 첫 데이터화 |

**주의(stale 경고):** C:\claude 의 `2026-06-29_corpus_scene_verification/seqcards/` 에는 by=None **null-skeleton**(눈이부시게·데릴남편오작두·미남이시네요 등)과 truncated 싸인_03/04가 섞여 있다. **이것들은 저작본이 아니다.** 정본은 본 허브 폴더 `seqcards_authored/`(literary 정본 반영본)만 쓴다.

---

## 3. 원본 텍스트(original_extracted) — 이번 세션 신규 확보

집 이어작업의 핵심 차단요인이었던 "대장금·도깨비 원본 부재"를 해소했다.

- **싸인 01–20** (기존): `original_extracted/싸인_NN.txt`. 헤딩 = `S#N` / 회경계 표기.
- **대장금 01–54** (신규): `대장금.zip`(54 txt, CP949)에서 추출. 헤딩 = `#N`. 대장금_01 = 31,927자.
- **도깨비 01–16** (신규): `도깨비.zip`(16 hwp)에서 **pyhwp TextTransform**으로 추출. 헤딩 = `S#N`. 회당 47–73 S# 헤딩. 01 = 36,317자/55씬.

**추출 재현법(도깨비 hwp, 집에서 필요시):** pyhwp 설치 후 `hwp5.cli.init_logger` import 깨짐 → 런타임 패치 1줄 후 `hwp5.hwp5txt.TextTransform().transform_hwp5_to_text()` 사용. soffice는 hwp 직접 로드 불가(H2Orestart 확장 필요). 상세 코드는 본 세션 transcript 참조. **단, 이미 txt로 허브에 들어있으므로 집에서 재추출 불필요.**

원본 zip 자체 위치(로컬): `C:\claude\db\Scripts\한국드라마02\{대장금,도깨비}.zip`.

---

## 4. 집에서 따로 복사해 보여줘야 할 파일 — **없음**

사용자 질문 "내가 로컬에서 따로 복사하여 보여 주어야 하는 파일이 있는가"에 대한 답:

> **아니오. 집에서 수동으로 복사·업로드할 파일은 없다.** 이어작업에 필요한 3종이
> 모두 허브에 들어있다: ① 원본 텍스트 90편(싸인20·대장금54·도깨비16) ② 저작 완료
> SeqCard 8편 + meta 5 ③ 방법론·핸드오프 문서.

집에서는 **허브를 clone**하면 끝이다. corpus_ko(트랙 A) 대용량 스토어는 **이어작업에 불필요**(트랙 B는 원본 정독으로만 만든다 — corpus_ko 재분할본 18.7% 결함이라 쓰지 않는다).

예외적으로 집에서 다룰 일이 생기는 경우만:
- **유명드라마 ~50편 확장 단계**에서 새 작품 원본이 필요하면, 그 작품 대본을 `C:\claude\db\Scripts` 류에서 같은 방식(zip→txt)으로 추출해 original_extracted에 추가. 현재 8편 + 본 추출분으로 당분간 불필요.

---

## 5. 집에서 다음 1편 착수하는 정확한 절차 (예: 싸인_08)

1. 허브 clone → `docs/sessions/2026-06-30_seqcard_continuation/` 진입.
2. `original_extracted/싸인_08.txt` 정독. `S#`/회경계로 씬 분리, 씬 개수 확인.
3. 각 씬마다 SeqCard 1행 작성 — 스키마(방법론 문서 참조):
   `{work_id, scene_no, heading, title(소제목), intent_gist(이 씬이 하는 일), core(16기능 中1), core2(보조 or null), skin{loc,time}, by:"opus_reading"}`
4. **16기능 택소노미**: ESTABLISH·ORACLE·INTRO·BOND·CONFLICT·REVERSAL·LOSS·PUNISH·REVELATION·REUNION·RELIEF·ROMANCE·PERIL·RESCUE·DESIRE·HOOK. **씬이 16기능에 안 맞으면 씬이 아니라 택소노미가 틀린 신호** → 택소노미 보강 우선 고려(반증가능성 유지).
5. 회차 끝에 `episode_meta.json` 동반: acts/core_dist/engine/**episode_function**(시리즈 내 이 회의 역할).
6. null 0 검증(by 전부 opus_reading, intent_gist·title 공란 0) 후 커밋·push.
7. 싸인 03·08–20 모두 끝나면 → `series_arc.json` 집계(episode_functions/turning_points/throughline) = 아크 전이 첫 데이터화.

**산출물 위상:** κ 통과 전까지 분석/PoC. prior 주입·corpus 승급 금지.

---

## 6. WHY (이 작업의 존재이유 — 흔들리면 다시 읽기)

LLM-2 완성에 필요한 "드라마 기획·구성·집필" craft는 **암묵지**라 사용자가 규칙으로 다 적어줄 수 없다. 유일한 길 = **많은 실제 데이터를 Claude에 보여주고, Claude가 '어떻게 만들어졌나'를 분석하며 학습법 자체를 스스로 발견**하게 하는 것. SeqCard 저작 = 단순 라벨링이 아니라 **학습 신호 설계 부트스트랩**(16기능 택소노미 제작, 스키마/청킹/JSON/임베딩/chroma 결정, '재료가 무엇이어야 하나' 자체를 데이터로 탐색).

**안전장치 2(합의):** ① 택소노미·스키마는 데이터에 **반증가능** 유지. ② 인간 블라인드 **κ≥0.6** = Claude가 *제 투사*가 아니라 *실제 craft*를 배우게 하는 닻(설계+채움+학습 닫힌 고리 = AI-judge-AI 편향, 블라인드 3모드 평가에서 실증된 위험의 재발 방지).
