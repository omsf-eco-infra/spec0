import dataclasses
import datetime
import requests
import warnings
from packaging.version import Version, InvalidVersion


@dataclasses.dataclass
class Release:
    version: Version
    release_date: datetime.datetime


class ReleaseSource:
    def _get_releases(self, package: str) -> list[Release]:
        raise NotImplementedError

    def get_releases(self, package: str) -> list[Release]:
        yield from self._get_releases(package)


class PyPIReleaseSource(ReleaseSource):
    def _get_releases(self, package: str) -> list[Release]:
        url = f"https://pypi.org/pypi/{package}/json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        releases_data = data.get("releases", {})
        release_list = []

        for version_str, files in releases_data.items():
            # Attempt to parse the version string
            try:
                parsed_version = Version(version_str)
            except InvalidVersion:
                warnings.warn(
                    f"Skipping invalid version '{version_str}' for package '{package}'."
                )
                continue

            # Determine earliest upload time among all distributions for that version
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

        # Sort releases by date descending (newest first)
        release_list.sort(key=lambda r: r.release_date, reverse=True)

        # Yield them in sorted order
        for release in release_list:
            yield release


class GitHubReleaseSource(ReleaseSource):
    def _get_releases(self, package: str) -> list[Release]:
        ...


class GitHubTagReleaseSource(ReleaseSource):
    def _get_releases(self, package: str) -> list[Release]:
        ...


class CondaReleaseSource(ReleaseSource):
    def __init__(self, channel_platforms: list[str] = None):
        self.platforms = platforms or ["conda-forge/linux-64", "conda-forge/noarch"]

    def get_releases(self, package: str) -> list[Release]:
        ...


class DefaultReleaseSource(ReleaseSource):
    def _try_release_source(self, source: ReleaseSource, package: str):
        try:
            return source.get_releases(package)
        except:
            return None

    def get_releases(self, package: str) -> list[Release]:
        sources = [
            PyPIReleaseSource(),
            GitHubReleaseSource(),
            GitHubTagReleaseSource(),
            CondaForgeReleaseSource(),
        ]
        for source in sources:
            releases = self._try_release_source(source, package)
            if releases:
                return releases

        raise ValueError(f"Failed to get releases for {package}")
