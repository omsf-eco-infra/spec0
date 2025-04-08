import datetime
from collections import defaultdict
from typing import Iterable

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from .releasesource import Release
from .utils.dates import next_quarter, quarter_to_date, shift_date_by_months

import logging

_logger = logging.getLogger(__name__)


class ReleaseFilter:
    def filter(self, package, releases): ...


def get_oldest_minor_release(releases: Iterable[Release]):
    """Get the oldest release for each minor release version."""
    oldest_minor_release = defaultdict(
        lambda: Release(
            version=None,
            release_date=datetime.datetime.max.replace(tzinfo=datetime.timezone.utc),
        )
    )

    for release in releases:
        if not release.version.is_prerelease:
            key = (release.version.epoch, release.version.major, release.version.minor)
            if release.release_date < oldest_minor_release[key].release_date:
                oldest_minor_release[key] = release

    return oldest_minor_release


def make_specifier(supported_minor_releases, include_upper_bound=True):
    """Create a specifier that includes all supported minor releases."""
    min_version = min(
        Version(f"{epoch}!{major}.{minor}")
        for epoch, major, minor in supported_minor_releases.keys()
    )
    spec = SpecifierSet(f">={min_version}")
    if include_upper_bound:
        upper_bound = max(
            Version(f"{epoch}!{major + 1}")
            for epoch, major, minor in supported_minor_releases.keys()
        )
        spec &= SpecifierSet(f"<{upper_bound}")
    return spec


class SPEC0(ReleaseFilter):
    """Filter using SPEC0 rules (time-only)"""

    def __init__(self, n_months=24, python_override=True):
        self.n_months = n_months
        self.python_override = python_override

    def _get_n_months(self, package: str):
        if package == "python" and self.python_override:
            return 36
        return self.n_months

    def _get_minimum_supported(self, package: str, releases: Iterable[Release]):
        oldest_minor_release = get_oldest_minor_release(releases)

        max_minor_release = max(oldest_minor_release)
        # always support at least the most recent minor release
        supported = {max_minor_release: oldest_minor_release[max_minor_release]}

        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

        for key, release in oldest_minor_release.items():
            drop_date = self.drop_date(package, release)
            if now < drop_date:
                _logger.debug(
                    f"Supporting {key} until {drop_date}, release date: "
                    f"{release.release_date}"
                )
                supported[key] = release

        return supported

    def drop_date(self, package, release):
        raise NotImplementedError()

    def filter(self, package, releases):
        return self._get_minimum_supported(package, releases)


class SPEC0StrictDate(SPEC0):
    def drop_date(self, package, release):
        n_months = self._get_n_months(package)
        return shift_date_by_months(release.release_date, n_months)


class SPEC0Quarter(SPEC0):
    def drop_date(self, package, release):
        n_months = self._get_n_months(package)
        naive_drop = shift_date_by_months(release.release_date, n_months)
        drop = quarter_to_date(next_quarter(naive_drop))
        return drop
