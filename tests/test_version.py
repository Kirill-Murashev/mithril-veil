import subprocess
import sys

from app import __version__
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_app_version_constant():
    assert __version__ == "0.1.0"


def test_health_endpoint_version():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == __version__


def test_cli_version_output():
    result = subprocess.run(
        [sys.executable, "-m", "app.cli.main", "version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout
