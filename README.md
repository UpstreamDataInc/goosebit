# gooseBit
<img src="docs/img/goosebit-logo.png" style="width: 100px; height: 100px; display: block;">

---

A simplistic remote update server implementing hawkBit™'s [DDI API](https://eclipse.dev/hawkbit/apis/ddi_api/).


## Setup

To set up, install the dependencies in `pyproject.toml` with `poetry install`.  Then you can run gooseBit by running `main.py`.

## Initial Startup

The first time you start gooseBit, you should change the default username and password inside `settings.yaml`.
The default login credentials for testing are `admin@goosebit.local`, `admin`.
