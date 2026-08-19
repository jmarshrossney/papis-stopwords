import pytest
from papis.format import FormatFailedError

from papis_stopwords import StopwordFormatter

DOC = {
    "author_list": [{"family": "Del Debbio", "given": "Luigi"}],
    "year": "2021",
    "title": "Efficient Modeling of Trivializing Maps for Lattice Theory",
    "short": "On Growth",
}


@pytest.fixture
def fmt():
    return StopwordFormatter()


def test_n_flag_drops_stopwords_before_slicing(fmt):
    assert fmt.format("{doc[title]:0.3NS}", DOC) == "Efficient Modeling Trivializing"


def test_plain_s_is_unchanged(fmt):
    assert fmt.format("{doc[title]:0.3S}", DOC) == "Efficient Modeling of"


def test_slice_start_is_honoured(fmt):
    assert fmt.format("{doc[title]:1.3NS}", DOC) == "Modeling Trivializing"


def test_conversion_still_composes(fmt):
    assert fmt.format("{doc[short]!t:0.2NS}", DOC) == "Growth"


def test_stopwords_are_matched_case_insensitively(fmt):
    assert fmt.format("{doc[short]:0.2NS}", DOC) == "Growth"


def test_slice_beyond_the_end_is_not_padded(fmt):
    assert fmt.format("{doc[short]:0.3NS}", DOC) == "Growth"


def test_ordinary_format_specs_are_untouched(fmt):
    assert fmt.format("{doc[title]:.9}", DOC) == "Efficient"


def test_ref_format_pattern(fmt):
    pattern = (
        "{doc[author_list][0][family]}{doc[year]}"
        "_{doc[title]!t:0.1NS}_{doc[title]!t:1.2NS}_{doc[title]!t:2.3NS}"
    )
    assert fmt.format(pattern, DOC) == (
        "Del Debbio2021_Efficient_Modeling_Trivializing"
    )


def test_non_string_field_is_rejected(fmt):
    with pytest.raises(FormatFailedError, match=r"author_list"):
        fmt.format("{doc[author_list]:0.2NS}", DOC)


SHORT = {
    "author_list": [{"family": "LeCun", "given": "Yann"}],
    "year": "2015",
    "title": "Deep Learning",
}


def test_separator_joins_selected_words(fmt):
    assert fmt.format("{doc[title]:0.3'-'S}", DOC) == "Efficient-Modeling-of"


def test_separator_combines_with_stopwords(fmt):
    assert fmt.format("{doc[title]:0.3N'-'S}", DOC) == "Efficient-Modeling-Trivializing"


def test_double_quoted_separator(fmt):
    assert fmt.format('{doc[title]:0.2N"-"S}', DOC) == "Efficient-Modeling"


def test_empty_separator(fmt):
    assert fmt.format("{doc[title]:0.2N''S}", DOC) == "EfficientModeling"


def test_multi_character_separator(fmt):
    assert fmt.format("{doc[title]:0.2N'::'S}", DOC) == "Efficient::Modeling"


def test_no_trailing_separator_when_field_is_short(fmt):
    """The whole point: a short title must not leave a dangling separator."""
    assert fmt.format("{doc[title]!t:0.3N'-'S}", SHORT) == "Deep-Learning"


def test_short_title_ref_has_no_trailing_underscore(fmt):
    pattern = "{doc[author_list][0][family]}{doc[year]}\\_{doc[title]!t:0.3N'\\_'S}"
    import papis.bibtex

    assert (
        papis.bibtex.ref_cleanup(fmt.format(pattern, SHORT), ref_word_separator="")
        == "LeCun2015_Deep_Learning"
    )


def test_apostrophes_survive_as_before(fmt):
    import papis.bibtex

    doc = {
        **SHORT,
        "title": "On Ising's Model of Ferromagnetism",
        "author_list": [{"family": "Peierls", "given": "Rudolf"}],
        "year": "1936",
    }
    pattern = "{doc[author_list][0][family]}{doc[year]}\\_{doc[title]!t:0.3N'\\_'S}"
    assert (
        papis.bibtex.ref_cleanup(fmt.format(pattern, doc), ref_word_separator="")
        == "Peierls1936_IsingS_Model_Ferromagnetism"
    )


def test_unterminated_separator_is_rejected(fmt):
    with pytest.raises(FormatFailedError, match=r"0\.2N'-S"):
        fmt.format("{doc[title]:0.2N'-S}", DOC)


def test_private_papis_api_is_still_present():
    """Canary: the plugin subclasses private papis API deliberately.

    If this fails, papis has moved the class and the plugin needs updating
    before the papis upper bound in pyproject.toml is raised.
    """
    from papis.format.python import PythonFormatter, _PythonStringFormatter

    assert issubclass(StopwordFormatter, PythonFormatter)
    assert isinstance(StopwordFormatter.psf, _PythonStringFormatter)
    assert StopwordFormatter.name == "stopwords"


def test_version_matches_pyproject() -> None:
    """The installed metadata agrees with pyproject.toml.

    ``__version__`` is derived from the installed distribution, so this catches
    a stale editable install -- which is how the version came to be reported as
    0.2.0 while pyproject.toml still said 0.1.0.

    pyproject.toml is read with a regex rather than ``tomllib`` because the
    package supports Python 3.10, where ``tomllib`` is not in the standard
    library and pulling in ``tomli`` for one assertion is not worth it.
    """
    import re
    from pathlib import Path

    import papis_stopwords

    pyproject = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    match = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
    assert match is not None, "no version found in pyproject.toml"
    assert papis_stopwords.__version__ == match.group(1)
