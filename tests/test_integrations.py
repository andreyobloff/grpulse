from src.api import GreenPulseApiController
from src.integrations import (
    NotificationMessage,
    SmtpEmailNotificationClient,
)


API_HEADERS = {"X-API-Key": "greenpulse-demo-key"}


class FakeSmtpConnection:
    sent_messages = []
    tls_started = False
    logged_in = False

    def __init__(self, host, port, timeout=10):
        self.host = host
        self.port = port
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def starttls(self):
        FakeSmtpConnection.tls_started = True

    def login(self, username, password):
        FakeSmtpConnection.logged_in = True

    def send_message(self, message):
        FakeSmtpConnection.sent_messages.append(message)


class BrokenSmtpConnection(FakeSmtpConnection):
    def send_message(self, message):
        raise RuntimeError("smtp unavailable")


def reset_fake_smtp() -> None:
    FakeSmtpConnection.sent_messages = []
    FakeSmtpConnection.tls_started = False
    FakeSmtpConnection.logged_in = False


def test_smtp_notification_is_sent() -> None:
    reset_fake_smtp()
    client = SmtpEmailNotificationClient(
        host="smtp.example.test",
        port=587,
        sender="greenpulse@example.test",
        recipient="operator@example.test",
        username="greenpulse",
        password="secret",
        smtp_factory=FakeSmtpConnection,
    )

    result = client.send(
        NotificationMessage(
            event_id="event-001",
            subject="GreenPulse notification",
            body="New reading created",
        ),
    )

    assert result.sent is True
    assert result.skipped is False
    assert len(FakeSmtpConnection.sent_messages) == 1
    assert FakeSmtpConnection.tls_started is True
    assert FakeSmtpConnection.logged_in is True


def test_duplicate_notification_is_skipped() -> None:
    reset_fake_smtp()
    client = SmtpEmailNotificationClient(
        host="smtp.example.test",
        port=587,
        sender="greenpulse@example.test",
        recipient="operator@example.test",
        smtp_factory=FakeSmtpConnection,
    )
    message = NotificationMessage(
        event_id="event-duplicate",
        subject="GreenPulse notification",
        body="New reading created",
    )

    first_result = client.send(message)
    second_result = client.send(message)

    assert first_result.sent is True
    assert second_result.sent is False
    assert second_result.skipped is True
    assert len(FakeSmtpConnection.sent_messages) == 1


def test_smtp_error_is_handled() -> None:
    client = SmtpEmailNotificationClient(
        host="smtp.example.test",
        port=587,
        sender="greenpulse@example.test",
        recipient="operator@example.test",
        smtp_factory=BrokenSmtpConnection,
    )

    result = client.send(
        NotificationMessage(
            event_id="event-error",
            subject="GreenPulse notification",
            body="New reading created",
        ),
    )

    assert result.sent is False
    assert result.skipped is False
    assert result.detail.startswith("smtp error")


def test_api_triggers_notification_after_reading_creation() -> None:
    reset_fake_smtp()
    client = SmtpEmailNotificationClient(
        host="smtp.example.test",
        port=587,
        sender="greenpulse@example.test",
        recipient="operator@example.test",
        smtp_factory=FakeSmtpConnection,
    )
    controller = GreenPulseApiController(notifier=client)

    response = controller.create_reading(
        headers=API_HEADERS,
        payload={
            "record_id": "REC-INTEGRATION-001",
            "station_id": "MSK-001",
            "district": "ЦАО",
            "sensor_type": "pm25",
            "value": 18.4,
        },
    )

    assert response.status_code == 201
    assert response.body["notification"]["sent"] is True
    assert len(FakeSmtpConnection.sent_messages) == 1


if __name__ == "__main__":
    test_smtp_notification_is_sent()
    test_duplicate_notification_is_skipped()
    test_smtp_error_is_handled()
    test_api_triggers_notification_after_reading_creation()
    print("GreenPulse integration tests passed")
