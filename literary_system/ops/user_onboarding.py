"""
literary_system/ops/user_onboarding.py
V476 — UserOnboarding + Subscription 관리 (ADR-012)

인터페이스:
  onboard(user_info) → OnboardResult
  create_subscription(user_id, plan, pg) → Subscription
  cancel_subscription(sub_id) → bool
  get_user(user_id) → User | None

LLM-0 준수: storage_fn / email_fn 주입 가능
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# ── 열거형 ───────────────────────────────────────────────────

class UserPlan(str, Enum):
    FREE       = "free"
    PRO        = "pro"
    ENTERPRISE = "enterprise"


class UserStatus(str, Enum):
    ACTIVE    = "active"
    SUSPENDED = "suspended"
    CHURNED   = "churned"


class PaymentGateway(str, Enum):
    STRIPE = "stripe"
    TOSS   = "toss"


class OnboardStep(str, Enum):
    REGISTERED   = "registered"
    VERIFIED     = "verified"
    SUBSCRIBED   = "subscribed"
    COMPLETED    = "completed"


# ── 데이터 모델 ──────────────────────────────────────────────

@dataclass
class User:
    user_id:    str
    email:      str
    name:       str
    plan:       UserPlan     = UserPlan.FREE
    status:     UserStatus   = UserStatus.ACTIVE
    region_id:  str          = "KR"
    cohort:     str          = ""
    created_at: str          = field(default_factory=lambda: _now())
    metadata:   Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscription:
    sub_id:     str
    user_id:    str
    plan:       UserPlan
    pg:         PaymentGateway
    amount:     float          = 0.0
    currency:   str            = "KRW"
    active:     bool           = True
    created_at: str            = field(default_factory=lambda: _now())
    cancelled_at: Optional[str] = None


@dataclass
class OnboardResult:
    user:   User
    step:   OnboardStep
    token:  str
    email_sent: bool = False


# ── 헬퍼 ─────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


# ── UserOnboarding ───────────────────────────────────────────

class UserOnboarding:
    """
    가입 / 플랜 / 구독 관리.

    storage_fn: (key, value) → None  (기본: 인메모리)
    email_fn:   (to, subject, body) → bool  (기본: 항상 True mock)
    """

    def __init__(
        self,
        storage_fn:  Optional[Callable[[str, Any], None]] = None,
        email_fn:    Optional[Callable[[str, str, str], bool]] = None,
        pg_fn:       Optional[Callable[[str, float, str], str]] = None,
    ) -> None:
        self._users:  Dict[str, User]         = {}
        self._subs:   Dict[str, Subscription] = {}
        self._tokens: Dict[str, str]          = {}  # token → user_id

        self._storage_fn = storage_fn or (lambda k, v: None)
        self._email_fn   = email_fn   or (lambda to, sub, body: True)
        self._pg_fn      = pg_fn      or (lambda user_id, amt, pg: _new_id("tx_"))

    # ── 가입 ────────────────────────────────────────────────

    def onboard(self, user_info: Dict[str, Any]) -> OnboardResult:
        """
        신규 사용자 가입.
        user_info 필수 키: email, name
        선택 키: plan, region_id, cohort
        """
        email = user_info.get("email", "").strip()
        name  = user_info.get("name",  "").strip()
        if not email:
            raise ValueError("onboard: email 필수")
        if not name:
            raise ValueError("onboard: name 필수")

        # 중복 이메일 확인
        for u in self._users.values():
            if u.email == email:
                raise ValueError(f"onboard: 이미 등록된 이메일 — {email}")

        user = User(
            user_id=_new_id("usr_"),
            email=email,
            name=name,
            plan=UserPlan(user_info.get("plan", UserPlan.FREE)),
            region_id=user_info.get("region_id", "KR"),
            cohort=user_info.get("cohort", ""),
        )
        token = _new_id("tok_")
        self._users[user.user_id]  = user
        self._tokens[token]        = user.user_id
        self._storage_fn(f"user:{user.user_id}", user)

        # 이메일 훅
        email_sent = self._email_fn(
            email,
            "Literary OS 가입을 환영합니다",
            f"안녕하세요 {name}님, 가입이 완료되었습니다.",
        )

        return OnboardResult(
            user=user,
            step=OnboardStep.REGISTERED,
            token=token,
            email_sent=bool(email_sent),
        )

    # ── 구독 ────────────────────────────────────────────────

    PLAN_PRICE: Dict[UserPlan, float] = {
        UserPlan.FREE:       0.0,
        UserPlan.PRO:    29000.0,
        UserPlan.ENTERPRISE: 99000.0,
    }

    def create_subscription(
        self,
        user_id: str,
        plan: UserPlan,
        pg: PaymentGateway = PaymentGateway.STRIPE,
    ) -> Subscription:
        user = self._users.get(user_id)
        if user is None:
            raise ValueError(f"create_subscription: 알 수 없는 user_id={user_id}")

        amount = self.PLAN_PRICE.get(plan, 0.0)
        if amount > 0:
            self._pg_fn(user_id, amount, pg.value)

        sub = Subscription(
            sub_id=_new_id("sub_"),
            user_id=user_id,
            plan=plan,
            pg=pg,
            amount=amount,
        )
        self._subs[sub.sub_id] = sub

        # 플랜 업데이트
        user.plan = plan
        self._storage_fn(f"sub:{sub.sub_id}", sub)
        return sub

    def cancel_subscription(self, sub_id: str) -> bool:
        sub = self._subs.get(sub_id)
        if sub is None:
            return False
        sub.active       = False
        sub.cancelled_at = _now()

        # 사용자 FREE 다운그레이드
        user = self._users.get(sub.user_id)
        if user:
            user.plan = UserPlan.FREE
        return True

    # ── 조회 ────────────────────────────────────────────────

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def get_user_by_token(self, token: str) -> Optional[User]:
        uid = self._tokens.get(token)
        return self._users.get(uid) if uid else None

    def get_subscription(self, sub_id: str) -> Optional[Subscription]:
        return self._subs.get(sub_id)

    def list_subscriptions(self, user_id: str) -> List[Subscription]:
        return [s for s in self._subs.values() if s.user_id == user_id]

    def suspend_user(self, user_id: str) -> bool:
        user = self._users.get(user_id)
        if user is None:
            return False
        user.status = UserStatus.SUSPENDED
        return True

    def reactivate_user(self, user_id: str) -> bool:
        user = self._users.get(user_id)
        if user is None:
            return False
        user.status = UserStatus.ACTIVE
        return True

    def user_count(self) -> int:
        return len(self._users)

    def active_subscription_count(self) -> int:
        return sum(1 for s in self._subs.values() if s.active)
