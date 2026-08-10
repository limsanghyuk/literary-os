# 후판 재저작 지시 (LOS-THICK-REAUTHOR-AGENT-BRIEF v1.0, 2026-08-10)

## 0. 왜 하는가
한국 드라마 후판(thick_sequence) 11작을 깊이 기준 `다양도@813 >= 0.748` 로 측정했더니
5작이 미달했다. 원인은 문장력이 아니라 **저작 방식**이다. 아래 4종 중 하나에 걸려 있다.

- F1 골격 충전: 문장 뼈대를 고정해 놓고 씬 표제로 빈칸만 채움
- F2 상위필드 복사: `event` 문장을 `cast`/`plant_payoff` 가 그대로 되받음
- F3 표제 나열: `event` 가 씬 표제를 ", 이어 / 마지막으로" 로 이은 목록
- F4 정형 꼬리: 진짜 내용 뒤에 기능 라벨 상투구를 붙임

기계적 상투구 제거로는 회복되지 않는다는 것이 실측되었다(강남 0.594→0.619).
**원문을 읽고 6개 필드를 새로 쓰는 것 외에 방법이 없다.**

## 1. 절대 규칙
1. **좌표는 한 글자도 건드리지 않는다.** 바꾸는 것은 오직 6개 내용 필드다:
   `event` · `cast[].desire_or_function` · `info_shift[].before` · `info_shift[].after`
   · `plant_payoff[].statement` · `scene_notes[].functional_propositions`
2. **배열 길이와 순서는 고정.** cast N명이면 문장 N개, 순서 그대로. 명제는 **씬별 개수가 정확히 일치**해야 한다(늘려도 줄여도 병합 거부).
3. **원문에 없는 사실을 쓰지 않는다.** 패킷의 `scenes[].text` 가 유일한 근거다.
4. 파일 생성은 **반드시 bash heredoc**(`cat > ... <<'PYEOF'` + python json.dump)으로 한다.
   Write/Edit 툴은 `C:\claude\...` 경로에서 조용히 잘린다.
5. 씬 표제(장소명)를 인용하지 않는다. "이어", "마지막으로", "~하게 된다는 사실이 확정된다" 같은
   기능 라벨 상투구를 쓰지 않는다.

## 2. 정답 형태 (기준작 = 경성스캔들 / 본보기 = 강남엄마따라잡기_01)
- `event` (4~5문장): 이 시퀀스에서 **무엇이 무엇을 일으켰는지**를 인과로 쓴다.
  씬 나열이 아니라, 앞 사건이 뒷 사건의 조건이 되는 사슬로 쓴다.
  마지막 문장은 이 시퀀스가 무엇을 남기고 닫히는지로 끝낸다.
- `cast[].desire_or_function` (1문장): **"…하려 하지만 …때문에 …된다"**.
  욕망 + 좌절이 한 문장 안에 있어야 한다. "그는 주인공이다" 같은 역할 상수 서두 금지.
  event 문장을 복사하거나 이름만 붙여 되받으면 실패(F2)다.
  **cast 를 쓸 때는 event 를 보지 말고, 그 인물이 이 시퀀스에서 원한 것부터 다시 생각한다.**
- `info_shift[].before`: "아직 모르는 상태다" 같은 상투구가 아니라
  **그 인물이 실제로 믿고 있던 명제**를 쓴다. after 는 그 믿음이 무엇으로 바뀌었는지.
  before 와 after 가 같은 문장이면 실패다.
- `plant_payoff[].statement`: 심어지거나 회수되는 **내용 자체**. thread_id 를 풀어쓴 말이 아니다.
- `scene_notes[].functional_propositions`: **다른 씬으로 옮기면 거짓이 되는 문장**만 쓴다.
  "이 씬은 인물을 소개한다" 는 어느 씬에나 참이므로 실패다.
  "민주가 자기 양육의 근거로 내미는 것이 상장과 대회 출전이라는 점에서, 이미 그녀도 상대의 기준을 쓰고 있다" 는 그 씬에서만 참이다.

## 3. 저작 순서 강제
`event` → `info_shift` → `cast` → `plant_payoff` → `scene_notes`
(cast 를 event 다음에 바로 쓰면 반드시 복사가 된다. 정보 이동을 먼저 정리하고 나서 인물로 간다.)

## 4. 작업 절차 (회차 1개 기준)
```
BASE=/sessions/compassionate-eager-lovelace/mnt/claude
```
1. 패킷 읽기: `$BASE/rework/<작품>/packets/<작품>_<NN>.thick_sequence.packet.json`
   - `sequences[]` 각 원소: `seq_id`, `characters`(cast 순서), `info_subjects`/`info_modes`,
     `plant`(kind/thread_id), `scenes[]`(scene_no, n_props, text=원문 슬라이스)
   - **원문 전체를 읽는다.** 요약만 보고 쓰면 반드시 상투구가 나온다.
2. authored JSON 작성:
   `$BASE/rework/authored/<작품>_<NN>.partN.json`
   (한 파일에 시퀀스 2~3개씩 나눠 담아도 되고 파일명 partN 은 자유. merge 가 glob 로 모은다.)
   형식:
```json
{"<seq_id>": {
  "event": "...",
  "cast": ["<characters[0] 문장>", "<characters[1] 문장>", ...],
  "info_before": ["..."], "info_after": ["..."],
  "plant": ["..."],
  "props": {"<scene_no>": ["...", "..."], ...}
}}
```
   `info_shift`/`plant` 가 0개면 `[]`. props 의 리스트 길이 = 그 씬의 `n_props`.
3. 병합: `python3 $BASE/rework/merge.py <작품> <NN>`  → ERRORS 나면 고쳐서 재실행
4. 채점: `python3 $BASE/rework/check_ep.py <작품> <NN>`
   - **주판정 다양도@813 >= 0.748 이 나올 때까지 고쳐 쓴다.** 이것만이 합격 조건이다.
   - 보조 FLAG 는 어디가 얕은지 알려주는 힌트일 뿐 합격을 바꾸지 않는다.
     단 `cast재기술%` 나 `명제표제인용%` 에 FLAG 가 뜨면 F2/F3 를 저지른 것이니 그 필드는 다시 쓴다.
     `회수보유%` FLAG 는 회차 단위로는 정상이다(작품 전체에서만 회수되므로) — 무시한다.

## 5. 본보기
`$BASE/rework/authored/강남엄마따라잡기_01.part1~5.json` 과
`$BASE/rework/강남엄마따라잡기/out/강남엄마따라잡기_01.thick_sequence.jsonl` 을 먼저 열어 볼 것.
같은 회차 원본은 0.558(FLAG 6항), 재저작본은 **0.779(FLAG 1항)** 이다.

## 6. 보고
회차별로 `<작품>_<NN>: 다양도 0.XXX 합격/불합격, FLAG n항` 한 줄씩. 200자 이내로 마무리.
합격시키지 못한 회차가 있으면 숨기지 말고 그대로 보고한다.
