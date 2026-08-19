# Run the full check suite: lint, typecheck, test.
_:
  @just lint typecheck test

# Format and lint the package using ruff.
lint:
  ruff format
  ruff check --fix

# Variant of `lint` that doesn't cause any changes to files (for CI).
lint-check:
  ruff format --check
  ruff check

# Run static type checker.
typecheck:
  pyright

# Run the test suite using pytest.
test:
  pytest

# Run tests with coverage report.
test-cov:
  pytest --cov=papis_stopwords --cov-report=term-missing --cov-fail-under=90

# Run the suite against a specific papis release, in a throwaway environment.
# The plugin subclasses papis private API, so the papis upper bound in
# pyproject.toml should only be raised once this passes for the new version.
test-papis version:
  #!/usr/bin/env bash
  set -euo pipefail
  venv="$(mktemp -d)/venv"
  uv venv "$venv" -q
  # The papis version is pinned explicitly here, so the project-wide
  # `exclude-newer` cutoff would only get in the way -- a release newer than
  # the cutoff is exactly what this recipe exists to test.
  uv pip install -q --python "$venv/bin/python" \
    --exclude-newer-package "papis=2100-01-01" \
    "papis=={{ version }}" pytest
  uv pip install -q --python "$venv/bin/python" --no-deps -e .
  "$venv/bin/python" -m pytest -q

# Build the wheel and source distribution.
build:
  uv build
