# Contributing

## Issues and PRs

- Anyone can open an issue.
- Issues are assigned by a maintainer to whoever will work on resolving them.
- To keep review load manageable, PRs are only reviewed if they:
  - resolve an issue you've been assigned to, or
  - are trivial (typos, small doc fixes, etc.).
- If you'd like to submit a larger change, please open an issue first so it can be discussed and assigned.
- Keep your PR in Draft until it's ready for review.

PRs that skip this process may be closed without review.

## Before opening a PR

- Format the Python code — see [Formatting](development.md#formatting).
- Follow the [docstring conventions](development.md#docstrings).
- If you add or change an endpoint, update [the API reference](api.md) and verify the behavior via the FastAPI docs at `/docs` or an HTTP client.

Run the same lint and formatting checks used by CI:

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
```

The `Lint and format` workflow runs on pull requests targeting `main` and pushes to `main`.
It reports violations without modifying files.
