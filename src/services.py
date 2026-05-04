from statistics import mean
from typing import Iterable

from src.models import (
    QualityStatus,
    SensorLimits,
    SensorReading,
    StationSummary,
    ValidationIssue,
)


class GreenPulseDataQualityService:
    def __init__(self) -> None:
        self.limits = self._build_limits()

    def validate_reading(
        self,
        reading: SensorReading,
    ) -> ValidationIssue | None:
        sensor_type = reading.sensor_type.lower()

        if not reading.station_id.strip():
            return self._issue(reading, "Station id is empty")

        if not reading.district.strip():
            return self._issue(reading, "District is empty")

        if sensor_type not in self.limits:
            return self._issue(reading, "Unknown sensor type")

        limits = self.limits[sensor_type]

        if reading.value < limits.min_value:
            return self._issue(reading, "Value is below allowed range")

        if reading.value > limits.max_value:
            return self._issue(reading, "Value is above allowed range")

        return None

    def validate_batch(
        self,
        readings: Iterable[SensorReading],
    ) -> list[ValidationIssue]:
        return [
            issue
            for issue in (
                self.validate_reading(reading)
                for reading in readings
            )
            if issue is not None
        ]

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
        station_readings = self._filter_by_station(station_id, readings)

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
        valid_readings = self._valid_readings(station_readings)

        return StationSummary(
            station_id=station_id,
            district=station_readings[0].district,
            readings_count=len(station_readings),
            invalid_count=len(issues),
            average_pm25=self._average_by_type(valid_readings, "pm25"),
            average_pm10=self._average_by_type(valid_readings, "pm10"),
            average_co2=self._average_by_type(valid_readings, "co2"),
            status=self._calculate_summary_status(valid_readings),
        )

    def calculate_city_status(
        self,
        readings: Iterable[SensorReading],
    ) -> QualityStatus:
        statuses = [
            self.detect_status(reading.sensor_type, reading.value)
            for reading in readings
            if self.validate_reading(reading) is None
        ]

        return self._highest_status(statuses)

    def find_stations(
        self,
        readings: Iterable[SensorReading],
    ) -> list[str]:
        return sorted(
            {
                reading.station_id
                for reading in readings
                if reading.station_id.strip()
            },
        )

    def build_station_report(
        self,
        readings: Iterable[SensorReading],
    ) -> list[StationSummary]:
        cached_readings = list(readings)

        return [
            self.calculate_station_summary(station_id, cached_readings)
            for station_id in self.find_stations(cached_readings)
        ]

    def _build_limits(self) -> dict[str, SensorLimits]:
        return {
            "pm25": SensorLimits(0.0, 1000.0, 35.0, 75.0),
            "pm10": SensorLimits(0.0, 1500.0, 60.0, 150.0),
            "co2": SensorLimits(250.0, 10000.0, 1000.0, 2000.0),
            "temperature": SensorLimits(-60.0, 60.0, 35.0, 45.0),
            "humidity": SensorLimits(0.0, 100.0, 80.0, 95.0),
            "noise": SensorLimits(0.0, 140.0, 65.0, 85.0),
        }

    def _issue(
        self,
        reading: SensorReading,
        message: str,
    ) -> ValidationIssue:
        return ValidationIssue(
            station_id=reading.station_id,
            sensor_type=reading.sensor_type,
            message=message,
        )

    def _filter_by_station(
        self,
        station_id: str,
        readings: Iterable[SensorReading],
    ) -> list[SensorReading]:
        return [
            reading
            for reading in readings
            if reading.station_id == station_id
        ]

    def _valid_readings(
        self,
        readings: Iterable[SensorReading],
    ) -> list[SensorReading]:
        return [
            reading
            for reading in readings
            if self.validate_reading(reading) is None
        ]

    def _calculate_summary_status(
        self,
        readings: Iterable[SensorReading],
    ) -> QualityStatus:
        statuses = [
            self.detect_status(reading.sensor_type, reading.value)
            for reading in readings
        ]

        return self._highest_status(statuses)

    def _highest_status(
        self,
        statuses: list[QualityStatus],
    ) -> QualityStatus:
        if not statuses:
            return QualityStatus.INVALID

        if QualityStatus.CRITICAL in statuses:
            return QualityStatus.CRITICAL

        if QualityStatus.WARNING in statuses:
            return QualityStatus.WARNING

        return QualityStatus.NORMAL

    def _average_by_type(
        self,
        readings: Iterable[SensorReading],
        sensor_type: str,
    ) -> float | None:
        values = [
            reading.value
            for reading in readings
            if reading.sensor_type.lower() == sensor_type
        ]

        if not values:
            return None

        return round(mean(values), 2)
