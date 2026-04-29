from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from statistics import mean
from typing import Iterable


class QualityStatus(Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    INVALID = "invalid"


@dataclass(frozen=True)
class SensorLimits:
    min_value: float
    max_value: float
    warning_value: float
    critical_value: float


@dataclass(frozen=True)
class SensorReading:
    station_id: str
    district: str
    sensor_type: str
    value: float
    measured_at: datetime


@dataclass(frozen=True)
class ValidationIssue:
    station_id: str
    sensor_type: str
    message: str


@dataclass(frozen=True)
class StationSummary:
    station_id: str
    district: str
    readings_count: int
    invalid_count: int
    average_pm25: float | None
    average_pm10: float | None
    average_co2: float | None
    status: QualityStatus


class GreenPulseDataQualityService:
    def __init__(self) -> None:
        self.limits = {
            "pm25": SensorLimits(
                min_value=0.0,
                max_value=1000.0,
                warning_value=35.0,
                critical_value=75.0,
            ),
            "pm10": SensorLimits(
                min_value=0.0,
                max_value=1500.0,
                warning_value=60.0,
                critical_value=150.0,
            ),
            "co2": SensorLimits(
                min_value=250.0,
                max_value=10000.0,
                warning_value=1000.0,
                critical_value=2000.0,
            ),
            "temperature": SensorLimits(
                min_value=-60.0,
                max_value=60.0,
                warning_value=35.0,
                critical_value=45.0,
            ),
            "humidity": SensorLimits(
                min_value=0.0,
                max_value=100.0,
                warning_value=80.0,
                critical_value=95.0,
            ),
            "noise": SensorLimits(
                min_value=0.0,
                max_value=140.0,
                warning_value=65.0,
                critical_value=85.0,
            ),
        }

    def validate_reading(
        self,
        reading: SensorReading,
    ) -> ValidationIssue | None:
        sensor_type = reading.sensor_type.lower()

        if not reading.station_id.strip():
            return ValidationIssue(
                station_id=reading.station_id,
                sensor_type=reading.sensor_type,
                message="Station id is empty",
            )

        if not reading.district.strip():
            return ValidationIssue(
                station_id=reading.station_id,
                sensor_type=reading.sensor_type,
                message="District is empty",
            )

        if sensor_type not in self.limits:
            return ValidationIssue(
                station_id=reading.station_id,
                sensor_type=reading.sensor_type,
                message="Unknown sensor type",
            )

        limits = self.limits[sensor_type]

        if reading.value < limits.min_value:
            return ValidationIssue(
                station_id=reading.station_id,
                sensor_type=reading.sensor_type,
                message="Value is below allowed range",
            )

        if reading.value > limits.max_value:
            return ValidationIssue(
                station_id=reading.station_id,
                sensor_type=reading.sensor_type,
                message="Value is above allowed range",
            )

        return None

    def validate_batch(
        self,
        readings: Iterable[SensorReading],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for reading in readings:
            issue = self.validate_reading(reading)

            if issue is not None:
                issues.append(issue)

        return issues

    def detect_status(
        self,
        sensor_type: str,
        value: float,
    ) -> QualityStatus:
        normalized_sensor_type = sensor_type.lower()

        if normalized_sensor_type not in self.limits:
            return QualityStatus.INVALID

        limits = self.limits[normalized_sensor_type]

        if value >= limits.critical_value:
            return QualityStatus.CRITICAL

        if value >= limits.warning_value:
            return QualityStatus.WARNING

        return QualityStatus.NORMAL

    def calculate_station_summary(
        self,
        station_id: str,
        readings: Iterable[SensorReading],
    ) -> StationSummary:
        station_readings = [
            reading
            for reading in readings
            if reading.station_id == station_id
        ]

        if not station_readings:
            return StationSummary(
                station_id=station_id,
                district="unknown",
                readings_count=0,
                invalid_count=0,
                average_pm25=None,
                average_pm10=None,
                average_co2=None,
                status=QualityStatus.INVALID,
            )

        issues = self.validate_batch(station_readings)
        valid_readings = [
            reading
            for reading in station_readings
            if self.validate_reading(reading) is None
        ]

        pm25_values = self._values_by_type(valid_readings, "pm25")
        pm10_values = self._values_by_type(valid_readings, "pm10")
        co2_values = self._values_by_type(valid_readings, "co2")

        summary_status = self._calculate_summary_status(valid_readings)

        return StationSummary(
            station_id=station_id,
            district=station_readings[0].district,
            readings_count=len(station_readings),
            invalid_count=len(issues),
            average_pm25=self._safe_average(pm25_values),
            average_pm10=self._safe_average(pm10_values),
            average_co2=self._safe_average(co2_values),
            status=summary_status,
        )

    def calculate_city_status(
        self,
        readings: Iterable[SensorReading],
    ) -> QualityStatus:
        statuses = [
            self.detect_status(
                sensor_type=reading.sensor_type,
                value=reading.value,
            )
            for reading in readings
            if self.validate_reading(reading) is None
        ]

        if not statuses:
            return QualityStatus.INVALID

        if QualityStatus.CRITICAL in statuses:
            return QualityStatus.CRITICAL

        if QualityStatus.WARNING in statuses:
            return QualityStatus.WARNING

        return QualityStatus.NORMAL

    def find_stations(
        self,
        readings: Iterable[SensorReading],
    ) -> list[str]:
        station_ids = {
            reading.station_id
            for reading in readings
            if reading.station_id.strip()
        }

        return sorted(station_ids)

    def build_station_report(
        self,
        readings: Iterable[SensorReading],
    ) -> list[StationSummary]:
        cached_readings = list(readings)

        return [
            self.calculate_station_summary(
                station_id=station_id,
                readings=cached_readings,
            )
            for station_id in self.find_stations(cached_readings)
        ]

    def _calculate_summary_status(
        self,
        readings: Iterable[SensorReading],
    ) -> QualityStatus:
        statuses = [
            self.detect_status(
                sensor_type=reading.sensor_type,
                value=reading.value,
            )
            for reading in readings
        ]

        if not statuses:
            return QualityStatus.INVALID

        if QualityStatus.CRITICAL in statuses:
            return QualityStatus.CRITICAL

        if QualityStatus.WARNING in statuses:
            return QualityStatus.WARNING

        return QualityStatus.NORMAL

    def _values_by_type(
        self,
        readings: Iterable[SensorReading],
        sensor_type: str,
    ) -> list[float]:
        return [
            reading.value
            for reading in readings
            if reading.sensor_type.lower() == sensor_type
        ]

    def _safe_average(
        self,
        values: list[float],
    ) -> float | None:
        if not values:
            return None

        return round(mean(values), 2)


def load_demo_readings() -> list[SensorReading]:
    measured_at = datetime.now()

    return [
        SensorReading("MSK-001", "ЦАО", "pm25", 18.4, measured_at),
        SensorReading("MSK-001", "ЦАО", "pm10", 42.7, measured_at),
        SensorReading("MSK-001", "ЦАО", "co2", 820.0, measured_at),
        SensorReading("MSK-002", "САО", "pm25", 39.2, measured_at),
        SensorReading("MSK-002", "САО", "pm10", 68.5, measured_at),
        SensorReading("MSK-002", "САО", "co2", 1150.0, measured_at),
        SensorReading("MSK-003", "ЮВАО", "pm25", 91.0, measured_at),
        SensorReading("MSK-003", "ЮВАО", "pm10", 180.0, measured_at),
        SensorReading("MSK-003", "ЮВАО", "co2", 2300.0, measured_at),
        SensorReading("MSK-004", "ЗАО", "pm25", -4.0, measured_at),
        SensorReading("MSK-004", "ЗАО", "unknown", 10.0, measured_at),
    ]


def print_station_report(
    summaries: list[StationSummary],
) -> None:
    for summary in summaries:
        print(
            "; ".join(
                [
                    f"station={summary.station_id}",
                    f"district={summary.district}",
                    f"readings={summary.readings_count}",
                    f"invalid={summary.invalid_count}",
                    f"avg_pm25={summary.average_pm25}",
                    f"avg_pm10={summary.average_pm10}",
                    f"avg_co2={summary.average_co2}",
                    f"status={summary.status.value}",
                ],
            ),
        )


def main() -> None:
    service = GreenPulseDataQualityService()
    readings = load_demo_readings()
    issues = service.validate_batch(readings)
    city_status = service.calculate_city_status(readings)
    station_report = service.build_station_report(readings)

    print("GreenPulse data quality review")
    print(f"city_status={city_status.value}")
    print(f"validation_issues={len(issues)}")
    print_station_report(station_report)

    for issue in issues:
        print(
            "; ".join(
                [
                    f"issue_station={issue.station_id}",
                    f"sensor={issue.sensor_type}",
                    f"message={issue.message}",
                ],
            ),
        )


if __name__ == "__main__":
    main()
