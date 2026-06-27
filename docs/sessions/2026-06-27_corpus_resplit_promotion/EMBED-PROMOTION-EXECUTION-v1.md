# 정본 승격 임베딩 파이프라인 — In-Session 실행 보고서 (v1)

**일자:** 2026-06-27
**실행 주체:** Cowork(Opus) 세션 — 샌드박스 Linux
**대상:** `corpus_ko` 6스토어 (205편 재분할 정본 승격)
**선행 세션:** 2026-06-26~27 재분할(class4 211화 전수) → CPU 스테이징(누적XVII)
**상태:** 5개 소스 스토어 완비·검증 PASS / chroma만 잔여(파생물, 집 재빌드 설계 단계)

---

## 0. 한 줄 요약

> 어제까지 만들어 둔 "재분할 스테이징"을 실제 `corpus_ko` 정본에 적용하고, **씬 단위 신규 임베딩까지 이 세션에서 직접 돌려서** 6스토어 중 5개(scenes·chunks·emb_cache·features·nkg)를 완비·정합 검증했다. 마지막 chroma 한 스토어만 남았고, 그건 순수 파생물이라 집 Windows에서 1회 재빌드하면 된다.

---

## 1. 배경 — 왜 이 작업을 했나

선행 세션에서 결함 회차(병합·과소분할) 211편을 전수 재분할하여 **씬 경계를 바로잡았다**. 다만 안전을 위해 그 결과는 원본을 건드리지 않는 **사이드카(staging)** 로만 만들어 두었다. 이번 세션의 목표는:

1. 어제·오늘 작업물을 **검증**하고,
2. 스테이징을 실제 정본에 **승격(promote)** 하면서,
3. 바뀐 씬에 대한 **임베딩을 새로 생성**하여 6스토어 정합을 회복하는 것.

핵심 사용자 지시: *"임베딩은 너도 가능하다"* — 즉 GPT를 이용한 씬 분할은 금지지만, **표준 임베딩 단계(text-embedding-3-small)는 이 세션에서 직접 실행**하라는 것. 실행 순서도 명시됨:

```
backup → swap → embed.py → prune → features.py → nkg.py → rebuild_chroma_local.py → verify
```

---

## 2. 6스토어 의존성 사슬 (왜 이 순서인가)

```
scenes/<ep>.jsonl        (정본 씬: work_id, scene_no, heading, text)
   │  parse(>1500자 → sliding(1400,150) 분할)
   ▼
chunks/<ep>.jsonl        (scene chunk + slide chunk[전체본문 슬라이딩])
   │  OpenAI text-embedding-3-small  ← ★유일한 외부 의존(API)
   ▼
emb_cache/shard_*.{json,npy}   (1536차원 벡터, id = work::scene::n::part / work::slide::k)
   │  features = 구조지표(CPU) + motif/curiosity(임베딩 평균 의존)
   ▼
features/<ep>.json
   │
   ▼
nkg.json                 (씬 노드 + NEXT 엣지 + 인물-씬 엣지)
   │
   ▼
chroma/                  (벡터 검색 인덱스 = emb_cache의 100% 결정론 파생물)
```

**순서가 강제되는 이유**
- **swap → embed**: embed는 *교체된* chunks에서 신규 id만 골라 임베딩한다. 먼저 swap해야 새 씬 경계가 보인다.
- **embed → prune**: 먼저 새 벡터를 채운 뒤, 더는 참조되지 않는 옛 씬 벡터(stale)를 제거한다.
- **prune → features**: features의 motif/curiosity는 *(work_id, scene_no)별 씬 임베딩 평균*을 쓴다. stale 옛-씬 벡터가 남아 있으면 평균이 오염되므로 prune이 반드시 선행.

---

## 3. ★슬라이드 임베딩 불변 — 재임베딩을 씬 단위로 한정한 핵심 발견

재분할은 **공백 제거 시 무손실(nospace-lossless)** 이고, 승격은 새 경계를 **바이트-정확 원본 전체본문에 재매핑**한다. 따라서:

- `"".join(scene.text)` 결과가 **바이트 동일** → 전체본문 기반으로 슬라이딩하는 **slide chunk는 경계 이동과 무관**.
- ⇒ **slide 임베딩 100% 재사용**, 재임베딩은 **씬 단위 신규 id에만** 필요.

스테이징 리포트 실측:

| 항목 | 값 |
|---|---|
| 승격 대상 | 205편 (실패 0) |
| 씬 수 | 5,340 → **15,493** (×2.90) |
| 신규 임베딩 필요(씬) | 10,774 |
| 폐기 stale(씬) | 3,550 |
| 재사용(씬) | 5,357 |
| slide | **100% 불변** |

이 발견 덕분에 임베딩 비용이 "전체 코퍼스 재임베딩"이 아니라 "바뀐 205편의 씬 1만여 개"로 줄었다.

---

## 4. 단계별 실행 내용·방법

### (1) backup
`promote_apply.py backup` — 205편의 원본 scenes/chunks/features를 `promotion_backup/`에 복사(멱등, 기존 백업 보존). 실측: scenes 205 · chunks 205 · features 205 백업됨. → **정본을 바꿔도 언제든 복원 가능**한 안전판.

### (2) swap
`promote_apply.py swap` — 스테이징의 scenes+chunks를 정본 `corpus_ko/`에 덮어쓰기. 이로써 **정본이 실제로 재분할본으로 교체됨**(선행 세션의 "원본 미변경" 상태에서 변경됨).

