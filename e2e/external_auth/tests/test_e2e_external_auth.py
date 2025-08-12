import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple

import httpx
import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:60053")
AUTH_SERVICE_BASE_URL = os.getenv("AUTH_SERVICE_BASE_URL", "http://localhost:8000")


# ---------------------
# Docker Compose helpers
# ---------------------


def _compose_cmd() -> list[str]:
    """Return a docker compose command list (v2 or fallback to docker-compose)."""
    compose_file = str(Path(__file__).resolve().parents[1] / "docker-compose.yml")
    # Try `docker compose`
    try:
        subprocess.run(["docker", "compose", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return ["docker", "compose", "-f", compose_file]
    except Exception:
        pass
    # Fallback `docker-compose`
    return ["docker-compose", "-f", compose_file]


def compose_up_build():
    cmd = _compose_cmd() + ["up", "-d", "--build"]
    print("\nRunning:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def compose_down():
    cmd = _compose_cmd() + ["down", "-v"]
    print("\nRunning:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


# ---------------------
# Pytest session-scoped fixtures
# ---------------------


@pytest.fixture(scope="session", autouse=True)
def compose_lifecycle():
    # Bring up compose once for the whole session
    compose_up_build()
    try:
        yield
    finally:
        # Always tear down at the end of session
        try:
            compose_down()
        except Exception as e:  # noqa: BLE001
            print("compose down failed:", e, file=sys.stderr)


@pytest.fixture(scope="session")
def ensure_services_ready(compose_lifecycle):
    ok, err = wait_for_service(f"{AUTH_SERVICE_BASE_URL}/health", timeout_seconds=20)
    assert ok, f"auth service not ready: {err}"

    ok, err = wait_for_service(f"{BASE_URL}/docs", timeout_seconds=20)
    assert ok, f"goosebit not ready: {err}"

    return True


# ---------------------
# HTTP helpers
# ---------------------


def wait_for_service(url: str, timeout_seconds: int = 120) -> Tuple[bool, str]:
    deadline = time.time() + timeout_seconds
    last_err = ""
    while time.time() < deadline:
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(url)
                if r.status_code == 200:
                    return True, ""
                last_err = f"status={r.status_code} body_prefix={r.text[:120]}"
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
        time.sleep(1.0)
    return False, last_err


def _auth_token(client: httpx.Client) -> str:
    creds = {"username": "admin@goosebit.local", "password": "admin"}
    setup_resp = client.post("/setup", data=creds, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if setup_resp.status_code == 200:
        return setup_resp.json()["access_token"]
    login_resp = client.post("/login", data=creds, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert login_resp.status_code == 200, login_resp.text
    return login_resp.json()["access_token"]


# ---------------------
# External Auth Tests
# ---------------------


def test_e2e_external_auth_smoke_and_health(ensure_services_ready):
    """Smoke test for external auth setup and goosebit endpoints"""

    with httpx.Client(base_url=AUTH_SERVICE_BASE_URL, follow_redirects=True, timeout=10.0) as client:
        health_resp = client.get("/health")
        assert health_resp.status_code == 200, f"Health check for auth service failed {health_resp.text}"

    with httpx.Client(base_url=BASE_URL, follow_redirects=True, timeout=10.0) as client:
        token = _auth_token(client)

        # Verify docs endpoint works
        health_resp = client.get("/docs")
        assert health_resp.status_code == 200, f"Health check for goosebit failed: {health_resp.text}"

        # Verify API access works
        api_resp = client.get("/api/v1/devices", headers={"Authorization": f"Bearer {token}"})
        assert api_resp.status_code == 200, api_resp.text


def test_e2e_device_registration_with_external_auth(ensure_services_ready):
    """Test device registration with external authentication - verify device state is REGISTERED not UNKNOWN"""

    with httpx.Client(base_url=BASE_URL, follow_redirects=True, timeout=20.0) as client:
        token = _auth_token(client)

        deadline = time.time() + 20
        dev_id = None
        registered_device = None

        while time.time() < deadline and dev_id is None:
            devices_resp = client.get("/api/v1/devices", headers={"Authorization": f"Bearer {token}"})
            assert devices_resp.status_code == 200, f"Failed to get devices: {devices_resp.text}"

            devices_data = devices_resp.json()
            devices = devices_data.get("devices", [])

            if devices:
                # Look for devices with REGISTERED state (not UNKNOWN)
                for device in devices:
                    device_state = device.get("last_state", "unknown").lower()

                    if device_state == "registered":
                        registered_device = device
                        dev_id = device["id"]
                        break

                if dev_id:
                    break

            time.sleep(5.0)

        assert dev_id, "No device with REGISTERED state found with external auth in time"
        assert registered_device is not None, "No registered device data found"

        # Verify device has required fields and proper state
        assert (
            registered_device.get("last_state", "").lower() == "registered"
        ), f"Device state is {registered_device.get('last_state')}, expected REGISTERED"
        assert "id" in registered_device, "Device missing id"
        assert "last_seen" in registered_device, "Device missing last_seen"

        # Verify external auth worked by checking device can be accessed individually
        device_detail_resp = client.get(f"/api/v1/devices/{dev_id}", headers={"Authorization": f"Bearer {token}"})
        assert device_detail_resp.status_code == 200, f"Cannot access device details: {device_detail_resp.text}"
        device_detail = device_detail_resp.json()
        assert device_detail["id"] == dev_id
        assert (
            device_detail.get("last_state", "").lower() == "registered"
        ), f"Individual device fetch shows state {device_detail.get('last_state')}, expected REGISTERED"
