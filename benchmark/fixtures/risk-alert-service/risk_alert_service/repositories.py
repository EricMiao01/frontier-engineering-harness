from __future__ import annotations

from dataclasses import replace

from .models import Account, Alert, Case, Transaction


class NotFoundError(LookupError):
    pass


class InMemoryAccountRepository:
    def __init__(self) -> None:
        self._items: dict[str, Account] = {}

    def add(self, account: Account) -> None:
        self._items[account.id] = account

    def get(self, account_id: str) -> Account:
        try:
            return self._items[account_id]
        except KeyError as exc:
            raise NotFoundError(f"account not found: {account_id}") from exc


class InMemoryTransactionRepository:
    def __init__(self) -> None:
        self._items: dict[str, Transaction] = {}

    def add(self, transaction: Transaction) -> None:
        self._items[transaction.id] = transaction

    def get(self, transaction_id: str) -> Transaction:
        try:
            return self._items[transaction_id]
        except KeyError as exc:
            raise NotFoundError(f"transaction not found: {transaction_id}") from exc


class InMemoryAlertRepository:
    def __init__(self) -> None:
        self._items: dict[str, Alert] = {}

    def add(self, alert: Alert) -> None:
        self._items[alert.id] = replace(alert)

    def get(self, alert_id: str) -> Alert:
        try:
            return replace(self._items[alert_id])
        except KeyError as exc:
            raise NotFoundError(f"alert not found: {alert_id}") from exc

    def list_for_account(self, account_id: str) -> list[Alert]:
        return [replace(item) for item in self._items.values() if item.account_id == account_id]


class InMemoryCaseRepository:
    def __init__(self) -> None:
        self._items: dict[str, Case] = {}

    def add(self, case: Case) -> None:
        self._items[case.id] = replace(case, alert_ids=list(case.alert_ids))

    def get(self, case_id: str) -> Case:
        try:
            item = self._items[case_id]
            return replace(item, alert_ids=list(item.alert_ids))
        except KeyError as exc:
            raise NotFoundError(f"case not found: {case_id}") from exc
