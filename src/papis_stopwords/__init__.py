"""A papis formatter that extends the ``python`` formatter's word slice.

This is a strict superset of the built-in ``python`` formatter: every pattern
that works there works here unchanged. It adds two things to the existing
``S`` (word-slice) format spec:

``N``
    Filter stopwords out of the field *before* the slice is taken. Given the
    title "On the theory of Brownian motion", ``:0.3S`` yields "On The Theory"
    whereas ``:0.3NS`` yields "Theory Brownian Motion". The word list comes
    from the ``format-stopwords`` configuration setting; setting it to an
    empty list makes the flag a no-op.

``'sep'``
    Join the selected words with *sep* rather than a single space, e.g.
    ``:0.3'-'S``. Because the separator is applied only *between* the words
    that survive, a field with fewer words than the slice asks for produces no
    trailing separator -- which a format pattern built from several
    single-word slices cannot avoid.

Both are optional and may be combined, in the order ``[start][.end][N]['sep']S``.
"""

from __future__ import annotations

from typing import Any, ClassVar

import papis.config
from papis.format.python import PythonFormatter, _PythonStringFormatter

__version__ = "0.2.0"

__all__ = ["DEFAULT_STOPWORDS", "StopwordFormatter"]

#: Words dropped from a field when the ``N`` flag is used. Deliberately
#: restricted to English function words that carry no bibliographic
#: information, so that the remaining words are the distinguishing ones.
DEFAULT_STOPWORDS = [
    "a",
    "an",
    "and",
    "as",
    "at",
    "but",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "via",
    "with",
    "within",
]

#: Punctuation stripped from a word before it is compared against the
#: stopword list, so that "of:" before a subtitle matches "of".
_PUNCTUATION = ":,.;!?()[]{}\"'"

papis.config.register_default_settings(
    {"settings": {"format-stopwords": DEFAULT_STOPWORDS}}
)


def _get_stopwords() -> frozenset[str]:
    return frozenset(w.lower() for w in papis.config.getlist("format-stopwords"))


def _is_stopword(word: str, stopwords: frozenset[str]) -> bool:
    return word.lower().strip(_PUNCTUATION) in stopwords


def _parse_slice_spec(body: str) -> tuple[int, int, bool, str]:
    """Parse the part of an ``S`` format spec preceding the ``S``.

    :returns: the slice bounds, whether to drop stopwords, and the separator
        used to join the selected words.
    """
    separator = " "
    if body and body[-1] in "'\"":
        quote = body[-1]
        start = body.rfind(quote, 0, -1)
        if start == -1:
            raise ValueError(f"Unterminated separator in format specifier '{body}S'")
        separator = body[start + 1 : -1]
        body = body[:start]

    drop_stopwords = bool(body) and body[-1] == "N"
    if drop_stopwords:
        body = body[:-1]

    try:
        if "." in body:
            istart, iend = body.split(".")
            istart = istart if istart else "0"
        else:
            istart, iend = "0", body

        return int(istart), int(iend), drop_stopwords, separator
    except ValueError:
        raise ValueError(f"Invalid format specifier '{body}S'") from None


class _StopwordStringFormatter(_PythonStringFormatter):
    def format_field(self, value: Any, format_spec: str) -> Any:
        if not format_spec or format_spec[-1] != "S":
            return super().format_field(value, format_spec)

        body = format_spec[:-1]

        # NOTE: defer to the built-in formatter unless one of the additions is
        # actually used, so that every existing pattern keeps its behaviour.
        if not body or (body[-1] not in "N'\""):
            return super().format_field(value, format_spec)

        istart, iend, drop_stopwords, separator = _parse_slice_spec(body)

        if not isinstance(value, str):
            raise ValueError(
                f"Unknown format code 'S' for type '{type(value).__name__}'"
            )

        words = [word for word in value.split(" ") if word]
        if drop_stopwords:
            stopwords = _get_stopwords()
            words = [word for word in words if not _is_stopword(word, stopwords)]

        return separator.join(words[istart:iend])


class StopwordFormatter(PythonFormatter):
    """The ``python`` formatter, extended with stopword and separator options.

    This formatter is named ``"stopwords"`` and can be selected with the
    :confval:`formatter` setting::

        [settings]
        formatter = stopwords
    """

    name: ClassVar[str] = "stopwords"
    psf = _StopwordStringFormatter()
