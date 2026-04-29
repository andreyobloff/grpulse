import subprocess
import sys


def test_greenpulse_app_runs_successfully():
    result = subprocess.run(
        [sys.executable, "src/greenpulse_app.py"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "GreenPulse data quality review" in result.stdout
    assert "city_status=critical" in result.stdout
    assert "validation_issues=2" in result.stdout


if __name__ == "__main__":
    test_greenpulse_app_runs_successfully()
    print("GreenPulse tests passed")
