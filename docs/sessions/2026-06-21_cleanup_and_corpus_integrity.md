# 세션 핸드오프 — 로컬 정리 + corpus_ko 무결성 검증·복구 (2026-06-21)

**실행자**: Cowork(설계·검증 모드)  |  **대상**: 로컬 `C:\claude`, `C:\Users\...\Documents\Claude\Projects\literary`, `C:\claude\db\corpus_ko`
**성격**: 코드 변경 0. 데이터 위생(housekeeping) + 무결성 실측 + 가역 복구. 허브 코드트리(HEAD 50500ad / V794) 무영향.

---

## 0. 한눈에 (TL;DR)

| # | 작업 | 결과 | 가역성 |
|---|---|---|---|
| 1 | `C:\claude` 루트 정리 | stale/고아 → `_archive/` 이동, 재생성 폐기물만 하드삭제 | 이동=가역 |
| 2 | `Documents\Claude\Projects\literary` 정리 | 3.8G → 696M(약 3.1G 확보). 중복 corpus 삭제(바이트 동일 입증 후) | 버전zip=가역, corpus=불가(중복확인) |
| 3 | `corpus_ko` 구조 무결성 검증 | CLEAN. 2,339 works에서 scenes=chunks=features 정합, 손상 0 | — |
| 4a | ChromaDB 경로 평탄화 | 이중 중첩 → 단일경로. 재오픈 검증 239,768 vec | 가역 |
| 4b | emb_cache 22 orphan npy | "데이터 구멍" 오경보 → 실측으로 **중복**으로 정정, 백업폴더 격리 | 가역(이동) |

---

## 1. 로컬 정리 2건

### 1-1. `C:\claude` 루트
- **삭제 대신 이동** 원칙. `_archive/`에 `literary-os_v599_STALE/`(낡은 사본·작업금지 마커), `V792_delivery/`(정본 zip이 `claude/`로 대체됨, 검증증적 보존), `orphan_scatter/`(레포 내부에 있어야 할 고아 3파일).
- **하드삭제**(재생성 가능 폐기물만): `.pytest_cache/`, `pytest-cache-files-*/`, `out/`(게이트테스트 런타임 산출).
- 근거 문서: `C:\claude\_archive\README_ARCHIVE.md`.

### 1-2. `Documents\Claude\Projects\literary`
- 이 폴더는 메모리상 **"구 분산저장 정정 대상"**. 정본은 `C:\claude`.
- **이동(보관)**: `클로드_old_versions_v308-v571/`(63M), `V792_delivery/`(30M) — 정본은 `C:\claude\claude`에 존재.
- **영구 삭제**: `corpus_ko/`(2.1G) + `corpus_ko.zip`(1.09G). **삭제 전 byte-identity 입증** — `C:\claude\db\corpus_ko`(superset, 더 신규·완전)와 무거운 데이터(txt/scenes/chunks/emb) 바이트 동일 확인, 고유 파일은 SQLite 저널 임시파일 2개뿐.
- **유지(고유 자료)**: `scripts/`(665 고유 원천 대본), `지피티/`(별도 GPT 트랙), `제미나이/`, INDEX/MEMORY/REPORT.
- 결과: 3.8G → 696M. 근거 문서: `..\literary\_archive\README_ARCHIVE_2026-06-21.md`.

---

## 2. corpus_ko 무결성 검증 (실측)

사용자 질의: "무결성 검증하라. 오늘 임베딩·chroma 마무리됐나."

| 지표 | 실측 | 비고 |
|---|---|---|
| 구조 정합 | CLEAN | 2,339 works에서 scenes=chunks=features 일치, 손상 0 |
| 임베딩 커버리지 | 100% | 라이브 청크 238,871 전수 임베딩 (ORPHAN=0) |
| ChromaDB | 완료 | ko_scenes 147,736 + ko_slides 92,032 = **239,768 vec** |
| features motif/curiosity | 전수 충전 | `manifest.json`의 "신규 97편 still 0"은 **stale 기록**(실측 충전됨) |

