# gooseBit
<img src="docs/img/goosebit-logo.png" style="width: 100px; height: 100px; display: block;">

---

A simplistic, opinionated remote update server implementing hawkBit™'s [DDI API](https://eclipse.dev/hawkbit/apis/ddi_api/).

## Setup

To set up, install the dependencies in `pyproject.toml` with `poetry install`.  Then you can run gooseBit by running `main.py`.

## Initial Startup

The first time you start gooseBit, you should change the default username and password inside `settings.yaml`.
The default login credentials for testing are `admin@goosebit.local`, `admin`.

## Assumptions
- [SWUpdate](https://swupdate.org) used on device side.

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
with the manually set feed and flavor values on a device to determine a matching rollout.

The feed is meant to model either different environments (like: dev, qa, live) or update channels (like. candidate,
fast, stable).

The flavor can be used for different type of builds (like: debug, prod).

### Pause updates
Device can be pinned to its current firmware.

### Realtime update logs
While an update is running, the update logs are captured and visualized in the frontend.