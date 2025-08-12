# gooseBit Plugin Example

A simple example plugin for testing and understanding gooseBit's plugin system.

This example plugin sets up a page which shows software count and/or device count.

## Setup

### Installation

1. Load the plugin into poetry env (in goosebit):
    ```bash
    poetry install --with goosebit_simple_stats
    ```

### Configuration

1. Enable the plugin in `goosebit.yaml`:
    - Uncomment the lines:
        ```yaml
        plugins:
            - goosebit_simple_stats
        ```
2. Configure the plugin:
    - Uncomment the lines (choose which data you want to show):
        ```yaml
        simple_stats_show:
            - device_count
            - software_count
        ```
3. Run gooseBit as normal.
