from src.demo_data import load_demo_readings
from src.models import StationSummary
from src.services import GreenPulseDataQualityService


def format_station_summary(summary: StationSummary) -> str:
    return "; ".join(
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

    for summary in station_report:
        print(format_station_summary(summary))

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