**판정: 오늘(06-21)의 임베딩·ChromaDB 둘 다 완료.** manifest 일부 필드가 stale이었을 뿐 실데이터는 완비.

---

## 3. 발견 결함 2건 + 처리

### 3a. ChromaDB 경로 이중 중첩 → 평탄화
- **증상**: `chroma_build/`가 `chroma_build/chroma_build/`로 한 단계 더 들어가 실데이터(sqlite 84MB + HNSW data_level0.bin 450MB)가 안쪽에 있고, 바깥엔 0바이트 스텁이 존재 → 기본 경로로 열면 빈 DB.
- **수정**: 실데이터를 한 단계 위로 flatten. chromadb 재오픈 검증 → ko_scenes 147,736 + ko_slides 92,032 = 239,768 vec 정상.

### 3b. emb_cache 22 npy json 결손 — **오경보 정정**(방법론 사례)
- **초기 진단(틀림)**: shard_0291~0312.npy(4,314 vec)가 json 사이드카 없음 → "4,314청크 데이터 구멍"으로 경보.
- **실측 정정**: 전체 청크 id(238,871 uniq) ↔ json 매핑 id(239,768) 대조 →
  - **ORPHAN = 0** (매핑 안 된 라이브 청크 0 = 모든 청크가 이미 임베딩됨)
  - EXTRA = 897 (코퍼스 재빌드로 사라진 청크의 stale 매핑 — RAG 무해 고아 벡터)
  - ChromaDB 239,768 = json 매핑수와 정확히 일치(chroma는 npy+json **쌍**에서만 빌드 → json 없는 22 npy는 애초에 chroma 미포함)
- **결론**: 22 json-less npy는 데이터 구멍이 아니라 **dedup/재빌드 잔여 중복 임베딩**. 커버리지 손실 0.
- **처리(가역)**: 하드삭제 대신 `emb_cache/_orphan_npy_no_json_20260621/`로 격리. 결과 **npy 1,202 ⟷ json 1,202 완전 정합, 미짝 0.**

---

## 4. 적용한 방식(방법론)

1. **실측 우선·미선언**: "마무리됐나" 질의에 manifest 기록을 그대로 믿지 않고 파일 스캔·chromadb 재오픈·id 집합 대조로 직접 입증. manifest stale 필드를 실측으로 기각.
2. **자기 오경보 정정**: 3b처럼 내가 먼저 낸 "데이터 구멍" 경보를 ORPHAN=0 대조로 스스로 반증하고 정정 — 파괴적 조치(재임베딩/삭제) 전 반드시 재검증.
3. **가역 우선(archive-over-delete)**: 판단 항목은 이동/격리, 순수 재생성 폐기물·중복확인 항목만 하드삭제.
4. **샌드박스 제약 회피**: bash 45s 캡 회피 위해 대용량 라인카운트 대신 `find | wc -l`·npy 헤더 파싱으로 벡터수 산출. /sessions 9.8G 한계로 중간 디스크저장 금지 → 단일프로세스 collect+compute 패턴.
5. **누적 반영**: 검증 판정·오경보 정정·평탄화 결과를 메모리(`project_corpus_ko_2031.md`)에 갱신.

---

## 5. 잔여(정직)

- **EXTRA 897 고아 벡터**: ChromaDB/json에 남은, 라이브 청크 없는 stale 매핑. RAG 무해라 이번 범위 제외. 차기 가지치기 후보.
- **`_orphan_npy_no_json_20260621/`**: 격리만 함. 일정 기간 후 안전 확인되면 영구 삭제 가능(현 시점 보존).
- **manifest.json 필드 stale**: "신규 97편 still 0" 등 일부 메타 필드가 실데이터보다 뒤처짐. 데이터 자체는 완비. 차기 manifest 재생성 시 정합화 권고.

---

**무영향 확인**: 본 세션은 로컬 데이터/디렉토리 위생 작업으로 허브 코드(HEAD 50500ad)·테스트·게이트 무변경.
