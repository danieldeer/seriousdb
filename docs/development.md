# Development guide

## Requirements

- Python 3.11 or newer
- `uv`

## Setup

```bash
uv sync
uv run pre-commit install
```

To sync development dependencies run following command:

```bash
uv sync --group dev
```

## Try it out

Open a Python shell with the project's dependencies available:

```bash
uv run python
```

```python
import seriousdb

seriousdb.set("name", "Alice")
seriousdb.get("name")
```

## Nix

> The project provides a Nix development environment with the tools required for local development.

### Enter Nix develop

From the project root, run:

```bash
nix develop
```

This starts a shell with the project's development dependencies available.

### Nix (in the Nix Shell)

```bash
python
```

Then import and use `seriousdb` as shown above.

## Formatting

### Format Python files with `ruff`:

#### uv

```bash
uv run ruff format .
```

### Nix (in Nix Shell)

```bash
ruff format .
```

### To check formatting without changing files:

#### uv

```bash
uv run ruff format --check .
```

### Nix (in Nix Shell)

```bash
ruff format --check .
```

## Markdown formatting

Markdown files are formatted with [`mdformat`](https://github.com/hukkin/mdformat)
(GFM tables and task lists via
[`mdformat-gfm`](https://github.com/hukkin/mdformat-gfm)).
Both are pinned in the `dev` dependency group because the formatting style may
change between versions.

### Format Markdown files with `mdformat`:

Tracked Markdown files only (`git ls-files` skips ignored files such as
`.pytest_cache/README.md`, which a bare `mdformat .` would pick up after a
test run). Generated files under `docs/reference/` are excluded:
they are owned by `scripts/docs-reference.py`, which has its own
staleness check.

#### uv (bash)

```bash
uv run --locked mdformat $(git ls-files '*.md' ':!docs/reference/**')
```

#### uv (PowerShell)

```powershell
uv run --locked mdformat (git ls-files '*.md' ':!docs/reference/**')
```

### Nix (in Nix Shell)

```bash
mdformat $(git ls-files '*.md' ':!docs/reference/**')
```

### To check formatting without changing files:

#### uv (bash)

```bash
uv run --locked mdformat --check $(git ls-files '*.md' ':!docs/reference/**')
```

#### uv (PowerShell)

```powershell
uv run --locked mdformat --check (git ls-files '*.md' ':!docs/reference/**')
```

### Nix (in Nix Shell)

```bash
mdformat --check $(git ls-files '*.md' ':!docs/reference/**')
```

## Linting

### Lint python files with `ruff`:

#### uv

```bash
uv run ruff check .
```

#### Nix (in Nix Shell)

```bash
ruff check .
```

### Type checking with `ty`

#### uv

```bash
uv run ty check .
```

#### Nix (in Nix Shell)

```bash
ty check .
```

### To fix linter errors and warning if possible run following command:

#### uv

```bash
uv run ruff check --fix .
```

### Nix (in Nix Shell)

```bash
ruff check --fix .
```

## Docstrings

Python docstrings follow the [NumPy style](https://numpydoc.readthedocs.io/en/latest/format.html).

Docstrings are required for public functions, classes and modules only; for private ones (prefixed
with `_`) they are optional. This is enforced by `ruff` (see [Linting](#linting)).

A docstring starts with a one-line summary, followed by the sections that apply, such as
`Parameters`, `Returns` and `Raises`:

```python
def select(self, key: str) -> str:
    """Return the value stored under `key`.

    Parameters
    ----------
    key : str
        Key to look up.

    Returns
    -------
    str
        The value stored under `key`.

    Raises
    ------
    ResourceNotFoundError
        If `key` does not exist.
    ServiceUnavailableError
        If no database has been loaded.
    """
```

See [`cache.py`](../src/seriousdb/cache.py) and [`api.py`](../src/seriousdb/api.py) for more
examples.

## Documentation

The docstrings above are the source for a generated, docstring-level API reference committed at
[`docs/reference/`](reference/index.md).
built with [Sphinx](https://www.sphinx-doc.org/) and
[sphinx-markdown-builder](https://pypi.org/project/sphinx-markdown-builder/) so it renders as plain
Markdown on GitHub — no hosted docs site required.

`docs/reference/` is committed, not gitignored, so it's readable straight from the repo. Don't edit
files under it by hand: edit the docstring instead and regenerate.

### Regenerate

#### uv

```bash
uv sync --group docs
uv run --group docs python scripts/docs-reference.py
```

#### Nix (in Nix Shell)

```bash
python scripts/docs-reference.py
```

Commit any resulting changes under `docs/reference/` along with your docstring change. CI (see
[`.github/workflows/docs.yml`](../.github/workflows/docs.yml)) rebuilds it and fails the check if
the committed output doesn't match, so a stale reference is caught before merge.

### Adding a module

`docs/_sphinx/index.rst` lists the modules that get a generated page, currently `seriousdb.api` and
`seriousdb.exceptions` — the two modules [architecture.md](architecture.md) calls out as public. To
add another, add its dotted path to the `autosummary` list in that file and regenerate; the page
layout itself comes from the template at
[`docs/_sphinx/_templates/autosummary/module.rst`](_sphinx/_templates/autosummary/module.rst).
