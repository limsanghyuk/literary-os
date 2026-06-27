# 정본 승격(Canonical Promotion) 핸드오프 — 205편 재분할 → corpus_ko

작성: 2026-06-27 (Cowork/Opus). 대상: 집(GPU/API) 실행자.
선행: class4 그라인드 종료(203 적용)+c3(2)=205 적용, 8 처분 → 결함 213 전수완결, 무손실위반 0.

---

## 1. 한 줄 요약

재분할된 205편을 corpus_ko 정본으로 승격하는 전 과정 중 **CPU로 가능한 모든 단계를
무손실·패리티 검증까지 끝내 STAGING에 적재**했다. 남은 단 하나의 게이트는 **임베딩
(OpenAI text-embedding-3-small)** 으로, 역할분담상 집/API 단계다. corpus_ko 정본은
이 세션에서 **일절 건드리지 않았다**(무결성 인증 보존).

## 2. 6-스토어 의존성 사슬 (실측)

```
scenes/<ep>.jsonl   --(A)-- canonical {work_id,scene_no,heading,text,method}
   |                          <- 재분할 경계 적용. CPU. [DONE] STAGING
chunks/<ep>.jsonl   --(B)-- 씬 chunk: len>1500 -> sliding(1400,150) part 분할
   |                          + slide chunk: 전체본문 sliding(1000,200)
   |                          <- parse.py 로직 그대로 복제. CPU. [DONE] STAGING
emb_cache/shard_*   --(C)-- id `{wid}::scene::{no}::{part}` / `{wid}::slide::{n}`
   |                          ★게이트: text-embedding-3-small (OpenAI). 집/API.
features/<ep>.json  --(D)-- 구조피처(CPU) + motif/curiosity(임베딩 의존)
   |                          <- (C) 이후. features.py.
nkg.json            --(E)-- 코퍼스 전역. CPU. nkg.py.
chroma              --(F)-- 벡터스토어. CPU. rebuild_chroma_local.py.
```

### 핵심 발견 — slide 임베딩은 불변
재분할은 **nospace-무손실**일 뿐 아니라, 승격 스테이징은 재분할 경계를 **바이트-정확
원본 전체본문에 재매핑**하므로 `"".join(scene.text)` 가 **바이트 단위로 원본과 동일**하다.
slide chunk는 전체본문을 char-offset 슬라이딩으로 자르므로 **경계 이동의 영향을 받지
않는다 -> slide 임베딩은 전량 그대로 재사용**. 재임베딩은 **씬 단위 신규 id에만** 필요.

## 3. STAGING 실측 결과 (CPU, 무손실 검증 통과)

| 항목 | 값 |
|---|---|
| 승격 대상 | 205편 |
| 씬 수 | 5,340 -> **15,493** (x2.90) |
| 재임베딩 필요(신규 씬 chunk) | **10,774** |
| 폐기 대상(stale 씬 id) | **3,550** |
| 재사용(불변 씬 id) | 5,357 |
| slide 임베딩 | **100% 불변** (전체본문 바이트동일) |
| 최대 씬 nospace | 7,921 (베를린=검증완료 genuine-long 클라이맥스) |

검증 게이트 (205/205 PASS, 실패 0):
- 스테이징 씬수 == 재분할 씬수(공백전용 fragment 제거 후)
- 스테이징 전체본문 == 원본 전체본문 **바이트 동일**
- scene_no 1..N 연속
- 공백전용 씬 0
- chunk scene_no ⊆ scene scene_no, 전 씬 chunk 커버

## 4. 집 실행 절차 (순서 엄수)

```bash
cd <WD>/2026-06-26_sequence_segmentation
# 전제: corpus_ko 경로 확인(스크립트 상단 CORP), /tmp/oai.key 배치
python3 promote_apply.py backup    # 1. 205편 scenes/chunks/features 원본 백업(멱등)
python3 promote_apply.py swap      # 2. STAGING scenes+chunks -> corpus_ko 복사
python3 embed.py                   # 3. 증분 임베딩(신규 씬 id만 자동 선별; slide 스킵)
python3 promote_apply.py prune     # 4. stale 씬 id를 emb_cache 샤드에서 제거
python3 features.py                # 5. 구조+motif/curiosity 재생성(신규 임베딩 사용)
python3 nkg.py                     # 6. 전역 지식그래프
python3 rebuild_chroma_local.py    # 7. 벡터스토어 재빌드
python3 promote_apply.py verify    # 8. 6-스토어 패리티(MISSING=0, ORPHAN=0 확인)
```

롤백: `promotion_backup/` 의 scenes/chunks/features 를 corpus_ko 로 되돌리면 원상복구.

## 5. 안전·정합 주의

- **반드시 swap -> embed 순서.** embed.py는 swap된 chunks를 읽어 신규 id를 선별하므로
  반대로 하면 신규 chunk가 없어 아무것도 안 함.
- verify가 MISSING>0 이면 embed 미완. ORPHAN>0 이면 prune 미실행.
- 이 절차는 corpus_ko 무결성 인증을 **재임베딩 완료 시점에 복원**한다. 그 전까지는
  스테이징만 존재하므로 정본은 안전.
- 처분 8편(우리생애최고의순간 healthy / 우아한세계·스카이캐슬_01 set-aside /
  신사의품격×4·선덕여왕_00 skip)은 승격 대상 아님.

## 6. 산출물 (이 세션)

- `promote_stage.py` — STAGING 빌더(재매핑+chunk재생성, 무손실 게이트 내장)
- `promote_apply.py` — 집 적용 오케스트레이터(backup/swap/prune/verify)
- `promotion_staging/{scenes,chunks}/*.jsonl` — 205편 정본 후보 + report
- `PROMOTION-HANDOFF-v1.md` — 본 문서
