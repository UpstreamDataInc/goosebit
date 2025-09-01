# gooseBit Plugin for Forwarded HTTP Header Support

Enables the use of standard Forwarded HTTP headers (RFC 7239). This has
been introduced because uvicorn (in conjunction with gunicorn) does not
support the feature (yet): [uvicorn#2237]

[uvicorn#2237]: https://github.com/encode/uvicorn/issues/2237

## Installation

When using a Docker image, the plugin can be installed as follows:

```dockerfile
FROM upstreamdata/goosebit

USER root

RUN pip install --no-cache-dir goosebit-forwarded-header

USER goosebit
```

## Configuration

Enable the plugin in `goosebit.yaml` (or set the corresponding environment variable):

```yaml
plugins:
  - goosebit_forwarded_header
```
