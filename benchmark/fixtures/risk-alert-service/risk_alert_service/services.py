from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .models import Alert, AuditRecord, Case, Notification, Transaction
from .ports import AuditPort, NotificationPort
from .repositories import (
    InMemoryAccountRepository,
    InMemoryAlertRepository,
    InMemoryCaseRepository,
    InMemoryTransactionRepository,
)
from .rules import RiskRule


def stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


@dataclass
class ScreeningService:
    accounts: InMemoryAccountRepository
    transactions: InMemoryTransactionRepository
    alerts: InMemoryAlertRepository
    rules: tuple[RiskRule, ...]
    audit: AuditPort
    alert_threshold: int = 60

    def screen(self, transaction: Transaction) -> Alert | None:
        account = self.accounts.get(transaction.account_id)
        self.transactions.add(transaction)
        results = tuple(
            result
            for rule in self.rules
            if (result := rule.evaluate(account, transaction)) is not None
        )
        score = sum(result.score for result in results)
        self.audit.append(
            AuditRecord(
                action="transaction_screened",
                entity_type="transaction",
                entity_id=transaction.id,
                details={"score": str(score), "matched_rules": str(len(results))},
            )
        )
        if score < self.alert_threshold:
            return None
        alert = Alert(
            id=stable_id("alert", transaction.id),
            account_id=transaction.account_id,
            transaction_id=transaction.id,
            score=score,
            reasons=tuple(result.reason for result in results),
        )
        self.alerts.add(alert)
        return alert


@dataclass
class CaseService:
    alerts: InMemoryAlertRepository
    cases: InMemoryCaseRepository
    notifications: NotificationPort
    audit: AuditPort

    def open_case(self, account_id: str, alert_ids: list[str], reviewer: str) -> Case:
        if not alert_ids:
            raise ValueError("a case requires at least one alert")
        unique_ids = list(dict.fromkeys(alert_ids))
        for alert_id in unique_ids:
            alert = self.alerts.get(alert_id)
            if alert.account_id != account_id:
                raise ValueError("all alerts must belong to the case account")
        case = Case(
            id=stable_id("case", account_id, *sorted(unique_ids)),
            account_id=account_id,
            alert_ids=unique_ids,
        )
        self.cases.add(case)
        self.notifications.send(
            Notification(
                recipient=reviewer,
                subject=f"New risk case {case.id}",
                body=f"Review {len(unique_ids)} alert(s) for account {account_id}.",
            )
        )
        self.audit.append(
            AuditRecord(
                action="case_opened",
                entity_type="case",
                entity_id=case.id,
                details={"account_id": account_id, "alert_count": str(len(unique_ids))},
            )
        )
        return case
