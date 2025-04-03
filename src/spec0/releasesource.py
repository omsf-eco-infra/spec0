import dataclasses
import datetime
import json
import requests
import warnings
from packaging.version import Version, InvalidVersion

from typing import Generator

from spec0.cacheddownload import get_file, CACHE_DIR


@dataclasses.dataclass
class Release:
    """A release of a package."""

    version: Version
    release_date: datetime.datetime


class ReleaseSource:
    """ABC for a source of package releases."""

    def _get_releases(self, package: str) -> Generator[Release, None, None]:
        raise NotImplementedError()

    def get_releases(self, package: str) -> Generator[Release, None, None]:
        yield from self._get_releases(package)


class PyPIReleaseSource(ReleaseSource):
    """A source of package releases from PyPI.

    Typically, you only need one instance of this class.
    """

    def _get_releases(self, package: str) -> Generator[Release, None, None]:
        url = f"https://pypi.org/pypi/{package}/json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        releases_data = data.get("releases", {})
        release_list = []

        for version_str, files in releases_data.items():
            try:
                parsed_version = Version(version_str)
            except InvalidVersion:
                warnings.warn(
                    f"Skipping invalid version '{version_str}' for package '{package}'."
                )
                continue

            earliest_date = None
            for file_info in files:
                upload_time_str = file_info.get("upload_time_iso_8601")
                if upload_time_str:
                    dt = datetime.datetime.fromisoformat(
                        upload_time_str.replace("Z", "+00:00")
                    )
                    if earliest_date is None or dt < earliest_date:
                        earliest_date = dt

            # Only add to list if we successfully found an upload date
            if earliest_date is not None:
                release_list.append(
                    Release(version=parsed_version, release_date=earliest_date)
                )

        release_list.sort(key=lambda r: r.release_date, reverse=True)
        for release in release_list:
            yield release


class GitHubReleaseSource(ReleaseSource):
    """
    Class to fetch all GitHub releases for a given repository using the GitHub GraphQL API.

    Parameters
    ----------
    github_token : str
        Personal access token (PAT) with permissions to query the desired repository.
    """

    def __init__(self, github_token: str):
        self.github_token = github_token

    def _get_releases(self, owner_repo: str):
        """
        Generate all releases for a repository in descending order of
        creation date (most recent first).

        Parameters
        ----------
        owner_repo : str
            A string in the format "owner/repo" that identifies the repository.

        Yields
        ------
        Release
            A `Release` object containing:
            - `version` (packaging.version.Version)
            - `release_date` (datetime.datetime)

        Warns
        -----
        UserWarning
            When `tagName` from GitHub cannot be parsed as a valid version.
        """
        owner, repo = owner_repo.split("/", 1)

        query = """
        query($owner: String!, $repo: String!, $after: String) {
          repository(owner: $owner, name: $repo) {
            releases(first: 100, after: $after, orderBy: {field: CREATED_AT, direction: DESC}) {
              pageInfo {
                endCursor
                hasNextPage
              }
              nodes {
                tagName
                createdAt
              }
            }
          }
        }
        """

        url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        has_next_page = True
        after_cursor = None

        while has_next_page:
            variables = {
                "owner": owner,
                "repo": repo,
                "after": after_cursor,
            }
            response = requests.post(
                url, json={"query": query, "variables": variables}, headers=headers
            )
            response.raise_for_status()

            data = response.json()
            releases_data = data["data"]["repository"]["releases"]

            for node in releases_data["nodes"]:
                tag_name = node["tagName"]
                try:
                    version = Version(tag_name)
                except InvalidVersion:
                    warnings.warn(f"Skipping invalid version: {tag_name}", UserWarning)
                    continue  # Skip this release

                release_date = datetime.datetime.fromisoformat(
                    node["createdAt"].replace("Z", "+00:00")
                )
                yield Release(version, release_date)

            has_next_page = releases_data["pageInfo"]["hasNextPage"]
            after_cursor = releases_data["pageInfo"]["endCursor"]


class CondaReleaseSource(ReleaseSource):
    """

    Parameters
    ----------
    channel_platforms : list[str]
        A list of strings of the form "channel/platform", e.g.,
        "conda-forge/linux-64".
    """

    def __init__(self, channel_platforms: list[str]):
        # TODO: determine if can use the bz2 instead
        self._repodata = {"packages": {}, "packages.conda": {}}

        for channel_platform in channel_platforms:
            channel, platform = channel_platform.split("/", 1)
            url = f"https://conda.anaconda.org/{channel}/{platform}/repodata.json"
            cachefile = CACHE_DIR / channel_platform / "repodata.json"
            cachefile = get_file(url, cachefile)
            with open(cachefile, "r") as f:
                data = json.load(f)

            # Merge packages
            for pkg_name, pkg_info in data.get("packages", {}).items():
                self._repodata["packages"][pkg_name] = pkg_info
            for pkg_name, pkg_info in data.get("packages.conda", {}).items():
                self._repodata["packages.conda"][pkg_name] = pkg_info

    def _get_releases(self, package):
        # Combine "packages" and "packages.conda" if present
        package_entries = self._repodata.get("packages", {})
        packages_conda_entries = self._repodata.get("packages.conda", {})
        all_packages = {**package_entries, **packages_conda_entries}

        releases = []
        for pkg_key, pkg_info in all_packages.items():
            if pkg_info.get("name") == package:
                version_str = pkg_info["version"]

                # The conda timestamp is in milliseconds since epoch
                timestamp = pkg_info.get("timestamp")
                if timestamp is not None:
                    release_date = datetime.datetime.fromtimestamp(
                        timestamp / 1000, datetime.timezone.utc
                    )
                else:
                    # warnings.warn(f"No release date for {pkg_key}")
                    release_date = None

                if release_date is not None:
                    releases.append(
                        Release(version=Version(version_str), release_date=release_date)
                    )

        # Sort in descending order by release_date (None dates go last)
        releases.sort(
            key=lambda r: (r.release_date is None, r.release_date), reverse=True
        )

        for release_obj in releases:
            yield release_obj
