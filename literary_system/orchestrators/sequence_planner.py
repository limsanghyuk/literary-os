"""
V325 - SequencePlanner  (Phase 3 → Rev.2)
MacroArc → 에피소드 시퀀스·씬 동적 연산.

【3인 검토 후 재설계 — CPE 확정 스펙】
  구 설계의 3가지 모순 해결:
    1. 장르 하드코딩 → 서사 파라미터 동적 연산으로 교체
    2. scenes_per_seq=15 고정 → 시퀀스 타입 × 긴장도 기반 산출
    3. 사인커브 분배 → 감정호(SequenceType) 기반 씬 밀도 결정

  동적 연산 원리:
    시퀀스 수 = runtime_min ÷ 시퀀스평균지속시간(11min)
               × 막계수 × 압력계수 × 플롯밀도계수
               → clamp [3, 8]

    씬    수 = seq_duration_min ÷ 씬평균지속시간(seq_type, tension)
               → clamp [2, 8]

  실측 한국 드라마 기준:
    - 1화 60~70분
    - 1화 18~35씬 (평균 씬 길이 2~4분)
    - 1화 3~8시퀀스 (시퀀스당 3~7씬)

  LLM 0회 — 완전 로컬
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any


# ────────────────────────────────────────────────────────────────
# 에피소드 포맷별 러닝타임 (분)
# ────────────────────────────────────────────────────────────────

EPISODE_RUNTIME: dict[str, int] = {
    "miniseries": 70,   # 70분 미니시리즈
    "standard":   65,   # 65분 일반 드라마
    "weekend":    60,   # 60분 주말극
    "special":    90,   # 90분 특별편
}
DEFAULT_RUNTIME = 65    # 분

AVG_SEQUENCE_DURATION_MIN = 11.0   # 시퀀스 평균 지속시간(분) — 실측 근거


# ────────────────────────────────────────────────────────────────
# 시퀀스 타입 (감정호 유형)
# ────────────────────────────────────────────────────────────────

class SequenceType(str, Enum):
    SETUP_HOOK     = "setup_hook"      # 오프닝 훅 — 회 시작, 갈고리
    PLOT_ADVANCE   = "plot_advance"    # 플롯 전진 — 일반 전개
    CONFLICT_PEAK  = "conflict_peak"   # 갈등 정점 — 대립 고조
    EMOTIONAL_BEAT = "emotional_beat"  # 감정 비트 — 내면·관계 씬
    TURNING_POINT  = "turning_point"   # 전환점 — 사건 역전
    CLIFFHANGER    = "cliffhanger"     # 클리프행어 — 회 마지막 충격
    RESOLUTION     = "resolution"      # 해소 — 긴장 풀기·여운


# 시퀀스 타입별 씬 평균 지속시간 (분)
# 긴장도 높을수록 씬이 짧아지는 기준값
SEQ_TYPE_BASE_SCENE_DUR: dict[SequenceType, float] = {
    SequenceType.SETUP_HOOK:     3.5,
    SequenceType.PLOT_ADVANCE:   3.0,
    SequenceType.CONFLICT_PEAK:  2.5,
    SequenceType.EMOTIONAL_BEAT: 4.0,
    SequenceType.TURNING_POINT:  2.0,
    SequenceType.CLIFFHANGER:    2.5,
    SequenceType.RESOLUTION:     3.5,
}

# 시퀀스 타입별 지속시간 범위 (min, max 분)
SEQ_TYPE_DURATION_RANGE: dict[SequenceType, tuple[float, float]] = {
    SequenceType.SETUP_HOOK:     (8.0,  12.0),
    SequenceType.PLOT_ADVANCE:   (10.0, 15.0),
    SequenceType.CONFLICT_PEAK:  (8.0,  13.0),
    SequenceType.EMOTIONAL_BEAT: (8.0,  14.0),
    SequenceType.TURNING_POINT:  (6.0,  10.0),
    SequenceType.CLIFFHANGER:    (5.0,   8.0),
    SequenceType.RESOLUTION:     (5.0,   9.0),
}

# 막(幕)별 시퀀스 구성 템플릿
# 각 막의 특성에 맞는 감정호 순서 패턴
ACT_SEQ_PATTERNS: dict[int, list[SequenceType]] = {
    1: [  # 기(起) — 세계 도입, 인물 등장
        SequenceType.SETUP_HOOK,
        SequenceType.PLOT_ADVANCE,
        SequenceType.EMOTIONAL_BEAT,
        SequenceType.CLIFFHANGER,
    ],
    2: [  # 승(承) — 갈등 전개, 관계 복잡화
        SequenceType.PLOT_ADVANCE,
        SequenceType.CONFLICT_PEAK,
        SequenceType.EMOTIONAL_BEAT,
        SequenceType.CONFLICT_PEAK,
        SequenceType.PLOT_ADVANCE,
        SequenceType.CLIFFHANGER,
    ],
    3: [  # 전(轉) — 위기 절정, 반전
        SequenceType.CONFLICT_PEAK,
        SequenceType.TURNING_POINT,
        SequenceType.CONFLICT_PEAK,
        SequenceType.EMOTIONAL_BEAT,
        SequenceType.CLIFFHANGER,
    ],
    4: [  # 결(結) — 해소, 여운
        SequenceType.RESOLUTION,
        SequenceType.EMOTIONAL_BEAT,
        SequenceType.CLIFFHANGER,
    ],
}

# 막별 시퀀스 수 계수 (압력·러닝타임 기반값에 곱함)
ACT_SEQ_MODIFIERS: dict[int, float] = {
    1: 0.85,   # 기: 소수 시퀀스 (세계관 설명 중심)
    2: 1.20,   # 승: 다수 시퀀스 (플롯 밀도 최대)
    3: 1.00,   # 전: 표준 (품질 집중)
    4: 0.70,   # 결: 소수 시퀀스 (압축 마무리)
}

# 서사 목표 문자열 (시퀀스 타입 + 막 기반)
SEQ_TYPE_GOALS: dict[SequenceType, list[str]] = {
    SequenceType.SETUP_HOOK:     ["오프닝 훅", "세계 진입", "인물 첫인상"],
    SequenceType.PLOT_ADVANCE:   ["플롯 전진", "관계 심화", "단서 제시", "장애물 등장"],
    SequenceType.CONFLICT_PEAK:  ["갈등 정점", "대립 격화", "위기 고조", "충돌"],
    SequenceType.EMOTIONAL_BEAT: ["감정 비트", "내면 토로", "관계 재정의", "기억 회상"],
    SequenceType.TURNING_POINT:  ["전환점", "반전 폭로", "결정적 선택", "판세 역전"],
    SequenceType.CLIFFHANGER:    ["클리프행어", "충격 엔딩", "다음 화 갈고리"],
    SequenceType.RESOLUTION:     ["해소와 여운", "감정 정리", "관계 회복"],
}


# ────────────────────────────────────────────────────────────────
# SequencePlan 데이터클래스
# ────────────────────────────────────────────────────────────────

@dataclass
class SequencePlan:
    """단일 시퀀스 계획 (Rev.2 — seq_type·duration_min 추가)."""
    seq_id:        str
    episode_no:    int
    seq_index:     int
    goal:          str
    tension_target: float
    scene_count:   int
    act_index:     int
    pct_start:     float
    pct_end:       float
    seq_type:      str   = SequenceType.PLOT_ADVANCE.value   # 신규
    duration_min:  float = 11.0                               # 신규: 예상 지속시간(분)

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq_id":         self.seq_id,
            "episode_no":     self.episode_no,
            "seq_index":      self.seq_index,
            "goal":           self.goal,
            "tension_target": round(self.tension_target, 4),
            "scene_count":    self.scene_count,
            "act_index":      self.act_index,
            "pct_start":      round(self.pct_start, 4),
            "pct_end":        round(self.pct_end, 4),
            "seq_type":       self.seq_type,
            "duration_min":   round(self.duration_min, 2),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SequencePlan":
        # 하위 호환: 신규 필드 없으면 기본값 사용
        return cls(
            seq_id        = d["seq_id"],
            episode_no    = d["episode_no"],
            seq_index     = d["seq_index"],
            goal          = d["goal"],
            tension_target= d["tension_target"],
            scene_count   = d["scene_count"],
            act_index     = d["act_index"],
            pct_start     = d["pct_start"],
            pct_end       = d["pct_end"],
            seq_type      = d.get("seq_type", SequenceType.PLOT_ADVANCE.value),
            duration_min  = d.get("duration_min", AVG_SEQUENCE_DURATION_MIN),
        )


# ────────────────────────────────────────────────────────────────
# SequencePlanner
# ────────────────────────────────────────────────────────────────

class SequencePlanner:
    """
    MacroArcCompiler 출력 → 에피소드별 시퀀스·씬 동적 산출.

    시퀀스 수와 씬 수를 모두 서사 파라미터로부터 연산.
    LLM 0회, 완전 로컬.

    사용 예:
        planner = SequencePlanner(format_type="standard")
        seqs = planner.plan(
            macro_arc_packet,
            episode_no=3,
            active_plot_lines=3,
        )
        # → 시퀀스 4~6개, 화당 씬 합계 20~30개 (현실적 범위)
    """

    def __init__(
        self,
        format_type:    str = "standard",    # miniseries / standard / weekend / special
        genre:          str = "drama",        # 참고용 (연산에 직접 개입 안 함)
        # 하위 호환: 구 파라미터 허용 (무시됨)
        seq_count:      int | None = None,
        scenes_per_seq: int | None = None,
    ) -> None:
        self.format_type     = format_type
        self.genre           = genre
        self._runtime_min    = EPISODE_RUNTIME.get(format_type, DEFAULT_RUNTIME)
        # 구 파라미터는 보존만 (연산에 미사용)
        self._legacy_seq_count      = seq_count
        self._legacy_scenes_per_seq = scenes_per_seq

    # ── 공개 API ─────────────────────────────────────────────────

    @property
    def runtime_min(self) -> int:
        return self._runtime_min

    def plan(
        self,
        macro_arc_packet:   dict[str, Any],
        episode_no:         int = 1,
        active_plot_lines:  int = 2,     # 활성 플롯 라인 수 (주·부·대척 등)
        episode_runtime_min: int | None = None,  # None이면 format_type 기준
    ) -> list[SequencePlan]:
        """
        MacroArc 패킷 → 시퀀스 목록 동적 생성.

        Args:
            macro_arc_packet:   MacroArcCompiler 출력 dict
            episode_no:         에피소드 번호 (1-based)
            active_plot_lines:  병렬 플롯 라인 수 (2=표준, 3=복잡, 1=단순)
            episode_runtime_min: 에피소드 러닝타임(분). None이면 format_type 사용.

        Returns:
            List[SequencePlan]  길이 = 동적 결정 [3, 8]
        """
        runtime    = episode_runtime_min or self._runtime_min
        act_idx    = self._resolve_act_index(macro_arc_packet, episode_no)
        pressure   = self._episode_pressure(macro_arc_packet, episode_no)

        # ① 시퀀스 수 동적 산출
        n          = self._calc_seq_count(runtime, act_idx, pressure, active_plot_lines)

        # ② 시퀀스 타입 배정 (막별 감정호 패턴 기반)
        seq_types  = self._assign_seq_types(n, act_idx)

        # ③ 시퀀스별 지속시간 배분 (총합 ≈ runtime)
        durations  = self._allocate_durations(seq_types, runtime)

        # ④ 씬 수 산출 (타입 × 긴장도 × 지속시간)
        plans: list[SequencePlan] = []
        for i, (st, dur) in enumerate(zip(seq_types, durations)):
            pct_start = sum(durations[:i]) / runtime
            pct_end   = sum(durations[:i+1]) / runtime
            tension   = self._calc_tension(st, act_idx, pct_start, pressure)
            scene_cnt = self._calc_scene_count(st, tension, dur)
            goal      = self._pick_goal(st, i)

            plans.append(SequencePlan(
                seq_id        = f"ep{episode_no:02d}_seq{i+1:02d}",
                episode_no    = episode_no,
                seq_index     = i + 1,
                goal          = goal,
                tension_target= tension,
                scene_count   = scene_cnt,
                act_index     = act_idx,
                pct_start     = round(min(pct_start, 1.0), 4),
                pct_end       = round(min(pct_end,   1.0), 4),
                seq_type      = st.value,
                duration_min  = round(dur, 2),
            ))

        return plans

    def total_scene_count(self, plans: list[SequencePlan]) -> int:
        return sum(p.scene_count for p in plans)

    def episode_summary(self, plans: list[SequencePlan]) -> dict[str, Any]:
        """에피소드 구성 요약."""
        total_scenes = self.total_scene_count(plans)
        total_dur    = sum(p.duration_min for p in plans)
        return {
            "seq_count":        len(plans),
            "total_scenes":     total_scenes,
            "total_duration_min": round(total_dur, 1),
            "avg_scenes_per_seq": round(total_scenes / len(plans), 1) if plans else 0,
            "seq_types":        [p.seq_type for p in plans],
        }

    # ── 시퀀스 수 동적 산출 ──────────────────────────────────────

    def _calc_seq_count(
        self,
        runtime:      int,
        act_idx:      int,
        pressure:     float,
        plot_lines:   int,
    ) -> int:
        """
        시퀀스 수 = (runtime / avg_seq_dur) × 막계수 × 압력계수 × 플롯계수
        결과 범위: [3, 8]
        """
        base       = runtime / AVG_SEQUENCE_DURATION_MIN            # ~6 (65min)
        act_mod    = ACT_SEQ_MODIFIERS.get(act_idx, 1.0)
        press_mod  = 0.85 + 0.30 * pressure                         # [0.85, 1.15]
        plot_mod   = 0.90 + 0.15 * min(max(plot_lines - 1, 0), 3)   # [0.90, 1.35]

        count = base * act_mod * press_mod * plot_mod
        return max(3, min(8, round(count)))

    # ── 시퀀스 타입 배정 ─────────────────────────────────────────

    def _assign_seq_types(
        self,
        n:       int,
        act_idx: int,
    ) -> list[SequenceType]:
        """
        막별 패턴에서 n개 시퀀스 타입 배정.
        패턴이 n보다 짧으면 PLOT_ADVANCE로 채움.
        패턴이 n보다 길면 앞에서 n개 선택 (CLIFFHANGER 보존).
        """
        pattern = list(ACT_SEQ_PATTERNS.get(act_idx, ACT_SEQ_PATTERNS[2]))

        if len(pattern) == n:
            return pattern

        if len(pattern) < n:
            # 부족한 만큼 PLOT_ADVANCE 삽입 (마지막 앞에)
            last  = pattern[-1]
            body  = pattern[:-1]
            extra = [SequenceType.PLOT_ADVANCE] * (n - len(pattern))
            return body + extra + [last]
        else:
            # 초과분: 끝의 CLIFFHANGER 보존, 앞에서 선택
            last  = pattern[-1]
            body  = pattern[:-1][:n-1]
            return body + [last]

    # ── 시퀀스 지속시간 배분 ─────────────────────────────────────

    def _allocate_durations(
        self,
        seq_types: list[SequenceType],
        runtime:   int,
    ) -> list[float]:
        """
        각 시퀀스 타입의 기준 지속시간 비율로 runtime 배분.
        합계가 runtime에 정확히 맞도록 정규화.
        """
        lo_hi = [SEQ_TYPE_DURATION_RANGE[st] for st in seq_types]
        mids  = [(lo + hi) / 2 for lo, hi in lo_hi]
        total = sum(mids)
        scale = runtime / total
        return [round(m * scale, 2) for m in mids]

    # ── 씬 수 동적 산출 ──────────────────────────────────────────

    def _calc_scene_count(
        self,
        seq_type: SequenceType,
        tension:  float,
        dur_min:  float,
    ) -> int:
        """
        씬 수 = 시퀀스지속시간 ÷ 씬평균지속시간(타입 × 긴장도)
        긴장도 높을수록 씬이 짧아져 씬 수 증가.
        결과 범위: [2, 8]
        """
        base_dur = SEQ_TYPE_BASE_SCENE_DUR[seq_type]
        # tension 보정: 0→120%, 0.5→100%, 1→80% (긴장=빠른 컷)
        tension_adj = base_dur * (1.20 - 0.40 * tension)
        count = dur_min / max(tension_adj, 0.5)
        return max(2, min(8, round(count)))

    # ── 긴장도 산출 ──────────────────────────────────────────────

    def _calc_tension(
        self,
        seq_type:     SequenceType,
        act_idx:      int,
        pct:          float,
        pressure_base: float,
    ) -> float:
        """
        긴장도 = 시퀀스 타입 기준값 × 에피소드 내 위치 보정 × 압력 스케일
        """
        type_base: dict[SequenceType, float] = {
            SequenceType.SETUP_HOOK:     0.30,
            SequenceType.PLOT_ADVANCE:   0.50,
            SequenceType.CONFLICT_PEAK:  0.75,
            SequenceType.EMOTIONAL_BEAT: 0.45,
            SequenceType.TURNING_POINT:  0.85,
            SequenceType.CLIFFHANGER:    0.80,
            SequenceType.RESOLUTION:     0.35,
        }
        base     = type_base.get(seq_type, 0.5)
        pos_adj  = 0.90 + 0.20 * pct          # 후반부일수록 소폭 상승
        press_adj= 0.80 + 0.40 * pressure_base
        return round(max(0.0, min(1.0, base * pos_adj * press_adj)), 4)

    # ── 보조 헬퍼 ────────────────────────────────────────────────

    def _resolve_act_index(
        self,
        packet:     dict[str, Any],
        episode_no: int,
    ) -> int:
        """MacroArc에서 현재 화의 막 번호 추출."""
        # 직접 act_index 제공 시 우선 사용
        if "act_index" in packet:
            return int(packet["act_index"])
        # act_breakpoints 기반 계산
        breakpoints = packet.get("act_breakpoints", [])
        if breakpoints:
            for act_no, bp in enumerate(breakpoints, start=1):
                if episode_no <= bp:
                    return act_no
            return len(breakpoints)
        # 전체 화 수 기반 4막 자동 추정
        total = packet.get("total_episode_count", packet.get("total_episodes", 16))
        frac  = episode_no / max(total, 1)
        if frac <= 0.25: return 1
        if frac <= 0.70: return 2
        if frac <= 0.90: return 3
        return 4

    def _episode_pressure(
        self,
        packet:     dict[str, Any],
        episode_no: int,
    ) -> float:
        """pressure_curve에서 현재 화 압력값 추출 (0~1)."""
        curve = packet.get("pressure_curve", [])
        if isinstance(curve, list) and curve:
            if episode_no <= len(curve):
                val = curve[episode_no - 1]
                if isinstance(val, (int, float)):
                    return float(max(0.0, min(1.0, val)))
        return 0.5

    def _pick_goal(self, seq_type: SequenceType, idx: int) -> str:
        pool = SEQ_TYPE_GOALS.get(seq_type, ["플롯 전진"])
        return pool[idx % len(pool)]
