from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from typing import Any
from uuid import uuid4


API_KEY = "greenpulse-demo-key"
ALLOWED_SENSOR_TYPES = {
    "pm25",
    "pm10",
    "co2",
    "temperature",
    "humidity",
    "noise",
}


@dataclass(frozen=True)
class ApiReading:
    record_id: str
    station_id: str
    district: str
    sensor_type: str
    value: float
    measured_at: str


@dataclass(frozen=True)
class ApiResponse:
    status_code: int
    body: dict[str, Any]


class GreenPulseApiStorage:
    def __init__(self) -> None:
        self._readings: dict[str, ApiReading] = {}

    def add_reading(
        self,
        reading: ApiReading,
    ) -> ApiReading:
        self._readings[reading.record_id] = reading
        return reading

    def list_readings(self) -> list[ApiReading]:
        return list(self._readings.values())

    def delete_reading(
        self,
        record_id: str,
    ) -> bool:
        if record_id not in self._readings:
            return False

        del self._readings[record_id]
        return True


class GreenPulseApiController:
    def __init__(
        self,
        api_key: str = API_KEY,
        storage: GreenPulseApiStorage | None = None,
    ) -> None:
        self.api_key = api_key
        self.storage = storage or GreenPulseApiStorage()

    def create_reading(
        self,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> ApiResponse:
        auth_error = self._validate_api_key(headers)
        if auth_error is not None:
            return auth_error

        validation_error = self._validate_payload(payload)
        if validation_error is not None:
            return validation_error

        reading = ApiReading(
            record_id=str(payload.get("record_id") or uuid4()),
            station_id=str(payload["station_id"]),
            district=str(payload["district"]),
            sensor_type=str(payload["sensor_type"]),
            value=float(payload["value"]),
            measured_at=str(
                payload.get("measured_at")
                or datetime.now(timezone.utc).isoformat()
            ),
        )

        self.storage.add_reading(reading)

        return ApiResponse(
            status_code=201,
            body={"message": "reading created", "reading": asdict(reading)},
        )

    def get_readings(
        self,
        headers: dict[str, str],
    ) -> ApiResponse:
        auth_error = self._validate_api_key(headers)
        if auth_error is not None:
            return auth_error

        readings = [asdict(reading) for reading in self.storage.list_readings()]

        return ApiResponse(
            status_code=200,
            body={"count": len(readings), "readings": readings},
        )

    def delete_reading(
        self,
        headers: dict[str, str],
        record_id: str,
    ) -> ApiResponse:
        auth_error = self._validate_api_key(headers)
        if auth_error is not None:
            return auth_error

        deleted = self.storage.delete_reading(record_id)

        if not deleted:
            return ApiResponse(
                status_code=404,
                body={"error": "reading not found"},
            )

        return ApiResponse(
            status_code=200,
            body={"message": "reading deleted", "record_id": record_id},
        )

    def _validate_api_key(
        self,
        headers: dict[str, str],
    ) -> ApiResponse | None:
        normalized_headers = {
            key.lower(): value
            for key, value in headers.items()
        }

        if normalized_headers.get("x-api-key") != self.api_key:
            return ApiResponse(
                status_code=401,
                body={"error": "invalid or missing api key"},
            )

        return None

    def _validate_payload(
        self,
        payload: dict[str, Any],
    ) -> ApiResponse | None:
        required_fields = ["station_id", "district", "sensor_type", "value"]

        for field_name in required_fields:
            if field_name not in payload:
                return ApiResponse(
                    status_code=400,
                    body={"error": f"missing field: {field_name}"},
                )

        sensor_type = str(payload["sensor_type"])
        if sensor_type not in ALLOWED_SENSOR_TYPES:
            return ApiResponse(
                status_code=400,
                body={"error": "unknown sensor type"},
            )

        try:
            float(payload["value"])
        except (TypeError, ValueError):
            return ApiResponse(
                status_code=400,
                body={"error": "value must be a number"},
            )

        return None


class GreenPulseRequestHandler(BaseHTTPRequestHandler):
    controller = GreenPulseApiController()

    def do_GET(self) -> None:
        if self.path == "/api/readings":
            response = self.controller.get_readings(dict(self.headers))
            self._send_json(response)
            return

        self._send_json(
            ApiResponse(status_code=404, body={"error": "endpoint not found"}),
        )

    def do_POST(self) -> None:
        if self.path != "/api/readings":
            self._send_json(
                ApiResponse(
                    status_code=404,
                    body={"error": "endpoint not found"},
                ),
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(raw_body or "{}")
        except json.JSONDecodeError:
            self._send_json(
                ApiResponse(status_code=400, body={"error": "invalid json"}),
            )
            return

        response = self.controller.create_reading(dict(self.headers), payload)
        self._send_json(response)

    def do_DELETE(self) -> None:
        prefix = "/api/readings/"

        if not self.path.startswith(prefix):
            self._send_json(
                ApiResponse(
                    status_code=404,
                    body={"error": "endpoint not found"},
                ),
            )
            return

        record_id = self.path.removeprefix(prefix)
        response = self.controller.delete_reading(dict(self.headers), record_id)
        self._send_json(response)

    def _send_json(
        self,
        response: ApiResponse,
    ) -> None:
        response_body = json.dumps(
            response.body,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(response.status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    server = HTTPServer((host, port), GreenPulseRequestHandler)
    print(f"GreenPulse API is running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
