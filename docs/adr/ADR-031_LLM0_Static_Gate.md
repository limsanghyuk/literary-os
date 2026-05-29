# ADR-031: LLM-0 정적 분석 게이트

Status: Accepted

## 문제
graph_intelligence/ 패키지의 LLM-0 정책 준수 여부를 런타임이 아닌
CI/CD 단계에서 보장하는 장치 부재 (P5).

## 결정
LLM0StaticGate: AST 정적 분석으로 graph_intelligence/ 내
외부 LLM 호출(openai, anthropic, litellm 등) 탐지.
release_gate GATES 목록에 추가.

탐지 대상: import, from-import, 직접 API 호출 패턴.

## 근거
P5 해소. LLM-0 정책 자동 시행 체계 확립.
