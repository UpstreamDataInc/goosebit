# gooseBit Plugin for Forwarded HTTP Header Support

Enables the use of standard Forwarded HTTP headers (RFC 7239). This has
been introduced because uvicorn (in conjunction with gunicorn) does not
support the feature (yet): [uvicorn#2237]

[uvicorn#2237]: https://github.com/encode/uvicorn/issues/2237

## Setup

### Installation

1. Load the plugin into poetry env (in goosebit):

    ```txt
    poetry install --with goosebit_forwarded_header
    ```

### Configuration

1. Enable the plugin in `goosebit.yaml`:

    ```yaml
    plugins:
        - goosebit_forwarded_header
    ```

2. Run gooseBit as normal.
