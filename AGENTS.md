# AGENTS.md

## Project overview

`papis-stopwords` — a [papis](https://github.com/papis/papis) formatter plugin that extends the built-in `python` formatter's word slice with stopword filtering and a join separator.

It exists to make citation keys readable: `ref-format` needs a few title words to disambiguate prolific authors, but the leading words of a title are often `On`, `The`, `Of`.

## Source layout

```
src/papis_stopwords/
  __init__.py      — the whole plugin: StopwordFormatter + spec parsing
tests/             — one test file
UPSTREAM.md        — draft feature request for papis itself (not yet filed)
```

## Commands

All via `just`; prefix with `uv run` if `just` isn't on the PATH.

| Command | What it does |
|---|---|
| `just` | lint → typecheck → test, in order |
| `just lint` | `ruff format` + `ruff check --fix` |
| `just lint-check` | Non-mutating variant for CI |
| `just typecheck` | `pyright` |
| `just test` | `pytest` |
| `just test-cov` | `pytest` with coverage, `--cov-fail-under=90` |
| `just test-papis 0.16.0` | Run the suite against one specific papis release |
| `just build` | `uv build` |

Setup: `uv sync --group dev`.

## The one thing to know before editing

**This plugin subclasses papis private API** — `papis.format.python._PythonStringFormatter`.

That is deliberate. Subclassing is what makes the plugin a strict superset of the built-in formatter: every stock pattern keeps working, and only the additions are new. Reimplementing `format_field` from scratch would drift from papis on every upstream change.

The cost is that a papis release can break it silently. Two guards exist:

- `dependencies = ["papis>=0.15,<0.17"]` — an explicit upper bound.
- `test_private_papis_api_is_still_present` — a canary test that fails with a clear message if the class moves.

**Raising the papis upper bound requires running `just test-papis <version>` first**, and adding the version to the `papis-versions` matrix in `.github/workflows/ci.yml`. Do not raise it on the strength of `uv sync` succeeding.

## Design constraints worth not rediscovering

- **The stopword flag cannot be a conversion (`!n`).** PEP 3101 permits one conversion per replacement field, so `{doc[title]!n!t:0.3S}` raises `ValueError`, and title-casing is needed at the same time. It has to live in the format spec.
- **Order matters and is free.** `convert_field` runs before `format_field`, so `!t` has already applied when stopwords are dropped, and stopwords are dropped before the slice — three words in means three *useful* words out.
- **`python-slugify` is a dead end.** It already accepts `stopwords=` and `ref_cleanup` already calls it, which makes it look like a five-line fix. It runs after truncation, is case-sensitive when `lowercase=False`, and splits on the separator, which is empty in a `ref-word-separator =` setup.
- **The separator is not cosmetic.** Building a key from several single-word slices leaves a dangling separator when the title is short (`LeCun2015_Deep_Learning_`); joining inside one slice makes the empty slot impossible.

## Deviations from the standard package template

- `requires-python = ">=3.10"` rather than `>=3.12`, to match papis' own floor — the plugin only ever runs inside a papis environment.
- No `docs/`, `examples/`, or publish workflow: this is a single-module plugin expected to be superseded upstream.
- Licensed GPL-3.0-or-later rather than MIT, because it imports and subclasses papis, which is GPL-3.0-or-later.
- An extra `papis-versions` CI job, for the private-API reason above.
