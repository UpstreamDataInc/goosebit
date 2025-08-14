import os
import sys
from pathlib import Path

import httpx
import pytest

from tests.e2e.utils import auth_token, compose_down, compose_up_build, wait_for_service

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:60053")
AUTH_SERVICE_BASE_URL = os.getenv("AUTH_SERVICE_BASE_URL", "http://localhost:8000")

COMPOSE_FILE = Path(__file__).resolve().parents[1].joinpath("docker-compose-invalid.yml")


def _compose_up_build():
    compose_up_build(COMPOSE_FILE)


def _compose_down():
    compose_down(COMPOSE_FILE, remove_orphans=True)


@pytest.fixture(scope="module", autouse=True)
def compose_lifecycle():
    # Ensure a clean slate for this module, then bring up compose
    try:
        _compose_down()
    except Exception as e:  # noqa: BLE001
        print("pre-clean compose down ignored:", e, file=sys.stderr)
    _compose_up_build()
    try:
        yield
    finally:
        # Always tear down at the end of module
        try:
            _compose_down()
        except Exception as e:  # noqa: BLE001
            print("compose down failed:", e, file=sys.stderr)


@pytest.fixture(scope="module")
def ensure_services_ready(compose_lifecycle):
    ok, err = wait_for_service(f"{AUTH_SERVICE_BASE_URL}/health", timeout_seconds=20)
    assert ok, f"auth service not ready: {err}"

    ok, err = wait_for_service(f"{BASE_URL}/docs", timeout_seconds=20)
    assert ok, f"goosebit not ready: {err}"

    return True


def test_e2e_external_auth_smoke_and_health(ensure_services_ready):
    """Smoke test for external auth setup and goosebit endpoints"""

    with httpx.Client(base_url=AUTH_SERVICE_BASE_URL, follow_redirects=True, timeout=10.0) as client:
        health_resp = client.get("/health")
        assert health_resp.status_code == 200, f"Health check for auth service failed {health_resp.text}"

    with httpx.Client(base_url=BASE_URL, follow_redirects=True, timeout=10.0) as client:
        token = auth_token(client)

        # Verify docs endpoint works
        health_resp = client.get("/docs")
        assert health_resp.status_code == 200, f"Health check for goosebit failed: {health_resp.text}"

        # Verify API access works
        api_resp = client.get("/api/v1/devices", headers={"Authorization": f"Bearer {token}"})
        assert api_resp.status_code == 200, api_resp.text


def test_e2e_device_registration_with_invalid_token_should_not_work(ensure_services_ready):
    """Verify device with invalid token does not appear in the database or list"""

    with httpx.Client(base_url=BASE_URL, follow_redirects=True, timeout=20.0) as client:
        token = auth_token(client)
        devices_resp = client.get("/api/v1/devices", headers={"Authorization": f"Bearer {token}"})

        assert devices_resp.status_code == 200, f"Failed to get devices: {devices_resp.text}"

        devices_data = devices_resp.json()
        devices = devices_data.get("devices", [])

        assert len(devices) == 0, f"Expected no devices, but found {len(devices)} devices: {devices}"
