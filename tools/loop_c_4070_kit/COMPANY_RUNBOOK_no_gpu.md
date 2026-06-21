# 회사(GPU 없음) 이어작업 런북 — SP-E.10 통합 누적 루프 준비

회사 환경=GPU 없음. **코드/통합/생성은 가능, 학습 실행만 집 4070 필요.** 작업 분리:

## A. 회사에서 가능 (GPU 불요)
1. **P0 생성기 이식**: `gen_p3.py`(show/tell)·`gen_p2.py`(구체vs평이) 로직을 `literary_system/learning/pairing/strategies/{p3,p2}.py`(현 스텁)에 구현. P1=critic_qualification.degrade(CAUSALITY) 재사용. (API 키 필요, GPU 불요)
2. **선호쌍 생성·게이팅**: 생성기→`learning/pairing/build()`(길이매칭 tokΔ≤5%·E4·work-level split held≥250). 토큰정확트림으로 100% 매칭.
3. **누적 루프 코드**: `loopc_closure.run_round`에 어댑터 체이닝(직전 어댑터 is_trainable 로드→DPO→adopt/rollback) 배선. **코드만**(실행은 집).
4. **완전 c3 R_struct 배선**: T3 7-pass 출력 씬을 `structural_nonregression(before,after)`에 연결.
5. ChromaDB 재빌드(`store_chroma.py`, CPU)·분석·문서. ※emb_cache 필요(집 로컬).

## B. 집(4070)에서만 (GPU 필요)
- 누적 루프 **실행**(라운드별 DPO 학습+per-token 측정): `train_4070_p0.py` 참조. 각 ~10-25분.
- c3 R_path 생성 측정: `c3_check.py` 참조.
- → 회사서 코드 작성 → 집서 실행 → 결과 허브. 왕복 구조.

## C. 집→회사 가져갈 것 (허브에 없는 로컬 데이터)
- **필수 아님**(순수 코드작업이면): 허브 pull로 충분.
- **생성기 테스트/ChromaDB 하려면**: `db/corpus_ko`(코퍼스)·`emb_cache`(1.3G) 복사.
- 참고용: `rounds_ledger.jsonl`(7라운드 수치, 단 허브 문서에 있음). 어댑터(lora_*)는 집 실행물.

## 참조 코드 (본 폴더)
- GPU-free: gen_p3.py, gen_p2.py, make_pairs.py
- GPU(집): train_4070_p0.py(per-token+KL+ledger), c3_check.py(R_path), RUN_ACCUMULATE.bat(독립5라운드)
- 검증 표준 I1~I5: per-token전용·길이매칭·verbatim0·작품분리·토크나이저잠금
