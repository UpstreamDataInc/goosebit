# gooseBit

<img src="docs/img/goosebit-logo.png" style="width: 100px; height: 100px; display: block;">

---

A simplistic, opinionated remote update server implementing hawkBit™'s [DDI API](https://eclipse.dev/hawkbit/apis/ddi_api/).

## Setup

To set up, install the dependencies in `pyproject.toml` with `poetry install`. Then you can run gooseBit by running `main.py`.

## Initial Startup

The first time you start gooseBit, you should change the default username and password inside `settings.yaml`.
The default login credentials for testing are `admin@goosebit.local`, `admin`.

## Assumptions

-   [SWUpdate](https://swupdate.org) used on device side.

## Current Feature Set

### Firmware repository

Uploading firmware images through frontend. All files should follow the format `{model}_{revision}_{version}`, where
`version` is either a semantic version or a datetime version in the format `YYYYMMDD-HHmmSS`.

### Automatic device registration

First time a new device connects, its configuration data is requested. `hw_model` and `hw_revision` are captured from
the configuration data (both fall back to `default` if not provided) which allows to distinguish different device
types and their revisions.

### Automatically update device to newest firmware

Once a device is registered it will get the newest available firmware from the repository based on model and revision.

### Manually update device to specific firmware

Frontend allows to assign specific firmware to be rolled out.

### Firmware rollout

Rollouts allow a fine-grained assignment of firmwares to devices. The reported device model and revision is combined
with the manually set feed value on a device to determine a matching rollout.

The feed is meant to model either different environments (like: dev, qa, live) or update channels (like. candidate,
fast, stable).

### Pause updates

Device can be pinned to its current firmware.

### Realtime update logs

While an update is running, the update logs are captured and visualized in the frontend.

## Development

### Code formatting and linting

Code is formatted using different tools

-   black and isort for `*.py`
-   biomejs for `*.js`, `*.json`
-   prettier for `*.html`, `*.md`, `*.yml`, `*.yaml`

Code is linted using different tools as well

-   flake8 for `*.py`
-   biomejs for `*.js`

Best to have pre-commit install git hooks that run all those tools before a commit:

```bash
poetry run pre-commit install
```

To manually apply the hooks to all files use:

```bash
pre-commit run --all-files
```

### Testing

Tests are implemented using pytest. To run all tests

```bash
poetry run pytest
```

### Structure

The structure of gooseBit is as follows:

-   `api`: Files for the API.
-   `ui`: Files for the UI.
    -   `bff`: Backend for frontend API.
    -   `static`: Static files.
    -   `templates`: Jinja2 formatted templates.
    -   `nav`: Navbar handler.
-   `updater`: DDI API handler and device update manager.
-   `updates`: SWUpdate file parsing.
-   `realtime`: Realtime API functionality with websockets.
-   `auth`: Authentication functions.
-   `models`: Database models.
-   `db`: Database config and initialization.
-   `schema`: Pydantic models used for API type hinting.
-   `permissions`: Permission handling and permission enums.
-   `settings`: Settings loader and handler.
-   `telemetry`: Telemetry data handlers.
-   `routes`: Routes for a giving endpoint, including the router.
