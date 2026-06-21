# 2026-06-21 한국드라마03 egg/alz 6편 데이터화 (corpus 2,242→2,339)

개발자 V793 편입(zip 14편→212 works) 후 **미편입으로 남았던 egg/alz 6편**(샌드박스 압축해제 도구 부재로 pending_home_env 등록분)을 데이터화. 사용자가 egg/alz를 폴더로 압축해제 → Claude가 변환·파싱·편입.

## 대상 (미추가 6편 = pending_home_env egg/alz 전부)
구해줘 · 달이뜨는강 · 데릴남편오작두 · 스위치 · 우아한가(.Egg) · 바람의화원(.alz)

## 처리 (기존 파이프라인 동일)
1. **변환**: hwp→hwp5txt(pyhwp), txt→cp949/utf-16 인코딩추정, pdf→pdftotext. 회차ID 정규식 `(\d+)[부회화]` + 작품명 정규화 + 중복회차는 최대길이 채택.
2. **파싱**: parse.py `build_scenes()`/`sliding()` **로직 그대로**(num/slug/fallback_block) → scenes/chunks(scene청크 + kind:slide 전문). 기존 2,242 비파괴, parse_stats 병합.
3. **NKG**: nkg.py 전체 재빌드(모델 불요) → 2,339 works.
4. **features(어휘)**: features.py feats() 그대로 → motif/curiosity=0(임베딩 의존, 집에서).

## 실측 결과
- **신규 97편 / 4,251 scenes** (구해줘16·달이뜨는강12·데릴남편오작두23·바람의화원16·스위치16·우아한가14).
- 파싱 방법: num 30 / slug 34 / fallback_block 33. 씬/편 min/med/max 5/39/129.
- 무결성: 97편 scenes+chunks+features 전수 존재·JSONL 정상 **이슈 0**. 기존 2,242 work_id와 중복 0.
- NKG 재빌드: 2,339 works · scene-nodes 138,588 · NEXT 136,249 · chars 14,385 · char-scene 120,175. 샘플(올드보이/마더/곡성) 정상.
- manifest works 2,242→**2,339**, last_increment 갱신.

## 캐비엇 / 집 로컬 잔여 (pending_home_env)
- fallback_block 33편(스위치·우아한가 등 슬러그/recap 헤딩)은 scene 분절 거침 — 단 **slide 청크로 전문 보존, 임베딩/RAG 손실 0**(기존 2,030과 동일 parse.py 기준).
- **신규 97편: 임베딩 + ChromaDB 재빌드 + features motif/curiosity 풀런 필요**(embed_par.py→store_chroma.py→features.py, OpenAI 키). 개발자 212편과 함께 1회 집 풀런으로 마무리.
- 데이터 원칙: 본 문서 verbatim 0(편수·통계만). corpus 원문은 로컬 전용.
