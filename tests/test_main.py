import datetime
import pytest
from packaging.version import Version

from spec0.releasesource import PyPIReleaseSource, CondaReleaseSource, Release
from spec0.releasefilters import SPEC0StrictDate

from spec0.main import *
from spec0.main import _major_minor_str


class DummySource:
    """
    A dummy source that implements get_releases.
    It returns a dictionary of releases if provided,
    otherwise returns None.
    """

    def __init__(self, releases):
        self._releases = releases

    def get_releases(self, package):
        return self._releases


class DummyFilter:
    """
    A dummy filter that simply passes through releases.
    Its drop_date method returns a fixed date.
    """

    def filter(self, package, releases):
        return releases

    def drop_date(self, package, release):
        return datetime.datetime(2021, 1, 1)


def test_default_sources():
    sources = default_sources()
    assert isinstance(sources, list)
    assert len(sources) == 2

    assert isinstance(sources[0], PyPIReleaseSource)
    assert isinstance(sources[1], CondaReleaseSource)


def test_default_filter():
    filter_obj = default_filter()
    assert isinstance(filter_obj, SPEC0StrictDate)
    assert filter_obj.n_months == 24
    assert filter_obj.python_override is True


@pytest.mark.parametrize(
    "version_str,expected",
    [
        ("1.2", "1.2"),  # For "1.2", epoch is 0, so just "major.minor"
        ("1!1.2", "1!1.2"),  # For "1!1.2", non-zero epoch is included
        ("0.3.4", "0.3"),  # For "0.3.4", only major and minor are used
    ],
)
def test_major_minor_str(version_str, expected):
    v = Version(version_str)
    result = _major_minor_str(v)
    assert result == expected


def test_main_uses_first_source_with_releases():
    v = Version("1.0")
    release_date = datetime.datetime(2020, 1, 1)
    dummy_release = Release(v, release_date)

    # The first source returns a valid releases dict.
    # The second source should not be used.
    source1 = DummySource({"r1": dummy_release})
    v2 = Version("2.0")
    source2 = DummySource({"r2": Release(v2, datetime.datetime(2020, 2, 2))})

    filter_obj = DummyFilter()
    result = main("testpkg", sources=[source1, source2], filter_=filter_obj)

    assert result["package"] == "testpkg"
    assert isinstance(result["releases"], list)
    assert len(result["releases"]) == 1
    release_info = result["releases"][0]
    assert release_info["version"] == v
    assert release_info["release-date"] == release_date
    assert release_info["drop-date"] == datetime.datetime(2021, 1, 1)


def test_main_uses_second_source_when_first_returns_none():
    v = Version("1.0")
    release_date = datetime.datetime(2020, 1, 1)
    dummy_release = Release(v, release_date)

    source1 = DummySource(None)
    source2 = DummySource({"r1": dummy_release})

    filter_obj = DummyFilter()
    result = main("testpkg", sources=[source1, source2], filter_=filter_obj)

    assert result["package"] == "testpkg"
    assert isinstance(result["releases"], list)
    assert len(result["releases"]) == 1


@pytest.mark.parametrize("release_date", [True, False])
@pytest.mark.parametrize("drop_date", [True, False])
def test_terminal_output_combined(capsys, release_date, drop_date):
    pkg_info = {
        "package": "mypackage",
        "releases": [
            {
                "version": Version("1.0"),
                "release-date": datetime.datetime(2020, 1, 1),
                "drop-date": datetime.datetime(2021, 1, 1),
            },
            {
                "version": Version("1!2.3"),
                "release-date": datetime.datetime(2020, 2, 2),
                "drop-date": datetime.datetime(2021, 2, 2),
            },
        ],
    }

    terminal_output(pkg_info, release_date=release_date, drop_date=drop_date)
    captured = capsys.readouterr().out
    header_line, _, first_row, second_row = captured.splitlines()

    # Fixed assertions that are always expected.
    assert "Package" in header_line
    assert "mypackage 1.0" in first_row
    assert "mypackage 1!2.3" in second_row

    # Check header for release date and drop date based on flags.
    if release_date:
        assert "Release Date" in header_line
        assert "2020-01-01" in first_row
        assert "2020-02-02" in second_row
    else:
        assert "Release Date" not in header_line
        assert "2020-01-01" not in first_row
        assert "2020-02-02" not in second_row

    if drop_date:
        assert "Drop Date" in header_line
        assert "2021-01-01" in first_row
        assert "2021-02-02" in second_row
    else:
        assert "Drop Date" not in header_line
        assert "2021-01-01" not in first_row
        assert "2021-02-02" not in second_row
