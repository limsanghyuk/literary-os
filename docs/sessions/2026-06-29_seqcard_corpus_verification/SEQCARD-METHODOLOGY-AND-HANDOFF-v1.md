# SeqCard 데이터화 — 방법론·핸드오프 종합문서 (v1)

> 작성: 2026-06-29 (Cowork/Opus 세션)
> 목적: 집 컴퓨터에서 이어 작업하기 위한 **작업 내용·방식·결과물·진행현황·이어가기 절차**의 단일 권위 문서
> 위상: 분석/PoC (κ게이트 미통과)

---

## 0. 한눈 요약 (TL;DR)
- **두 개의 데이터화 트랙은 목적이 다르다.** 기존 `corpus_ko`는 **LLM-1 완성용**(씬 본문 분할·임베딩·features·NKG = 측정/검색/Critic substrate). 지금의 SeqCard는 **LLM-2~3용 자율기획 substrate**(원본 정독 기반 *의도층*: 소제목+의도+기능). 같은 "데이터화"라도 **재료·소스·산출이 다르다.**
- **원본이 권위 소스다.** SeqCard는 `corpus_ko`의 재분할본이 아니라 **원본 추출본(original_extracted)**을 정독해 만든다. corpus_ko 재분할에 분할결함 18.7%가 있기 때문(별도 감사 확인).
- **"코퍼스 미저장 ↔ 집 이어작업"은 모순이 아니다.** κ게이트는 *corpus_ko 학습 타깃 승급*만 막는다. **핸드오프 영속화는 허브가 담당한다.** 집은 허브를 클론해 이어간다. (자세히 §5)
- SeqCard 전용 저장소 `seqcard_intent`(별도 chroma + emb_cache)는 **집(GPU/임베딩)에서 빌드**한다. 단 κ통과 전엔 *분석용*으로만, planner prior 주입은 금지.

---

## 1. 왜 두 트랙인가 — 사용자 방향성 (2026-06-29 확정)

| 항목 | 트랙 A: corpus_ko (기존) | 트랙 B: SeqCard 의도층 (지금) |
|------|--------------------------|-------------------------------|
| 목적 | **LLM-1** 완성 (공식 검증·RAG·Critic baseline) | **LLM-2~3** 자율 기획·구성 |
| 데이터 단위 | 씬 본문(scenes) + 듀얼청킹(chunks) | 씬 *의도*(소제목+의도+기능) + 회차메타 |
| 무엇을 잡나 | "무슨 말이 오갔나"(내용) | "이 씬이 무슨 일을 하나"(기능/의도) |
| 소스 | (초기) 다양 → 재분할본 (결함 18.7%) | **원본 추출본 정독** (무손실 권위) |
| 임베딩 공간 | 본문 임베딩 (corpus_ko) | **분리된 의도 공간** `seqcard_intent` |
| 산출 학습물 | physics 상관·fitness·Critic | 전이문법 prior·회차기능 전이·설계 RAG |
| 작성 주체 | 파이프라인(자동 분할·임베딩) | **Opus 전씬 정독(by=opus_reading)** |

**핵심:** 사용자가 정확히 짚은 대로, 지금 데이터화는 **방식이 다르다.** corpus_ko가 "측정 가능한 본문 코퍼스"였다면, SeqCard는 "회차 마이크로플롯 **설계도** 코퍼스"다. 전자는 분석 엔진의 입력, 후자는 **생성 엔진(LLM-2~3)의 학습 prior** 재료다.

**원본 primacy:** 작업을 진행하며 원본의 중요성이 재확인됐다. 회차 경계·연속 씬번호·절단 없는 본문은 원본에서만 신뢰 확보된다(예: 싸인 7부 = 06.hwp[씬1–15]+07.hwp[씬16–65] 연속 65씬은 원본 대조로만 확정). 향후 모든 SeqCard는 **원본(`C:\claude\db\Scripts\한국드라마02` 등)에서 추출 → 정독**을 표준으로 한다.

---

## 2. 작업 방식 (method) — 재현 가능한 절차

1. **원본 추출**: hwp/hwp5/doc/docx/pdf → txt. 도구: `hwp.py`, `detect.py`, soffice/hwp5txt 라우팅. 산출 → `original_extracted/<work>.txt`.
2. **씬 경계 결정**: 원본의 씬 헤딩(`씬/N`, `S#N`, `# N` 등) 결정론 regex. GPT-API 분할 **금지**(사용자 지시). 다회차 1파일이면 회차 경계(`제 N회`, `- N부 엔딩 -`) 우선 검출 후 연속 씬번호 부여.
3. **전씬 정독 → 카드 저작**: Opus가 모든 씬을 읽고 각 씬에 대해
   - `title`(소제목): 그 씬을 한 줄로 요약한 장면 제목
   - `intent_gist`(의도): 이 씬이 회차/시리즈에서 *하는 일*
   - `core`/`core2`: 16기능 택소노미 1차/2차 (§3)
   - `skin`: 장소·시간 (heading 파생)
   를 **null 없이** 채운다. `by="opus_reading"`.
4. **회차 메타 작성**: `episode_meta.json` — acts(막별 scene_range+function+gist), core_dist(기능 분포), engine(서사 엔진 노트), **episode_function**(시리즈 내 회차 역할), themes.
5. **설계도 md**: 사람이 읽는 회차 설계도(회차기능·막별·core분포·의미축). episode_function 진화 thesis 누적.
6. **검증**: 씬수=jsonl 줄수=episode_meta.scene_count 일치, core_dist 합=씬수, scene_no 연속성, null-free.
7. **허용 자동화**: text-embedding-3-small 임베딩, 결정론 regex만. (LLM 분할/라벨 자동생성 금지)

---

