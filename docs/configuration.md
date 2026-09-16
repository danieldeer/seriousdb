# Project configuration

By default, the project requires zero configuration.
This means the application runs out of the box without additional setup.

To apply custom configurations, environment variables are used.

## Adding new environment variables (for Developers)

In this project, environment variables must be prefixed with `SERIOUSDB_` to avoid conflicts with other system variables.

An environment variable must always be accessed inside [config.py](../src/seriousdb/config.py) and imported from there.
Reading an environment variable requires a default value to align with the zero-config principle.
Every new environment variable must be added to the `.env.example` file along with a brief explanatory description.

### Examples

`.env.example` and `.env`
```bash
EXAMPLE_KEY=EXAMPLE_VALUE # Wrong. Missing prefix and description

# Example variable to show how it must be defined
SERIOUSDB_EXAMPLE_KEY=EXAMPLE_VALUE # Right. Includes prefix and description
```

`config.py`
```python
EXAMPLE_KEY = os.getenv("SERIOUSDB_EXAMPLE_KEY")  # Wrong. Missing default value

EXAMPLE_KEY = os.getenv(
    "SERIOUSDB_EXAMPLE_KEY", "example default value"
)  # Right. Has a default value
```

### How to use environment variables in code

As mentioned above, environment variables must always be read inside `config.py`. From there, they can be imported app-wide.

```python
example = os.getenv(
    "SERIOUSDB_EXAMPLE_KEY", "example default value"
)  # Wrong. Must be accessed in config.py

# ---

from .config import EXAMPLE_KEY

example = EXAMPLE_KEY  # Right. Imported from config-py
```

## Configuring environment variables (for Users)

The project provides a `.env.example` file which can be copied and renamed to `.env` to apply custom settings.
Undefined environment variables will fall back to the default values defined in `config.py`.

More information about individual environment variables and their default values can be found in `config.py` or `.env.example`.
