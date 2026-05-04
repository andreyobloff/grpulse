from datetime import datetime

from src.models import SensorReading


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
