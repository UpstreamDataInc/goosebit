import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple

import boto3
import httpx
import pytest
from botocore.exceptions import ClientError

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:60053")
MINIO_URL = os.getenv("E2E_MINIO_URL", "http://localhost:9000")
MINIO_BUCKET = os.getenv("E2E_MINIO_BUCKET", "goosebit")
MINIO_ACCESS_KEY = os.getenv("E2E_MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("E2E_MINIO_SECRET_KEY", "minioadmin")


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
    # Wait for services once per session
    ok, err = wait_for_service(f"{BASE_URL}/docs", timeout_seconds=180)
    assert ok, f"goosebit not ready: {err}"
    ok, err = wait_for_service(f"{MINIO_URL}/minio/health/live", timeout_seconds=180)
    assert ok, f"minio not ready: {err}"
    ensure_minio_bucket()
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
# MinIO helpers
# ---------------------


def ensure_minio_bucket():
    s3 = boto3.resource(
        "s3",
        endpoint_url=MINIO_URL,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )

    bucket = s3.Bucket(MINIO_BUCKET)
    try:
        s3.meta.client.head_bucket(Bucket=MINIO_BUCKET)
        print(f"MinIO bucket '{MINIO_BUCKET}' exists")
    except ClientError:
        print(f"\nCreating MinIO bucket '{MINIO_BUCKET}'...\n")
        bucket.create(CreateBucketConfiguration={"LocationConstraint": "us-east-1"})


# ---------------------
# Software helpers
# ---------------------


def _ensure_artifact(client: httpx.Client, token: str) -> tuple[dict, str]:
    """Ensure a software artifact exists (upload if needed). Return the chosen software dict and its version."""
    list_resp = client.get("/api/v1/software", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    items = list_resp.json().get("software", [])

    if not items:
        # Upload artifact
        swu_path = Path(__file__).resolve().parents[1] / "update.swu"
        assert swu_path.exists(), f"Missing test artifact: {swu_path}"
        with swu_path.open("rb") as f:
            files = {"file": (swu_path.name, f, "application/octet-stream")}
            up_resp = client.post("/api/v1/software", files=files, headers={"Authorization": f"Bearer {token}"})
        assert up_resp.status_code == 200, up_resp.text
        uploaded_id = up_resp.json()["id"]
        # Re-fetch to get version
        list_resp = client.get("/api/v1/software", headers={"Authorization": f"Bearer {token}"})
        items = list_resp.json()["software"]
        sw = next(x for x in items if x["id"] == uploaded_id)
    else:
        sw = items[-1]

    sw_version = sw["version"]
    return sw, sw_version


def _ensure_artifact_and_rollout(client: httpx.Client, token: str, feed: str = "default") -> tuple[dict, str]:
    """Ensure an artifact exists and create a rollout targeting the given feed.
    Returns the software dict and its version.
    """
    sw, version = _ensure_artifact(client, token)
    ro_resp = client.post(
        "/api/v1/rollouts",
        json={"name": f"e2e {version}", "feed": feed, "software_id": sw["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ro_resp.status_code == 200, ro_resp.text
    ro_id = ro_resp.json().get("id")
    assert isinstance(ro_id, int), f"Invalid rollout id: {ro_resp.text}"
    return sw, version


def test_e2e_smoke_setup_login_and_basic_routes(ensure_services_ready):
    with httpx.Client(base_url=BASE_URL, follow_redirects=True, timeout=20.0) as client:
        token = _auth_token(client)

        # Protected API
        api_resp = client.get("/api/v1/devices", headers={"Authorization": f"Bearer {token}"})
        assert api_resp.status_code == 200, api_resp.text

        # UI page via session cookie
        client.cookies.set("session_id", token)
        ui_resp = client.get("/ui/devices")
        assert ui_resp.status_code == 200, f"Expected 200 rendering devices UI, got {ui_resp.status_code}"
        assert "Devices" in ui_resp.text or "Edit Devices" in ui_resp.text

        # Root path renders while authenticated
        root_resp = client.get("/")
        assert root_resp.status_code == 200
        assert "gooseBit" in root_resp.text or "Devices" in root_resp.text


def test_e2e_artifact_upload_and_minio_presence(ensure_services_ready):
    with httpx.Client(base_url=BASE_URL, follow_redirects=True, timeout=20.0) as client:
        token = _auth_token(client)
        sw, _ = _ensure_artifact(client, token)

        # Verify artifact presence in MinIO when applicable
        sw_name = sw.get("name")
        sw_hash = sw.get("hash")
        if sw_name and isinstance(sw_name, str) and sw_name.startswith(f"s3://{MINIO_BUCKET}/"):
            key = sw_name.replace(f"s3://{MINIO_BUCKET}/", "")
            assert sw_hash and sw_hash in key, f"Expected object key to include hash {sw_hash}, got {key}"
            s3c = boto3.client(
                "s3",
                endpoint_url=MINIO_URL,
                aws_access_key_id=MINIO_ACCESS_KEY,
                aws_secret_access_key=MINIO_SECRET_KEY,
            )
            deadline_s3 = time.time() + 30
            last_exc = None
            while time.time() < deadline_s3:
                try:
                    s3c.head_object(Bucket=MINIO_BUCKET, Key=key)
                    break
                except ClientError as e:
                    last_exc = e
                    time.sleep(1.0)
            else:
                raise AssertionError(f"Object not found in MinIO bucket={MINIO_BUCKET}, key={key}: {last_exc}")


def test_e2e_device_update_rollout_to_version(ensure_services_ready):
    # Sanity: service docs should be reachable
    ok, err = wait_for_service(f"{BASE_URL}/docs", timeout_seconds=180)
    assert ok, f"Service not ready: {err}"

    with httpx.Client(base_url=BASE_URL, follow_redirects=True, timeout=20.0) as client:
        token = _auth_token(client)

        # Ensure we have an artifact and rollout prepared
        _, target_version = _ensure_artifact_and_rollout(client, token)

        # Poll until a device registers (created by e2e/swupdate container)
        deadline = time.time() + 60
        dev_id = None
        initial_version = None
        while time.time() < deadline and dev_id is None:
            devices = client.get("/api/v1/devices", headers={"Authorization": f"Bearer {token}"})
            assert devices.status_code == 200
            body = devices.json()
            devs = body.get("devices", [])
            if devs:
                # Pick the most recently seen device
                dev = sorted(devs, key=lambda d: d.get("last_seen") or 0, reverse=True)[0]
                dev_id = dev["id"]
                initial_version = dev.get("sw_version")
                break
            time.sleep(3.0)
        assert dev_id, "No device registered with the update server in time"

        # Now wait until the device reports the new version and finished state
        finished = False
        observed_version = None
        while time.time() < deadline:
            d = client.get(f"/api/v1/devices/{dev_id}", headers={"Authorization": f"Bearer {token}"})
            assert d.status_code == 200
            dev = d.json()
            observed_version = dev.get("sw_version")
            if observed_version == target_version:
                finished = True
                break
            time.sleep(5.0)

        assert finished, (
            f"Device {dev_id} did not finish update to {target_version}. "
            f"initial={initial_version}, observed={observed_version}"
        )
