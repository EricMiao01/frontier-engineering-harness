from risk_alert_service.models import Account, Transaction
from risk_alert_service.ports import RecordingAuditPort
from risk_alert_service.repositories import InMemoryAccountRepository, InMemoryAlertRepository, InMemoryTransactionRepository
from risk_alert_service.rules import ElevatedAccountRule, HighRiskDestinationRule, LargeAmountRule
from risk_alert_service.services import ScreeningService


def build_service() -> tuple[ScreeningService, RecordingAuditPort]:
    accounts = InMemoryAccountRepository()
    accounts.add(Account(id="acct-1", country="TW", risk_tier="elevated"))
    audit = RecordingAuditPort()
    service = ScreeningService(
        accounts=accounts,
        transactions=InMemoryTransactionRepository(),
        alerts=InMemoryAlertRepository(),
        rules=(LargeAmountRule(), HighRiskDestinationRule(frozenset({"XZ"})), ElevatedAccountRule()),
        audit=audit,
    )
    return service, audit


def test_combined_rules_create_alert() -> None:
    service, audit = build_service()
    alert = service.screen(Transaction(id="tx-1", account_id="acct-1", amount=12_000, currency="USD", destination_country="XZ"))
    assert alert is not None
    assert alert.score == 135
    assert alert.id == "alert_045ef594d81d"
    assert len(alert.reasons) == 3
    assert audit.records[-1].details == {"score": "135", "matched_rules": "3"}


def test_below_threshold_records_audit_without_alert() -> None:
    service, audit = build_service()
    alert = service.screen(Transaction(id="tx-2", account_id="acct-1", amount=100, currency="USD", destination_country="US"))
    assert alert is None
    assert audit.records[-1].details == {"score": "25", "matched_rules": "1"}
