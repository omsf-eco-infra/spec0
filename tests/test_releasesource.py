import pytest
import responses
import warnings
import datetime
import os
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


MOCK_REPODATA = {
    "packages": {
        "mypackage-2.2.0-0.tar.bz2": {
            "name": "mypackage",
            "version": "2.2.0",
            # 2023-03-03T12:00:00Z => 1677844800000 ms epoch
            "timestamp": 1677844800000,
        },
        "mypackage-2.1.0-0.tar.bz2": {
            "name": "mypackage",
            "version": "2.1.0",
            # 2023-02-10T09:00:00Z => 1676019600000 ms epoch
            "timestamp": 1676019600000,
        },
        "mypackage-1.9.0-0.tar.bz2": {
            "name": "mypackage",
            "version": "1.9.0",
            # 2023-01-15T20:00:00Z => 1673812800000 ms epoch
            "timestamp": 1673812800000,
        },
    },
}


class TestCondaReleaseSource:
    @responses.activate
    def test_valid_only_versions(self):
        """
        Test that when repodata contains only valid versions, we get them
        in descending release_date order, with no warnings.
        """
        url = "https://conda.anaconda.org/mock-channel/mock-platform/repodata.json"
        responses.add(
            method=responses.GET,
            url=url,
            json=MOCK_REPODATA,
            status=200,
        )

        # Instantiate the source. It will download the mocked repodata.
        source = CondaReleaseSource(["mock-channel/mock-platform"])
        releases = list(source._get_releases("mypackage"))

        # We should have 3 releases
        assert len(releases) == 3

        # Check versions
        versions = [r.version for r in releases]
        assert versions == [
            Version("2.2.0"),
            Version("2.1.0"),
            Version("1.9.0"),
        ]

        # Check release dates
        release_dates = [r.release_date for r in releases]
        assert_is_descending(release_dates)
        assert release_dates == [
            datetime.datetime(2023, 3, 3, 12, 0, tzinfo=datetime.timezone.utc),
            datetime.datetime(2023, 2, 10, 9, 0, tzinfo=datetime.timezone.utc),
            datetime.datetime(2023, 1, 15, 20, 0, tzinfo=datetime.timezone.utc),
        ]

    @pytest.mark.parametrize("package_name", ["python", "numpy", "scipy"])
    @requires_internet
    def test_integration_releases(self, package_name):
        """
        Integration test using real data from conda-forge for the given package.
        Checks:
          1) We get at least one release.
          2) The release dates are in descending order.
        """
        source = CondaReleaseSource(["conda-forge/linux-64"])
        releases = list(source._get_releases(package_name))

        assert len(releases) > 0

        dates = [r.release_date for r in releases if r.release_date is not None]
        assert_is_descending(dates)


MOCK_GH_RESPONSE_VALID_ONLY = {
    "data": {
        "repository": {
            "releases": {
                "pageInfo": {"endCursor": None, "hasNextPage": False},
                "nodes": [
                    {"tagName": "2.2.0", "createdAt": "2023-03-03T12:00:00Z"},
                    {"tagName": "2.1.0", "createdAt": "2023-02-10T09:00:00Z"},
                    {"tagName": "1.9.0", "createdAt": "2023-01-15T20:00:00Z"},
                ],
            }
        }
    }
}

MOCK_GH_RESPONSE_MIXED = {
    "data": {
        "repository": {
            "releases": {
                "pageInfo": {"endCursor": None, "hasNextPage": False},
                "nodes": [
                    {"tagName": "10.0.0", "createdAt": "2024-01-01T12:00:00Z"},
                    {
                        "tagName": "not-a-valid-version",
                        "createdAt": "2024-01-02T12:00:00Z",
                    },
                    {"tagName": "9.9.9", "createdAt": "2023-12-15T12:00:00Z"},
                ],
            }
        }
    }
}

MOCK_GH_RESPONSE_PAGE1 = {
    "data": {
        "repository": {
            "releases": {
                "pageInfo": {"endCursor": "CURSOR1", "hasNextPage": True},
                "nodes": [
                    {"tagName": "3.0.0", "createdAt": "2024-01-05T12:00:00Z"},
                    {"tagName": "2.5.0", "createdAt": "2023-12-20T12:00:00Z"},
                ],
            }
        }
    }
}

