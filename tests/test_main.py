import datetime
from packaging.version import Version

from spec0.releasesource import Release, DefaultReleaseSource
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


def test_default_filter():
    filter_obj = default_filter()
    assert isinstance(filter_obj, SPEC0StrictDate)
    assert filter_obj.n_months == 24
    assert filter_obj.python_override is True


def test_main():
    v = Version("1.0")
    release_date = datetime.datetime(2020, 1, 1)
    dummy_release = Release(v, release_date)
    source = DummySource({"r1": dummy_release})
    filter_obj = DummyFilter()
    result = main("testpkg", source=source, filter_=filter_obj)
    assert result["package"] == "testpkg"
    assert isinstance(result["releases"], list)
    assert len(result["releases"]) == 1
    release_info = result["releases"][0]
    assert release_info["version"] == v
    assert release_info["release-date"] == release_date
    assert release_info["drop-date"] == datetime.datetime(2021, 1, 1)


def test_main_integration():
    # smoke test for integration with default params
    source = DefaultReleaseSource()
    results = main("numpy", source)
    assert results["package"] == "numpy"
    assert len(results["releases"]) > 0
    recent_release = results["releases"][0]
    assert isinstance(recent_release["version"], Version)
    assert isinstance(recent_release["release-date"], datetime.datetime)
    assert isinstance(recent_release["drop-date"], datetime.datetime)
