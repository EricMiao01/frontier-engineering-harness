import pytest

from risk_alert_service.models import Alert
from risk_alert_service.ports import RecordingAuditPort, RecordingNotificationPort
from risk_alert_service.repositories import InMemoryAlertRepository, InMemoryCaseRepository
from risk_alert_service.services import CaseService


def build_service() -> tuple[CaseService, RecordingNotificationPort, RecordingAuditPort]:
    alerts = InMemoryAlertRepository()
    alerts.add(Alert(id="a-1", account_id="acct-1", transaction_id="tx-1", score=70, reasons=("r1",)))
    alerts.add(Alert(id="a-2", account_id="acct-1", transaction_id="tx-2", score=80, reasons=("r2",)))
    alerts.add(Alert(id="a-3", account_id="acct-2", transaction_id="tx-3", score=90, reasons=("r3",)))
    notifications = RecordingNotificationPort()
    audit = RecordingAuditPort()
    return CaseService(alerts, InMemoryCaseRepository(), notifications, audit), notifications, audit


def test_open_case_deduplicates_alerts_and_notifies() -> None:
    service, notifications, audit = build_service()
    case = service.open_case("acct-1", ["a-2", "a-1", "a-2"], reviewer="analyst@example.com")
    assert case.alert_ids == ["a-2", "a-1"]
    assert notifications.sent[0].recipient == "analyst@example.com"
    assert audit.records[0].details["alert_count"] == "2"


def test_case_rejects_alert_from_other_account() -> None:
    service, _, _ = build_service()
    with pytest.raises(ValueError, match="all alerts"):
        service.open_case("acct-1", ["a-1", "a-3"], reviewer="analyst@example.com")
