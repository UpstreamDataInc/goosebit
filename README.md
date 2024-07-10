# goosebit
<img src="docs/img/goosebit-logo.png?raw=true" style="width: 100px; height: 100px; display: block;">

---

A simplistic remote update server.


## Setup

To set up, install the dependencies in `pyproject.toml` with `poetry install`.  Then you can run GooseBit by running `main.py`.

## Initial Startup

The first time you start GooseBit, you should change the default username and password inside `goosebit/settings.py`, as well as generate a new secret key.
The default login credentials for testing are `admin@goosebit.local`, `admin`.