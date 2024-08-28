# gooseBit

<img src="docs/img/goosebit-logo.png" style="width: 100px; height: 100px; display: block;">

---

A simplistic, opinionated remote update server implementing hawkBit™'s [DDI API](https://eclipse.dev/hawkbit/apis/ddi_api/).

## Quick Start

### Installation

1. Install dependencies using [Poetry](https://python-poetry.org/):
    ```bash
    poetry install
    ```
2. Launch gooseBit:
    ```bash
    python main.py
    ```

### Initial Configuration

Before running gooseBit for the first time, update the default credentials in `settings.yaml`. The default login for testing purposes is:

-   **Username:** `admin@goosebit.local`
-   **Password:** `admin`

## Assumptions

-   Devices use [SWUpdate](https://swupdate.org) for managing software updates.

## Features

### Device Registry

When a device connects to gooseBit for the first time, it is automatically added to the device registry. The server will then request the device's configuration data, including:

-   `hw_model` and `hw_revision`: Used to match compatible software.
-   `sw_version`: Indicates the currently installed software version.

The registry tracks each device's status, including the last online timestamp, installed software version, update state, and more.

### Software Repository

Software packages (`*.swu` files) can be hosted directly on the gooseBit server or on an external server. gooseBit parses the software metadata to determine compatibility with specific hardware models and revisions.

### Device Update Modes

Devices can be configured with different update modes. The default mode is `Rollout`.

#### 1. Manual Update to Specified Software

Assign specific software to a device manually. Once installed, no further updates will be triggered.

#### 2. Automatic Update to Latest Software

Automatically updates the device to the latest compatible software, based on the reported `hw_model` and `hw_revision`. Note: versions are interpreted as [SemVer](https://semver.org) versions.

#### 3. Software Rollout

Rollouts target all devices with a specified "feed" value, ensuring that the assigned software is installed on all matching devices. Rollouts also track success and error rates, with future plans for automatic aborts. If multiple rollouts exist for the same feed, the most recent rollout takes precedence.

### Pause Updates

Devices can be pinned to their current software version, preventing any updates from being applied.

### Real-time Update Logs

While updates are in progress, gooseBit captures real-time logs, which are accessible through the device repository.

## Development

### Database

Create or upgrade database

```bash
poetry run aerich upgrade
```

After a model change create the migration

```bash
poetry run aerich migrate
```

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
-   `auth`: Authentication functions and permission handling.
-   `models`: Database models.
-   `db`: Database config and initialization.
-   `schema`: Pydantic models used for API type hinting.
-   `settings`: Settings loader and handler.
-   `telemetry`: Telemetry data handlers.
-   `routes`: Routes for a giving endpoint, including the router.
