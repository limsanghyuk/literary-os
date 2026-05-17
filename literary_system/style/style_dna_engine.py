"""
V313→V322: StyleDNAEngine — 독립 문체 엔진
V312 authorial_habit(3개)에서 컴파일 가능한 계층으로 승격.
15개 장르 프로파일 + 사용자 커스텀 지원.
LLM 0회.
"""
from __future__ import annotations
from typing import Any

_PROFILES: dict[str, dict[str, Any]] = {
    # ── 절제 계열 ──────────────────────────────────────────
    "restrained_low_burn": {
        "description": "저온 연소 절제형. 한국 느와르/가족극 기본",
        "pdi_baseline": 0.33,
        "dialogue_compression": 0.72,
        "cadence": "mixed_short_mid",
        "metaphor_density": "low",
        "pov_stability": "high",
        "closure_style": "resonant_not_declarative",
        "forbidden": ["결국", "마치", "그는 슬펐다", "배신의 공기",
                      "그제야", "이상하게도", "어쩌면"],
        "preferred": ["gesture_before_emotion", "object_before_confession",
                      "silence_as_pressure"],
    },
    "cold_observational": {
        "description": "냉정 관찰형. 다큐멘터리/사회비판극",
        "pdi_baseline": 0.28,
        "dialogue_compression": 0.80,
        "cadence": "mid_long_flat",
        "metaphor_density": "very_low",
        "pov_stability": "very_high",
        "closure_style": "accumulative_resonance",
        "forbidden": ["감동적인", "눈물", "용기"],
        "preferred": ["fact_before_feeling", "institutional_detail", "ironic_distance"],
    },
    "minimalist_realism": {
        "description": "최소주의 리얼리즘. 일상 압력형",
        "pdi_baseline": 0.38,
        "dialogue_compression": 0.65,
        "cadence": "short_declarative",
        "metaphor_density": "minimal",
        "pov_stability": "high",
        "closure_style": "open_ending",
        "forbidden": ["결말처럼", "해결됐다"],
        "preferred": ["everyday_gesture", "incomplete_action", "residue_in_ordinary"],
    },
    # ── 압력 계열 ──────────────────────────────────────────
    "thriller_pressure": {
        "description": "단문 타격형 서스펜스",
        "pdi_baseline": 0.30,
        "dialogue_compression": 0.85,
        "cadence": "short_punchy",
        "metaphor_density": "minimal",
        "pov_stability": "high",
        "closure_style": "structural_suspense",
        "forbidden": ["안도", "해결", "평화"],
        "preferred": ["action_before_thought", "truncated_dialogue", "body_sensation"],
    },
    "slow_burn_escalation": {
        "description": "느린 압력 상승형. 긴 호흡 서스펜스",
        "pdi_baseline": 0.31,
        "dialogue_compression": 0.70,
        "cadence": "long_to_short_acceleration",
        "metaphor_density": "low",
        "pov_stability": "high",
        "closure_style": "unresolved_pressure",
        "forbidden": ["갑자기", "충격적으로"],
        "preferred": ["incremental_detail", "environmental_pressure", "delayed_reveal"],
    },
    # ── 감성 계열 ──────────────────────────────────────────
    "warm_humanist": {
        "description": "따뜻한 인간주의. 가족/생활극",
        "pdi_baseline": 0.42,
        "dialogue_compression": 0.55,
        "cadence": "natural_conversational",
        "metaphor_density": "medium",
        "pov_stability": "medium",
        "closure_style": "gentle_resolution",
        "forbidden": ["AI_generic_emotion"],
        "preferred": ["small_kindness", "habitual_gesture", "mundane_miracle"],
    },
    "melodramatic_peak": {
        "description": "절정형 멜로드라마",
        "pdi_baseline": 0.45,
        "dialogue_compression": 0.50,
        "cadence": "emotional_crescendo",
        "metaphor_density": "medium",
        "pov_stability": "medium",
        "closure_style": "cathartic_peak",
        "forbidden": ["cheap_cliffhanger"],
        "preferred": ["peak_emotion_with_object", "confession_scene", "reversal"],
    },
    # ── 복합/실험 계열 ────────────────────────────────────
    "ironic_detachment": {
        "description": "아이러니 거리두기. 블랙코미디/사회풍자",
        "pdi_baseline": 0.35,
        "dialogue_compression": 0.68,
        "cadence": "flat_with_sudden_cut",
        "metaphor_density": "low",
        "pov_stability": "high",
        "closure_style": "ironic_non_resolution",
        "forbidden": ["감동", "희망적인"],
        "preferred": ["understatement", "deadpan_observation", "systemic_irony"],
    },
    "documentary_observational": {
        "description": "다큐멘터리 관찰형",
        "pdi_baseline": 0.27,
        "dialogue_compression": 0.78,
        "cadence": "mid_long",
        "metaphor_density": "very_low",
        "pov_stability": "very_high",
        "closure_style": "accumulative_resonance",
        "forbidden": ["dramatic_declaration"],
        "preferred": ["contextual_repeat", "institutional_language"],
    },
    "lyrical_introspective": {
        "description": "서정적 내면 탐구형",
        "pdi_baseline": 0.40,
        "dialogue_compression": 0.60,
        "cadence": "flowing_variable",
        "metaphor_density": "medium_high",
        "pov_stability": "medium",
        "closure_style": "lyrical_open",
        "forbidden": ["action_thriller_pace"],
        "preferred": ["interior_monologue", "sensory_detail", "temporal_shift"],
    },
    "political_cold": {
        "description": "정치 냉정형. 권력 드라마",
        "pdi_baseline": 0.29,
        "dialogue_compression": 0.82,
        "cadence": "clipped_formal",
        "metaphor_density": "minimal",
        "pov_stability": "very_high",
        "closure_style": "power_equilibrium_shift",
        "forbidden": ["personal_confession", "emotional_outburst"],
        "preferred": ["institutional_language", "indirect_threat", "silence_as_power"],
    },
    "legal_procedural": {
        "description": "법정 절차형",
        "pdi_baseline": 0.31,
        "dialogue_compression": 0.75,
        "cadence": "question_answer_rhythm",
        "metaphor_density": "low",
        "pov_stability": "high",
        "closure_style": "verdict_with_doubt",
        "forbidden": ["deus_ex_machina"],
        "preferred": ["procedural_detail", "witness_contradiction", "evidence_object"],
    },
    "medical_clinical": {
        "description": "의학 임상형",
        "pdi_baseline": 0.32,
        "dialogue_compression": 0.76,
        "cadence": "technical_rhythm",
        "metaphor_density": "low",
        "pov_stability": "high",
        "closure_style": "clinical_with_human_cost",
        "forbidden": ["miracle_cure"],
        "preferred": ["bodily_detail", "technical_language", "patient_object"],
    },
    "corporate_strategic": {
        "description": "기업 전략형",
        "pdi_baseline": 0.33,
        "dialogue_compression": 0.78,
        "cadence": "boardroom_rhythm",
        "metaphor_density": "low",
        "pov_stability": "high",
        "closure_style": "strategic_shift",
        "forbidden": ["personal_revenge_obvious"],
        "preferred": ["boardroom_subtext", "numbers_as_pressure", "alliance_shift"],
    },
    "noir_existential": {
        "description": "실존주의 느와르",
        "pdi_baseline": 0.28,
        "dialogue_compression": 0.80,
        "cadence": "fatalistic_rhythm",
        "metaphor_density": "low",
        "pov_stability": "high",
        "closure_style": "tragic_inevitability",
        "forbidden": ["happy_resolution", "coincidence_rescue"],
        "preferred": ["moral_ambiguity", "rain_and_shadow", "no_exit_situation"],
    },
}

