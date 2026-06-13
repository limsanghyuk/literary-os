# 공식 성분 재정의 결과 (③, 2026-06-13)

FE-7에서 역상관이던 energy/motif/climax를 재정의·재검정.

## 성분별 vs (전문가+관객) Kendall τ (n=62)
| 성분 | τ | 판정 |
|---|---|---|
| conflict_mean (기존) | +0.16 | ✅ 핵심 신호 유지 |
| conflict_arc (기존) | +0.17 | ✅ 최강 신호 유지 |
| o_energy (기존) | −0.15 | ❌ 역신호 |
| e_scenelen / e_dialogue / e_energyvar / e_conf_escalation (energy 재정의) | +0.03/+0.03/−0.01/0.00 | △ 중립화(해는 제거, 양신호 없음) |
| m_callback / m_callback_late (motif 재정의) | −0.06/−0.04 | △ 약함 |
| m_coherence (주제 균일도) | −0.137 | → **반전 활용** |
| **thematic_complexity = 1−coherence** | **+0.137** | ✅ **신규 양신호** |

## 재정의 fitness (conflict_mean + conflict_arc + thematic_complexity + curiosity)
| 방식 | concordance |
|---|---|
| 등가중 | 0.587 |
| 적합(in-sample) | 0.594 |
| LOO-CV | 0.586 |

(이전 6성분 음가중 모델 0.640 대비 약간 낮으나, 본 모델은 전부 양신호·등가중≈CV로 **과적합 거의 없고 해석 가능**.)

## 결론 (정직)
1. **강건한 양신호는 conflict(밀도+동역학)와 thematic_complexity 뿐.** energy/motif는 재정의해도 양신호 안 됨 → fitness에서 제거 또는 중립화.
2. **DRSE 잔향은 임베딩 유사 기반으론 작동 안 함**(callback τ≈−0.05) → 모티프 사전/엔티티 재등장 기반으로 근본 재설계 필요(다음 과제).
3. **결정적 함의**: 씬통계 기반 공식의 명성 일치 천장 ≈ 0.6 < **패널 0.73**. → 공식은 *값싼 baseline*, **패널이 고정밀 보상신호**. 자가 학습 루프는 둘을 하이브리드로(공식=1차 sanity, 패널=교정 보상).

## fitness v2 권고
fitness_v2 = w1·conflict_mean + w2·conflict_arc + w3·thematic_complexity + w4·curiosity (energy/motif/climax 제외). 보상은 패널 쌍대로 캘리브레이션.
