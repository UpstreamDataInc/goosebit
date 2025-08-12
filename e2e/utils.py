import subprocess
from pathlib import Path
from typing import List


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
