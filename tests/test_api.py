from src.api import GreenPulseApiController


API_HEADERS = {"X-API-Key": "greenpulse-demo-key"}


def test_create_reading_success() -> None:
    controller = GreenPulseApiController()

    response = controller.create_reading(
        headers=API_HEADERS,
        payload={
            "record_id": "REC-API-001",
            "station_id": "MSK-001",
            "district": "ЦАО",
            "sensor_type": "pm25",
            "value": 18.4,
        },
    )

    assert response.status_code == 201
    assert response.body["reading"]["record_id"] == "REC-API-001"


def test_get_readings_success() -> None:
    controller = GreenPulseApiController()

    controller.create_reading(
        headers=API_HEADERS,
        payload={
            "record_id": "REC-API-001",
            "station_id": "MSK-001",
            "district": "ЦАО",
            "sensor_type": "co2",
            "value": 820.0,
        },
    )

    response = controller.get_readings(headers=API_HEADERS)

    assert response.status_code == 200
    assert response.body["count"] == 1
    assert response.body["readings"][0]["station_id"] == "MSK-001"


def test_delete_reading_success() -> None:
    controller = GreenPulseApiController()

    controller.create_reading(
        headers=API_HEADERS,
        payload={
            "record_id": "REC-API-001",
            "station_id": "MSK-001",
            "district": "ЦАО",
            "sensor_type": "pm10",
            "value": 42.7,
        },
    )

    delete_response = controller.delete_reading(
        headers=API_HEADERS,
        record_id="REC-API-001",
    )
    list_response = controller.get_readings(headers=API_HEADERS)

    assert delete_response.status_code == 200
    assert list_response.body["count"] == 0


def test_missing_api_key_is_rejected() -> None:
    controller = GreenPulseApiController()

    response = controller.get_readings(headers={})

    assert response.status_code == 401


def test_invalid_payload_is_rejected() -> None:
    controller = GreenPulseApiController()

    response = controller.create_reading(
        headers=API_HEADERS,
        payload={
            "station_id": "MSK-001",
            "district": "ЦАО",
            "sensor_type": "unknown",
            "value": 18.4,
        },
    )

    assert response.status_code == 400


def test_delete_unknown_reading_returns_404() -> None:
    controller = GreenPulseApiController()

    response = controller.delete_reading(
        headers=API_HEADERS,
        record_id="UNKNOWN",
    )

    assert response.status_code == 404


if __name__ == "__main__":
    test_create_reading_success()
    test_get_readings_success()
    test_delete_reading_success()
    test_missing_api_key_is_rejected()
    test_invalid_payload_is_rejected()
    test_delete_unknown_reading_returns_404()
    print("GreenPulse API tests passed")
