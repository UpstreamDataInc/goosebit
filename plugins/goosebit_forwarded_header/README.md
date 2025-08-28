# gooseBit Plugin for Forwarded HTTP Header Support

Enables the use of standard Forwarded HTTP headers (RFC 7239). This has
been introduced because uvicorn (in conjunction with gunicorn) does not
support the feature (yet): [uvicorn#2237]

[uvicorn#2237]: https://github.com/encode/uvicorn/issues/2237

## Installation

E.g. in Dockerfile, install with pip:

```txt
pip install goosebit-forwarded-header
```

## Configuration

Enable the plugin in `goosebit.yaml`:

```yaml
plugins:
  - goosebit_forwarded_header
```
