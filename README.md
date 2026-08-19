> [!IMPORTANT]
> This is a 100% vibe-coded plugin (Claude Opus 5 through Claude Code, Aug 2026) intended for personal use. My intention is to test it myself for a while, discover any issues, and then submit a PR to papis itself with human-verified code.

# papis-stopwords

A [papis](https://github.com/papis/papis) formatter plugin that can drop stopwords before slicing words out of a field.

It is a strict superset of the built-in `python` formatter: every pattern that works there works here unchanged.
It adds two options to the existing `S` word-slice spec, in the order `[start][.end][N]['sep']S`:

- **`N`** filters stopwords out of the field *before* the slice is taken.
- **`'sep'`** joins the selected words with `sep` instead of a single space.

> [!WARNING] This plugin subclasses `papis.format.python._PythonStringFormatter`, which is private API.
> That is deliberate — it is what makes the plugin a strict superset of the built-in formatter rather than a reimplementation — but it means a papis release can break it without warning.
> Tested against papis 0.15.0 and 0.16.0.


## Why

papis builds citation keys with `ref-format`.
Taking the first three words of a title is a reliable way to disambiguate authors who publish several papers a year, but those words are frequently useless:

| Title | `:0.3S` | `:0.3NS` |
| --- | --- | --- |
| On the theory of Brownian motion | `On The Theory` | `Theory Brownian Motion` |
| Attention is all you need | `Attention Is All` | `Attention All You` |

The separator exists because building a key from three single-word slices glued together in the pattern — `{doc[title]:0.1S}\_{doc[title]:1.2S}\_{doc[title]:2.3S}` — leaves a dangling separator whenever the title has fewer words than the pattern has slots, giving `LeCun2015_Deep_Learning_`.
Joining inside a single slice removes the empty slot entirely, because the separator is only ever placed *between* words that exist.

## Install

Not published to PyPI; install from the repository:

```console
uv tool install papis --with git+https://github.com/jmarshrossney/papis-stopwords
```

`uv tool install` is declarative — it rebuilds the tool environment from exactly the requirements given on the command line.
If your papis install already has extras (`citeproc-py` for CSL output, say), repeat them in the same command or they will be
dropped:

```console
uv tool install papis --with citeproc-py \
  --with git+https://github.com/jmarshrossney/papis-stopwords
```

Then select it in `~/.config/papis/config`:

```ini
[settings]
formatter = stopwords
```

## Use

```ini
ref-word-separator =
ref-format = {doc[author_list][0][family]}{doc[year]}\_{doc[title]!t:0.3N'\_'S}
```

The word list comes from the `format-stopwords` setting, which defaults to a short list of English function words.
Override it in the `[settings]` section:

```ini
format-stopwords = ["a", "an", "and", "of", "the"]
```

Setting it to `[]` turns the `N` flag into a no-op without editing any format pattern.

## Compatibility

| papis | status |
| --- | --- |
| 0.15.0 | tested, 19/19 |
| 0.16.0 | tested, 19/19 — `_PythonStringFormatter.format_field` is byte-identical to 0.15 |

papis requires Python >= 3.10, and this plugin matches that floor rather than setting its own.

To run the suite against a specific papis release:

```console
just test-papis 0.16.0
```

## Development

```console
uv sync --group dev
just              # lint, typecheck, test
```

See `AGENTS.md` for the full recipe list and the design constraints behind the format spec.

## Notes

- The flag must live in the format spec rather than being a conversion like `!n`, because PEP 3101 permits only one conversion per replacement field — `{doc[title]!n!t:0.3S}` is a `ValueError`, and title-casing is needed too.
- Stopword matching is case-insensitive and ignores surrounding punctuation, so `On` and `of:` both match.
- The separator may be single- or double-quoted, and may be empty (`''`) or several characters long.
- `python-slugify` accepts a `stopwords=` argument and papis already calls it in `ref_cleanup`, but that route does not work here: it runs after truncation, it is case-sensitive when `lowercase=False`, and it splits on the separator, which is empty in a `ref-word-separator =` setup.
- The separators are backslash-escaped because `ref-word-separator =` (empty) is what collapses multi-word surnames and that also eats unescaped underscores; `papis.bibtex.ref_cleanup` exempts `\_`.
- Keeping the separator empty (rather than setting it to `_`) is deliberate: with `_` the apostrophe in `Ising's` becomes a separator too, giving `Ising_S_Model` instead of `IsingS_Model`.

