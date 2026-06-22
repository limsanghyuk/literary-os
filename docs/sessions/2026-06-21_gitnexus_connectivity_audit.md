# 2026-06-21 GitNexus 연결성 전수조사 — 고립/죽은 모듈 17개

literary_system 701 모듈 import 그래프 전수. **상대import 해석 + 심볼/상수 grep 2중 검증**(1차 거짓고립 26→18→실검증 17).

## 방법 (정확도)
- ast import 그래프(절대+상대 `from . / from ..` 해석) → 들어오는 엣지 0 후보.
- 후보별 실제 심볼(class/def) 또는 상수(`*_FIELDS`)가 자기파일 밖에서 참조되는지 grep 교차검증.
- 교정: `finetune.train_local`은 1차 고립이었으나 실측 22참조(연결됨) → 제외. strategies p2/p3/p4는 상대import로 연결 확인.

## ★확정 고립 17 (생산·테스트 어디서도 미참조)

### A. 과거 유산(legacy) 죽은 코드 — 1
- `gates/v587_exit_gate` (209줄): V587 시절 Exit 게이트. 현 V794 → **명백한 leftover**. 삭제 권고.

### B. 미배선 데이터 계약 스텁 — schemas 11
모두 1줄 상수(`*_FIELDS=[...]`), **상수 외부참조 0**:
character_grid · commander_briefing · critic_decision_packet · final_acceptance_packet · format_constitution_packet · intent_seed_packet · literary_state_snapshot · pressure_cast_plan · residue_variation_plan · scene_digest · character_birth_gate_result.
→ 7-pass 생성 패킷 필드 정의지만 packet_compiler/validator/scene_generation_orchestrator 어디서도 미사용. **생성본체 미완 배선의 전방 스캐폴딩**. 연결 or 제거 결정 필요.

### C. 미배선 스텁 — retrieval 3 + adapters 2
- `retrieval/{briefing,relation,scene}_retriever` (각 7~8줄 스텁): RAG 리트리버, HybridRetrieverV2(V589)에 흡수됐을 가능성. 미참조.
- `adapters/project_pipeline`(38) · `adapters/spec_designer`(53): 미배선.

## 판정
- **깨진 코드 아님 — 미사용**. A(유산)는 죽은 leftover, B/C는 *정의됐으나 미연결* 전방 스캐폴딩.
- ⚠️ 개발자 G_CONNECTIVITY(V666 "고립0")가 이 17개를 못 잡음 — V666 이후 추가분이거나 게이트 스코프 차이. **연결성 게이트 재보정 권고**.
- 코드 삭제/배선은 개발자 영역 → 본 문서는 조사 결과·권고만.

## 부기: NKG(서사 신경망)는 별개·정상
코드 연결성(GitNexus)과 별개로, 데이터 측 NKG는 2,339 works·138,588 scene-node·정상(개발자/내 검증). 본 감사는 *코드* 연결성.
