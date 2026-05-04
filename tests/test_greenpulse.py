import subprocess
import sys

from src.demo_data import load_demo_readings
from src.models import QualityStatus
from src.services import GreenPulseDataQualityService


def test_application_runs_successfully() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "src.greenpulse_app"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "GreenPulse data quality review" in result.stdout
    assert "city_status=critical" in result.stdout
    assert "validation_issues=2" in result.stdout


def test_city_status_is_calculated_correctly() -> None:
    service = GreenPulseDataQualityService()
    readings = load_demo_readings()

    assert service.calculate_city_status(readings) == QualityStatus.CRITICAL


def test_validation_detects_invalid_readings() -> None:
    service = GreenPulseDataQualityService()
    readings = load_demo_readings()
    issues = service.validate_batch(readings)

    assert len(issues) == 2


if __name__ == "__main__":
    test_application_runs_successfully()
    test_city_status_is_calculated_correctly()
    test_validation_detects_invalid_readings()
    print("GreenPulse refactoring tests passed")
