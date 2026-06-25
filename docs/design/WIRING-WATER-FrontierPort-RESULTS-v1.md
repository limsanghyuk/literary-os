# 물 흘리기 — GenerativePort 실생성 좌석 + FrontierPort 스모크 (v1, 2026-06-24)

상태: **물 흘림 PASS(FrontierPort)** / LLM1Port=집 4070 대기. 선행: WIRING-ORCHESTRATOR-POC-RESULTS-v1.
산출: `examples/generative_ports.py`(FrontierPort+LLM1Port), `examples/wiring_poc_water.py`.

## 0. 한 줄
배관 PoC(템플릿)에 **실제 생성 좌석**을 끼워, FrontierPort(gpt-4o-mini)로 **진짜 한국어 대본 산문**을 12기관 배관에 흘려보냈다. "수도관에 물이 흐른다"를 처음 실증.

## 1. 무엇을 했나 (논리 1~3 대응)
- **계약 불변 교체**: `GenerativePort.generate(prompt,*,episode_idx)` 그대로. `FormulaFallbackPort` → `FrontierPort`(API, 가용) / `LLM1Port`(집 4070, 졸업 8B+lora_v3). 내부만 교체(논리 3).
- **문맥 보강**: 화 루프 프롬프트에 로그라인·인물·K·갈등압력(이전화 누적)·payoff·직전화 요약 주입(`wiring_poc_water.py`). 로그라인은 Synopsis Assembler(③·빈칸) 자리 = 현재 수동 시드.
- **품질 지표 하니스**: 길이·한글비율·대사줄·템플릿여부.

## 2. FrontierPort 스모크 결과 (추적자 3화, 이 세션 실행)
- 1화 689자 / 2화 561자 … **실제 대본체 산문 생성**(지문+대사), 로그라인·인물 정합(한지수·박도현·윤·정, "정의의 경계 의심" 주제 반영).
- **갈등압력 피드백 생존**: cp_in이 화마다 텐서에서 갱신되어 프롬프트에 주입됨(N→N+1 채널이 산문 생성까지 연결).
- 지표 캐비엇: dialogue_lines=0으로 잡혔으나 이는 출력이 `**이름**` 볼드 헤더라 `이름:` 정규식이 못 잡은 것(산문엔 대사 다수). → 지표 정규식 보강 필요.

## 3. 정직한 경계
- **이건 LLM-1 품질 기준선이 아니다.** Frontier(gpt-4o-mini)는 좌석·물흐름 증명용 프록시. **논리 1의 진짜 ①(졸업한 8B의 한국 드라마 산문 품질)은 LLM1Port를 집 4070에서 돌려야** 측정된다.
- 품질 측정축은 BROAD-MEASUREMENT의 A(거시일관성)+B(다축 craft)로 확장 필요(현재 하니스는 표면지표만).
- 로그라인 수동 = ③ Synopsis Assembler 미구현 자리.

## 4. 집 RTX 4070 런북 — LLM1Port 실행(=진짜 ①)
```
cd C:\claude  (literary-os 클론 위치)
set PYTHONPATH=%CD%
REM 졸업 어댑터 확인: C:\claude\4070_oneclick\lora_v3_5
python examples\wiring_poc_water.py llm1 3
```
- 의존: torch+cu124·transformers·peft·bitsandbytes(졸업 환경 그대로). 4bit 로드.
- 산출: 3화 실 산문 + 지표. 이걸 **명작 코퍼스 동일 회차와 쌍대(5축 critic)로 비교**하면 LLM-1 산문의 첫 품질 신호.
- 다음: S9~S15 어댑터 배선(계약 불변) → Synopsis Assembler(logline 자동).