# 장르 → 프로파일 매핑
_GENRE_TO_PROFILE: dict[str, str] = {
    "political_thriller": "political_cold",
    "noir_crime":         "noir_existential",
    "revenge_drama":      "slow_burn_escalation",
    "family_melodrama":   "warm_humanist",
    "romance_drama":      "melodramatic_peak",
    "thriller_suspense":  "thriller_pressure",
    "historical_drama":   "restrained_low_burn",
    "medical_drama":      "medical_clinical",
    "legal_drama":        "legal_procedural",
    "corporate_drama":    "corporate_strategic",
    "documentary":        "documentary_observational",
    "general_drama":      "restrained_low_burn",
}


class StyleDNAEngine:
    """
    장르/톤 → StyleDNAPacket 컴파일.
    15개 프로파일 + 사용자 커스텀 merge 지원.
    """

    def compile(
        self,
        genre: str,
        tone_keywords: list[str] | None = None,
        custom_overrides: dict | None = None,
        project_id: str = "",
    ) -> dict[str, Any]:
        profile_name = _GENRE_TO_PROFILE.get(genre, "restrained_low_burn")
        base = dict(_PROFILES[profile_name])

        # 톤 보정
        if tone_keywords:
            if "melancholic" in tone_keywords and base["pdi_baseline"] > 0.36:
                base["pdi_baseline"] = max(0.30, base["pdi_baseline"] - 0.04)
            if "pressure" in tone_keywords:
                base["dialogue_compression"] = min(0.88, base["dialogue_compression"] + 0.05)

        # 커스텀 override
        if custom_overrides:
            base.update(custom_overrides)

        return {
            "project_id":    project_id,
            "profile_name":  profile_name,
            "genre":         genre,
            **base,
        }

    def validate(self, text: str, dna: dict[str, Any]) -> dict[str, Any]:
        """생성된 텍스트가 StyleDNA를 위반했는지 로컬 검사."""
        violations = []
        for kw in dna.get("forbidden", []):
            if kw in text:
                violations.append({"type": "forbidden_phrase", "keyword": kw})

        # PDI 근사 검사
        emotion_words = {"슬펐다", "기뻤다", "두려웠다", "느꼈다", "깨달았다"}
        action_words  = {"걷", "쥐", "놓", "멈", "바라", "삼키"}
        words = text.split()
        emo_cnt = sum(1 for w in words if any(e in w for e in emotion_words))
        act_cnt = sum(1 for w in words if any(a in w for a in action_words))
        total = max(emo_cnt + act_cnt, 1)
        pdi_actual = act_cnt / total
        pdi_target = dna.get("pdi_baseline", 0.35)
        if pdi_actual < pdi_target - 0.10:
            violations.append({"type": "pdi_below_target",
                                "actual": round(pdi_actual, 2),
                                "target": pdi_target})

        return {
            "violations": violations,
            "passed": len(violations) == 0,
            "violation_count": len(violations),
        }

    def list_profiles(self) -> list[str]:
        return list(_PROFILES.keys())
