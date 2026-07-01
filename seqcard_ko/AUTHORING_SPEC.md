# SeqCard 저작 스펙 (의도층 / Track B)

## 출력: 회차당 두 파일
1. `<work>_<NN>.seqcard.jsonl` — 씬 1줄 = JSON 1레코드, 9필드:
   {work_id, scene_no(int,1부터), heading(원본 마커행 trim; 마커 없으면 장소행), title(소제목 6~18자),
    intent_gist(이 씬이 '무슨 일을 하는가'=기능/의도, 줄거리 요약 금지, 본문 근거 기반),
    core(필수, 16기능 중 1), core2(보조 1개 또는 null — null 허용 유일 필드),
    skin(장르 외피 한 구절), by:"sonnet_reading"}
2. `<work>_<NN>.episode_meta.json`:
   {work_id, scene_count(int), core_dist(코어별 카운트 dict), episode_function(시리즈 내 이 회차 역할 한국어 한 문장), by:"sonnet_reading"}

## 16기능 택소노미 (core/core2는 반드시 이 중 하나, 대문자)
ESTABLISH(설정) ORACLE(암시/복선) INTRO(첫등장) BOND(유대) CONFLICT(갈등) REVERSAL(반전)
LOSS(상실/죽음) PUNISH(응징) REVELATION(폭로/진상) REUNION(재회) RELIEF(이완/유머)
ROMANCE(로맨스) PERIL(위기) RESCUE(구출/해결) DESIRE(욕망/야심) HOOK(클리프행어)
※ 씬이 16기능에 안 맞으면 가장 가까운 기능 선택. REVEAL/REWARD 등 비표준 라벨 금지.

## 씬 경계
- 번호 마커(`N.`,`씬N`,`S#N` 등) 있으면 그 줄이 씬 시작. heading=그 줄.
- 마커 없는 회차(프로즈형): 장소/시간 전환으로 씬 분리. heading=장소행.
- OMIT/결번 마커는 레코드 만들지 않음. authored 레코드수 = 실제 씬수.

## 원칙
- intent_gist는 줄거리("누가 무엇을 했다")가 아니라 기능("이 씬이 서사에서 하는 일").
- 전수 저작: 누락 씬 없이 1번부터 끝까지. null은 core2만 허용.
