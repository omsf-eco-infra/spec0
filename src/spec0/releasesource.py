import dataclasses
import datetime
import requests
import warnings
from packaging.version import Version, InvalidVersion

from typing import Generator


@dataclasses.dataclass
class Release:
    """A release of a package."""

    version: Version
    release_date: datetime.datetime


class ReleaseSource:
    """ABC for a source of package releases."""

    def _get_releases(self, package: str) -> Generator[Release]:
        raise NotImplementedError()

    def get_releases(self, package: str) -> Generator[Release]:
        yield from self._get_releases(package)


class PyPIReleaseSource(ReleaseSource):
    """A source of package releases from PyPI.

    Typically, you only need one instance of this class.
    """

    def _get_releases(self, package: str) -> Generator[Release]:
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
    def _get_releases(self, package: str) -> Generator[Release]: ...


class GitHubTagReleaseSource(ReleaseSource):
    def _get_releases(self, package: str) -> Generator[Release]: ...


class CondaReleaseSource(ReleaseSource):
    """

    Parameters
    ----------
    channel_platforms : list[str]
        A list of strings of the form "channel/platform", e.g.,
        "conda-forge/linux-64".
    """

    def __init__(self, channel_platforms: list[str]):
        # TODO: we should handle caching of the repodata (and maybe get it
        # as bz2?)
        self._repodata = {"packages": {}, "packages.conda": {}}

        for channel_platform in channel_platforms:
            channel, platform = channel_platform.split("/", 1)
            url = f"https://conda.anaconda.org/{channel}/{platform}/repodata.json"
            resp = requests.get(url)
            resp.raise_for_status()

            data = resp.json()
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
                    warnings.warn(f"No release date for {pkg_key}")
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


class DefaultReleaseSource(ReleaseSource):
    def _try_release_source(self, source: ReleaseSource, package: str):
        try:
            return source.get_releases(package)
        except:
            return None

    def get_releases(self, package: str) -> Generator[Release]:
        sources = [
            PyPIReleaseSource(),
            GitHubReleaseSource(),
            GitHubTagReleaseSource(),
            CondaForgeReleaseSource(),
        ]
        for source in sources:
            releases = self._try_release_source(source, package)
            if releases:
                yield from releases

        raise ValueError(f"Failed to get releases for {package}")
