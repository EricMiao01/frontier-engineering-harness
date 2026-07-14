from __future__ import annotations

from typing import Protocol

from .models import AuditRecord, Notification


class NotificationPort(Protocol):
    def send(self, notification: Notification) -> None: ...


class AuditPort(Protocol):
    def append(self, record: AuditRecord) -> None: ...


class RecordingNotificationPort:
    def __init__(self) -> None:
        self.sent: list[Notification] = []

    def send(self, notification: Notification) -> None:
        self.sent.append(notification)


class RecordingAuditPort:
    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def append(self, record: AuditRecord) -> None:
        self.records.append(record)
