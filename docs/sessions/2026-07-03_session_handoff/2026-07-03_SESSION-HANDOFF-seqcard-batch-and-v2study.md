# 세션 핸드오프 — SeqCard 오류수정→신규7편저작→v2본연구 (2026-07-03)
_"2>1>3 순서, 저작은 8인 이상 병렬" 지시의 전체 배치 완주 기록. 커밋 84355a17 → 2099be1c (9커밋, 09:07~19:20 KST)._

## 0. TL;DR
오늘 하루 3단계를 순서대로 완료했다: **(2) 기존 데이터 오류 수정 → (1) 신규 7편 SeqCard 저작(22→29작) → (3) SeqCard v2 스키마 본연구**. 코퍼스는 22작/457화/29,873씬에서 **29작/577화/37,166씬**으로 확장됐고, v2 스키마는 hook_flag 필드 하나만 정식 채택이 확정되고 나머지 4개 신규필드는 review-only 또는 재설계 대상으로 판정됐다. 전 과정 독립 재검증(에이전트 자체보고 불신 원칙) + 매 단계 허브 push+원격검증을 거쳤다.

## 1. 오늘의 커밋 타임라인 (origin/main 기준, 시간순)

| 시각(KST) | 커밋 | 내용 |
|---|---|---|
| 11:07 | `84355a17` | ★(2)오류수정: CONFLICT_persist 22작 중 16작 재계산 오류 정정 + 베토벤바이러스 15화 결번 명시 |
| 11:35 | `7806d94f` | 스카이캐슬 23번째 작품, 20화 1353씬 |
| 11:47 | `d8e1a88d` | 추적자 24번째 작품, 16화 884씬 |
| 12:06 | `b3b7a46a` | 스토브리그 25번째 작품, 16화 1003씬 |
| 12:20 | `016bb5ad` | W 26번째 작품, 16화 1220씬 |
| 12:51 | `1815af88` | 시크릿가든 27번째 작품, 20화 888씬 |
| 13:15 | `cc9082fd` | 밀회 28번째 작품, 16화 1144씬 |
| 16:11 | `6a304f2f` | 그들이사는세상 29번째 작품, 16화 801씬 — ★신규 7편 배치 완전 종료 |
| 19:20 | `2099be1c` | ★(3)SeqCard v2 본연구: 6장르 391씬, schema v2.1 검증 |

**참고**: 원래 지시는 "8편"이었으나 꽃보다남자는 원본 검증 과정에서 비공식 팬 요약본(진짜 대본 아님)으로 확인되어 제외 — 실질 7편.

## 2. (2) 오류수정 상세 — `84355a17`
직전 세션(2026-07-02) 독립 재검증에서 발견한 문제 2건을 원본 jsonl 기준 재계산으로 수정:
1. **CONFLICT_persist 광범위 오류**: `_ALL_series_arc.json`에서 22작 중 **16작**이 실제 재계산값과 불일치(8a8ce608 정규화 커밋 때 원인불명 오류로 추정). core 필드만·회차경계 제외라는 일관된 방법론으로 전 작품 재계산. 예: 카인과아벨 0.256→0.184, 시티헌터 0.272→0.171, 하얀거탑 0.383→0.317.
2. **베토벤바이러스 series_arc.json 자체 오류**: conflict_persist=0.071(오기재)→0.313(재계산). 이 0.071이 "군상극은 CONFLICT_persist가 낮다"는 가설의 핵심 근거로 개발자 문서에 인용됐으나, 실제로는 비밀의숲(0.205)보다 **높아 가설과 반대 방향** — 해당 결론 폐기 필요.
3. **베토벤바이러스 15화 결번 명시**: 원본 HWP가 8KB로 본문 없음(Scripts 원본+corpus_ko 양쪽 확인) — 복구 불가, `complete:false`+`missing_episodes:[15]`로 시리즈 arc에 명시.

## 3. (1) 신규 7편 저작 — 파이프라인 (매 작품 동일 반복)
1. **원본 스캔마커 식별**: 작품마다 씬 경계 표기가 상이 — 스카이캐슬="씬N.장소", 추적자="씬N장소"(마침표없음), 스토브리그=마커없음/공백줄구분, W="씬/N장소"(슬래시), 시크릿가든="S#N. 장소/시간"("S#N. 삭제"=스킵), 밀회=마커없음/"장소.시간."(대사와 혼동주의), 그들이사는세상="씬N. 장소".
2. **8~10인 Sonnet 병렬 웨이브** (에피소드당 1에이전트, 회차 전체 아크 맥락 보존): 9필드 고정 스키마(work_id/scene_no/heading/title/intent_gist/core/core2/skin/by) 저작.
3. **독립 bash 검증** (에이전트 자체보고 불신): scene_no 연속성·9필드 null 없음·core/core2 16종 유효값·work_id 일관성·core_dist 합계=scene_count·recompute 정확 일치·NUL바이트 스캔 7항목 자동 스크립트.
4. **발견된 버그마다 즉시 수정** (거의 매 작품에서 최소 1건 발생 — 아래 §5).
5. **series_arc.json 구축**: CONFLICT_persist(회차내부 전이만, core필드만) + episode_top_core_trajectory + scene_transition_grammar_top20.
6. **`_ALL_series_arc.json` 갱신**: 신규 작품 알파벳순 삽입 + totals 재계산(works/episodes/scenes/core_dist 병합 후 재정렬).
7. **허브 push+원격검증**: `/tmp/hubN` 클론(PAT는 uploads의 "키 (1).docx"에서 매 세션 재추출) → `git add -f -A -- seqcard_ko`(docs/sessions는 별도) → 한국어 상세 커밋 → push → `git fetch`+`git show origin/main:<path>`+`json.load`로 실제 반영 확인.