## 3. 16기능 택소노미 (core/core2 값)
`ESTABLISH, ORACLE, INTRO, BOND, CONFLICT, REVERSAL, LOSS, PUNISH, REVELATION, REUNION, RELIEF, ROMANCE, PERIL, RESCUE, DESIRE, HOOK`

- core=주기능(필수), core2=보조기능(nullable). 한 씬이 두 일을 하면 core2 채움.
- 분포(core_dist)는 회차의 *기능 지문*. episode_function 추론의 기반.

---

## 4. 스키마

**씬 카드 jsonl** (1줄=1씬):
```json
{"work_id":"싸인_07","scene_no":1,"heading":"씬/1 N, 검찰청 건물 복도",
 "title":"굳은 얼굴로 모여드는 국과수 간부들","intent_gist":"법의관 납치 긴급사건 발생…",
 "core":"ESTABLISH","core2":"PERIL","skin":"검찰청 복도·낮","by":"opus_reading"}
```
조인키=(work_id, scene_no). C층 확장 예약: payoff_to/mirror/arc_tag.

**회차 메타 json**: {work_id, series_id, episode_index, scene_count, genre, source, acts[], core_dist, engine[], episode_function, themes[], by}.

**시리즈 아크 json** (전회차 완주 시 집계): episode_functions, turning_points, throughline.

---

## 5. 집 컴퓨터에서 이어가는 법 (핵심 질문 답)

**"코퍼스에 안 넣으면 어떻게 이어가나?"**
→ **이어가기 매체는 허브다.** corpus_ko는 *학습 타깃 저장소*이고, κ게이트(블라인드 인간 κ≥0.6) 통과 전엔 분석/PoC 라벨을 학습 타깃으로 못 넣는다. 그러나 **작업 영속화·핸드오프는 corpus_ko가 아니라 허브 git이 담당**한다. 둘은 역할이 다르다.

집 절차:
1. 허브 클론 → `docs/sessions/2026-06-29_seqcard_corpus_verification/` 에 **데이터(jsonl/meta/md) + 원본추출본 + 스크립트 + 본 방법론문서** 전부 존재.
2. 이 문서(§2 방식)대로 다음 회차 저작을 **다른 세션(Opus/Sonnet)**에서 이어감. 진행은 §6 ledger로 추적.
3. SeqCard 전용 저장소 `seqcard_intent`(별도 chroma + emb_cache, text-embedding-3-small) **빌드는 집에서**(임베딩 연산). 단 *분석용*으로만; planner prior 주입은 κ통과 후.
4. 싸인 전부(01~20) 완주 → `series_arc.json` 집계 → 그때 아크 전이 첫 데이터화.

**요약:** 코퍼스(corpus_ko) ≠ 핸드오프 매체(허브). 미저장은 "학습 승급 보류"일 뿐, 이어작업은 허브로 완전히 가능.

---

## 6. 진행 현황 Ledger (싸인)

| 회차 | 씬수 | jsonl | episode_meta | md | 상태 |
|------|------|-------|--------------|----|------|
| 싸인_01 | 49 | ✅ | ⬜ | ✅ | 완성 (원본 재검증 대기: -2씬 이슈) |
| 싸인_02 | 74 | ✅ | ⬜ | ✅ | 완성 (원본 재검증 대기) |
| 싸인_03 | 52(목표) | ⚠ 19/52 truncated | ✅(52) | ✅ | **재생성 필요** (씬20 절단) |
| 싸인_04 | 61 | ✅ | ✅ | ✅ | 완성 (원본 재검증 대기) |
| 싸인_05 | 63 | ✅ | ✅ | ✅ | 완성 |
| 싸인_06 | 59 | ✅ | ✅ | ✅ | 완성 (신규) |
| 싸인_07 | 65 | ✅ | ✅ | ✅ | 완성 (신규, 06.hwp+07.hwp 완본) |
| 싸인_08~19 | - | ⬜ | ⬜ | ⬜ | 미착수 (현 C:\claude 08~19는 stale null skeleton) |
| 싸인_20(최종) | 68(씬#1–68) | ⬜ | ⬜ | ⬜ | 미착수 |
| 대장금_01 | - | ✅ | - | ✅ | 완성 (타 시리즈 샘플) |

**다음 계획:** 싸인_03 복원 → 08~19 → 20 → 01·02·04 재검증 → series_arc.json. 싸인 완주 후 Sonnet 4.6 모드로 유명 드라마 ~50편 동일 방식.

---

## 7. episode_function 진화 thesis (1화→7화)
1화 ESTABLISH12 지배 → 2화 CONFLICT17·PERIL14·REVELATION12 → 3화 ESTABLISH14(1년후 리셋) → 4화 REVELATION13+ESTABLISH12 → 5화 REVELATION16=ESTABLISH16 동률+PERIL8 → 6화 REVELATION19(시리즈 단독 최다)+**RESCUE5 신규**+PERIL10 → **7화 REVELATION12+ESTABLISH10=RESCUE10(5→10 증폭)+PERIL8 앙상블(이봉 구조)**.

→ thesis: '같은 시리즈 안에서 **보조 함수가 회차마다 교체**된다'. 이것이 회차 간 기능 전이(아크 진행) 학습이 **시리즈 전회차 데이터화를 요구**하는 핵심 근거. SeqCard 트랙의 존재 이유.

---

## 8. 산출물 위치
- 허브: `docs/sessions/2026-06-29_seqcard_corpus_verification/` (jsonl·meta·md·원본추출본·스크립트·STATUS·본 문서)
- literary 마운트: `seqcards/` + 루트 `*.seqcard.md` + 본 문서
- 아키텍처 결정 근거: `SEQCARD-DATAFICATION-ARCH-v1.md` (ToT 3안→채택 B)