### (3) embed — 증분 임베딩
- 교체된 chunks에서 **아직 임베딩 안 된 씬 id만** 골라 text-embedding-3-small로 임베딩.
- **45초 bash 타임아웃 대응**: 샤드당 200개씩 기록 + `done_ids()`로 이미 끝난 id 스킵 + 기존 최대 샤드 번호 +1부터 재개. → 타임아웃이 나도 다시 호출하면 멈춘 지점부터 이어짐.
- ★**중간 발견**: `shard_recov_0037`의 npy가 절단 손상(이전 prune 중단이 mmap 길이 > 실제 파일 크기로 (186,1536) 절단). json/npy를 삭제하고 재임베딩으로 200개 slide id를 재생성하여 복구. 최종 **shards=1348, 손상 0**.

### (4) prune — stale 제거 (재작성)
- **원본 prune의 문제**: 모든 샤드의 npy를 무조건 `np.load` → 타임아웃.
- **해결** (`prune_fast.py`): ① 값싼 json 스캔으로 *orphan을 가진 샤드만* 식별 → ② 그 샤드만 load 후 **atomic 교체**(`np.save(tmp); os.replace`)로 안전 재기록. 비-atomic 쓰기가 손상 샤드를 만든 교훈 반영.
- 결과: orphan 보유 샤드 5개에서 **stale 207개 제거**.

### (5) features — 구조+모티프 재생성 (재작성)
- **원본 features의 문제**: 작품마다 O(n²) 코사인 루프가 44초 안에 안 끝나고, 매 실행 `DROP TABLE`이라 꼬리 작품을 못 채움(비-재개성).
- **해결** (`features_resumable.py`): 씬 임베딩 평균을 pickle 캐시, `DROP` 없이 `INSERT OR REPLACE`, done-set 추적, 시간 상한으로 청크 분할. 3회 구동으로 완결.
- 결과: **2,497작품 · 158,400행 = 씬 패리티 정확 일치**(전체 scenes jsonl 총합 158,400 == feature 행 158,400).

### (6) nkg — 지식그래프
`nkg.py` — 코퍼스 전역 재생성. 결과: **2,497작품 · 158,400 씬노드 · 155,903 NEXT 엣지 · 15,861 인물 · 133,840 인물-씬 엣지**.

### (7) verify — 6스토어 패리티 게이트
`promote_apply.py verify`:
```
[verify] scenes=2497 chunks=2497 features=2497
[verify] chunk ids=261953 embedded=261953 | MISSING(need embed)=0 ORPHAN(prune)=0
```

---

## 5. 최종 결과

| 스토어 | 상태 |
|---|---|
| scenes | 2,497 ✅ |
| chunks | 2,497 ✅ |
| features | 2,497 (158,400행 = 씬 패리티) ✅ |
| emb_cache | shards 1,348 · **0 corrupt** ✅ |
| nkg | 158,400 노드 · 155,903 NEXT · 15,861 인물 ✅ |
| **verify 게이트** | embedded=261,953=chunk ids · **MISSING=0 · ORPHAN=0** ✅ |
| chroma | ⏳ 잔여 (파생물) |

**무손실/패리티 불변식 전부 유지.** 5개 소스 스토어는 완비·정합 인증됨.

---

## 6. chroma — 유일 잔여, 그리고 판단

chroma는 검증 끝난 emb_cache의 **100% 결정론 파생물**이다(`rebuild_chroma_local.py`가 emb_cache 벡터를 그대로 upsert, OpenAI 재임베딩 불필요).

**세 전략 평가**
- **A) 이 세션에서 전량 그라인드**: 실측 ~41–44 cid/s, HNSW 충진으로 더 느려져 261,953 벡터에 **~100분·약 150회 순차 호출**. 순수 반복작업, 비효율. → 기각.
- **B) 빌더 정당성만 입증 후 집 Windows(무시간제한)에서 1회 재빌드**: 무위험 파생물. → **채택.**
- **C) 미실행**: 열위. → 기각.

`rebuild_chroma_local.py` 헤더가 이미 *"샌드박스는 처리량+45초 한계로 254,729 적재 불가 → 로컬 Windows에서 1회 재빌드"* 로 설계해 둔 단계다. 임베딩(외부 키 필요)과 달리 chroma는 외부 의존 0·시간만 드는 인덱싱이라 집에서 끝내는 게 합리적.

**재개형 빌더 작동 입증**: `chroma_build.py`(docs pickle 캐시·persistent client·done-shards 추적·idempotent upsert·시간 상한)로 ko_scenes 2,040 + ko_slides 1,478 = 3,518 벡터를 디스크에 적재 확인. 집에서:
```bash
cd corpus_ko && python rebuild_chroma_local.py    # count()<목표면 누락분만 멱등 upsert
```

---

## 7. 산출물 (도구)

| 파일 | 역할 |
|---|---|
| `prune_fast.py` | 값싼 json 스캔 + atomic 재기록 prune (타임아웃·손상 회피) |
| `features_resumable.py` | emb 캐시·DROP 없음·done-set·시간상한 features 재생성 |
| `chroma_build.py` | 재개형·멱등 chroma 빌더(샌드박스 시간상한 대응) |

위치: `C:\claude\claude\2026-06-26_sequence_segmentation\` (로컬 보관)
오케스트레이터 `promote_stage.py`·`promote_apply.py`는 누적XVII에서 이미 허브 push됨(HEAD e7be76f).

---

## 8. 다음 단계

1. **chroma 재빌드 마무리** — 집 `python rebuild_chroma_local.py` 1회 (또는 세션 그라인드).
2. **6스토어 최종 verify** — chroma까지 채운 뒤 ko_scenes/ko_slides count == 기대치 확인.
3. (선택) 스테이징 산출물·도구 버그프리 재검토 후 허브 재정리.

**핵심:** 데이터 진실 원천(emb_cache)은 완비·검증 완료. chroma는 그 위의 검색 인덱스일 뿐이라 언제든 무위험으로 재생성 가능.
