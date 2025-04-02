import datetime
from packaging.version import Version

from spec0.releasesource import PyPIReleaseSource, CondaReleaseSource, Release
from spec0.releasefilters import SPEC0StrictDate

from spec0.main import *


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