### 최종 코퍼스 상태
| 항목 | 시작(84355a17) | 종료(6a304f2f) |
|---|---|---|
| 작품 수 | 22 | **29** |
| 화 수 | 457 | **577** |
| 씬 수 | 29,873 | **37,166** |

7편 개별 스탯: 스카이캐슬(20화/1353씬/conflict_persist 0.277) · 추적자(16화/884씬/0.224) · 스토브리그(16화/1003씬/0.277) · W(16화/1220씬/0.163) · 시크릿가든(20화/888씬/0.338) · 밀회(16화/1144씬/0.381, 코퍼스 최고치) · 그들이사는세상(16화/801씬/0.337).

## 4. (3) SeqCard v2 본연구 — 파이프라인
1. **대상 선정**: 파일럿(2026-07-02, 싸인_03+베토벤바이러스_01=118씬,2장르)과 겹치지 않는 6개 장르 1화씩(스카이캐슬=사회스릴러, 스토브리그=스포츠경영, 밀회=불륜멜로, 그들이사는세상=가족일일멜로, W=판타지웹툰, 시크릿가든=로코판타지) = **391씬**.
2. **Sonnet 6인 병렬 라벨링**: 기존 v1 SeqCard 씬(heading+intent_gist) 위에 v2.1 신규필드(episode_role 6종/tension_role 4종+앵커정의/hook_flag/continuity_break+broken_thread_id/character_driving_want/scene_blocks_need+need_ref) + 에피소드내부 엣지 레이어(causal/callback/plant_payoff/subplot_counterpoint) 추가.
3. **독립 bash 검증**: 6작품 391씬 전수, scene_no 1:1 대응·범주값 유효성·continuity_break↔broken_thread_id 정합·scene_blocks_need↔need_ref 정합 — 0 errors.
4. **GPT-4.1 블라인드 3-run 교차판정**: `run_full_study.py`(collaborator 핸드오프 스켈레톤) 실행. **기술적 이슈 2건 해결**: (a) OpenAI `response_format:json_object`는 프롬프트에 "json" 리터럴 단어가 반드시 있어야 함(400 에러로 발견, 프롬프트에 문구 추가로 해결), (b) 104씬 대작(밀회)은 gpt-4.1 단일호출이 45초 셸타임아웃을 초과 → 33씬 단위 배치분할 후 병합으로 해결(파일럿 설계서의 사전 경고와 일치).
5. **다수결+합의도 산출** → 클로드 라벨과 필드별 PABAK(불리언)/Cohen's kappa(범주형) 층화 비교, 파일럿 수치와 직접 대조.

### 핵심 결과 (파일럿→본연구 비교)
| 필드 | 파일럿(n=118) | 본연구(n=391) | 판정 |
|---|---|---|---|
| hook_flag | PABAK +0.86 | **+0.91** | ★재현·강화 — 자동게이트 확정 |
| tension_role(앵커개정) | κ +0.37 | **+0.48** | 유일하게 개정이 실효 |
| continuity_break | PABAK +0.53 | +0.41(하락) | 스토브리그 저작에이전트 정의표류(원인규명) |
| episode_role(8→6병합) | κ +0.37 | +0.37(무변화) | ★병합 무효 — GPT 자체 3-run 내부합의도도 0.81로 낮아 근본적 개념모호성으로 재해석 |
| scene_blocks_need(need_ref필수화) | PABAK +0.39 | +0.25(악화) | 재조작화가 오히려 GPT/Claude true비율을 2배→5배로 벌림 |

**최종 판정**: hook_flag만 정식 스키마 편입 확정, tension_role 조건부, 나머지 3필드는 review-only 유지 또는 재설계 대상.

