# Contributing

## Issues and PRs

- Anyone can open an issue.
- Issues are assigned by a maintainer to whoever will work on resolving them.
- To keep review load manageable, PRs are only reviewed if they:
  - resolve an issue you've been assigned to, or
  - are trivial (typos, small doc fixes, etc.).
- If you'd like to submit a larger change, please open an issue first so it can be discussed and assigned.
- Keep your PR in Draft until it's ready for review.
- The target branch for PRs is always `development` branch.

PRs that skip this process may be closed without review.

## Before opening a PR

- Format the Python code — see [Formatting](development.md#formatting).
- Follow the [docstring conventions](development.md#docstrings).
- If you add or change a public function, update [the API reference](api.md) and add or adjust tests to cover the new behavior.

Commits are always run pre-commit to enforce `uv lock`, `type check` ,`pytest` , `linting`, `formatting` and `conventional commit`

---

## Commit Message Guidelines

This project follows the **Conventional Commits** version 1.0.0 specification for all commit messages.
These rules are validated and enforced via `pre-commit`.

---

### Format Reference

```text
<type>[optional scope]: <short summary>
<BLANK LINE>
[optional body: detailed explanation of motivation and context]
<BLANK LINE>
[optional footer(s): issue references, BREAKING CHANGE]
```

---

### Commit Types

- **`feat`**: A new feature for the user (bumps **MINOR**).
- **`fix`**: A bug fix for the user (bumps **PATCH**).
- **`docs`**: Documentation only changes (README, guides, docstrings).
- **`style`**: Formatting, white-space, missing semi-colons; no production code logic change.
- **`refactor`**: Code restructuring that neither fixes a bug nor adds a feature.
- **`perf`**: Code changes that improve performance / speed / memory usage (bumps **PATCH**).
- **`test`**: Adding missing tests or correcting existing tests; no production code change.
- **`build`**: Changes that affect the build system or external dependencies (`pyproject.toml`, package upgrades).
- **`ci`**: Changes to CI/CD configuration files and scripts (GitHub Actions, GitLab CI, `pre-commit.ci`).
- **`chore`**: Maintenance / housekeeping tasks that don't modify source code or tests (`.gitignore`, release scripts).
- **`revert`**: Reverts a previous commit.

> **Breaking Changes**: Append `!` after the type/scope (e.g., `feat!: drop python 3.8 support`) to indicate a **MAJOR** version bump. Document details in the footer starting with `BREAKING CHANGE:`.

---

### Body Structure & Rules

* **Blank Line**: Must be preceded by a single blank line after the subject line.
* **Line Length**: Wrap lines at **72 characters** (standard Git convention).
* **Content**: Focus on the **"why"** and **"what"**, not the "how" (the diff already shows how):
  * What is the motivation for this change?
  * How does it differ from previous behavior?
  * Are there any side effects or trade-offs?
* **Formatting**: Free-form text. Multiple paragraphs and markdown bullet points are allowed.

---

### Examples

**Example A: Simple Body**
```text
fix(auth): prevent token refresh race condition

Multiple concurrent API requests were triggering duplicate refresh calls,
invalidating active sessions. Added a mutex lock around the token 
exchange service.
```

**Example B: Multi-paragraph with Bullet Points**
```text
refactor(database): migrate connection pool to async engine

Replaces the synchronous connection pool to eliminate thread blocking 
under high concurrent load.

- Remove SQLAlchemy sync session handlers
- Initialize AsyncEngine in application lifespan
- Update repository methods to use async/await
```

**Example C: Breaking Change in Body/Footer**
```text
feat(api)!: switch authentication scheme to bearer tokens

Require OAuth2 Bearer tokens in Authorization headers instead of API keys.

BREAKING CHANGE: The `x-api-key` header is no longer accepted. All clients 
must migrate to `Authorization: Bearer <token>`.
```
