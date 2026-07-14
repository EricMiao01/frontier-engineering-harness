from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import Account, RuleResult, Transaction


class RiskRule(Protocol):
    id: str

    def evaluate(self, account: Account, transaction: Transaction) -> RuleResult | None: ...


@dataclass(frozen=True)
class LargeAmountRule:
    threshold: int = 10_000
    id: str = "large-amount"

    def evaluate(self, account: Account, transaction: Transaction) -> RuleResult | None:
        if transaction.amount < self.threshold:
            return None
        return RuleResult(self.id, 60, f"amount {transaction.amount} exceeds {self.threshold}")


@dataclass(frozen=True)
class HighRiskDestinationRule:
    high_risk_countries: frozenset[str]
    id: str = "high-risk-destination"

    def evaluate(self, account: Account, transaction: Transaction) -> RuleResult | None:
        if transaction.destination_country not in self.high_risk_countries:
            return None
        return RuleResult(self.id, 50, f"destination {transaction.destination_country} is high risk")


@dataclass(frozen=True)
class ElevatedAccountRule:
    id: str = "elevated-account"

    def evaluate(self, account: Account, transaction: Transaction) -> RuleResult | None:
        if account.risk_tier != "elevated":
            return None
        return RuleResult(self.id, 25, "account risk tier is elevated")
