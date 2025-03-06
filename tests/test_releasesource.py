import pytest
import responses
import warnings
import datetime
from packaging.version import Version

from requires_internet import requires_internet

from spec0.releasesource import *

MOCK_RESPONSE_VALID_ONLY = {
    "releases": {
        "2.2.0": [{"upload_time_iso_8601": "2023-03-03T12:00:00Z"}],
        "2.1.0": [{"upload_time_iso_8601": "2023-02-10T09:00:00Z"}],
        "1.9.0": [{"upload_time_iso_8601": "2023-01-15T20:00:00Z"}],
    }
}

MOCK_RESPONSE_MIXED = {
    "releases": {
        "10.0.0": [{"upload_time_iso_8601": "2024-01-01T12:00:00Z"}],
        "not-a-valid-version": [{"upload_time_iso_8601": "2024-01-02T12:00:00Z"}],
        "9.9.9": [{"upload_time_iso_8601": "2023-12-15T12:00:00Z"}],
    }
}


def assert_is_descending(dates):
    """
    Assert that a list of datetimes is sorted in descending order.
    (i.e., each date is newer or the same as the next)
    """
    assert all(dates[i] >= dates[i + 1] for i in range(len(dates) - 1))


class TestPyPIReleaseSource:
    @responses.activate
    def test_valid_only_versions(self):
        url = "https://pypi.org/pypi/example-lib-valid/json"
        responses.add(
            method=responses.GET,
            url=url,
            json=MOCK_RESPONSE_VALID_ONLY,
            status=200,
        )

        source = PyPIReleaseSource()
        releases = list(source.get_releases("example-lib-valid"))

        assert len(releases) == 3
        versions = [r.version for r in releases]
        assert versions == [Version("2.2.0"), Version("2.1.0"), Version("1.9.0")]

        release_dates = [r.release_date for r in releases]
        assert_is_descending(release_dates)
        assert release_dates == [
            datetime.datetime(2023, 3, 3, 12, 0, tzinfo=datetime.timezone.utc),
            datetime.datetime(2023, 2, 10, 9, 0, tzinfo=datetime.timezone.utc),
            datetime.datetime(2023, 1, 15, 20, 0, tzinfo=datetime.timezone.utc),
        ]

    @responses.activate
    def test_mixed_versions_warning(self):
        url = "https://pypi.org/pypi/example-lib-mixed/json"
        responses.add(
            method=responses.GET,
            url=url,
            json=MOCK_RESPONSE_MIXED,
            status=200,
        )

        with pytest.warns(UserWarning, match="Skipping invalid version"):
            warnings.simplefilter("always")
            source = PyPIReleaseSource()
            releases = list(source.get_releases("example-lib-mixed"))

        assert len(releases) == 2
        versions = [r.version for r in releases]
        assert versions == [Version("10.0.0"), Version("9.9.9")]

        release_dates = [r.release_date for r in releases]
        assert_is_descending(release_dates)
        assert release_dates == [
            datetime.datetime(2024, 1, 1, 12, 0, tzinfo=datetime.timezone.utc),
            datetime.datetime(2023, 12, 15, 12, 0, tzinfo=datetime.timezone.utc),
        ]

    @pytest.mark.parametrize("package_name", ["pandas", "numpy", "scipy"])
    @requires_internet
    def test_integration_packages(self, package_name):
        """
        Integration test that calls the real PyPI API for the given package.
        Checks:
          1) We get at least one release.
          2) The release dates are in descending order.
        """
        source = PyPIReleaseSource()
        releases = list(source.get_releases(package_name))

        assert len(releases) > 0

        dates = [r.release_date for r in releases]
        assert_is_descending(dates)
