# 비밀의숲 ep01 SourceSceneAlignmentRecord — 구축 방법론 및 결과

- 목적: GPT의 EXT6 교차검토 문제4("원본 76블록 ↔ SceneCard 72씬 사이 정렬 원장이 없다")를 해소하는 공식 증빙 원장.
- 산출: `seqcard_ko/_ext6_audit/비밀의숲_01.source_scene_alignment.jsonl` (72행, SceneCard 72씬 전수 커버)
- 원본: `seqcard_ko/original_extracted/비밀의숲_01~16.txt` (사용자 제공 원본 `.hwp` 16화 전량을 이번에 직접 파싱해 신규 추출·저장)

## 구축 절차

1. **원본 재추출**: 사용자가 제공한 `비밀의숲.zip`(16화 `.hwp`, cp949 파일명)을 olefile+zlib 기반 HWP5 BodyText 파서(`hwp_extract.py`, 신규 작성)로 직접 파싱해 16화 전체를 평문 추출. `seqcard_ko/original_extracted/`에 저장(기존 컨벤션 `{work}_{NN}.txt`을 따름, 다른 40여 작품과 동일 포맷).
2. **소스 블록 확보**: `corpus_ko/chunks/비밀의숲_01.jsonl`에 이미 존재하던 헤딩 기반 원문 파싱 결과(79개 레코드, `scene_no`+`heading`+`text` 필드) — 이 79개가 SceneCard 72씬의 실제 소스 근거(evidence 텍스트)와 축자 일치함을 확인(예: `무성母(놀라 우뚝 멈춘다...) 왜, 왜요?!` 대사가 Claude EXT6 CastPresence의 evidence_ref와 정확히 일치).
3. **정렬 알고리즘**: `difflib.SequenceMatcher`로 79개 corpus 헤딩 시퀀스와 72개 SceneCard 헤딩 시퀀스를 순서보존 정렬(LCS 기반). 72건은 헤딩 완전일치 1:1 자동 정렬(`VERIFIED_AUTOMATED`). 나머지 7건(5개 클러스터)은 정렬 알고리즘이 "delete"(대응 없음)로 표시 → 원문 내용을 직접 대조해 인접 SceneCard 씬으로 병합 배정(`VERIFIED_MANUAL_REVIEWED`, 근거를 `alignment_note`에 기록).
4. **원본 대조 검증**: 79개 source_block 전량의 heading 텍스트를 방금 재추출한 원본(`original_extracted/비밀의숲_01.txt`)에서 검색해 문자 오프셋(start/end)을 확보 — **79/79 전량 위치 확인 성공**. 이는 (a) corpus_ko/chunks가 실제 원본에서 파생됐다는 것과 (b) 방금 재추출한 원본이 기존 corpus_ko와 동일 소스임을 이중으로 교차검증한다.
5. **해시 기록**: 각 source_block의 corpus 텍스트에 대해 SHA256을 계산해 `source_hashes`에 기록(향후 변조·재현성 검증용).

## 병합 클러스터 5건 (내용 근거)

| SceneCard 씬 | 병합된 corpus 원본 블록 | 근거 |
|---|---|---|
| 8 (동/안방. 낮) | 8, 9, 10 | 회상(서부지검 주차장/시목의 차안)과 현재(무성의 집 거실) 인서트 2블록이 뒤따르는 안방 장면에 흡수 |
| 33 (동/집무실. 낮) | 35, 35(중복) | corpus_ko 원본 데이터 자체에 동일 scene_no(35)로 중복 채번된 청크 2개 존재 — SceneCard가 이를 하나로 정리 |
| 46 (서부지검/시목의 검사실. 밤) | 48, 48(중복) | 상동 |
| 53 (동/407호 법정. 낮) | 55, 55(중복) | 상동 |
| 56 (동/주차장. 낮) | 58, 59, 60 | 25년전 회상(시목의 집/방)과 현재(서부지검 주차장) 인서트가 뒤따르는 주차장 장면에 흡수 |

## 발견된 데이터 품질 이슈 (투명하게 기록)

- `corpus_ko/chunks/비밀의숲_01.jsonl`에 **scene_no 35, 48, 55가 각각 2회씩 중복 채번**되어 있음(원본 파싱 단계의 기존 결함, 이번 조사로 처음 발견). 콘텐츠 자체는 유효하나 번호 체계에 결함이 있어 `by_scene_no` 딕셔너리 방식으로 단순 조회하면 앞쪽 레코드가 유실될 위험이 있었음 — 리스트 인덱스 기반 재처리로 수정해 실제로는 79개 레코드 전량이 정렬에 반영됨.
- `hwp_extract.py`의 원본 재추출은 완벽하지 않음 — 일부 인라인 서식 제어문자(하이퍼링크·필드 마커 등 확장 컨트롤)가 완전히 걸러지지 않아 드물게 깨진 문자(예: `Ҙ`, `݈`)가 섞임. 핵심 대사·지문 텍스트 자체는 훼손되지 않았으나, 완벽한 조판 재현이 필요하면 후속 정제가 필요함.

## 검증 결과 요약

```
SceneCard 72씬 전수 커버: 72/72 (누락 0)
자동 1:1 정렬: 67건
수동 검토 병합: 5건 (7개 corpus 블록 흡수)
원본(재추출 hwp) 오프셋 매칭: 79/79
```
