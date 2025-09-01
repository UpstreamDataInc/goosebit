# gooseBit Simple Stats Plugin

A simple example plugin for testing and understanding gooseBit's plugin system.

This plugin sets up a page which shows software count and/or device count.

## Installation

When using a Docker image, the plugin can be installed as follows:

```dockerfile
FROM upstreamdata/goosebit

USER root

RUN pip install --no-cache-dir goosebit-simple-stats

USER goosebit
```

## Configuration

Enable the plugin in `goosebit.yaml` (or set the corresponding environment variable):

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
