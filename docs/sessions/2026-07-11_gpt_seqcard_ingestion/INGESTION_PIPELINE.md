# GPT SeqCard 산출물 정본 편입 파이프라인

GPT가 저작한 SeqCard 산출물을 `seqcard_ko/` 정본에 **이중 게이트 무손실**로 편입하는 실측 규약. 2026-07-11 4편(결혼못하는남자·101번째프로포즈·공주가돌아왔다·시티헌터) 편입 시 확립.

## 0. 전제
- GPT 산출 스키마 = Claude 정본 스키마 **동일**(벤치마크 채택). 콘텐츠는 무손실 그대로 사용, 배치·발번·값형태만 교정.
- 게이트 통과(ERRORS 0)가 정본 편입의 **유일 기준**. 에이전트 자기보고 불신.
- 무단 push 금지. 편입 스테이징 → 변환 → 이중 게이트 → 정본 복사 순.

## 1. 소스 배치
- 스테이징 소스: `outputs/gpt_eval/<work>/<work>/` (2중 폴더).
- 편입 대상 dir: `authored/`(seqcard + episode_meta + full_series_arc), `authored_seq/`, `authored_arc/`, `authored_edges/`(local_edges + payoff + cross), `authored_chararc/`, `authored_relarc/`.
- **복사 제외**(스키마 밖): `authored_gpt_extended/`, `analysis_extract/`.

## 2. 실측된 실제 결함과 변환 규약 (편마다 상이)
1. **episodearc.turning_point 형태 불일치** = 게이트 크래시. 정본 요구 = `{seq_index:int(1..nseq), desc}`. GPT는 편별로 string / `{scene_no,event}` / `{seq_index,desc}` 혼재.
   → 정규화: string은 첫 `S\d+` 파싱 → member_scene_nos로 seq_index 역매핑, `{scene_no}`는 직접 역매핑, 범위밖은 중앙 시퀀스 폴백. (transform.py `normalize_tp`)
2. **seqblueprint work_id 맨키**(bare key) = SEQ work_id FK FAIL.
   → `{작품}_{NN}` 정규화(episodearc 동반). (transform.py)
3. **브리지 엣지(gap≠0)가 local 파일에 혼입** = 게이트는 통과함(verify_new_layers는 local gap≠0 불금지, cross만 gap≠0 강제). 규약 위생상 cross로 이동(무손실, edge_id 보존). (transform.py `split_bridges`)
4. **`lx` 접두 edge_id** = 게이트 통과(발번 포맷 미검사). 편입엔 무해, 보존.

변환 스크립트(transform.py)는 outputs 스테이징에서 실행. 정본 복사 전 ERRORS 0 확인.

## 3. 이중 게이트 (정본 복사 전·후 모두 ERRORS 0 필수)
허브 게이트 스크립트는 `tools/`에 위치:
- **Stage1/2/3**: `python tools/verify_work.py <work>` — SceneCard(SSOT)·SequenceBlueprint·EpisodeArc·FullSeriesArc 검증.
- **그래프층**: `python tools/verify_new_layers.py <work>` — LocalEdge·PayoffCandidate·CharArc·RelArc·CrossEpisodeEdge 검증. (BASE는 cwd 상대 `seqcard_ko`)

키셋(게이트 강제): SEQ 18 · ARC 13 · FULL 17 · LOCAL_EDGE 12 · CHARARC 8 · RELARC 9 · PAYOFF 7.
불변식: I-COVER · I-PARTITION · I-COUNT · edge_id/candidate_id 전역 유일 · work_id FK = `f"{work}_{ep:02d}"` · placeholder 검사 · anti-gaming(최다반복 text < 15%).

## 4. 시티헌터 완본 교체 (특수 케이스)
구 정본 = 20화 Stage1/2/3만(그래프층 없음, 씬수 GPT와 상이). GPT판 = 20화 완본 + 6계층 그래프(파일럿 유일 브리지0, work_id·turning_point 이미 conformant → 변환 불요).
처리: 구 정본 백업 → 구 Stage1/2/3 제거(원본 대본 보존) → GPT 6계층 복사 → 이중 게이트 ERRORS 0. 구 `_series_arc.json`(구 포맷) 폐기.

## 5. 2026-07-11 편입 실측
| 작품 | 화수 | 씬 | seq | 밀도 |
|---|---|---|---|---|
| 결혼못하는남자 | 16 | 1250 | 189 | 0.151 |
| 101번째프로포즈 | 15 | 1125 | 184 | 0.164 |
| 공주가돌아왔다 | 16 | 1117 | 160 | 0.143 |
| 시티헌터 | 20 | 1356 | 171 | 0.126 |

`by` 필드 = `gpt-5.6-thinking...`로 출처 각인 보존. 4편 모두 이중 게이트 ERRORS 0.
