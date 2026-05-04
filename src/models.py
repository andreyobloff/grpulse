from dataclasses import dataclass
from datetime import datetime
from enum import Enum


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
