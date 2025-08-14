import subprocess
import time
from pathlib import Path
from typing import List, Tuple

import httpx


def compose_cmd(compose_file: Path) -> List[str]:
    """Return a docker compose command list (v2 or fallback to docker-compose).

    Always pins the compose file passed by the caller so each suite can use its own
    docker-compose.yml living alongside the tests.
    """
    compose_file = Path(compose_file).resolve()
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return ["docker", "compose", "-f", str(compose_file)]
    except Exception:
        return ["docker-compose", "-f", str(compose_file)]


def compose_up_build(compose_file: Path) -> None:
    cmd = compose_cmd(compose_file) + ["up", "-d", "--build"]
    print("\nRunning:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def compose_down(compose_file: Path, remove_orphans: bool = True) -> None:
    cmd = compose_cmd(compose_file) + ["down", "-v"]
    if remove_orphans:
        cmd.append("--remove-orphans")
    print("\nRunning:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


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


def auth_token(client: httpx.Client) -> str:
    creds = {"username": "admin@goosebit.local", "password": "admin"}
    setup_resp = client.post("/setup", data=creds, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if setup_resp.status_code == 200:
        return setup_resp.json()["access_token"]
    login_resp = client.post("/login", data=creds, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert login_resp.status_code == 200, login_resp.text
    return login_resp.json()["access_token"]
