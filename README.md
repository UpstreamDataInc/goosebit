# gooseBit

<img src="https://upstreamdatainc.github.io/goosebit/img/goosebit-logo.png" style="width: 100px; height: 100px; display: block;">

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/UpstreamDataInc/goosebit/badge)](https://scorecard.dev/viewer/?uri=github.com/UpstreamDataInc/goosebit)

---

A simplistic, opinionated remote update server implementing hawkBit™'s [DDI API](https://eclipse.dev/hawkbit/apis/ddi_api/).

## Deployment

### Docker Compose Demo

The Docker Compose demo [docker/demo/docker-compose.yml] may serve as inspiration for a containerized (cloud) deployment.
It uses PostgreSQL as the database and NGINX as a reverse proxy.

> [!WARNING]
> Do not use the demo (as-is) in production!

Make sure you have [Docker](https://www.docker.com/get-started/) (and Docker Compose) installed.
Then run:

```txt
docker compose -f docker/demo/docker-compose.yml up
```

Visit gooseBit at: [https://localhost](https://localhost)

[docker/demo/docker-compose.yml]: https://github.com/UpstreamDataInc/goosebit/blob/master/docker/demo/docker-compose.yml

### Configuration

gooseBit can be configured through a configuration file (`/etc/goosebit.yaml`) or by setting environment variables.
For the available options and their defaults, see [goosebit.yaml].
The environment variable corresponding to e.g. the `poll_time` YAML setting would be `GOOSEBIT_POLL_TIME`.
Environment variables for nested settings are constructed using `__` as the separator:

```txt
GOOSEBIT_DEVICE_AUTH__ENABLE=true
```

Alternatively, a JSON string can be assigned:

```txt
GOOSEBIT_DEVICE_AUTH='{"enable": true}'
```

[goosebit.yaml]: https://github.com/UpstreamDataInc/goosebit/blob/master/goosebit.yaml

### Database

By default, SQLite is used as the database. For more sophisticated setups, PostgreSQL is supported.
To use PostgreSQL, set `db_uri` or the `GOSSEBIT_DB_URI` environment variable to something like:

```txt
postgres://user:password@host:5432/db_name
```

### Artifact Storage

The software packages managed by gooseBit are either stored on the local filesystem (`artifacts_dir` setting) or an S3-compatible object storage.

## Assumptions

- Devices use [SWUpdate](https://swupdate.org) for managing software updates.

## Features

### Device Registry

When a device connects to gooseBit for the first time, it is automatically added to the device registry. The server will then request the device's configuration data, including:

- `hw_model` and `hw_revision`: Used to match compatible software.
- `sw_version`: Indicates the currently installed software version.

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

## Development with Poetry

### Initial Setup

Install Poetry as described [here](https://python-poetry.org/docs/#installation).

Then, to install gooseBit's dependencies, run:

```txt
poetry install
```

Initialize the database:

```txt
poetry run aerich upgrade
```

Launch gooseBit:

```txt
poetry run python -m goosebit
```

The service is now available at: [http://localhost:60053](http://localhost:60053)

### Database

Initialize or migrate database:

```txt
poetry run aerich upgrade
```

After a model change create the migration:

```txt
poetry run aerich migrate
```

To seed some sample data (attention: drops all current data) use:

```txt
poetry run generate-sample-data
```

### Code formatting and linting

Code is formatted using different tools

- black and isort for `*.py`
- biomejs for `*.js`, `*.json`
- prettier for `*.html`, `*.md`, `*.yml`, `*.yaml`

Code is linted using different tools as well

- flake8 for `*.py`
- biomejs for `*.js`

Best to have pre-commit install git hooks that run all those tools before a commit:

```txt
poetry run pre-commit install
```

To manually apply the hooks to all files use:

```txt
poetry run pre-commit run --all-files
```

### Testing

Tests are implemented using pytest. You can run all the tests with:

```txt
poetry run pytest
```

To run only the unit tests:

```txt
poetry run pytest tests/unit
```

To run only the end-to-end tests:

```txt
poetry run pytest tests/e2e
```

## Development with Docker (and PostgreSQL)

### Running the Containers

```txt
docker compose -f docker/docker-compose-dev.yml up --build
```

### Applying the Migrations

```txt
docker exec goosebit-dev python -m aerich upgrade
```

### Using the Interactive Debugger

You might need [rlwrap](https://github.com/hanslub42/rlwrap) to fix readline support.

Place `breakpoint()` before the code you want to debug. The server will reload automatically.
Then, connect to remote PDB (when the breakpoint has been hit):

```txt
rlwrap telnet localhost 4444
```

To exit the debugger, press `Ctrl + ]` and then `q`.

## Architecture

### Structure

The structure of gooseBit is as follows:

- `api`: Files for the API.
- `ui`: Files for the UI.
  - `bff`: Backend for frontend API.
  - `static`: Static files.
  - `templates`: Jinja2 formatted templates.
  - `nav`: Navbar handler.
- `updater`: DDI API handler and device update manager.
- `updates`: SWUpdate file parsing.
- `auth`: Authentication functions and permission handling.
- `models`: Database models.
- `db`: Database config and initialization.
- `schema`: Pydantic models used for API type hinting.
- `settings`: Settings loader and handler.
- `storage`: Storage for software artifacts.
- `telemetry`: Telemetry data handlers.
- `routes`: Routes for a giving endpoint, including the router.
