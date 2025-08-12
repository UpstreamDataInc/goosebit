# gooseBit E2E tests

This directory contains a minimal end-to-end (E2E) test that boots the app with docker-compose and exercises initial setup, auth, and a couple of protected routes.

## Prerequisites

- Docker + Docker Compose
- Python 3.11+ (to run the test runner locally) or use `docker compose run` to run tests in a container

## Services

`docker-compose.yml` starts:

- minio (S3-compatible storage)
- goosebit (the FastAPI app, listening on port 60053)
- swupdate (test client container; not used by the smoke test yet)

## Run

1. Build and start the stack

    ```bash
    cd e2e
    docker compose up -d --build
    ```

2. Run the tests from the repo root (they target http://localhost:60053 by default):

    ```bash
    poetry install --with tests
    poetry run pytest -q e2e/tests
    ```

    You can customize the base URL via env var:

    ```bash
    E2E_BASE_URL=http://127.0.0.1:60053 poetry run pytest -q e2e/tests
    ```

3. Tear down when done:

    ```bash
    docker compose down -v
    ```

## What the smoke test does

- Waits for `/docs` to become available
- POSTs to `/setup` to create the initial admin user
- Calls `/api/v1/devices` with Bearer token
- Sets the `session_id` cookie and loads `/ui/devices`
- Hits `/` and expects to land on the UI

## Next steps

- Add tests that upload artifacts to minio via the app and verify download URLs
- Exercise device flows (register device, assign rollout, check logs)
- Optionally run tests inside a container for hermetic CI
