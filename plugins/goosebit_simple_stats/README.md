# gooseBit Simple Stats Plugin

A simple example plugin for testing and understanding gooseBit's plugin system.

This plugin sets up a page which shows software count and/or device count.

## Installation

E.g. in Dockerfile, install with pip:

```txt
pip install goosebit-simple-stats
```

## Configuration

Enable the plugin in `goosebit.yaml`:

```yaml
plugins:
  - goosebit_simple_stats
```

Configure which data to show:

```yaml
simple_stats_show:
  - device_count
  - software_count
```
