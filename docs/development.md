# Development

---

### Installation

Install development dependencies using [Poetry](https://python-poetry.org/):

```shell
poetry install --with dev
```

gooseBit also has dependencies for documentation and tests, you can install them all with:

```shell
poetry install --with dev,docs,tests
```

You can also just install all extras with:

```shell
poetry install --all-extras
```

## Development

### Code formatting and linting

Code is formatted using different tools

-   black and isort for `*.py`
-   biomejs for `*.js`, `*.json`
-   prettier for `*.html`, `*.md`, `*.yml`, `*.yaml`
-   djlint for `*.html.jinja`

Code is linted using different tools as well

-   flake8 for `*.py`
-   biomejs for `*.js`
-   djlint for `*.html.jinja`

Best to have pre-commit install git hooks that run all those tools before a commit:

```bash
poetry run pre-commit install
```

To manually apply the hooks to all files use:

```bash
poetry run pre-commit run --all-files
```

### Testing

Tests are implemented using pytest. To run all tests

```bash
poetry run pytest
```

### Structure

The structure of gooseBit is as follows:

-   `api`: Files for the API.
-   `ui`: Files for the UI.
    -   `bff`: Backend for frontend API.
    -   `static`: Static files.
    -   `templates`: Jinja2 formatted templates.
    -   `nav`: Navbar handler.
-   `updater`: DDI API handler and device update manager.
-   `updates`: SWUpdate file parsing.
-   `auth`: Authentication functions and permission handling.
-   `models`: Database models.
-   `db`: Database config and initialization.
-   `schema`: Pydantic models used for API type hinting.
-   `settings`: Settings loader and handler.
-   `telemetry`: Telemetry data handlers.
-   `routes`: Routes for a giving endpoint, including the router.
