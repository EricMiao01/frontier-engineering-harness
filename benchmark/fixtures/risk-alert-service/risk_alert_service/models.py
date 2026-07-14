from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AlertStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    CLOSED = "closed"


class CaseStatus(str, Enum):
    OPEN = "open"
    ESCALATED = "escalated"
    CLOSED = "closed"


@dataclass(frozen=True)
class Account:
    id: str
    country: str
    risk_tier: str = "standard"


@dataclass(frozen=True)
class Transaction:
    id: str
    account_id: str
    amount: int
    currency: str
    destination_country: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    score: int
    reason: str


@dataclass
class Alert:
    id: str
    account_id: str
    transaction_id: str
    score: int
    reasons: tuple[str, ...]
    status: AlertStatus = AlertStatus.OPEN


@dataclass
class Case:
    id: str
    account_id: str
    alert_ids: list[str]
    status: CaseStatus = CaseStatus.OPEN


@dataclass(frozen=True)
class Notification:
    recipient: str
    subject: str
    body: str


@dataclass(frozen=True)
class AuditRecord:
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, str]
