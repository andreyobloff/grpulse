from src.demo_data import load_demo_readings
from src.models import QualityStatus
from src.services import GreenPulseDataQualityService
from src.greenpulse_app import format_station_summary


def test_city_status_is_calculated_correctly() -> None:
    service = GreenPulseDataQualityService()
    readings = load_demo_readings()

    assert service.calculate_city_status(readings) == QualityStatus.CRITICAL


def test_validation_detects_invalid_readings() -> None:
    service = GreenPulseDataQualityService()
    readings = load_demo_readings()
    issues = service.validate_batch(readings)

    assert len(issues) == 2


def test_station_report_is_created() -> None:
    service = GreenPulseDataQualityService()
    readings = load_demo_readings()
    report = service.build_station_report(readings)

    assert len(report) == 4
    assert report[0].station_id == "MSK-001"


def test_station_summary_formatting() -> None:
    service = GreenPulseDataQualityService()
    readings = load_demo_readings()
    summary = service.calculate_station_summary("MSK-001", readings)
    formatted_summary = format_station_summary(summary)

    assert "station=MSK-001" in formatted_summary
    assert "district=ЦАО" in formatted_summary
    assert "status=normal" in formatted_summary


if __name__ == "__main__":
    test_city_status_is_calculated_correctly()
    test_validation_detects_invalid_readings()
    test_station_report_is_created()
    test_station_summary_formatting()
    print("GreenPulse tests passed")
