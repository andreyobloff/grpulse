import subprocess
import sys

result = subprocess.run(
    [sys.executable, "src/greenpulse_app.py"],
    capture_output=True,
    text=True
)

assert "GreenPulse application started" in result.stdout
print("GreenPulse tests passed")
