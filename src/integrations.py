from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import logging
import os
import smtplib
from typing import Any, Protocol


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NotificationMessage:
    event_id: str
    subject: str
    body: str


@dataclass(frozen=True)
class IntegrationResult:
    provider: str
    sent: bool
    skipped: bool
    detail: str


class NotificationClient(Protocol):
    def send(
        self,
        message: NotificationMessage,
    ) -> IntegrationResult:
        pass


class NotificationLog:
    def __init__(self) -> None:
        self._sent_event_ids: set[str] = set()

    def has_sent(
        self,
        event_id: str,
    ) -> bool:
        return event_id in self._sent_event_ids

    def mark_sent(
        self,
        event_id: str,
    ) -> None:
        self._sent_event_ids.add(event_id)


class SmtpEmailNotificationClient:
    def __init__(
        self,
        host: str,
        port: int,
        sender: str,
        recipient: str,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
        timeout: int = 10,
        smtp_factory: Any | None = None,
        notification_log: NotificationLog | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.sender = sender
        self.recipient = recipient
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.timeout = timeout
        self.smtp_factory = smtp_factory or smtplib.SMTP
        self.notification_log = notification_log or NotificationLog()

    def send(
        self,
        message: NotificationMessage,
    ) -> IntegrationResult:
        if self.notification_log.has_sent(message.event_id):
            return IntegrationResult(
                provider="smtp",
                sent=False,
                skipped=True,
                detail="duplicate event skipped",
            )

        if not self._is_configured():
            logger.warning("SMTP integration is not configured")
            return IntegrationResult(
                provider="smtp",
                sent=False,
                skipped=False,
                detail="smtp config missing",
            )

        email_message = self._build_email(message)

        try:
            with self.smtp_factory(
                self.host,
                self.port,
                timeout=self.timeout,
            ) as smtp_connection:
                if self.use_tls:
                    smtp_connection.starttls()

                if self.username and self.password:
                    smtp_connection.login(self.username, self.password)

                smtp_connection.send_message(email_message)
        except Exception as error:
            logger.exception("SMTP notification failed")
            return IntegrationResult(
                provider="smtp",
                sent=False,
                skipped=False,
                detail=f"smtp error: {error}",
            )

        self.notification_log.mark_sent(message.event_id)

        return IntegrationResult(
            provider="smtp",
            sent=True,
            skipped=False,
            detail="email notification sent",
        )

    def _build_email(
        self,
        message: NotificationMessage,
    ) -> EmailMessage:
        email_message = EmailMessage()
        email_message["From"] = self.sender
        email_message["To"] = self.recipient
        email_message["Subject"] = message.subject
        email_message.set_content(message.body)
        return email_message

    def _is_configured(self) -> bool:
        return bool(self.host and self.sender and self.recipient)


class IntegrationEventFactory:
    @staticmethod
    def reading_created(
        record_id: str,
        station_id: str,
        district: str,
        sensor_type: str,
        value: float,
    ) -> NotificationMessage:
        return NotificationMessage(
            event_id=f"reading-created:{record_id}",
            subject=f"GreenPulse: новое измерение {station_id}",
            body=(
                "Создана новая запись экологического мониторинга.\n"
                f"ID записи: {record_id}\n"
                f"Станция: {station_id}\n"
                f"Район: {district}\n"
                f"Тип датчика: {sensor_type}\n"
                f"Значение: {value}"
            ),
        )


def build_smtp_client_from_environment() -> SmtpEmailNotificationClient | None:
    host = os.getenv("GREENPULSE_SMTP_HOST", "")
    sender = os.getenv("GREENPULSE_NOTIFY_FROM", "")
    recipient = os.getenv("GREENPULSE_NOTIFY_TO", "")

    if not host or not sender or not recipient:
        return None

    port = int(os.getenv("GREENPULSE_SMTP_PORT", "587"))
    username = os.getenv("GREENPULSE_SMTP_USERNAME")
    password = os.getenv("GREENPULSE_SMTP_PASSWORD")
    use_tls = os.getenv("GREENPULSE_SMTP_TLS", "true").lower() == "true"

    return SmtpEmailNotificationClient(
        host=host,
        port=port,
        sender=sender,
        recipient=recipient,
        username=username,
        password=password,
        use_tls=use_tls,
    )