MOCK_GH_RESPONSE_PAGE2 = {
    "data": {
        "repository": {
            "releases": {
                "pageInfo": {"endCursor": None, "hasNextPage": False},
                "nodes": [
                    {"tagName": "2.2.0", "createdAt": "2023-11-10T12:00:00Z"},
                    {"tagName": "2.0.0", "createdAt": "2023-10-01T12:00:00Z"},
                ],
            }
        }
    }
}


class TestGitHubReleaseSource:
    @responses.activate
    def test_valid_only_versions(self):
        """Test that valid versions are parsed and returned in descending order."""
        url = "https://api.github.com/graphql"
        responses.add(
            responses.POST,
            url,
            json=MOCK_GH_RESPONSE_VALID_ONLY,
            status=200,
        )

        token = "FAKE_TOKEN"
        source = GitHubReleaseSource(token)
        releases = list(source._get_releases("octocat/Hello-World"))

        # Verify the number of releases.
        assert len(releases) == 3

        # Check that the versions are correctly parsed.
        versions = [r.version for r in releases]
        assert versions == [Version("2.2.0"), Version("2.1.0"), Version("1.9.0")]

        # Verify that the release dates are in descending order.
        release_dates = [r.release_date for r in releases]
        assert_is_descending(release_dates)
        assert release_dates == [
            datetime.datetime(2023, 3, 3, 12, 0, tzinfo=datetime.timezone.utc),
            datetime.datetime(2023, 2, 10, 9, 0, tzinfo=datetime.timezone.utc),
            datetime.datetime(2023, 1, 15, 20, 0, tzinfo=datetime.timezone.utc),
        ]

    @responses.activate
    def test_mixed_versions_warning(self):
        """Test that invalid version strings trigger a warning and are skipped."""
        url = "https://api.github.com/graphql"
        responses.add(
            responses.POST,
            url,
            json=MOCK_GH_RESPONSE_MIXED,
            status=200,
        )

        token = "FAKE_TOKEN"
        with pytest.warns(UserWarning, match="Skipping invalid version"):
            warnings.simplefilter("always")
            source = GitHubReleaseSource(token)
            releases = list(source._get_releases("octocat/Hello-World"))

        # Only the valid versions should be returned.
        assert len(releases) == 2
        versions = [r.version for r in releases]
        assert versions == [Version("10.0.0"), Version("9.9.9")]

        release_dates = [r.release_date for r in releases]
        assert_is_descending(release_dates)
        assert release_dates == [
            datetime.datetime(2024, 1, 1, 12, 0, tzinfo=datetime.timezone.utc),
            datetime.datetime(2023, 12, 15, 12, 0, tzinfo=datetime.timezone.utc),
        ]

    @responses.activate
    def test_pagination(self):
        """
        Test that pagination is handled correctly by returning all releases from
        multiple pages in the proper order.
        """
        url = "https://api.github.com/graphql"
        # Simulate two paginated responses.
        responses.add(
            responses.POST,
            url,
            json=MOCK_GH_RESPONSE_PAGE1,
            status=200,
        )
        responses.add(
            responses.POST,
            url,
            json=MOCK_GH_RESPONSE_PAGE2,
            status=200,
        )

        token = "FAKE_TOKEN"
        source = GitHubReleaseSource(token)
        releases = list(source._get_releases("octocat/Hello-World"))

        # We expect 4 releases total.
        assert len(releases) == 4

        # Check the expected version order.
        expected_versions = [
            Version("3.0.0"),
            Version("2.5.0"),
            Version("2.2.0"),
            Version("2.0.0"),
        ]
        versions = [r.version for r in releases]
        assert versions == expected_versions

        # Verify that the release dates are in descending order.
        release_dates = [r.release_date for r in releases]
        assert_is_descending(release_dates)

    @pytest.mark.skipif(
        not os.environ.get("GITHUB_TOKEN"), reason="GITHUB_TOKEN not set"
    )
    def test_integration_openpathsampling(self):
        """
        Integration test using the real GitHub API to fetch releases for the
        repository openpathsampling/openpathsampling. Checks that at least one
        release is returned and that the releases are in descending order.
        """
        token = os.environ["GITHUB_TOKEN"]
        source = GitHubReleaseSource(token)
        releases = list(source._get_releases("openpathsampling/openpathsampling"))
        assert len(releases) > 0
        release_dates = [r.release_date for r in releases]
        assert_is_descending(release_dates)
