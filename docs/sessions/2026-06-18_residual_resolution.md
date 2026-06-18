# 잔여 과제 3인 전문가 해결·검토 보고 (2026-06-18)

**질문**: ① features.py·nkg.py 미실행이 문제인가, 해결해 마무리 가능한가 ② 로컬 데이터베이스 구축은 완료되었나 ③ A안이 힘들면 B안(전용 배치 핸드오프)도 검토.

---

## 1. 3인 전문가 진단 (CSA 데이터아키텍트 · CSC 코퍼스과학자 · Principal 엔지니어)

세 잔여 항목을 분리 진단했다. 핵심 = **"무엇이 영구(durable) 산출물이고 무엇이 파생(derived)·재빌드 대상인가"**.

| 항목 | 성격 | 의존 | API/비용 | 결론 |
|---|---|---|---|---|
| **features.py** (SceneFeature) | 파생(재빌드) + features/*.json은 **영구** | scenes + emb_cache | 무(無)·로컬 | **샌드박스 해결 가능** |
| **nkg.py** (캐릭터 그래프) | **영구**(nkg.json, FUSE) | scenes만 | 무·로컬 | **샌드박스 해결 가능** |
| **ChromaDB** (벡터 인덱스) | **파생·휘발(ephemeral)** — 집에서 재빌드 | emb_cache shards | 무·로컬 | 디스크 한계, 88% 실증 |

**합의**: features·nkg는 API·비용 0, scenes/emb_cache만 필요 → 샌드박스에서 즉시 실행 가능. ChromaDB는 sqlite를 FUSE에 못 올려 **본래 집 로컬에서 재빌드하는 파생 인덱스**(메모리 기록과 일치). 따라서 "마무리 가능한가" = **예, features·nkg는 완결. ChromaDB는 집 재빌드가 정상 경로.**

---

## 2. 실행 결과 (해결)

### ✅ nkg.py — 완료 (영구 산출물)
- **2,030작품 · scene_nodes 122,681 · NEXT edges 120,651 · characters 12,660 · char-scene edges 106,894**
- `nkg.json` + `nkg_summary.json` 갱신(FUSE durable). 캐릭터 추출 정상: 올드보이(대수·우진·미도), 마더(혜자·경배), 곡성(종구·이삼) 등.

### ✅ features.py — 완료 (영구 산출물)
- 임베딩 풀로드가 단일 45초 창을 못 넘겨, **작품별 임베딩 버킷(emb_byw/*.npz 425개)을 1회 사전 산출** → 재개형 버스트로 잔여 425작품 완결.
- `features/*.json` **2,030/2,030 완비**(durable). 손상 1건(이죽일놈의사랑_11 0바이트) 재생성.
- `scene_features.db` 재빌드: **122,681 rows / 2,030 works**. 평균 conflict 0.269 / energy 2.919 / motif 0.474 / curiosity 0.341 (정상 분포).

### ◐ ChromaDB — 88% 실증 (휘발·집 재빌드 대상)
- **950/1075 shards · 182,788 vectors**(ko_scenes 113,484 + ko_slides 69,304), **1,732작품 색인**.
- 의미 검증: 대장금 54화·도깨비 16·겨울연가 20·시그널 32·꽃보다남자 21·제빵왕김탁구 30 등 신규 명작 전부 색인 확인.
- 100% 미달 사유 = **샌드박스 /sessions 디스크 9.8G 한계**(잔여 ~125 shard에 ~550M 필요, 가용 380M). ChromaDB는 어차피 FUSE에 영구 저장 불가 → **집 로컬 `store_chroma.py` 1회 재빌드가 정규 경로**. 88%는 "전 코퍼스에서 파이프라인이 작동함"의 충분한 실증.

---

## 3. 로컬 데이터베이스 구축은 완료되었나 — 답변

**영구(durable) 코퍼스 = 100% 완료.** 집에서 그대로 쓰거나 파생물을 1회 재빌드하면 끝.

| 영구 산출물(FUSE) | 상태 |
|---|---|
| scenes/ (씬 JSONL) | **2,030 작품** ✅ |
| chunks (scene+slide) | **209,144** ✅ |
| emb_cache/ (임베딩 shard) | **1,075 npy** = 전 청크 임베딩·검증 ✅ |
| features/ (SceneFeature JSON) | **2,030** ✅ |
| nkg.json (캐릭터 그래프) | **2,030 / 122,681 노드** ✅ |

**파생(집 1회 재빌드)**: ChromaDB(`store_chroma.py`), scene_features.db(`features.py`) — 둘 다 무API·로컬·각 수십 분. sqlite/ChromaDB는 FUSE 쓰기 불가이므로 **설계상 로컬 재빌드가 정상**이며 결함이 아님.

→ **결론: 데이터 구축 본체는 완료. 남은 건 집에서 파생 인덱스 1회 재빌드(자동·무비용)뿐.**

---

## 4. B안(전용 배치 핸드오프) 검토

**B안** = 변환·임베딩을 샌드박스 버스트로 쪼개지 말고, 집 로컬에서 전용 배치 스크립트(`run_all.bat`)로 일괄 처리.

| | A안(샌드박스 점진, 채택) | B안(집 전용 배치) |
|---|---|---|
| 장점 | 즉시 실행·결과 실시간 검증·영구 산출물 이미 확보 | 디스크·시간 제약 없음, ChromaDB 100% 한 번에 |
| 단점 | 45초 창·디스크 9.8G 제약 | 집 PC 필요, 지금 당장 불가 |
| 현 위치 | **영구물 100% 완료** | ChromaDB/features.db 재빌드만 남음 |

**판정**: A안으로 **영구 산출물은 전부 확보**했으므로 B안은 *대체*가 아니라 **마지막 파생 재빌드 단계**로 흡수된다. 집에서 아래 2줄이면 완전체.

```powershell
cd C:\...\corpus_ko
python store_chroma.py    # ChromaDB 1075/1075 재빌드 (무API)
python features.py        # scene_features.db 재빌드 (무API) — 이미 features/*.json 있으면 생략 가능
```

(주의: 메모리 기록대로 Drive corpus_ko.zip은 인코딩 교정 전 stale일 수 있음 → 집 복원 시 교정본 재동기화.)

---

## 5. 한 줄
features·nkg는 **샌드박스에서 완결**(영구 산출물 2,030/2,030), ChromaDB는 **설계상 집 재빌드 대상**(88% 실증). **로컬 DB 구축 본체는 완료**됐고, B안은 별도 대안이 아니라 집에서의 무비용 재빌드 1단계로 수렴한다.
