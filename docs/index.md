# Home

---

### What is gooseBit?

A simplistic, opinionated remote update server implementing hawkBit™'s [DDI API](https://eclipse.dev/hawkbit/apis/ddi_api/),
designed to make remote updates of embedded devices easier.

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

Automatically updates the device to the latest compatible software, based on the reported `hw_model` and `hw_revision`.

#### 3. Software Rollout

Rollouts target all devices with a specified "feed" value, ensuring that the assigned software is installed on all matching devices. Rollouts also track success and error rates, with future plans for automatic aborts. If multiple rollouts exist for the same feed, the most recent rollout takes precedence.

### Pause Updates

Devices can be pinned to their current software version, preventing any updates from being applied.

### Real-time Update Logs

While updates are in progress, gooseBit captures real-time logs, which are accessible through the device repository.
