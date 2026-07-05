# 세션 핸드오프 — 2026-07-05 (더킹투하츠 완료 + 10편 슬레이트 상태)

> 목적: 오늘 작업 내용·방식·결과물을 체계적으로 기록하고, **집 컴퓨터 환경에서 곧바로 이어작업**할 수 있게 절차를 남긴다.
> 대상 독자: 다음 세션(회사/집)의 Claude, 그리고 개발자.

---

## 0. TL;DR

- **더킹투하츠(작품 #3/10) 4층 저작 완료·엄격게이트 통과·허브 push 완료.**
- 완전작 20/20화, 1110씬 · 167시퀀스 · FullSeriesArc 1(완결형 open_ending=false).
- 허브 `origin/main` HEAD = **`15d4922`**, `seqcard_ko/`에 81개 파일 추가, 원격 fresh clone에서 strict gate **ERRORS 0** 재검증.
- **다음 = 작품 #4/10 구르미그린달빛** (씬카드 부재 예상 → Stage 1 원본정독부터).

---

## 1. 오늘 한 일 (What)

### 1.1 더킹투하츠 4층 수직 저작
10편 슬레이트를 **1편씩** 4층으로 저작하는 작업의 3번째. 순서상 원래 #3였던 **신사의품격은 소스 사용불가로 SKIP**, 더킹투하츠가 실제 #3가 됨.

| 계층 | 산출물 | 규모 | 저장 위치 |
|---|---|---|---|
| Stage 1 · SceneBlueprint (SSOT) | `더킹투하츠_NN.seqcard.jsonl` ×20 + `더킹투하츠_NN.episode_meta.json` ×20 | 20화 / **1110씬** | `seqcard_ko/authored/` |
| Stage 2 · SequenceBlueprint | `더킹투하츠_NN.seqblueprint.jsonl` ×20 | **167시퀀스** (ratio 0.150) | `seqcard_ko/authored_seq/` |
| Stage 2 · EpisodeArc | `더킹투하츠_NN.episodearc.json` ×20 | 20 회차아크 | `seqcard_ko/authored_arc/` |
| Stage 3 · FullSeriesArc | `더킹투하츠_full_series_arc.json` ×1 | 전체 시놉시스(17키) | `seqcard_ko/authored/` |

**회차별 실측 (씬 / 시퀀스):**

```
ep01 44/7   ep02 38/6   ep03 43/7   ep04 66/10  ep05 56/8
ep06 47/7   ep07 44/7   ep08 55/8   ep09 53/8   ep10 58/9
ep11 71/10  ep12 63/10  ep13 48/7   ep14 58/9   ep15 66/10
ep16 59/9   ep17 73/11  ep18 63/9   ep19 53/8   ep20 52/7
합계: 1110씬 / 167시퀀스 (ratio = 167/1110 = 0.150, 밀도 밴드 [0.13,0.16] 내)
```

### 1.2 작품 내용 지문 (분석 결과)
- **로그라인:** 철없는 대한민국 왕자 이재하가 남북 합동 WOC에 파견된 북한 교관 김항아와 사랑에 빠지지만, 클럽M 봉구의 암살 음모로 형(국왕 재강)을 잃고 마지못해 왕좌에 오르며 남북 전쟁 위기를 남북 합동 왕실 결혼으로 돌파한다.
- **series_core_dist (16기능 집계):** CONFLICT 238 > PERIL 201 > ESTABLISH 90 > REVELATION 80 > LOSS 73 > BOND 71 > REVERSAL 70 > DESIRE 60 > ROMANCE 59 > ORACLE 52 …
- **conflict_persist:** 0.61 (높음 = 갈등이 전 회차 지속되는 정치 스릴러 지문).
- **open_ending:** false — 봉구 ICC 단죄 + 4년 후 남북 공존 평화로 서사가 완결됨. (미생은 corpus에 11/20화만 있어 부분작·open_ending=true였던 것과 대비되는 **완전작**.)

---

## 2. 작업 방식 (How) — 재현 가능한 파이프라인

**Compaction-내성 3-스테이지 파이프라인** (컨텍스트가 끊겨도 각 스테이지가 독립 재개 가능):

1. **Stage 1 (씬카드 = SSOT):** 원본 정독으로 회차별 씬카드 저작. 9키 고정: `{work_id, scene_no, heading, title, intent_gist, core, core2, skin, by}`. 씬 저작은 **Sonnet 멀티에이전트 (회차당 1에이전트) 병렬**이 표준 (Opus 순차 저작 금지).
2. **Stage 2 (SequenceBlueprint + EpisodeArc):** 씬카드를 goal-obstacle-turn 단위로 타일링. Sonnet 병렬 웨이브(6~7 에이전트).
3. **Stage 3 (FullSeriesArc):** Opus가 회차아크들을 fan-in 하여 전체 시놉시스 저작(17키).

**★ Trust-but-verify (필수 원칙):** Sonnet 에이전트의 "ERRORS 0 PASS" 자기보고는 **신뢰하지 않는다.** 반드시 독립 디스크 검증을 거친다. 이번에도 그대로 적용:

- `verify_work.py`(우회불가 엄격게이트)를 디스크의 실제 산출물에 대해 직접 실행 → `ERRORS 0 — 엄격게이트 ALL PASS` 확인.
- 게이트 검사 항목: 정확 키셋(seq 18키 / arc 13키 / full 17키, miss+extra 양방), `value_shift`는 dict `{from,to}` 형태, `turn_class ∈ {RISE,FALL,REVEAL,STALL}`, `core_mix ⊆ CORE_ENUM(16)` 이고 실제 member 씬에 등장, 밀도 floor `ratio ≥ 0.11`, 커버리지 불변식(I-COVER 전 씬 정확히 1시퀀스 / I-PARTITION 교집합 ∅ / I-COUNT Σ=scene_count / ACT-COVER / SEASON-COVER).

**게이트 실행 커맨드:**
```bash
cd /sessions/<sandbox>/mnt/outputs && python3 verify_work.py 더킹투하츠
# 기대 출력: [더킹투하츠] eps=[1..20] scenes=1110 seqs=167 ratio=0.150x / ERRORS 0 — 엄격게이트 ALL PASS
```

---

## 3. 결과물 위치 (Where)

### 3.1 로컬 정본 (집·회사 공통 물리경로 = `C:\claude\db\seqcard_ko`)
```
seqcard_ko/authored/더킹투하츠_01..20.seqcard.jsonl        (20)
seqcard_ko/authored/더킹투하츠_01..20.episode_meta.json    (20)
seqcard_ko/authored_seq/더킹투하츠_01..20.seqblueprint.jsonl (20)
seqcard_ko/authored_arc/더킹투하츠_01..20.episodearc.json  (20)
seqcard_ko/authored/더킹투하츠_full_series_arc.json        (1)
= 총 81파일
```

### 3.2 허브 (github.com/limsanghyuk/literary-os)
- 브랜치 `main`, HEAD **`15d4922`** (직전 `a2427f8`=미생).
- 위 81파일이 `seqcard_ko/` 하위에 커밋됨.
- 커밋 메시지: `seqcard_ko: 더킹투하츠 4-layer authored (slate #3/10)`.
- 원격 재검증: fresh `git clone --depth 1` 후 `verify_work.py 더킹투하츠` → **ERRORS 0** 확인 완료.

---

## 4. 10편 슬레이트 진행 현황

| # | 작품 | 상태 | 비고 |
|---|---|---|---|
| 1 | 궁 | ✅ 완료 | 기존 씬카드 존재 (24화 스토어에 존재) |
| 2 | 미생 | ✅ 완료 | 씬카드 부재→Stage1부터. corpus 11/20화만=부분작(open_ending=true) |
| — | 신사의품격 | ⏭️ SKIP | 소스 사용불가 |
| 3 | 더킹투하츠 | ✅ 완료 (오늘) | 완전작 20화, open_ending=false |
| **4** | **구르미그린달빛** | **▶ 다음** | 씬카드 부재 예상→Stage1 원본정독부터 |
| 5 | 뉴하트 | ⬜ 대기 | |
| 6 | 내이름은김삼순 | ⬜ 대기 | |
| 7~9 | (대체 3편) | ⬜ 미정 | 10편 채우기용, 소스 가용성 확인 후 선정 |

> 진행 원칙: **1편씩** 순차. 각 편 = Stage1→2→3→verify(ERRORS 0)→로컬저장→허브 push→원격 재검증→토큰 파쇄→메모리 갱신. 슬레이트는 확정지시라 순차진행 인가됨(무단시작 금지 예외).

---

## 5. 집 컴퓨터에서 이어작업 하는 법 (Resume Procedure)

집 환경은 **허브 clone만으로 자급**된다(원본·저작본·게이트·문서 전부 허브에 있음, corpus_ko 불요 — 트랙 B는 원본 정독 기반).

### 5.1 최신 상태 동기화
```bash
git clone https://github.com/limsanghyuk/literary-os.git   # 또는 git pull
# seqcard_ko/authored, authored_seq, authored_arc 확인
```
로컬 `C:\claude\db\seqcard_ko`가 뒤처졌으면 허브 정본으로 sync.

### 5.2 작품 #4 구르미그린달빛 착수 (미생·더킹투하츠와 동일 절차)
1. **원본 확보:** `C:\claude\db\Scripts\` 하위에서 구르미그린달빛 원본 스크립트 탐색. 포맷별 추출(hwp5=olefile+zlib 커스텀 파서, txt/doc/docx/pdf 라우팅). 씬 헤딩 포맷은 **회차마다 다를 수 있으니 파싱 전 패턴 탐지 필수**.
2. **Stage 1:** Sonnet 멀티에이전트(회차당 1) 병렬로 씬카드 저작 → `authored/구르미그린달빛_NN.seqcard.jsonl` + `episode_meta.json`.
3. **Stage 2:** Sonnet 병렬 웨이브로 SequenceBlueprint + EpisodeArc.
4. **Stage 3:** Opus로 FullSeriesArc.
5. **검증:** `verify_work.py 구르미그린달빛` → `ERRORS 0` 필수(자기보고 불신, 디스크 직접검증).
6. **push:** `/tmp` 클론 → `seqcard_ko/`에 파일 복사 → commit → push → 원격 fresh clone 재검증.
7. **정리:** 토큰 shred + temp clone 삭제 + 메모리 갱신.

### 5.3 인증 (허브 push용)
- **쓰기 토큰 = classic PAT** (`키-1072e05f.docx`, `ghp_...`, scopes=repo+workflow). **fine-grained PAT는 read 전용**(push 403).
- 추출 시 `python-docx`가 lxml 버전 문제로 깨질 수 있음 → **zipfile로 `word/document.xml` 직접 파싱**해 `ghp_[A-Za-z0-9]{36,}` 정규식으로 뽑는 방식이 안정적.
- push URL: `https://<TOKEN>@github.com/limsanghyuk/literary-os.git`
- 한글 파일명: `git config core.quotepath false` 설정.
- 토큰은 bash env로만 사용, echo/commit 금지, **사용 직후 shred**.

---

## 6. 검증 게이트 재확인용 스니펫 (verify_work.py는 outputs/에 있음)

핵심 불변식(이걸 통과 못 하면 저작 결함):
- 씬 타일링: 시퀀스들의 `member_scene_nos`가 회차 전 씬을 빈틈·중복 없이 덮음(seq1은 1에서 시작, 마지막은 최종 씬에서 끝).
- `scene_span == [min,max]`, `scene_budget == len(member_scene_nos)`.
- `core_mix`의 각 값은 그 시퀀스 member 씬의 `core`/`core2`에 **실제 등장**해야 함(발명 금지). ← 미생·더킹투하츠 둘 다 여기서 Sonnet 자기보고 위반이 적발돼 prune 교정함.
- `act_structure` 4막이 시퀀스 인덱스를 타일링, `value_shift`는 dict.

---

## 7. 다음 세션 첫 액션

1. 허브 pull → `seqcard_ko` 최신 확인.
2. `C:\claude\db\Scripts`에서 **구르미그린달빛 원본** 가용성·포맷 확인.
3. 가용하면 Stage 1 착수. 불가하면 대체작(뉴하트/내이름은김삼순 등) 소스 확인 후 사용자에게 순서 확인.

*(작성: cowork_opus · 2026-07-05)*