## 5. 이번 배치에서 발견된 버그/이슈 전체 목록 (재발방지용)
1. **`core2: null` 위반** (스카이캐슬 ep4/8) — 규칙 위반 시 core와 동일값으로 수정.
2. **core_dist가 core+core2를 합산** (스토브리그 ep08 등 과거) — core만 집계하도록 모든 프롬프트에 명문화.
3. **원본 trailing NUL 바이트** (추적자 ep03/06, 그들이사는세상 ep03/05 등 다수) — `bytes.replace(b'\x00',b'')` 표준 수정패턴.
4. **bash 마운트 desync**(파일 tools로 정상 저장됐으나 bash가 stale/truncated 버전을 봄) — 그들이사는세상 15화에서 재확인, **Write로 재작성한 후에도 bash `cp`가 옛 버전을 복사하는 신규 변종 발견**. 유일한 해결책: Read 도구 내용을 bash heredoc으로 목적지에 직접 하드코딩(cp 경유 금지).
5. **에이전트의 완전 허위 완료 보고** (밀회 13화) — "완료" 보고에도 파일이 실제로 존재하지 않음. 이후 전 프롬프트에 "저장 후 Read로 재확인" 의무화.
6. **세션 간 `/tmp/hubN` 미지속** — 새 세션/컨테이너에서 이전 클론이 사라짐. 매 세션 시작 시 클론 존재 확인 후 없으면 PAT 재추출부터.
7. **OpenAI `response_format:json_object` 요구사항** — 메시지에 "json" 리터럴 단어 필수(신규 발견, run_full_study.py 패치로 해결).
8. **셸 45초 타임아웃 vs 대작 GPT 판정** — 104씬 단일 API 호출이 타임아웃 초과 → 33씬 배치분할+병합.
9. **저작 에이전트의 필드 정의 표류** (스토브리그 continuity_break=true 91%, 타작품 14~28%와 크게 이탈) — 멀티에이전트 병렬 라벨링의 구조적 위험으로 실측 확인.

## 6. 최종 검증 (전부 완료)
- 7편 저작: 각 작품 push 직후 `git fetch origin main` + `git show origin/main:<path>` + `json.load`로 원격 내용이 로컬과 바이트 단위 일치함을 확인(6회 반복).
- `_ALL_series_arc.json` 최종: `{"works":29,"episodes":577,"scenes":37166}` — 원격에서 직접 재확인 완료.
- v2 본연구: 6작품 391씬 newfields/edges 파일 0 errors 독립검증 + majority.jsonl/contested.jsonl 원격 push 확인(25개 파일, `2099be1c`).
- 본 핸드오프 문서 자체도 §8에서 재검증(아래).

## 7. 다음 단계 (미결정, 개발자 판단 대기)
- continuity_break 지표 회복을 위해 스토브리그_01 재라벨(개별 에이전트 정의표류 QA) 후 5작품 재계산.
- episode_role은 병합으로 해결 안 됨 확인 — tension_role에 효과있었던 "예시 기반 앵커 정의" 방식을 episode_role에도 시도할지 결정 필요.
- scene_blocks_need는 review-only를 넘어 폐기 여부 결정 필요.
- 엣지 레이어(causal/callback/plant_payoff/subplot_counterpoint, 6작품 243개)는 이번에도 교차판정 미실시 — 다음 라운드 과제.
- 코퍼스 확장(목표 30작+) 지속 여부, 또는 v2 확정 필드(hook_flag)만 전체 29작 소급 라벨링 착수 여부.

## 7-1. 회사 컴퓨터 이어작업 — 실행 가능한 체크리스트 (재현 검증 완료)
v2 본연구에 쓴 도구 5종을 `docs/sessions/2026-07-03_seqcard_v2_full_study/tools/`에 **이번에 신규로 push**했다(원래 파일럿 스크립트 `run_full_study.py`는 실행 시 OpenAI 400에러가 나는 미수정 버그가 있었음 — 아래 §7-2). 전부 스모크테스트로 end-to-end 동작 검증 완료.

- [ ] **환경 준비**: uploads의 "키 (1).docx"에서 `OPENAI_API_KEY`(gpt 키) 재추출(세션 휘발) → `export OPENAI_API_KEY=...`
- [ ] **1단계(Claude 라벨링 확장)**: 아직 라벨링 안 한 작품/화에 새 v2.1 필드 추가하려면, 이번 세션 6개 에이전트 프롬프트(`docs/sessions/2026-07-03_seqcard_v2_full_study/2026-07-03_SeqCard-v2_본연구_결과.md` §부록 참고, 원문 프롬프트는 이번 대화 로그) 패턴 그대로 `{work}.newfields.jsonl` + `{work}.edges.jsonl` 생성.
- [ ] **2단계(GPT 판정)**: `tools/run_one.py <work> <work>.seqcard.jsonl <run_idx 1|2|3> gpt-4.1` 을 run_idx=1,2,3 각각 실행(파일당 30~40초, 여러 작품은 `&`+`wait`로 병렬화 가능). **씬 100개 이상 대작은 셸 45초 제한에 걸리므로 `tools/batch_judge.py <work> <path> <run_idx> gpt-4.1 <start> <end>` 로 33씬 단위 분할 후 `tools/merge_batches.py <work> <run_idx> <start1>