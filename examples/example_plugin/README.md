# gooseBit Example Plugin

This is a basic example plugin to provide a framework for creating custom plugins for gooseBit.

## Plugin Requirements

Plugins are identified automatically with entry points. This means that you must define the relevant section in your `pyproject.toml` file.

### `poetry`

```toml
[tool.poetry.plugins.'goosebit.plugins']
example_plugin = "example_plugin"
```

### Other systems

```toml
[proejct.entry-points.'goosebit.plugins']
example_plugin = "example_plugin"
```
