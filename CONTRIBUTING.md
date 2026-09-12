# Contributing to seriousdb

Thanks for your interest in contributing! This project is a small, early-stage
key-value store, which makes it a great place to make your first open source
contribution.

## Getting Started

1. Fork the repository and clone your fork:

   ```bash
   git clone https://github.com/YOUR-USERNAME/seriousdb.git
   cd seriousdb
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the project and its dependencies:

   ```bash
   pip install .
   ```

4. Create a branch for your change:

   ```bash
   git checkout -b my-change
   ```

## Making Changes

- Keep pull requests small and focused on a single change. This makes them
  easier to review and more likely to be merged quickly.
- If your change addresses an open issue, reference it in your commit message
  and pull request description (e.g. `Closes #3`).
- If you're planning a larger change, consider opening an issue first to
  discuss it before investing significant time.

## Code Formatting

Before submitting a pull request, format your code with
[Black](https://black.readthedocs.io/):

```bash
uv tool run black <src>
```

## Submitting a Pull Request

1. Push your branch to your fork:

   ```bash
   git push origin my-change
   ```

2. Open a pull request against the `main` branch of
   `danieldeer/seriousdb`.
3. Describe what your change does and why. If it closes an issue, mention it
   explicitly (e.g. `Closes #3`).

## Questions

If anything is unclear, feel free to open an issue asking for clarification.
